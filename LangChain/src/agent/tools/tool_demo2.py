from langchain_core.tools import BaseTool
from typing import Any, Type
from pydantic import BaseModel, Field, create_model

import sys
import os
# 将 src 目录添加到 Python 路径
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
# 现在可以正常导入
from agent.my_llm import llm


class SearchArgs(BaseModel):
    query: str = Field(..., description='需要进行互联网查询的查询信息')


class MyWebSearchTool(BaseTool):
    name: str = "web_search2"#定义工具的名称
    description:str="使用这个工具可以进行网络搜索。"
    # 第一种写法
    # args_schema:Type[BaseModel] = SearchArgs
    # 第二种写法
    def __init__(self, **kwargs):
        super().__init__(kwargs)
        self.args_schema = create_model("SearchInput", query=(str, Field(..., description='需要进行互联网查询的信息')))

    def run(self,query: str) -> str:
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

    # 如果为异步调用时，定义一个 async 的 run 方法    
    async def run(self, query: str) -> str: 
        return await self._run(query)
    
        