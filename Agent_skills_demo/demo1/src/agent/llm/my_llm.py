from langchain_openai import ChatOpenAI

from src.agent.llm.env_utils import ZHIPU_KEY, ZHIPU_URL

llm = ChatOpenAI(
    model="glm-5.1",                     # Coding Plan 模型
    temperature=0.5,
    openai_api_key=ZHIPU_KEY,              # 使用相同的 key
    openai_api_base=ZHIPU_URL,                 # Coding Plan 端点
    max_tokens=4096,
)

# llm = ChatOpenAI(  # 第一种
#     model_name="deepseek-chat",
#     # model_name="deepseek-reasoner",
#     temperature=1.2,
#     api_key=DEEPSEEK_API_KEY,
#     base_url=DEEPSEEK_BASE_URL,
# )

# llm = ChatDeepSeek(  # 第一种
#     # model_name="deepseek-chat",
#     model_name="deepseek-reasoner",
#     temperature=1.3,
#     api_key=DEEPSEEK_API_KEY,
#     base_url=DEEPSEEK_BASE_URL,
# )
# resp = llm.invoke('用三句话简单介绍一下：机器学习的基本概念')
# print(type(resp))
# print(resp)
#
#
# llm = ChatDeepSeek(  # langchain-deepseek： 第二种
#     model_name="deepseek-r1-0528",
#     # model_name="deepseek-v3",
#     temperature=1.3,
#     api_key=ALIBABA_API_KEY,
#     api_base=ALIBABA_BASE_URL,
# )

# llm = BailianCustomChatModel(  # 自定义 的类来调用大模型： 第三种
#     model_name="deepseek-r1-0528",
#     api_key=ALIBABA_API_KEY,
#     base_url=ALIBABA_BASE_URL,
# )


# 在线的openai的大模型
# llm = ChatOpenAI(
#     model_name="gpt-4.1-mini",
#     temperature=0.5,
#     api_key=OPENAI_API_KEY,
#     base_url=OPENAI_BASE_URL,
# )

# llm = ChatOpenAI(
#     model='qwen3-max',
#     # model='qwen-plus',
#     # model='qwen3-8b',
#     temperature=0.6,
#     api_key=ALIBABA_API_KEY,
#     base_url=ALIBABA_BASE_URL,
# )


# 速率限制
# rate_limiter = InMemoryRateLimiter(
#     requests_per_second=0.1,  # 每10秒允许1个请求
#     check_every_n_seconds=0.1,  # 每100毫秒检查一次是否允许发出请求
#     max_bucket_size=10,  #  控制最大突发请求数量
# )

# llm = init_chat_model(  # V1.0后才有的写法
#     model="deepseek-r1-0528",
#     model_provider="openai",
#     api_key=ALIBABA_API_KEY,
#     base_url=ALIBABA_BASE_URL,
#     rate_limiter=rate_limiter
# )

# zhipuai_client = ZhipuAI(api_key=ZHIPU_API_KEY)