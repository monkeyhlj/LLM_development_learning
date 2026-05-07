# -*- coding: utf-8 -*-
# @Time    : 2026/5/6 16:07
# @Author  : houlj12
# @File    : my_test_async.py
# @Description :

import asyncio
from langgraph_sdk import get_client

client = get_client(url="http://localhost:2024")  # 接口地址


async def main():
    async for chunk in client.runs.stream(
            None,  # Threadless run
            "agent",  # Name of assistant. Defined in langgraph.json.
            input={
                "messages": [
                    {
                        "role": "human",
                        "content": "给当前用户一个祝福语",
                    }
                ]
            },
            config={"configurable": {"user_name": "user_123"}}
    ):
        print(f"Receiving new event of type: {chunk.event}...")
        print(chunk.data)
        print("\n\n")


if __name__ == '__main__':
    asyncio.run(main())
