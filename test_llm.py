import httpx
from openai import OpenAI

API_KEY = "sk-fc23b1b4b5a7463798382421fb042824"
BASE_URL = "https://www.rightapi.ai/codex/v1"
MODEL = "gpt-5.6-luna"

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