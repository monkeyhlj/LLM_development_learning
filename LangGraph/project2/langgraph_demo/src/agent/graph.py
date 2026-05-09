from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.types import RunnableConfig
from langgraph.graph.message import AnyMessage
from my_llm import llm
from src.agent.tools.tool_demo9 import get_user_name, greet_user
from src.agent.my_state import CustomState
from src.agent.tools.tool_demo7 import MySearchTool
from src.agent.tools.tool_demo3 import calculate3
from src.agent.tools.tool_demo6 import runnable_tool


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


my_tool = MySearchTool()


# 提示词模板的函数：由用户传入内容，组成一个动态的系统提示词
def prompt(state: AgentState, config: RunnableConfig) -> list[AnyMessage]:
    user_name = config['configurable'].get('user_name', 'zs')
    print(user_name)
    system_message = f'你是一个智能助手，当前用户的名字是: {user_name}'
    return [{'role': 'system', 'content': system_message}] + state.messages


graph = create_react_agent(
    llm,
    tools=[get_weather, calculate3, runnable_tool, my_tool, get_user_name, greet_user],
    # prompt="You are a helpful assistant"
    prompt=prompt,
    state_schema=CustomState,  # 指定自定义状态类
)

# """LangGraph single-node graph template.
#
# Returns a predefined response. Replace logic and configuration as needed.
# """
#
# from __future__ import annotations
#
# from dataclasses import dataclass
# from typing import Any, Dict
#
# from langgraph.graph import StateGraph
# from langgraph.runtime import Runtime
# from typing_extensions import TypedDict
#
#
# class Context(TypedDict):
#     """Context parameters for the agent.
#
#     Set these when creating assistants OR when invoking the graph.
#     See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
#     """
#
#     my_configurable_param: str
#
#
# @dataclass
# class State:
#     """Input state for the agent.
#
#     Defines the initial structure of incoming data.
#     See: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
#     """
#
#     changeme: str = "example"
#
#
# async def call_model(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
#     """Process input and returns output.
#
#     Can use runtime context to alter behavior.
#     """
#     return {
#         "changeme": "output from call_model. "
#         f"Configured with {(runtime.context or {}).get('my_configurable_param')}"
#     }
#
#
# # Define the graph
# graph = (
#     StateGraph(State, context_schema=Context)
#     .add_node(call_model)
#     .add_edge("__start__", "call_model")
#     .compile(name="New Graph")
# )
