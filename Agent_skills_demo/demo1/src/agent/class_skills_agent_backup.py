from langchain.agents import create_agent, AgentState
from langchain_mcp_adapters.client import MultiServerMCPClient
from agent.llm.log_utils import log
from agent.llm.my_llm import llm
from agent.mcp_tool_config import gaode_mcp_server_config, my12306_mcp_server_config, analysis_mcp_server_config
from agent.skills_list import SKILLS
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.tools import BaseTool, tool, InjectedToolCallId
from typing import Callable, List, Dict

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
        "data_analysis": all_tools.get("fenxi", [])
    }
    return skill_tool_mapping.get(skill_name, [])


class SkillMiddleware(AgentMiddleware):
    """优化后的技能中间件：减少冗余日志输出"""

    def __init__(self, all_tools: Dict[str, List[BaseTool]]):
        super().__init__()
        self.all_tools = all_tools
        self.base_tools = [load_skill]
        self._pre_register_all_tools()

        # 优化缓存机制
        self.last_skills_loaded = set()  # 使用集合提高查找效率
        self.logged_skill_tools = set()  # 新增：记录已日志过的技能工具组合

    def _pre_register_all_tools(self):
        """预先注册所有工具到中间件"""
        all_tool_instances = []
        for tool_category in self.all_tools.values():
            all_tool_instances.extend(tool_category)
        self.tools = all_tool_instances + self.base_tools

    async def awrap_model_call(
            self,
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        """异步方法： 异步中间中间件"""

        try:
            # 获取当前已加载的技能
            current_skills = set(request.state.get('skills_loaded', []))

            # 优化：使用集合运算检测技能变化
            newly_loaded_skills = current_skills - self.last_skills_loaded
            removed_skills = self.last_skills_loaded - current_skills

            # 只在技能状态实际变化时输出日志
            if newly_loaded_skills or removed_skills:
                log.info(f"技能状态变化: 加载→{newly_loaded_skills}, 移除→{removed_skills}")
                self.last_skills_loaded = current_skills.copy()

                # 技能变化时重置工具日志记录
                self.logged_skill_tools.clear()

            # 构建动态工具列表
            dynamic_tools = self.base_tools.copy()

            # 关键修复：确保每个技能的工具加载日志只输出一次
            for skill in current_skills:
                skill_tools = get_tools_by_skill(skill, self.all_tools)
                if skill_tools:
                    # 为当前技能生成唯一标识
                    skill_tools_key = f"{skill}_{len(skill_tools)}"

                    # 只有未记录过的技能工具组合才输出日志
                    if skill_tools_key not in self.logged_skill_tools:
                        log.info(f"加载技能 '{skill}' 的工具，数量: {len(skill_tools)}")
                        self.logged_skill_tools.add(skill_tools_key)

                    dynamic_tools.extend(skill_tools)

            # 调试信息：只在调试模式下输出详细工具列表
            tool_names = [tool.name for tool in dynamic_tools if hasattr(tool, 'name')]
            log.debug(f"当前可用工具: {tool_names}")

            # 构建简化的技能提示信息
            skills_prompt = self._build_skills_prompt(current_skills)

            # 更新系统消息（避免重复累积）
            new_system_message = self._update_system_message(request, skills_prompt)

            # 创建修改后的请求
            modified_request = request.override(
                tools=dynamic_tools,
                system_message=new_system_message
            )

            # 异步调用处理器
            response = await handler(modified_request)

            return response

        except Exception as e:
            log.error(f"技能中间件执行错误: {e}")
            # 出错时回退到基础工具
            fallback_request = request.override(tools=self.base_tools)
            return await handler(fallback_request)

    def _build_skills_prompt(self, current_skills: set) -> str:
        """构建技能提示信息"""
        if not current_skills:
            return "\n## 技能状态\n当前未加载技能，请使用 load_skill 工具加载所需技能。"

        skill_list = ", ".join(sorted(current_skills))  # 排序确保输出一致性
        return f"\n## 技能状态\n已加载技能: {skill_list}"

    def _update_system_message(self, request: ModelRequest, skills_prompt: str) -> SystemMessage:
        """更新系统消息，避免重复累积"""
        current_system_message = getattr(request, 'system_message', None)
        if current_system_message and hasattr(current_system_message, 'content'):
            current_content = str(current_system_message.content)

            # 更精确地移除旧技能提示
            lines = current_content.split('\n')
            clean_lines = []
            skip_next = False
            for line in lines:
                if line.startswith('## 技能状态'):
                    skip_next = True  # 跳过技能状态行
                    continue
                if skip_next and line.strip() == "":
                    skip_next = False  # 遇到空行后停止跳过
                    continue
                if not skip_next:
                    clean_lines.append(line)

            clean_content = '\n'.join(clean_lines).strip()
            new_content = clean_content + skills_prompt
        else:
            new_content = skills_prompt

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
        "fenxi": analysis_mcp_server_config,
    })

    # 获取所有工具并按服务器分类
    gaode_tools = await mcp_client.get_tools(server_name="gaode")
    railway_tools = await mcp_client.get_tools(server_name="12306")
    fenxi_tools = await mcp_client.get_tools(server_name="fenxi")

    print(f'所有工具数量 - 高德: {len(gaode_tools)}, 铁路: {len(railway_tools)}, 分析: {len(fenxi_tools)}')

    # 验证工具名称
    print("工具名称验证:")
    for i, tool in enumerate(gaode_tools + railway_tools + fenxi_tools):
        tool_name = getattr(tool, 'name', '未知名称')
        print(f"工具 {i + 1}: {tool_name}")

    # 按类别组织工具
    categorized_tools = {
        "gaode": gaode_tools,
        "12306": railway_tools,
        "fenxi": fenxi_tools
    }

    # 创建具备真正技能支持的单智能体
    agent = create_agent(
        model=llm,
        tools=[load_skill],  # 初始只暴露load_skill工具
        middleware=[SkillMiddleware(categorized_tools)],
        state_schema=SkillState,
        system_prompt="""您是一个多功能智能助手，采用渐进式技能加载架构。

请严格遵循以下工作流程：
1. 首先分析用户请求属于哪个技能领域
2. 使用load_skill工具加载相应的技能说明
3. 技能加载后，系统会自动提供该领域的专用工具
4. 按照技能说明中的指导使用合适的工具
5. 提供专业、准确的回答

可用技能领域：
- 高德导航 (gaode_navigation): 地图导航、路径规划
- 铁路查询 (railway_booking): 火车票查询、预订
- 数据分析 (data_analysis): 数据统计、分析报告

请先加载技能，再使用相应工具！""",
    )

    return agent


# 创建基于Skills架构的智能体
skills_agent = asyncio.run(create_skills_based_agent())
