# -*- coding: utf-8 -*-
# @Time    : 2026/5/6 23:01
# @Author  : houlj12
# @File    : tool_demo1.py
# @Description :
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class CalculateArgs(BaseModel):  # 1个用法
    a: float = Field(description="第一个需要输入的数字。")
    b: float = Field(description="第二个需要输入的数字。")
    operation: str = Field(description="运算类型，只能是add、subtract、multiply和divide中的任意一个。")

@tool('calculate', args_schema=CalculateArgs)
def calculate2(a: float, b: float, operation: str) -> float:
    """工具函数：计算两个数字的运算结果"""
    print(f"调用 calculate 工具，第一个数字：{a}，第二个数字：{b}，运算类型：{operation}")
    result = 0.0
    match operation:
        case "add":
            result = a + b
        case "subtract":
            result = a - b
        case "multiply":
            result = a * b
        case "divide":
            if b != 0:
                result = a / b
            else:
                raise ValueError("除数不能为零")

    return result

print(calculate2.name)
print(calculate2.description)
print(calculate2.args)
print(calculate2.args_schema.model_json_schema())
print(calculate2.return_direct)

