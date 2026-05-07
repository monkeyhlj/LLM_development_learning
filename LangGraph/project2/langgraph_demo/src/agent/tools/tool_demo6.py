# -*- coding: utf-8 -*-
# @Time    : 2026/5/7 17:35
# @Author  : houlj12
# @File    : tool_demo6.py
# @Description :

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from src.agent.my_llm import llm

# 定义提示词模板
prompt = (  # 外层的模板
    PromptTemplate.from_template("帮我生成一个简短的，关于{topic}的报幕词。")
    + "，要求：1、内容搞笑一点；"
    + "2、输出的内容采用{language}。"
)

# 创建处理链
chain = prompt | llm | StrOutputParser()

# 定义工具参数模型
class ToolArgs(BaseModel):
    topic: str = Field(description="报幕词的主题")
    language: str = Field(description="报幕词采用的语言")

# 将链转换为工具
runnable_tool = chain.as_tool(
    name='chain_tool',
    description='这是一个专门生成报幕词的工具',
    args_schema=ToolArgs,
)

# 打印工具信息
print(runnable_tool.args_schema.model_json_schema())
print(runnable_tool.name)
print(runnable_tool.description)


