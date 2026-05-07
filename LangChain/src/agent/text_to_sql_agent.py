import sys
import os
# 将 src 目录添加到 Python 路径
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
# 现在可以正常导入
from agent.my_llm import llm

from typing import List
from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from agent.tools.text_to_sql_tools import ListTablesTool, TableSchemaTool, SQLQueryTool, SQLQueryCheckerTool
from agent.utils.db_utils import PostgreSQLDatabaseManager


def get_tools(host: str, port: int, username: str, password: str, database: str) -> List[BaseTool]:
    """获取 PostgreSQL 数据库相关的工具列表"""
    # 构建 PostgreSQL 连接字符串
    connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    manager = PostgreSQLDatabaseManager(connection_string)
    return [
        ListTablesTool(db_manager=manager),
        TableSchemaTool(db_manager=manager),
        SQLQueryTool(db_manager=manager),
        SQLQueryCheckerTool(db_manager=manager),
    ]


# 配置数据库连接信息
tools = get_tools(
    host='127.0.0.1',
    port=5432,
    username='postgres',
    password='123123',
    database='test_db4'
)

system_prompt = """
你是一个专门设计用于与 SQL 数据库交互的 AI 代理。

给定一个输入问题，你需要按照以下步骤操作：
1. 创建一个语法正确的 {dialect} 查询语句
2. 执行查询并查看结果
3. 基于查询结果返回最终答案

除非用户明确指定要获取的具体示例数量，否则始终将查询结果限制为最多 {top_k} 条。

你可以通过相关列对结果进行排序，以返回数据库中具有意义的示例。
永远不要查询特定表的所有列，只获取与问题相关的列。

在执行查询之前，你必须仔细检查查询语句。如果在执行查询时遇到错误，请重写查询并再次尝试。

绝对不要对数据库执行任何数据操作语言（DML）语句（如 INSERT、UPDATE、DELETE、DROP 等）。

开始处理问题时，你应该始终先查看数据库中有哪些表可以查询。不要跳过这一步。
然后，你应该查询最相关的模式结构信息。
""".format(
    dialect='PostgreSQL',  # 数据库方言
    top_k=5,               # 默认返回结果的最大数量
)

# 创建 Agent
agent = create_agent(
    llm,
    tools=tools,
    system_prompt=system_prompt,
)


# # 本地测试
# for step in agent.stream(
#     input={'messages': [{'role': 'user', 'content': '数据库中有多少个部门，每个部门都有哪些员工？'}]},
#     stream_mode="values"
# ):
#     step['messages'][-1].pretty_print()  # 打印每一步的输出



