import asyncio
from typing import List

from src.agent.skills_agent import skills_agent


def _format_items(items: List[str]) -> str:
    if not items:
        return "无"
    return ", ".join(items)


async def chat_loop() -> None:
    print("=== Skills Agent Chat ===")
    print("输入内容开始对话，输入 q / quit / exit 退出。")

    last_tool_call_count = 0
    last_skills: set[str] = set()

    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() in {"q", "quit", "exit"}:
            print("已退出对话。")
            break

        if not user_input:
            print("请输入有效内容。")
            continue

        response = await skills_agent.handle_message(user_input)

        loaded_skills = skills_agent.get_loaded_skills()
        all_tool_calls = skills_agent.get_last_tool_calls()

        current_skills = set(loaded_skills)
        newly_loaded_skills = sorted(current_skills - last_skills)

        new_tool_calls = all_tool_calls[last_tool_call_count:]

        skill_called = bool(newly_loaded_skills) or ("load_skill" in new_tool_calls)
        tool_called = bool(new_tool_calls)

        print("\nAgent:", response)
        print("\n--- 运行信息 ---")
        print("当前已加载技能:", _format_items(loaded_skills))
        print("本轮新增技能:", _format_items(newly_loaded_skills))
        print("本轮新增工具调用:", _format_items(new_tool_calls))
        print("是否调用 skill:", "是" if skill_called else "否")
        print("是否调用工具:", "是" if tool_called else "否")

        last_skills = current_skills
        last_tool_call_count = len(all_tool_calls)


if __name__ == "__main__":
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        print("\n对话已中断。")
