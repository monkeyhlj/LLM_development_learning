import json
from typing import List, Dict, Any, Optional
from qwen_agent.memory import Memory
from qwen_agent.tools.es_retrieval import ESRetrievalTool


class ESMemory(Memory):
    """
    使用Elasticsearch实现的记忆类，用于文档片段的索引和管理
    """
    
    def __init__(self, cfg: Optional[Dict] = None):
        super().__init__(cfg)
        self.cfg = cfg or {}
        # 初始化ES检索工具
        self.es_tool = ESRetrievalTool(cfg)
    
    def add(self, content: str, metadata: Optional[Dict] = None):
        """
        添加内容到记忆中
        :param content: 要添加的内容
        :param metadata: 元数据
        """
        # 将内容保存到临时文件或已有的文档集合中
        # 暂时模拟文档存储
        pass
    
    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """
        根据查询检索最相关的内容
        :param query: 查询字符串
        :param top_k: 返回最相关的k个结果
        :param kwargs: 额外参数
        :return: 检索到的结果列表
        """
        # 使用ES检索工具进行查询
        try:
            params = {
                "query": query,
                "files": kwargs.get("files", [])  # 从参数中获取文档列表
            }
            
            results = self.es_tool.call(params, **kwargs)
            
            # 格式化返回结果
            formatted_results = []
            for result in results:
                if 'error' not in result:
                    formatted_results.append({
                        'content': result.get('content', ''),
                        'metadata': {
                            'source': result.get('file_path', ''),
                            'title': result.get('title', ''),
                            'score': result.get('score', 0.0)
                        }
                    })
            
            # 只返回top_k个结果
            return formatted_results[:top_k]
        
        except Exception as e:
            print(f"ES检索出错: {e}")
            return []

    def clear(self):
        """
        清除记忆内容
        """
        # 可以选择删除ES索引中的相关文档
        pass