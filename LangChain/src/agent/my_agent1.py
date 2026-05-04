from langchain.agents import create_agent

import sys
import os
# 将 src 目录添加到 Python 路径
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
# 现在可以正常导入
from agent.my_llm import llm

def send_email(to: str, subject: str, body: str):
    """发送邮件"""
    email = {
        "to": to,
        "subject": subject,
        "body": body
    }
    # ... 邮件发送逻辑

    return f"邮件已发送至 {to}"

agent = create_agent(
    llm,
    tools=[send_email],
    system_prompt="你是一个邮件助手。请始终使用 send_email 工具。"
)