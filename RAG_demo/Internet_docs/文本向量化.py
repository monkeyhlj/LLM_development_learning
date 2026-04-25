import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.environ['api_key'],  # 如果您没有配置环境变量，请在此处用您的API Key进行替换
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # 百炼服务的base_url
)

completion = client.embeddings.create(
    model="text-embedding-v3",
    input="['免费资源bin3.cn\n[全部免费无套路]\nQQ群912671597','免费资源bin3.cn\n[全部免费无套路]\nQQ群912671597','免费资源bin3.cn\n[全部免费无套路]\nQQ群912671597','免费资源bin3.cn\n[全部免费无套路]\nQQ群912671597','免费资源bin3.cn\n[全部免费无套路]\nQQ群912671597','免费资源bin3.cn\n[全部免费无套路]\nQQ群912671597','免费资源bin3.cn\n[全部免费无套路]\nQQ群912671597','免费资源bin3.cn\n[全部免费无套路]\nQQ群912671597','免费资源bin3.cn\n[全部免费无套路]\nQQ群912671597','免费资源bin3.cn\n[全部免费无套路]\nQQ群912671597','免费资源bin3.cn\n[全部免费无套路]\nQQ群912671597','免费资源bin3.cn\n[全部免费无套路]\nQQ群912671597']",
    dimensions=1024, # 指定向量维度（仅 text-embedding-v3 支持该参数）
    encoding_format="float"
)

print(completion.model_dump_json())