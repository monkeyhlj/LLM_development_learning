import sys
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import asyncio
from pathlib import Path

# 设置项目路径
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# 导入agent相关模块
from typing import List
from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from src.agent.tools.text_to_sql_tools import ListTablesTool, TableSchemaTool, SQLQueryTool, SQLQueryCheckerTool
from src.agent.utils.db_utils import PostgreSQLDatabaseManager
from src.agent.my_llm import llm
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = FastAPI(title="SQL Agent Web测试界面", description="通过自然语言查询数据库")

# 确保静态文件目录存在
static_dir = Path(__file__).parent.parent / "static"
templates_dir = Path(__file__).parent.parent / "templates"

# 创建目录如果不存在
static_dir.mkdir(exist_ok=True)
templates_dir.mkdir(exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 配置模板
templates = Jinja2Templates(directory=str(templates_dir))


# 请求模型
class QueryRequest(BaseModel):
    question: str
    stream: bool = False
    session_id: Optional[str] = None


# 响应模型
class QueryResponse(BaseModel):
    success: bool
    question: str
    answer: str
    sql_queries: List[str] = []
    results: Optional[List[Dict]] = None
    steps: List[Dict] = []
    timestamp: str
    error: Optional[str] = None


# 会话管理
class SessionManager:
    def __init__(self):
        self.sessions = {}

    def get_or_create(self, session_id: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'history': [],
                'created_at': datetime.now()
            }
        return self.sessions[session_id]

    def add_history(self, session_id: str, query: str, response: Dict):
        session = self.get_or_create(session_id)
        session['history'].append({
            'query': query,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        # 保留最近50条记录
        if len(session['history']) > 50:
            session['history'] = session['history'][-50:]


session_manager = SessionManager()


def get_tools(host: str, port: int, username: str, password: str, database: str) -> List[BaseTool]:
    """获取 PostgreSQL 数据库相关的工具列表"""
    connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    manager = PostgreSQLDatabaseManager(connection_string)
    return [
        ListTablesTool(db_manager=manager),
        TableSchemaTool(db_manager=manager),
        SQLQueryTool(db_manager=manager),
        SQLQueryCheckerTool(db_manager=manager),
    ]


# 配置数据库连接信息
username = os.getenv('PG_USERNAME', 'postgres')
password = os.getenv('PG_PASSWORD', '')
host = os.getenv('PG_HOST', '127.0.0.1')
port = int(os.getenv('PG_PORT', '5432'))
database = os.getenv('PG_DATABASE', 'test_db')

print(f"连接数据库: {host}:{port}/{database} 用户: {username}")

# 创建工具实例
try:
    tools = get_tools(
        host=host,
        port=port,
        username=username,
        password=password,
        database=database
    )
    print("数据库连接成功")
except Exception as e:
    print(f"数据库连接失败: {e}")
    tools = []

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
    dialect='PostgreSQL',
    top_k=5,
)

# 创建 Agent
try:
    if tools:
        agent = create_agent(
            llm,
            tools=tools,
            system_prompt=system_prompt,
        )
        print("Agent创建成功")
    else:
        agent = None
        print("警告: 工具初始化失败，Agent未创建")
except Exception as e:
    print(f"Agent创建失败: {e}")
    agent = None


def extract_sql_and_results(messages):
    """从agent消息中提取SQL查询和结果"""
    sql_queries = []
    results = None

    for msg in messages:
        if hasattr(msg, 'content'):
            content = str(msg.content)
            # 提取SQL语句（支持多种格式）
            import re
            # 匹配SELECT语句
            sql_pattern = r'(SELECT\s+.*?(?:;|$))'
            matches = re.findall(sql_pattern, content, re.IGNORECASE | re.DOTALL)
            if matches:
                sql_queries.extend(matches)

            # 尝试提取结果数据
            if '结果' in content or 'result' in content.lower():
                # 查找JSON格式的数据
                json_pattern = r'\{[^{}]*\}'
                json_matches = re.findall(json_pattern, content)
                for json_str in json_matches:
                    try:
                        data = json.loads(json_str)
                        if isinstance(data, list):
                            results = data
                            break
                        elif isinstance(data, dict) and 'results' in data:
                            results = data['results']
                            break
                    except:
                        pass

    return sql_queries, results


def extract_step_metadata(message) -> Dict[str, Any]:
    """提取步骤元信息（消息类型、工具调用）"""
    message_type = getattr(message, 'type', message.__class__.__name__)
    metadata: Dict[str, Any] = {
        'message_type': str(message_type)
    }

    tool_names: List[str] = []

    # ToolMessage 通常直接带有 name
    tool_name = getattr(message, 'name', None)
    if tool_name:
        tool_names.append(str(tool_name))

    # AIMessage 可能带 tool_calls
    direct_tool_calls = getattr(message, 'tool_calls', None)
    if isinstance(direct_tool_calls, list):
        for call in direct_tool_calls:
            if isinstance(call, dict) and call.get('name'):
                tool_names.append(str(call['name']))

    # 兼容 additional_kwargs 内的 tool_calls
    additional_kwargs = getattr(message, 'additional_kwargs', {}) or {}
    extra_tool_calls = additional_kwargs.get('tool_calls', [])
    if isinstance(extra_tool_calls, list):
        for call in extra_tool_calls:
            if isinstance(call, dict):
                function_info = call.get('function', {})
                if isinstance(function_info, dict) and function_info.get('name'):
                    tool_names.append(str(function_info['name']))

    # 去重并保持顺序
    unique_tools: List[str] = []
    seen = set()
    for name in tool_names:
        if name not in seen:
            unique_tools.append(name)
            seen.add(name)

    if unique_tools:
        metadata['tools_called'] = unique_tools
        metadata['tool'] = unique_tools[0]

    return metadata


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页"""
    # 直接读取HTML文件
    html_path = Path(__file__).parent.parent / "templates" / "chat.html"
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


def create_default_template():
    """创建默认模板文件"""
    template_path = templates_dir / "chat.html"
    default_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Agent 智能查询助手</title>
    <link rel="stylesheet" href="/static/style.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="app-container">
        <div class="chat-main">
            <div class="chat-header">
                <h1>SQL Agent 智能查询助手</h1>
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="welcome-message">
                    <h2>欢迎使用 SQL Agent</h2>
                    <p>请在下方输入您的问题</p>
                </div>
            </div>
            <div class="chat-input-area">
                <textarea id="userInput" placeholder="输入您的问题..." rows="3"></textarea>
                <button id="sendBtn">发送</button>
            </div>
        </div>
    </div>
    <script>
        const chatMessages = document.getElementById('chatMessages');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');

        function addMessage(content, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        async function sendQuery() {
            const question = userInput.value.trim();
            if (!question) return;

            addMessage(question, 'user');
            userInput.value = '';
            addMessage('思考中...', 'bot');

            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: question})
                });
                const data = await response.json();

                // 移除最后的加载消息
                chatMessages.removeChild(chatMessages.lastChild);

                if (data.success) {
                    addMessage(data.answer, 'bot');
                } else {
                    addMessage(`错误: ${data.error}`, 'error');
                }
            } catch (error) {
                chatMessages.removeChild(chatMessages.lastChild);
                addMessage(`请求失败: ${error.message}`, 'error');
            }
        }

        sendBtn.addEventListener('click', sendQuery);
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendQuery();
            }
        });
    </script>
</body>
</html>"""

    template_path.write_text(default_template, encoding='utf-8')
    print(f"已创建默认模板: {template_path}")


@app.post("/query")
async def query_database(query: QueryRequest):
    """处理查询请求"""
    # 检查agent是否可用
    if agent is None:
        return QueryResponse(
            success=False,
            question=query.question,
            answer="",
            error="Agent未正确初始化，请检查数据库连接和配置",
            timestamp=datetime.now().isoformat()
        )

    try:
        print(f"收到查询: {query.question}")

        # 记录所有步骤
        steps = []
        final_answer = ""
        all_messages = []

        # 使用stream模式收集所有步骤
        for step in agent.stream(
                input={'messages': [{'role': 'user', 'content': query.question}]},
                stream_mode="values"
        ):
            messages = step.get('messages', [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    step_metadata = extract_step_metadata(last_message)
                    step_info = {
                        'timestamp': datetime.now().isoformat(),
                        'content': str(last_message.content)[:500],  # 限制长度
                        **step_metadata
                    }
                    steps.append(step_info)
                    all_messages.append(last_message)
                    final_answer = str(last_message.content)

        # 提取SQL和结果
        sql_queries, results = extract_sql_and_results(all_messages)

        # 保存到会话
        if query.session_id:
            response_data = {
                'answer': final_answer,
                'sql_queries': sql_queries,
                'results': results
            }
            session_manager.add_history(query.session_id, query.question, response_data)

        return QueryResponse(
            success=True,
            question=query.question,
            answer=final_answer,
            sql_queries=sql_queries,
            results=results,
            steps=steps,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return QueryResponse(
            success=False,
            question=query.question,
            answer="",
            error=str(e),
            timestamp=datetime.now().isoformat()
        )


@app.post("/query/stream")
async def query_database_stream(query: QueryRequest):
    """流式处理查询请求"""

    async def generate():
        try:
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.now().isoformat()})}\n\n"

            # 流式处理agent步骤
            for step in agent.stream(
                    input={'messages': [{'role': 'user', 'content': query.question}]},
                    stream_mode="values"
            ):
                messages = step.get('messages', [])
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        content = str(last_message.content)
                        step_metadata = extract_step_metadata(last_message)
                        step_data = {
                            'type': 'step',
                            'content': content,
                            'timestamp': datetime.now().isoformat(),
                            **step_metadata
                        }
                        yield f"data: {json.dumps(step_data, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.1)  # 小延迟，让前端更流畅

            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done', 'timestamp': datetime.now().isoformat()})}\n\n"

        except Exception as e:
            error_data = {
                'type': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/tables")
async def list_tables():
    """获取所有表名"""
    if not tools:
        return {"success": False, "error": "工具未初始化", "tables": []}

    try:
        list_tables_tool = tools[0]  # ListTablesTool
        result = list_tables_tool._run()

        # 解析结果
        tables = []
        if isinstance(result, str):
            # 根据实际输出格式解析
            lines = result.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('表') and not line.startswith('Table'):
                    # 移除可能的序号和点号
                    import re
                    table_name = re.sub(r'^\d+\.\s*', '', line)
                    if table_name:
                        tables.append(table_name)
        elif isinstance(result, list):
            tables = result
        else:
            tables = [str(result)]

        return {"success": True, "tables": tables}
    except Exception as e:
        print(f"获取表列表失败: {e}")
        return {"success": False, "error": str(e), "tables": []}


@app.get("/schema/{table_name}")
async def get_table_schema(table_name: str):
    """获取表结构"""
    if not tools:
        return {"success": False, "error": "工具未初始化"}

    try:
        schema_tool = tools[1]  # TableSchemaTool
        result = schema_tool._run(table_name)
        return {"success": True, "schema": str(result)}
    except Exception as e:
        print(f"获取表结构失败: {e}")
        return {"success": False, "error": str(e)}


@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """获取会话历史"""
    session = session_manager.get_or_create(session_id)
    return {"success": True, "history": session['history']}


@app.post("/clear_history/{session_id}")
async def clear_history(session_id: str):
    """清空会话历史"""
    session_manager.sessions[session_id] = {
        'history': [],
        'created_at': datetime.now()
    }
    return {"success": True}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_ready": agent is not None,
        "tools_ready": len(tools) > 0
    }


if __name__ == "__main__":
    import uvicorn

    print("=" * 50)
    print("启动FastAPI服务器...")
    print(f"模板目录: {templates_dir}")
    print(f"静态文件目录: {static_dir}")
    print("访问 http://localhost:8888 打开测试界面")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8888)