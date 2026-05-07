# -*- coding: utf-8 -*-
# @Time    : 2026/5/6 23:01
# @Author  : houlj12
# @File    : tool_demo1.py
# @Description :
from typing import Annotated
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from agent.my_state import CustomState


@tool
def get_user_name(
        tool_call_id: Annotated[str, InjectedToolCallId],
        config: RunnableConfig
) -> Command:
    """获取当前用户的username，以便生成祝福语句"""
    user_name = config['configurable'].get('user_name', 'zs')
    print(f"调用工具，传入的用户名是: {user_name}")

    # 模拟
    return Command(update={
        "username": user_name,  # 更新状态中的用户名
        # 更新一条工具执行后的消息: ToolMessage类型
        "messages": [
            ToolMessage(
                content='成功的得到当前用户的username',
                tool_call_id=tool_call_id
            )
        ]
    })

@tool
def greet_user(state: Annotated[CustomState, InjectedState]) -> str:
    """在获取用户的username之后，生成祝福语句"""
    username = state['username']  # 从状态中获取用户名
    return f'祝贺你：{username}!'

