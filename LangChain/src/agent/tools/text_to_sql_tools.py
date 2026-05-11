import json
import sys
import os
from datetime import datetime

from langchain_core.tools import BaseTool
from pydantic import create_model, Field
from typing import Optional, List
from src.agent.utils.db_utils import PostgreSQLDatabaseManager
from src.agent.utils.log_utils import log
from dotenv import load_dotenv

load_dotenv()


class ListTablesTool(BaseTool):
    """列出数据库中的所有表及其描述信息"""

    name: str = "sql_db_list_tables"
    description: str = "列出PostgresSQL数据库中的所有表名及其描述信息。当需要了解数据库中有哪些表时使用。"

    db_manager: PostgreSQLDatabaseManager

    def _run(self) -> str:
        try:
            tables_info = self.db_manager.get_tables_with_comments()

            if not tables_info:
                return "数据库中没有找到任何表。"

            result = f"数据库中共有 {len(tables_info)} 个表:\n\n"
            for i, table_info in enumerate(tables_info):
                table_name = table_info['table_name']
                table_comment = table_info['table_comment']

                # 处理空描述的情况
                if not table_comment or table_comment.isspace():
                    description_display = "（暂无描述）"
                else:
                    description_display = table_comment

                result += f"{i + 1}. 表名: {table_name}\n"
                result += f"    描述: {description_display}\n\n"

            return result

        except Exception as e:
            log.exception(e)
            return f"列出表时出错: {str(e)}"

    async def _arun(self) -> str:
        """异步执行"""
        return self._run()


class TableSchemaTool(BaseTool):
    """获取表的模式信息"""

    name: str = "sql_db_schema"
    description: str = "获取PostgresSQL数据库中指定表的详细模式信息，包括列定义、主键、外键等。输入应为表名列表，以获取所有表信息。"

    db_manager: PostgreSQLDatabaseManager

    def __init__(self, db_manager: PostgreSQLDatabaseManager):
        super().__init__(db_manager=db_manager)  # 将 db_manager 传递给父类
        self.db_manager = db_manager
        # 动态创建参数 schema
        self.args_schema = create_model(
            "TableSchemaToolArgs",
            table_names=(Optional[List[str]], Field(None, description='表名的列表，如果为None则获取所有表'))
        )

    def _run(self, table_names: Optional[List[str]] = None) -> str:
        """返回表结构信息"""
        try:
            schema_info = self.db_manager.get_table_schema(table_names)
            return schema_info if schema_info else "未找到匹配的表"
        except Exception as e:
            log.exception(e)
            return f"获取表模式信息时出错：{str(e)}"

    async def _arun(self) -> str:
        """异步执行"""
        return self._run()


class SQLQueryTool(BaseTool):
    """执行SQL查询工具类"""

    name: str = "sql_db_query"
    description: str = "在PostgreSQL数据库中执行安全的SELECT查询并返回结果。输入应为有效的SQL SELECT查询语句。"

    db_manager: PostgreSQLDatabaseManager

    def __init__(self, db_manager: PostgreSQLDatabaseManager):
        super().__init__(db_manager=db_manager)  # 将 db_manager 传递给父类
        self.db_manager = db_manager
        # 修正：参数应该是 query，而不是 table_names
        self.args_schema = create_model(
            "SQLQueryToolArgs",
            query=(str, Field(..., description='需要执行的SQL SELECT查询语句'))
        )

    def _run(self, query: str) -> str:
        """执行工具逻辑"""
        try:
            result = self.db_manager.execute_query(query)
            # 将查询结果转换为字符串格式返回
            if isinstance(result, list):
                if not result:
                    return "查询执行成功，但未返回任何结果。"

                # 限制输出长度，避免 token 过多
                def custom_serializer(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()  # 转换为 ISO 8601 格式字符串
                    raise TypeError(f"Type {type(obj)} not serializable")

                result_str = json.dumps(result, ensure_ascii=False, indent=2, default=custom_serializer)
                if len(result_str) > 10000:
                    result_str = result_str[:10000] + "\n... (输出过长，已截断)"
                return result_str
            return str(result) if result else "查询执行成功，但未返回任何结果。"
        except Exception as e:
            log.exception(e)
            return f"执行查询时出错: {str(e)}"

    async def _arun(self, query: str) -> str:
        """异步执行"""
        return self._run(query)


class SQLQueryCheckerTool(BaseTool):
    """检查SQL查询语法"""

    name: str = "sql_db_query_checker"
    description: str = "检查SQL查询语句的语法是否正确，提供验证反馈。输入应为要检查的SQL查询。"

    db_manager: PostgreSQLDatabaseManager

    def __init__(self, db_manager: PostgreSQLDatabaseManager):
        super().__init__(db_manager=db_manager)  # 将 db_manager 传递给父类
        self.db_manager = db_manager
        self.args_schema = create_model(
            "SQLQueryCheckerToolArgs",
            query=(str, Field(..., description='需要检查语法正确性的SQL查询语句'))
        )

    def _run(self, query: str) -> str:
        """执行工具逻辑"""
        try:
            result = self.db_manager.validate_query(query)
            return result
        except Exception as e:
            log.exception(e)
            return f"检查查询时出错: {str(e)}"

    async def _arun(self, query: str) -> str:
        """异步执行"""
        return self._run(query)


if __name__ == '__main__':
    # PostgresSQL 数据库连接配置（从环境变量读取）
    username = os.getenv('PG_USERNAME', 'postgres')
    password = os.getenv('PG_PASSWORD', '')
    host = os.getenv('PG_HOST', '127.0.0.1')
    port = int(os.getenv('PG_PORT', '5432'))
    database = os.getenv('PG_DATABASE', 'test_db')
    # print(f"连接配置 - 用户名: {username}, 主机: {host}, 端口: {port}, 数据库: {database}")

    # 构建 PostgresSQL 连接字符串
    connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    manager = PostgreSQLDatabaseManager(connection_string)

    # tool = ListTablesTool(db_manager=manager)  # 测试第一个工具
    # print(tool.invoke({}))

    # tool = TableSchemaTool(db_manager=manager)  # 测试第二个工具
    # print(tool.invoke({'table_names': ['users', 'orders']}))

    # tool = SQLQueryTool(db_manager=manager)  # 测试第三个工具
    # print(tool.invoke({'query': 'select count(*) from users'}))

    tool = SQLQueryCheckerTool(db_manager=manager)  # 测试第四个工具
    print(tool.invoke({'query': 'select count(*) from users'}))
