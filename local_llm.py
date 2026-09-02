import json
import os
import re
from urllib.request import Request, urlopen


LOCAL_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "local-deepseek-data-agent",
)

LOCAL_CHAT_URL = os.getenv(
    "OLLAMA_CHAT_URL",
    "http://127.0.0.1:11434/api/chat",
)


def call_local_model(prompt, system_prompt=None):
    if system_prompt is None:
        system_prompt = (
            "你是一个数据分析 Agent 的意图识别模块。"
            "你必须只返回合法 JSON，"
            "不能返回解释、Markdown 或其他文字。"
        )
    request_data = {
        "model": LOCAL_MODEL,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    }

    request = Request(
        LOCAL_CHAT_URL,
        data=json.dumps(request_data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=180) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

    return result["message"]["content"].strip()


def extract_json(text):
    """
    DeepSeek-R1 可能会先输出思考过程，
    所以只提取第一个 JSON 对象。
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError(
            f"模型没有返回 JSON：{text}"
        )

    return json.loads(match.group())