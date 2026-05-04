from langchain_core.tools import tool
from pydantic import BaseModel, Field

import sys
import os
# 将 src 目录添加到 Python 路径
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
# 现在可以正常导入
from agent.my_llm import llm


@tool('my_web_search', parse_docstring=True)
def web_search(query: str) -> str:
    """
    互联网搜索的工具，可以搜索所有公开的信息。

    Args:
        query: 搜索查询字符串，描述你想要搜索的信息。

    Returns:
        返回搜索结果信息，该信息是一个文本字符串。
    """
    try:
        resp = llm.web_search.web_search(
            search_engine='search_pro',
            search_query=query,
        )
        if resp.search_result:
            return "\n\n".join([d.content for d in resp.search_result])
        return "没有搜索到任何结果"

    except Exception as e:
        print(e)
        return f"Error: {e}"



# class SearchArgs(BaseModel):
#     query: str = Field(..., description='需要进行互联网查询的查询信息')
#     # second: int = Field(..., description='第二个参数')

# @tool('my_web_search', args_schema=SearchArgs, description='互联网搜索的工具，可以搜索所有公开的信息')
# def web_search2(query: str) -> str:
#     pass


# # 测试
# if __name__ == '__main__':
#     print(web_search.name)                     # 工具的名字
#     print(web_search.description)              # 工具的描述
#     print(web_search.args)                     # 工具的参数
#     print(web_search.args_schema.model_json_schema())  # 工具的参数 json schema（描述 json 字符串）

#     result = web_search.invoke({'query': '如何使用 langchain?'})
#     print(result)



