import os
from typing import Dict, List, Optional, Union
import json
from pathlib import Path
import fitz  # PyMuPDF for PDF files
import docx  # python-docx for DOCX files
from pydantic import BaseModel

from qwen_agent.tools.base import BaseTool, register_tool
from qwen_agent.utils.tokenization_qwen import count_tokens


class ESChunk(BaseModel):
    content: str
    metadata: dict
    token: int

    def __init__(self, content: str, metadata: dict, token: int):
        super().__init__(content=content, metadata=metadata, token=token)

    def to_dict(self) -> dict:
        return {'content': self.content, 'metadata': self.metadata, 'token': self.token}


class ESRecord(BaseModel):
    url: str
    raw: List[ESChunk]
    title: str

    def __init__(self, url: str, raw: List[ESChunk], title: str):
        super().__init__(url=url, raw=raw, title=title)

    def to_dict(self) -> dict:
        return {'url': self.url, 'raw': [x.to_dict() for x in self.raw], 'title': self.title}


@register_tool('es_retrieval')
class ESRetrievalTool(BaseTool):
    description = '使用Elasticsearch从给定文件列表中检索出和问题相关的内容，支持文件类型包括：txt, pdf, docx'
    parameters = [{
        'name': 'query',
        'type': 'string',
        'description': '需要在文档中检索的查询内容',
        'required': True
    }, {
        'name': 'files',
        'type': 'array',
        'items': {
            'type': 'string'
        },
        'description': '待解析的文件路径列表，支持本地文件路径。',
        'required': True
    }]

    def __init__(self, cfg: Optional[Dict] = None):
        super().__init__(cfg)
        # 从配置中获取ES连接信息，如果未提供则使用默认值
        self.es_host = self.cfg.get('es_host', 'localhost')
        self.es_port = self.cfg.get('es_port', 9200)
        self.es_username = self.cfg.get('es_username', 'elastic')
        self.es_password = self.cfg.get('es_password', '5A7C1+=PbQCpkw1jvu-8')
        
        # 初始化ES连接
        try:
            from elasticsearch import Elasticsearch
            es_url = f"http://{self.es_host}:{self.es_port}"
            self.es_client = Elasticsearch(es_url)
            
            # 测试连接
            if not self.es_client.ping():
                raise ConnectionError("无法连接到Elasticsearch")
            
            self.index_name = self.cfg.get('index_name', 'qwen_agent_docs')
            
            # 创建索引
            self._create_index_if_not_exists()
            
        except ImportError:
            raise ImportError("请先安装elasticsearch: pip install elasticsearch")
        except Exception as e:
            print(f"警告: 无法连接到Elasticsearch: {e}，将使用默认检索工具")
            self.es_client = None

    def _create_index_if_not_exists(self):
        """创建ES索引（如果不存在）"""
        mapping = {
            "mappings": {
                "properties": {
                    "title": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "file_path": {
                        "type": "keyword"
                    },
                    "chunk_id": {
                        "type": "integer"
                    }
                }
            }
        }

        if not self.es_client.indices.exists(index=self.index_name):
            self.es_client.indices.create(index=self.index_name, body=mapping)

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """从PDF文件中提取文本内容"""
        text = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"Error reading PDF file {file_path}: {e}")
        return text

    def _extract_text_from_docx(self, file_path: str) -> str:
        """从DOCX文件中提取文本内容"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            print(f"Error reading DOCX file {file_path}: {e}")
            return ""

    def _extract_text_from_txt(self, file_path: str) -> str:
        """从TXT文件中提取文本内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    return file.read()
            except:
                print(f"无法读取文件 {file_path}")
                return ""
        except Exception as e:
            print(f"Error reading TXT file {file_path}: {e}")
            return ""

    def _get_document_content(self, file_path: str) -> str:
        """根据文件扩展名提取文档内容"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        if extension == '.pdf':
            return self._extract_text_from_pdf(file_path)
        elif extension == '.docx':
            return self._extract_text_from_docx(file_path)
        elif extension == '.txt':
            return self._extract_text_from_txt(file_path)
        else:
            print(f"Unsupported file type: {extension}")
            return ""

    def _split_into_chunks(self, content: str, file_path: str, max_chunk_size: int = 1000) -> List[ESRecord]:
        """将文档内容分割成块"""
        if not content.strip():
            return []
            
        chunks = []
        words = content.split()
        doc_title = Path(file_path).name

        # 按指定大小分割文本
        for i in range(0, len(words), max_chunk_size):
            chunk_words = words[i:i + max_chunk_size]
            chunk_text = ' '.join(chunk_words)
            chunk_token_count = count_tokens(chunk_text)

            chunk_metadata = {
                'source': str(file_path),
                'title': doc_title,
                'chunk_id': i // max_chunk_size
            }

            chunk = ESChunk(content=chunk_text, metadata=chunk_metadata, token=chunk_token_count)
            chunks.append(chunk)

        return [ESRecord(url=str(file_path), raw=chunks, title=doc_title)]

    def _index_document(self, file_path: str):
        """索引单个文档到ES"""
        content = self._get_document_content(file_path)
        if not content.strip():
            print(f"警告: 文件 {file_path} 为空或无法读取")
            return

        # 分割文档
        records = self._split_into_chunks(content, file_path)

        # 索引到ES
        for record in records:
            for i, chunk in enumerate(record.raw):
                doc = {
                    "title": record.title,
                    "content": chunk.content,
                    "file_path": record.url,
                    "chunk_id": i
                }
                self.es_client.index(index=self.index_name, body=doc)

        print(f"已索引文件: {file_path}")

    def call(self, params: Union[str, dict], **kwargs) -> list:
        """ES检索工具的调用方法"""
        if self.es_client is None:
            return []

        import json5
        params = self._verify_json_format_args(params)
        files = params.get('files', [])
        query = params.get('query', '')

        if isinstance(files, str):
            files = json5.loads(files)

        # 索引所有文档（如果尚未索引）
        for file_path in files:
            self._index_document(file_path)

        # 执行搜索
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "content"],
                    "type": "best_fields"
                }
            },
            "size": 10
        }

        try:
            response = self.es_client.search(index=self.index_name, body=search_body)
            results = []

            if response['hits']['total']['value'] > 0:
                for hit in response['hits']['hits']:
                    source = hit['_source']
                    results.append({
                        'url': source.get('file_path', ''),
                        'text': [source.get('content', '')]  # 保持与原有格式兼容
                    })

            return results

        except Exception as e:
            print(f"ES搜索时出错: {e}")
            return []