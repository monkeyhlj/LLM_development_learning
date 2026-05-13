from src.agent.llm.env_utils import gaode_key

gaode_mcp_server_config = {  # 高德地图MCP服务端 里面有各种高德给你提供公交、地铁、公交、驾车、步行、骑行、POI搜索、IP定位、逆地理编码、云图服务、云图审图、云图审
    "url": f"https://mcp.amap.com/mcp?key={gaode_key}",
    "transport": "streamable_http",
}


# 12306的MCP服务端（工具的配置）
my12306_mcp_server_config = {
    "url": "https://mcp.api-inference.modelscope.net/29a0b3c327ab45/mcp",
    "transport": "streamable_http",
}


# # 数据分析报表的MCP服务端（工具的配置）
# analysis_mcp_server_config = {
#     "url": "https://mcp.api-inference.modelscope.net/312fc85d97954a/sse",
#     "transport": "sse",
# }