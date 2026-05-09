# -*- coding: utf-8 -*-
# @Time    : 2026/5/7 22:58
# @Author  : houlj12
# @File    : my_agent.py
# @Description :
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.prebuilt import create_react_agent

from src.agent.my_llm import llm
from src.agent.tools.tool_demo6 import runnable_tool

from dotenv import load_dotenv
import os

load_dotenv()


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


# checkpointer = InMemorySaver()  # 短期记忆，保持到内存中


DB_URI = os.getenv("DATABASE_URL")

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    # checkpointer.setup()  # 第一次运行加
    agent = create_react_agent(
        llm,
        tools=[runnable_tool, get_weather],
        prompt="你是一个智能助手，尽可能的调用工具回答用户的问题",
        checkpointer=checkpointer,
    )

    # 测试
    config = {
        "configurable": {
            "thread_id": "1"
        }
    }

    rest = list(agent.get_state(config))
    print(rest)

    resp1 = agent.invoke(
        input={"messages": [{"role": "user", "content": "今天，北京的天气怎么样？"}]},
        config=config,
    )

    print(resp1['messages'][-1].content)

    resp2 = agent.invoke(
        input={"messages": [{"role": "user", "content": "那，长沙呢？"}]},
        config=config,
    )

    print(resp2['messages'][-1].content)
