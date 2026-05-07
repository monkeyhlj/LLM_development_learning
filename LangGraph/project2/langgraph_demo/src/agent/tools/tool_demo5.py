# -*- coding: utf-8 -*-
# @Time    : 2026/5/6 23:01
# @Author  : houlj12
# @File    : tool_demo1.py
# @Description :
from typing import Annotated

from langchain_core.tools import tool, StructuredTool


def calculate5(
        a: float,
        b: float,
        operation: str) -> float:
    """工具函数：计算两个数字的运算结果

    Args:
        a: 第一个需要输入的数字。
        b: 第二个需要输入的数字。
        operation: 运算类型，只能是add、subtract、multiply和divide中的任意一个。

    Returns:
        返回两个输入数字的运算结果。
    """
    print(f"调用 calculate 工具，第一个数字: {a}，第二个数字: {b}，运算类型: {operation}")
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


async def calculate6(
        a: float,
        b: float,
        operation: str) -> float:
    """工具函数：计算两个数字的运算结果

    Args:
        a: 第一个需要输入的数字。
        b: 第二个需要输入的数字。
        operation: 运算类型，只能是add、subtract、multiply和divide中的任意一个。

    Returns:
        返回两个输入数字的运算结果。
    """
    print(f"调用 calculate 工具，第一个数字: {a}，第二个数字: {b}，运算类型: {operation}")
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


calculator = StructuredTool.from_function(
    func=calculate5,
    name="calculator",
    description="工具函数：计算两个数字的商",
    return_direct=False,
    coroutine=calculate6
)
