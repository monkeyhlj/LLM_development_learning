# -*- coding: utf-8 -*-
# @Time    : 2026/5/13 11:39
# @Author  : houlj12
# @File    : test_skills_agent.py
# @Description :
import asyncio
from src.agent.skills_agent import skills_agent


async def test_agent():
    print("==== 用例1: 显式加载天气技能 ====")
    user_question = "加载技能 weather_query"
    response = await skills_agent.handle_message(user_question)
    print("用户问题:", user_question)
    print("模型响应:", response)
    loaded_skills = skills_agent.get_loaded_skills()
    called_tools = skills_agent.get_last_tool_calls()
    print("已加载技能:", loaded_skills)
    print("调用工具:", called_tools)
    assert "weather_query" in loaded_skills, "weather_query 技能未被加载"
    assert "load_skill" in called_tools, "未检测到 load_skill 工具调用"

    print("\n==== 用例2: 询问某城市天气，触发天气工具 ====")
    user_question = "请查询北京天气"
    response = await skills_agent.handle_message(user_question)
    print("用户问题:", user_question)
    print("模型响应:", response)
    loaded_skills = skills_agent.get_loaded_skills()
    called_tools = skills_agent.get_last_tool_calls()
    print("已加载技能:", loaded_skills)
    print("调用工具:", called_tools)
    assert "weather_query" in loaded_skills, "天气查询时 weather_query 技能未保持加载"
    assert "weather_query" in called_tools, "天气查询时未检测到 weather_query 工具调用"

    print("\n==== 用例3: 另一个城市天气问答 ====")
    user_question = "那上海的天气呢？"
    response = await skills_agent.handle_message(user_question)
    print("用户问题:", user_question)
    print("模型响应:", response)
    loaded_skills = skills_agent.get_loaded_skills()
    called_tools = skills_agent.get_last_tool_calls()
    print("已加载技能:", loaded_skills)
    print("调用工具:", called_tools)
    assert "weather_query" in called_tools, "连续追问天气时未调用 weather_query 工具"

    print("\n==== 用例4: 显式加载高德技能 ====")
    user_question = "加载技能 gaode_navigation"
    response = await skills_agent.handle_message(user_question)
    print("用户问题:", user_question)
    print("模型响应:", response)
    loaded_skills = skills_agent.get_loaded_skills()
    called_tools = skills_agent.get_last_tool_calls()
    print("已加载技能:", loaded_skills)
    print("调用工具:", called_tools)
    assert "gaode_navigation" in loaded_skills, "gaode_navigation 技能未被加载"
    assert "load_skill" in called_tools, "高德技能加载时未检测到 load_skill 工具调用"

    print("\n==== 用例5: 高德路线规划查询 ====")
    user_question = "请帮我规划从北京到上海的导航路线"
    response = await skills_agent.handle_message(user_question)
    print("用户问题:", user_question)
    print("模型响应:", response)
    loaded_skills = skills_agent.get_loaded_skills()
    called_tools = skills_agent.get_last_tool_calls()
    print("已加载技能:", loaded_skills)
    print("调用工具:", called_tools)
    assert "gaode_navigation" in loaded_skills, "路线查询时 gaode_navigation 技能未保持加载"

    print("\n==== 用例6: 未知技能异常处理 ====")
    user_question = "加载技能 unknown_skill"
    response = await skills_agent.handle_message(user_question)
    print("用户问题:", user_question)
    print("模型响应:", response)
    loaded_skills = skills_agent.get_loaded_skills()
    called_tools = skills_agent.get_last_tool_calls()
    print("已加载技能:", loaded_skills)
    print("调用工具:", called_tools)


# 运行测试
if __name__ == "__main__":
    asyncio.run(test_agent())
