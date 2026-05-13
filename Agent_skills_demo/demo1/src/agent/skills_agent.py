from langchain.agents import create_agent, AgentState
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.agent.llm.log_utils import log
from src.agent.llm.my_llm import llm
from src.agent.mcp_tool_config import gaode_mcp_server_config, my12306_mcp_server_config
from src.agent.skills_list import SKILLS, build_skill_catalog_text
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool, tool, InjectedToolCallId
from typing import Any, Callable, List, Dict
from pathlib import Path
import importlib.util

from typing_extensions import Annotated
from langgraph.types import Command
import asyncio


# 定义技能状态Schema
class SkillState(AgentState):
    """技能状态管理"""
    skills_loaded: Annotated[List[str], lambda current, new: current + [s for s in new if s not in current]] = []


# 技能映射到具体工具的函数
def get_tools_by_skill(skill_name: str, all_tools: Dict[str, List[BaseTool]]) -> List[BaseTool]:
    """根据技能名称获取对应的工具列表"""
    skill_tool_mapping = {
        "gaode_navigation": all_tools.get("gaode", []),
        "railway_booking": all_tools.get("12306", []),
        "weather_query": all_tools.get("weather", []),
    }
    return skill_tool_mapping.get(skill_name, [])


def _call_local_weather_script(city: str) -> dict:
    """从 weather skill 的 scripts 目录动态加载并调用本地假天气函数。"""
    script_path = Path(__file__).with_name("skills") / "weather_query" / "scripts" / "fake_weather_service.py"
    fallback = {
        "city": city,
        "condition": "未知",
        "temperature_c": 25,
        "humidity": 50,
    }

    if not script_path.exists():
        return fallback

    spec = importlib.util.spec_from_file_location("weather_query_fake_weather_service", script_path)
    if spec is None or spec.loader is None:
        return fallback

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    getter = getattr(module, "get_fake_weather", None)
    if getter is None:
        return fallback
    return getter(city)


@tool("weather_query")
async def weather_query(city: str) -> str:
    """查询指定城市天气（本地模拟数据，不调用真实 API）。"""
    weather = _call_local_weather_script(city)
    return (
        f"城市: {weather['city']}\n"
        f"天气: {weather['condition']}\n"
        f"温度: {weather['temperature_c']}°C\n"
        f"湿度: {weather['humidity']}%"
    )


class SkillMiddleware(AgentMiddleware):
    """
    优化后的技能中间件：实现渐进式工具加载和智能日志管理

    核心功能：
    1. 动态工具过滤：根据已加载技能动态调整可用工具列表
    2. 状态感知：监控技能加载状态变化并相应调整行为
    3. 智能日志：避免重复日志输出，提升调试效率
    4. 错误恢复：在异常情况下优雅降级到基础工具集

    设计原理：
    基于Claude Skills架构，通过中间件拦截模型调用请求，实现工具的动态加载和卸载。
    这种架构解决了传统Agent一次性暴露所有工具导致的"工具过多降智"问题[1](@ref)。
    """

    def __init__(self, all_tools: Dict[str, List[BaseTool]]):
        """
        初始化技能中间件

        参数:
            all_tools: 字典，按技能类别分类的所有可用工具
                格式: {"技能类别名": [工具列表], ...}
                例如: {"gaode": [map_tool1, map_tool2], "12306": [train_tool1, train_tool2]}

        初始化过程:
            1. 调用父类初始化
            2. 存储工具分类字典
            3. 设置基础工具（始终可用的工具，如load_skill）
            4. 预注册所有工具到中间件系统
            5. 初始化状态缓存机制[2](@ref)
        """
        super().__init__()  # 调用父类AgentMiddleware的初始化方法
        self.all_tools = all_tools  # 存储按类别分类的所有工具
        self.base_tools = [load_skill]  # 基础工具：始终对Agent可见的工具

        # 预注册所有工具到中间件，确保系统能识别所有工具名称
        self._pre_register_all_tools()

        # 初始化状态缓存机制，用于优化性能和避免重复日志
        self.last_skills_loaded = set()  # 上次已加载的技能集合（使用集合提高查找效率）
        self.logged_skill_tools = set()  # 已记录过日志的技能工具组合（避免重复输出）

    def _pre_register_all_tools(self):
        """
        预先注册所有工具到中间件系统

        为什么需要预注册：
        - LangChain中间件机制要求所有可能使用的工具必须在中间件中预注册
        - 否则在动态添加工具时会报"unknown tool names"错误
        - 这确保了系统能正确识别和验证所有工具名称

        实现步骤：
        1. 从分类工具字典中提取所有工具实例
        2. 合并基础工具和分类工具
        3. 将合并后的工具列表注册到中间件的tools属性[2](@ref)
        """
        # 收集所有分类工具实例
        all_tool_instances = []
        for tool_category in self.all_tools.values():
            all_tool_instances.extend(tool_category)

        # 合并基础工具和分类工具，并注册到中间件
        self.tools = all_tool_instances + self.base_tools

    async def awrap_model_call(
            self,
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        """
        异步模型调用包装方法 - 中间件的核心逻辑

        执行流程：
        1. 状态检测：检查当前已加载的技能状态
        2. 工具过滤：根据技能状态动态构建工具列表
        3. 提示更新：更新系统消息中的技能提示信息
        4. 请求修改：创建包含过滤后工具的新请求
        5. 调用处理：将修改后的请求传递给下一个处理器

        参数:
            request: ModelRequest - 包含当前模型调用请求的所有信息
                - messages: 消息历史
                - tools: 当前可用工具列表
                - state: 当前Agent状态（包含skills_loaded等）
            handler: Callable - 下一个中间件或最终模型调用的处理器

        返回:
            ModelResponse - 模型调用响应结果[7](@ref)
        """
        try:
            # ==================== 1. 技能状态检测 ====================
            # 从请求状态中获取当前已加载的技能列表，转换为集合提高查找效率
            current_skills = set(request.state.get('skills_loaded', []))

            # 使用集合运算检测技能状态变化（新增和移除的技能）
            newly_loaded_skills = current_skills - self.last_skills_loaded  # 新增技能
            removed_skills = self.last_skills_loaded - current_skills  # 移除技能

            # 只在技能状态实际发生变化时输出变更日志（优化性能）
            if newly_loaded_skills or removed_skills:
                log.info(f"技能状态变化: 加载→{newly_loaded_skills}, 移除→{removed_skills}")
                # 更新缓存状态
                self.last_skills_loaded = current_skills.copy()
                # 技能变化时清空工具日志记录，确保新技能的工具日志能正常输出
                self.logged_skill_tools.clear()

            # ==================== 2. 动态工具列表构建 ====================
            # 始终包含基础工具（如load_skill）
            dynamic_tools = self.base_tools.copy()

            # 遍历当前已加载的技能，添加对应的工具
            for skill in current_skills:
                # 获取该技能对应的工具列表
                skill_tools = get_tools_by_skill(skill, self.all_tools)
                if skill_tools:
                    # 为当前技能工具组合生成唯一标识（技能名+工具数量）
                    skill_tools_key = f"{skill}_{len(skill_tools)}"

                    # 确保每个技能的工具加载日志只输出一次（避免重复）
                    if skill_tools_key not in self.logged_skill_tools:
                        log.info(f"加载技能 '{skill}' 的工具，数量: {len(skill_tools)}")
                        self.logged_skill_tools.add(skill_tools_key)  # 标记为已记录

                    # 将技能工具添加到动态工具列表
                    dynamic_tools.extend(skill_tools)

            # ==================== 3. 调试信息输出 ====================
            # 只在调试模式下输出详细的工具列表信息（生产环境可关闭）
            tool_names = [tool.name for tool in dynamic_tools if hasattr(tool, 'name')]
            log.debug(f"当前可用工具: {tool_names}")

            # ==================== 4. 系统消息更新 ====================
            # 构建反映当前技能状态的提示信息
            skills_prompt = self._build_skills_prompt(current_skills)
            # 更新系统消息，避免提示信息重复累积
            new_system_message = self._update_system_message(request, skills_prompt)

            # ==================== 5. 请求修改和处理器调用 ====================
            # 创建修改后的请求对象，包含过滤后的工具和更新的系统消息
            modified_request = request.override(
                tools=dynamic_tools,  # 动态过滤后的工具列表
                system_message=new_system_message  # 更新后的系统消息
            )

            # 异步调用下一个处理器（可能是下一个中间件或最终的模型调用）
            response = await handler(modified_request)

            return response

        except Exception as e:
            # ==================== 6. 异常处理 ====================
            # 记录错误信息，包括详细的异常堆栈
            log.error(f"技能中间件执行错误: {e}", exc_info=True)

            # 优雅降级：出错时回退到基础工具集，确保Agent基本功能可用
            fallback_request = request.override(tools=self.base_tools)
            return await handler(fallback_request)

    def _build_skills_prompt(self, current_skills: set[str]) -> str:
        """
        构建技能状态提示信息

        参数:
            current_skills: 当前已加载的技能集合

        返回:
            str: 格式化后的技能状态提示文本[6](@ref)
        """
        if not current_skills:
            return "\n## 技能状态\n当前未加载技能，请使用 load_skill 工具加载所需技能。"

        # 对技能名称进行排序，确保输出的一致性（避免随机顺序）
        skill_list = ", ".join(sorted(current_skills))
        return f"\n## 技能状态\n已加载技能: {skill_list}"

    def _update_system_message(self, request: ModelRequest, skills_prompt: str) -> SystemMessage:
        """
        更新系统消息，避免提示信息重复累积

        问题背景：
        - 每次模型调用都会添加技能提示，如果不清理会导致提示信息无限增长
        - 这会造成token浪费和上下文窗口污染

        解决方案：
        1. 检查现有系统消息内容
        2. 移除旧的技能状态提示部分
        3. 添加新的技能状态提示[3](@ref)

        参数:
            request: 当前模型请求对象
            skills_prompt: 新的技能提示文本

        返回:
            SystemMessage: 更新后的系统消息对象
        """
        # 获取当前系统消息对象
        current_system_message = getattr(request, 'system_message', None)

        if current_system_message and hasattr(current_system_message, 'content'):
            # 将当前内容转换为字符串
            current_content = str(current_system_message.content)

            # 按行分割内容，便于逐行处理
            lines = current_content.split('\n')
            clean_lines = []  # 存储清理后的行
            skip_next = False  # 标记是否跳过当前行（用于跳过技能状态相关行）

            # 遍历每一行，移除旧的技能状态提示
            for line in lines:
                if line.startswith('## 技能状态'):
                    skip_next = True  # 遇到技能状态标题行，开始跳过
                    continue
                if skip_next and line.strip() == "":
                    skip_next = False  # 遇到空行，停止跳过
                    continue
                if not skip_next:
                    clean_lines.append(line)  # 保留非技能状态相关行

            # 重新组合清理后的内容
            clean_content = '\n'.join(clean_lines).strip()
            # 添加新的技能提示信息
            new_content = clean_content + skills_prompt
        else:
            # 如果没有现有系统消息，直接使用技能提示作为内容
            new_content = skills_prompt

        # 创建新的系统消息对象
        return SystemMessage(content=new_content)


# 优化后的 load_skill 工具
@tool
async def load_skill(skill_name: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
    """将技能的完整内容加载到智能体的上下文中。"""

    log.info(f"正在查找技能: {skill_name}")

    for skill in SKILLS:
        if skill["name"] == skill_name:
            log.info(f"✅ 技能加载成功: {skill_name}")
            return Command(
                update={
                    "messages": [ToolMessage(
                        content=f"已加载技能: {skill_name}\n\n{skill['content']}",
                        tool_call_id=tool_call_id
                    )],
                    "skills_loaded": [skill_name]
                }
            )

    # 未找到技能
    available = ", ".join(s["name"] for s in SKILLS)
    log.warning(f"技能未找到: {skill_name}，可用技能: {available}")
    return Command(
        update={
            "messages": [ToolMessage(
                content=f"未找到技能 '{skill_name}'。可用技能: {available}",
                tool_call_id=tool_call_id
            )]
        }
    )


# 创建基于Skills架构的智能体
async def create_skills_based_agent():
    # 创建MCP客户端获取所有工具
    mcp_client = MultiServerMCPClient({
        "gaode": gaode_mcp_server_config,
        "12306": my12306_mcp_server_config,
    })

    # 获取所有工具并按服务器分类
    gaode_tools = await mcp_client.get_tools(server_name="gaode")
    railway_tools = await mcp_client.get_tools(server_name="12306")
    # fenxi_tools = await mcp_client.get_tools(server_name="fenxi")

    print(f'所有工具数量 - 高德: {len(gaode_tools)}, 铁路: {len(railway_tools)}')

    # 验证工具名称
    print("工具名称验证:")
    for i, tool in enumerate(gaode_tools + railway_tools):
        tool_name = getattr(tool, 'name', '未知名称')
        print(f"工具 {i + 1}: {tool_name}")

    # 按类别组织工具
    categorized_tools = {
        "gaode": gaode_tools,
        "12306": railway_tools,
        "weather": [weather_query],
    }

    # 创建具备真正技能支持的单智能体
    agent = create_agent(
        model=llm,
        tools=[load_skill],  # 初始只暴露load_skill工具
        middleware=[SkillMiddleware(categorized_tools)],
        state_schema=SkillState,
        system_prompt=f"""您是一个多功能智能助手，采用渐进式技能加载架构。

请严格遵循以下工作流程：
1. 首先分析用户请求属于哪个技能领域
2. 使用load_skill工具加载相应的技能说明
3. 技能加载后，系统会自动提供该领域的专用工具
4. 按照技能说明中的指导使用合适的工具
5. 提供专业、准确的回答

可用技能领域：
{build_skill_catalog_text()}

请先加载技能，再使用相应工具！""",
    )

    return agent


class SkillsAgentRunner:
    """为 LangGraph agent 提供兼容的多轮 handle_message 接口。"""

    def __init__(self):
        self._agent = None
        self._messages: List[BaseMessage] = []
        self._skills_loaded: List[str] = []
        self._last_tool_calls: List[str] = []

    async def _get_agent(self):
        if self._agent is None:
            self._agent = await create_skills_based_agent()
        return self._agent

    async def handle_message(self, message: str) -> str:
        agent = await self._get_agent()
        result = await agent.ainvoke({
            "messages": [*self._messages, HumanMessage(content=message)],
            "skills_loaded": self._skills_loaded,
        })

        self._messages = result.get("messages", self._messages)
        self._skills_loaded = result.get("skills_loaded", self._skills_loaded)
        self._last_tool_calls = self._extract_tool_calls(self._messages)
        return self._extract_text_response(result)

    def get_loaded_skills(self) -> List[str]:
        return list(self._skills_loaded)

    def get_last_tool_calls(self) -> List[str]:
        return list(self._last_tool_calls)

    @staticmethod
    def _extract_tool_calls(messages: List[BaseMessage]) -> List[str]:
        called_tools: List[str] = []
        for message in messages:
            tool_calls = getattr(message, "tool_calls", None)
            if not tool_calls:
                continue
            for call in tool_calls:
                name = call.get("name") if isinstance(call, dict) else None
                if name:
                    called_tools.append(name)
        return called_tools

    def _extract_text_response(self, result: Dict[str, Any]) -> str:
        messages = result.get("messages", [])
        for message in reversed(messages):
            content = getattr(message, "content", "")
            if not content:
                continue
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                text_parts = [
                    item.get("text", "")
                    for item in content
                    if isinstance(item, dict) and item.get("type") == "text"
                ]
                if text_parts:
                    return "\n".join(part for part in text_parts if part)
        return str(result)


# 创建基于Skills架构的智能体
skills_agent = SkillsAgentRunner()
