# -*- coding: utf-8 -*-
# @Time    : 2026/5/7 22:58
# @Author  : houlj12
# @File    : my_agent.py
# @Description :
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.store.postgres import PostgresStore
from langgraph.checkpoint.postgres import PostgresSaver
from src.agent.my_llm import llm
from src.agent.tools.tool_demo6 import runnable_tool
from dotenv import load_dotenv
import os

load_dotenv()


def get_weather(city: str) -> str:
    """查询某个城市的天气信息"""
    return f"It's always sunny in {city}!"


# checkpointer = InMemorySaver()  # 短期记忆，保持到内存中

# pip install langgraph-checkpoint-sqlite
# conn = sqlite3.connect("chat_history.db", check_same_thread=False)
# checkpointer = SqliteSaver(conn)


DB_URI = os.getenv("DATABASE_URL")

from langmem import create_manage_memory_tool, create_search_memory_tool

with (
    PostgresStore.from_conn_string(DB_URI) as store,
    PostgresSaver.from_conn_string(DB_URI) as checkpointer,
):
    checkpointer.setup()
    store.setup()

    # ⭐⭐⭐ 关键修改：添加这两个记忆工具 ⭐⭐⭐
    namespace = ("memories", "user_default")  # 定义记忆存储的“文件夹”

    manage_memory_tool = create_manage_memory_tool(namespace=namespace)  # 用于“写入/更新”记忆
    search_memory_tool = create_search_memory_tool(namespace=namespace)  # 用于“搜索/读取”记忆

    # ⭐ 把记忆工具加到 tools 列表中 ⭐
    agent = create_react_agent(
        llm,
        tools=[get_weather, manage_memory_tool, search_memory_tool],  # 重点在这里
        prompt="你是一个智能助手，尽可能的调用工具回答用户的问题。当用户询问天气时，必须调用工具获取天气信息。",
        checkpointer=checkpointer,
        store=store,
    )

    # 配置处理...
    config = {"configurable": {"thread_id": "1"}}

    # 现在测试一下记忆功能
    print("=== 测试1: 让 Agent 记住信息 ===")
    resp1 = agent.invoke(
        input={"messages": [{"role": "user", "content": "记住，我的名字是张三，我喜欢晴天。"}]},
        config=config,
    )
    print(resp1['messages'][-1].content)

    print("\n=== 测试2: 让 Agent 回忆信息 ===")
    resp2 = agent.invoke(
        input={"messages": [{"role": "user", "content": "我叫什么名字？我喜欢什么天气？"}]},
        config=config,
    )
    print(resp2['messages'][-1].content)
