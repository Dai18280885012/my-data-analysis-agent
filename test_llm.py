import httpx
import os
from openai import OpenAI

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://www.rightapi.ai/codex/v1")
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

if not API_KEY:
    raise RuntimeError(
        "未找到 OPENAI_API_KEY，请先在当前 PowerShell 配置新的 API Key。"
    )

base_url = BASE_URL.rstrip("/") + "/"

http_client = httpx.Client(
    base_url=base_url,
    trust_env=False,
    timeout=60,
)

client = OpenAI(
    api_key=API_KEY,
    base_url=base_url,
    http_client=http_client,
)

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "user",
            "content": "请只回复：模型连接成功",
        }
    ],
)

print(response.choices[0].message.content)
