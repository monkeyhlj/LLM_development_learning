from langchain.agents import create_agent

import sys
import os
# 将 src 目录添加到 Python 路径
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
# 现在可以正常导入
from LangChain.src.agent.tools.tool_demo2 import MyWebSearchTool
from agent.my_llm import llm

from agent.tools.tool_demo1 import web_search

web_search_tool = MyWebSearchTool()# 创建一个自定义的工具

agent = create_agent(
    llm,
    # tools=[web_search],
    tools=[web_search_tool],
    system_prompt="你是一个智能助手，尽可能的调用工具回答用户的问题。"
)


