from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from log_utils import log


class PostgreSQLDatabaseManager:
    """PostgreSQL数据库管理器，负责数据库连接和基本操作"""

    def __init__(self, connection_string: str):
        """
        初始化 PostgreSQL 数据库连接

        Args:
            connection_string: PostgreSQL 连接字符串，格式为:
            postgresql://username:password@host:port/database
        """
        self.engine = create_engine(connection_string, pool_size=5)

    def get_table_names(self) -> list[str]:
        """获取数据库中所有表名"""
        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except Exception as e:
            log.exception(e)
            raise ValueError(f"获取表名失败: {str(e)}")

    def get_tables_with_comments(self) -> List[dict]:
        """
        获取数据库中所有表的名称和描述信息。

        Returns:
            List[dict]: 一个字典列表，每个字典包含 'table_name' 和 'table_comment' 键。
        """
        try:
            # PostgreSQL 从 pg_catalog 或 information_schema 获取表注释
            query = text("""
                SELECT 
                    c.relname AS table_name,
                    obj_description(c.oid) AS table_comment
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relkind = 'r'
                    AND n.nspname = 'public'
                ORDER BY table_name
            """)
            with self.engine.connect() as connection:
                result = connection.execute(query)
                tables_info = [{'table_name': row[0], 'table_comment': row[1] or ''} for row in result]
                return tables_info
        except SQLAlchemyError as e:
            log.exception(e)
            raise ValueError(f"获取表名及描述信息失败: {str(e)}")

    def get_table_schema(self, table_names: Optional[List[str]] = None) -> str:
        """
        获取指定表的模式信息（包含字段注释）

        Args:
            table_names: 表名列表，如果为None则获取所有表
        """
        try:
            inspector = inspect(self.engine)
            schema_info = []

            tables_to_process = table_names if table_names else self.get_table_names()

            for table_name in tables_to_process:
                # 获取表注释
                table_comment = ""
                try:
                    table_comment_query = text("""
                        SELECT obj_description(c.oid)
                        FROM pg_catalog.pg_class c
                        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                        WHERE c.relname = :table_name AND n.nspname = 'public'
                    """)
                    with self.engine.connect() as conn:
                        result = conn.execute(table_comment_query, {"table_name": table_name})
                        row = result.fetchone()
                        table_comment = row[0] if row and row[0] else ""
                except Exception:
                    pass

                schema_info.append(f"\n=== 表名: {table_name} ===")
                if table_comment:
                    schema_info.append(f"表描述: {table_comment}")

                # 获取列信息
                columns = inspector.get_columns(table_name)
                # 获取主键约束
                pk_constraint = inspector.get_pk_constraint(table_name)
                primary_keys = pk_constraint['constrained_columns'] if pk_constraint else []
                # 获取外键约束
                foreign_keys = inspector.get_foreign_keys(table_name)

                # 构建外键映射
                fk_map = {}
                for fk in foreign_keys:
                    for col in fk['constrained_columns']:
                        fk_map[col] = f"{fk['referred_table']}.{fk['referred_columns'][0]}"

                schema_info.append("| 字段名 | 类型 | 可为空 | 主键 | 外键 | 说明 |")
                schema_info.append("|--------|------|--------|------|------|------|")

                for col in columns:
                    col_name = col['name']
                    col_type = str(col['type'])
                    nullable = "是" if col.get('nullable', True) else "否"
                    is_pk = "是" if col_name in primary_keys else "否"
                    is_fk = fk_map.get(col_name, "无")
                    comment = col.get('comment', "") or ""

                    schema_info.append(f"| {col_name} | {col_type} | {nullable} | {is_pk} | {is_fk} | {comment} |")

                schema_info.append("")

            return "\n".join(schema_info)

        except SQLAlchemyError as e:
            log.exception(e)
            raise ValueError(f"获取表结构失败: {str(e)}")

    def execute_query(self, query: str) -> List[dict]:
        """
        执行SQL查询并返回结果

        Args:
            query: SQL 查询语句

        Returns:
            List[dict]: 查询结果列表
        """
        # 安全检查：防止数据修改操作
        forbidden_keywords = ['insert', 'update', 'delete', 'drop', 'alter', 'create', 'grant', 'truncate']
        query_lower = query.lower().strip()

        # 检查是否以SELECT或WITH开头
        if not (query_lower.startswith('select') or query_lower.startswith('with')):
            if any(keyword in query_lower for keyword in forbidden_keywords):
                raise ValueError("出于安全考虑，只允许执行SELECT查询和WITH查询")

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                # 将结果转换为字典列表
                if result.returns_rows:
                    columns = result.keys()
                    rows = result.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                return []
        except SQLAlchemyError as e:
            log.exception(e)
            raise ValueError(f"执行查询失败: {str(e)}")

    def validate_query(self, query: str) -> str:
        """
        验证SQL查询语法是否正确

        Args:
            query: 要验证的SQL查询

        Returns:
            str: 验证结果信息
        """
        # 基本语法检查
        if not query or not query.strip():
            return "错误：查询不能为空"

        # 检查是否以SELECT或WITH开头
        query_lower = query.lower().strip()
        if not (query_lower.startswith('select') or query_lower.startswith('with')):
            return "警告：建议使用SELECT或WITH查询，其他操作可能被限制"

        # 尝试解析查询（使用 EXPLAIN 验证语法，不实际执行）
        try:
            with self.engine.connect() as connection:
                # 使用 EXPLAIN 验证语法
                connection.execute(text(f"EXPLAIN {query}"))
            return "验证通过：SQL语法正确"
        except SQLAlchemyError as e:
            return f"验证失败：{str(e)}"


if __name__ == '__main__':
    # PostgreSQL 数据库连接配置
    DB_CONFIG = {
        "host": "localhost",
        "port": 5432,
        "username": "postgres",
        "password": "123123",
        "database": "test_db4"
    }

    connection_string = f"postgresql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

    manager = PostgreSQLDatabaseManager(connection_string)

    # 测试获取表名
    tables = manager.get_table_names()
    print("表名列表:", tables)

    # 测试获取带注释的表
    tables_with_comments = manager.get_tables_with_comments()
    print("带注释的表:", tables_with_comments)

    # 测试获取表结构
    if tables:
        schema = manager.get_table_schema([tables[0]])
        print("表结构:\n", schema)