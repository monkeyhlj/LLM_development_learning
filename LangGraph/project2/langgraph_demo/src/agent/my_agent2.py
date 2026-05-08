# -*- coding: utf-8 -*-
# @Time    : 2026/5/7 22:58
# @Author  : houlj12
# @File    : my_agent.py
# @Description :
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from agent.my_llm import llm
from agent.tools.tool_demo6 import runnable_tool

# checkpointer = InMemorySaver()  # 短期记忆，保持到内存中

# pip install langgraph-checkpoint-sqlite
# conn = sqlite3.connect("chat_history.db", check_same_thread=False)
# checkpointer = SqliteSaver(conn)

DB_URI = 'postgresql://postgres:123123@localhost:5432/langgraph_db'

from langgraph.store.postgres import PostgresStore
from langgraph.checkpoint.postgres import PostgresSaver


with (
    PostgresStore.from_conn_string(DB_URI) as store,
    PostgresSaver.from_conn_string(DB_URI) as checkpointer,
):
    # checkpointer.setup()
    store.setup()
    agent = create_react_agent(
        llm,
        tools=[runnable_tool],
        prompt="你是一个智能助手，尽可能的调用工具回答用户的问题",
        checkpointer=checkpointer,
        store=store,
    )

    # 测试
    config = {
        "configurable": {
            "thread_id": "1"
        }
    }

    # rest = list(agent.get_state(config))  # 从短期存储中，返回所有当前会话的上下文
    rest = list(agent.get_state_history(config))#从长期存储中，返回所有当前会话的上下文
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
