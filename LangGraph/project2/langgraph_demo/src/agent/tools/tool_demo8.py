# -*- coding: utf-8 -*-
# @Time    : 2026/5/6 23:01
# @Author  : houlj12
# @File    : tool_demo1.py
# @Description :
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import tool

@tool
def get_user_info_by_name(config: RunnableConfig) -> dict:
    """获取用户的所有信息，包括：性别，年龄等"""
    user_name = config['configurable'].get('user_name', 'zs')
    print(f"调用工具，传入的用户名是：{user_name}")
    # 模拟
    return {'username': user_name, 'sex': '男', 'age': 18}




