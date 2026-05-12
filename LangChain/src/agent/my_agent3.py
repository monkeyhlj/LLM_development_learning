from langchain.agents import create_agent

import sys
import os

# 将 src 目录添加到 Python 路径
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.agent.my_llm import llm
from src.agent.tools.tool_mcp import mcp_weather


agent = create_agent(
    llm,
    tools=[mcp_weather],
    system_prompt="你是一个智能助手，优先通过 MCP tools 来回答用户问题。",
)


if __name__ == "__main__":
    print("MCP tools 测试 agent 已启动。")
    print("提示: 请先在另一个终端运行 fake_mcp_server.py")

    while True:
        user_input = input("\n请输入问题(输入 exit 退出): ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("已退出。")
            break

        try:
            result = agent.invoke(
                {
                    "messages": [
                        {"role": "user", "content": user_input}
                    ]
                }
            )
            print("\nAgent 输出:")
            print(result)
        except Exception as e:
            print(f"调用失败: {e}")
