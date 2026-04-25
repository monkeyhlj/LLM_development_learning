# base.py 深度解析

`base.py` 是 qwen_agent 工具系统的基础设施，定义了**工具注册机制**和**工具基类**。

---

## 1. 全局工具注册表 `TOOL_REGISTRY`

```python
TOOL_REGISTRY = {}  # 全局字典: tool_name → tool_class
```

所有工具都注册到这个字典中，框架通过名称查找和实例化工具。

---

## 2. `register_tool` 装饰器（L44-59）

标准 Python **decorator factory** 模式（带参数的装饰器）：

```python
@register_tool('my_image_gen')   # Step 1: register_tool('my_image_gen') 执行，返回 decorator
class MyImageGen(BaseTool): ...  # Step 2: decorator(MyImageGen) 执行，设置 name + 注册
```

等价于：

```python
class MyImageGen(BaseTool): ...
MyImageGen = register_tool('my_image_gen')(MyImageGen)
```

内部逻辑：

```python
def register_tool(name, allow_overwrite=False):
    def decorator(cls):
        # 1. 冲突检测：如果 cls.name 已有值且与 name 不同，报错
        # 2. cls.name = name          ← 设置类属性（所以子类不需要自己声明 name）
        # 3. TOOL_REGISTRY[name] = cls ← 注册到全局字典
        return cls
    return decorator
```

**关键点**：子类的 `name` 字段不需要手动声明，`register_tool` 装饰器自动设置。

---

## 3. `is_tool_schema` 函数（L62-106）

验证一个 dict 是否是合法的 OpenAI 兼容 JSON Schema。

核心技巧（L100-106）：

```python
try:
    jsonschema.validate(instance={}, schema=obj['parameters'])
except jsonschema.exceptions.SchemaError:
    return False          # schema 本身有问题（如 "type": "bogus"）
except jsonschema.exceptions.ValidationError:
    pass                  # schema 合法，只是 {} 不满足要求 — 无所谓
return True
```

- 传入 `instance={}` 是一个**巧妙的技巧**：目的是验证 schema 语法本身，而非验证数据
- `SchemaError` = schema 格式错误（真正关心的） → return False
- `ValidationError` = schema 没问题，空 dict 不符合要求（预期中的） → 忽略
- JSON Schema 的合法性由 **meta-schema** 定义（JSON Schema 规范自身发布的 schema，如 Draft 7）
- 例如 `"type": "bogus"` 不合法，因为 meta-schema 规定 type 只能是 `["array","boolean","integer","null","number","object","string"]`

---

## 4. `BaseTool` 抽象基类（L109-191）

所有工具的父类，定义工具的标准接口。

### 4.1 类属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | str | 工具名称，由 `register_tool` 设置，LLM 通过此名称调用工具 |
| `description` | str | 功能描述，LLM 据此决定何时使用该工具 |
| `parameters` | list 或 dict | 参数定义，支持两种格式（见下文） |

### 4.2 `__init__`（L114-123）

```python
def __init__(self, cfg=None):
    self.cfg = cfg or {}
    if not self.name:
        raise ValueError(...)       # name 必须已设置（register_tool 已完成）
    if isinstance(self.parameters, dict):
        if not is_tool_schema(...):  # 仅 dict 格式才校验 OpenAI schema
            raise ValueError(...)
```

**关于子类的 `__init__`**：
- 如果子类**不定义** `__init__`（如 `MyImageGen`）→ Python 自动调用 `BaseTool.__init__`，无需 `super()`
- 如果子类**重写** `__init__`（如 `DocParser`）→ 必须显式调用 `super().__init__(cfg)` 否则父类初始化被跳过

### 4.3 `call()` — 抽象方法（L125-138）

```python
@abstractmethod
def call(self, params: Union[str, dict], **kwargs) -> Union[str, list, dict, ...]:
    raise NotImplementedError
```

子类必须实现。这是工具的**实际执行入口**，接收 LLM 生成的参数，返回执行结果。

### 4.4 `_verify_json_format_args()` — 参数校验（L140-162）

**作用**：在 LLM 原始输出和工具逻辑之间的**安全守卫**。

```
LLM 生成: '{"query": "雇主责任险"}'  (原始字符串)
    ↓ _verify_json_format_args()
验证后:  {"query": "雇主责任险"}      (可信的 dict)
```

处理流程：
1. 字符串 → dict 解析（使用宽容的 `json_loads`，容忍 LLM 的小格式问题）
2. 校验 `required` 参数是否齐全
3. 如果 parameters 是 OpenAI dict 格式，用 `jsonschema` 做完整校验
4. 返回干净的 dict

**使用方式**：几乎所有工具的 `call()` 第一行都调用它：

```python
# retrieval.py, doc_parser.py, storage.py, keyword_search.py, ...
def call(self, params, **kwargs):
    params = self._verify_json_format_args(params)  # ← 第一行
    ...
```

### 4.5 Properties — 服务于两个受众

#### 给 LLM 看的（告诉 LLM 有哪些工具、怎么调用）：

| Property | 用途 | 调用位置 |
|----------|------|----------|
| `.function` | 返回 `{name, description, parameters}` dict | `fncall_agent.py:84` — 传给 LLM 的 functions 参数 |
| `.name_for_human` | 工具的人类可读名称 | `qwen_fncall_prompt.py:345` — 格式化 system prompt 中的工具描述 |
| `.args_format` | 告诉 LLM 用 JSON 格式传参 | `qwen_fncall_prompt.py:359` — 自动适配中英文 |

#### 给框架用的（控制工具执行行为）：

| Property | 用途 | 调用位置 |
|----------|------|----------|
| `.file_access` | 是否需要传入文件 | `fncall_agent.py:116` — 决定是否从消息中提取文件传给工具 |

### 4.6 参数的两种格式

```python
# 格式 1: Qwen 列表格式（大多数内置工具使用）
parameters = [{'name': 'query', 'type': 'string', 'description': '...', 'required': True}]

# 格式 2: OpenAI dict 格式（标准 JSON Schema）
parameters = {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
```

列表格式在 `_verify_json_format_args` 调用时校验；dict 格式在 `__init__` 时通过 `is_tool_schema` 校验。

---

## 5. `BaseToolWithFileAccess`（L193-217）

`BaseTool` 的扩展子类：

- `file_access` 返回 `True`（BaseTool 返回 False）
- 多一个 `work_dir`（默认 `workspace/tools/{tool_name}/`）
- `call()` 前自动将远程文件下载到本地工作目录
- `code_interpreter` 等需要操作文件的工具继承此类

---

## 6. 在 Agent Loop 中的完整角色

```
┌─ FnCallAgent._run() Agent Loop ──────────────────────────────────┐
│                                                                    │
│  1. 收集工具 schema:                                                │
│     functions = [tool.function for tool in self.function_map]      │
│         → 使用 .function 属性 (name + description + parameters)    │
│         → 使用 .name_for_human + .args_format 格式化 prompt        │
│                                                                    │
│  2. 调用 LLM:                                                      │
│     LLM 看到工具描述，生成 function_call (工具名 + 参数字符串)       │
│                                                                    │
│  3. 解析 LLM 输出 → tool_name + tool_args (原始字符串)              │
│                                                                    │
│  4. 执行工具:                                                       │
│     if tool.file_access → 额外传入消息中的文件                      │
│     tool.call(tool_args)                                           │
│       └→ _verify_json_format_args(tool_args) → 校验后的 dict        │
│       └→ 子类的实际逻辑运行                                         │
│                                                                    │
│  5. 工具结果追加到 messages → 回到步骤 2 继续循环                    │
└────────────────────────────────────────────────────────────────────┘
```

**总结**：`BaseTool` 的成员服务两个受众——properties 给 **LLM**（让它知道工具的存在和用法），`_verify_json_format_args` 和 `file_access` 给**框架**（安全地将 LLM 输出桥接到工具执行）。
