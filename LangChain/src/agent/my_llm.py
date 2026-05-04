import warnings
warnings.filterwarnings("ignore")

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = os.getenv('ZHIPU_KEY')
URL = os.getenv('ZHIPU_URL')

llm = ChatOpenAI(
    model="glm-5.1",                     # Coding Plan 模型
    temperature=0.5,
    openai_api_key=API_KEY,              # 使用相同的 key
    openai_api_base=URL,                 # Coding Plan 端点
    max_tokens=4096,
)

# messages = [
#     SystemMessage(content="你是一个助手，请用中文回复。"),
#     HumanMessage(content="请问你是？"),
# ]

# response = llm.invoke(messages)
# print(response.content)