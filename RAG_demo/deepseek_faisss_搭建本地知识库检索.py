# ==================== 1. 导入必要的库 ====================
from PyPDF2 import PdfReader
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import OpenAI  # 注意：此处导入但实际未使用，实际使用的是Tongyi
from langchain_community.callbacks.manager import get_openai_callback
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Tongyi
from typing import List, Tuple

# 警告：请勿将API密钥硬编码在代码中，此处仅为示例
DASHSCOPE_API_KEY = "sk-590ae16cd93940feb9440b342eda2673"

# ==================== 2. 从PDF提取文本和页码信息 ====================
def extract_text_with_page_numbers(pdf) -> Tuple[str, List[int]]:
    """
    从PDF中提取文本并记录每行文本对应的页码
    参数：
    pdf: PDF文件对象
    返回：
    text: 提取的文本内容
    page_numbers: 每行文本对应的页码列表
    """
    text = ""
    page_numbers = []

    for page_number, page in enumerate(pdf.pages, start=1):
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text
            # 记录当前页的每一行，为每一行分配当前页码
            page_numbers.extend([page_number] * len(extracted_text.split("\n")))
        # else:
        #     Logger.warning(f"No text found on page {page_number}.")

    return text, page_numbers

# ==================== 3. 处理文本并创建向量数据库 ====================
def process_text_with_splitter(text: str, page_numbers: List[int]) -> FAISS:
    """
    处理文本并创建向量存储
    参数：
    text：提取的文本内容
    page_numbers：每行文本对应的页码列表
    返回：
    knowledgeBase：基于FAISS的向量存储对象
    """
    # 创建文本分割器，用于将长文本分割成小块
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", " ", " "],  # 分隔符优先级列表
        chunk_size=1000,      # 每个块的最大字符数
        chunk_overlap=200,    # 块之间的重叠字符数
        length_function=len,
    )

    # 分割文本
    chunks = text_splitter.split_text(text)
    print(f"文本被分割成 {len(chunks)} 个块。")

    # 创建嵌入模型（使用阿里云DashScope）
    embeddings = DashScopeEmbeddings(
        model="text-embedding-v1",
        dashscope_api_key=DASHSCOPE_API_KEY,
    )

    # 从文本块创建FAISS向量存储知识库
    knowledgeBase = FAISS.from_texts(chunks, embeddings)
    print("已从文本块创建知识库。")

    # 存储每个文本块对应的页码信息（将页码信息作为元数据附加）
    knowledgeBase.page_info = {chunk: page_numbers[i] for i, chunk in enumerate(chunks)}

    return knowledgeBase

# ==================== 4. 主程序流程 ====================
if __name__ == "__main__":
    # 4.1 读取PDF文件
    pdf_reader = PdfReader('./浦发上海浦东发展银行西安分行个金客户经理考核办法.pdf')

    # 4.2 提取文本和页码信息
    text, page_numbers = extract_text_with_page_numbers(pdf_reader)
    print(f"提取的文本长度: {len(text)} 个字符。")

    # 4.3 处理文本并创建知识库
    knowledgeBase = process_text_with_splitter(text, page_numbers)

    # 4.4 (可选) 保存FAISS向量数据库到本地，以便后续重用
    # knowledgeBase.save_local('./faiss-1')

    # 4.5 初始化大语言模型（使用阿里云通义千问）
    llm = Tongyi(model_name="qwen-turbo", dashscope_api_key=DASHSCOPE_API_KEY)

    # 4.6 设置用户查询问题
    query = "客户经理被投诉了，投诉一次扣多少分"

    if query:
        # 执行相似度搜索，找到与查询最相关的文档块
        docs = knowledgeBase.similarity_search(query)

        # 加载问答链（stuff模式：将所有相关文档块放入上下文）
        chain = load_qa_chain(llm, chain_type="stuff")

        # 准备输入数据
        input_data = {"input_documents": docs, "question": query}

        # 使用回调函数跟踪API调用成本
        with get_openai_callback() as cost:
            # 执行问答链
            response = chain.invoke(input=input_data)
            print(f"查询已处理。成本: {cost}")
            print(response["output_text"])

        # 显示相关文本块来源的页码
        unique_pages = set()
        print("\n相关文本块来源页码：")
        for doc in docs:
            text_content = getattr(doc, "page_content", "")
            source_page = knowledgeBase.page_info.get(text_content.strip(), "未知")
            if source_page not in unique_pages:
                unique_pages.add(source_page)
                print(f"文本块页码: {source_page}")