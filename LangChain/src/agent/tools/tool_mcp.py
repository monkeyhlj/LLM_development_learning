from langchain_core.tools import tool
import json
from urllib import request


MCP_SERVER_URL = "http://127.0.0.1:8765/mcp"


def call_mcp_tool(tool_name: str, arguments: dict, server_url: str = MCP_SERVER_URL) -> str:
    """调用 MCP server 的通用函数。"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }

    req = request.Request(
        server_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    if "error" in result:
        raise RuntimeError(f"MCP error: {result['error']}")

    return json.dumps(result.get("result", {}), ensure_ascii=False)


@tool("mcp_weather", parse_docstring=True)
def mcp_weather(city: str) -> str:
    """
    来自 MCP 的天气工具示例。这个工具会调用 MCP server 的 weather 工具。

    Args:
        city: 城市名称，例如 Beijing、Shanghai。

    Returns:
        MCP server 返回的天气信息字符串。
    """
    try:
        return call_mcp_tool("weather", {"city": city})
    except Exception as e:
        return f"MCP call failed: {e}"


if __name__ == "__main__":
    # 本地快速测试，先启动 fake_mcp_server.py
    print(mcp_weather.invoke({"city": "Beijing"}))
