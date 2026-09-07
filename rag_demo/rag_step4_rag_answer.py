import requests
import re

from rag_step3_retrieve import search_documents

def clean_answer(answer):
    return re.sub(
        r"<think>.*?</think>\s*",
        "",
        answer,
        flags=re.DOTALL,
    ).strip()


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "local-deepseek-data-agent"


def build_context(results):
    context_parts = []

    for index, document in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][index]

        context_parts.append(
            f"""[资料 {index + 1}]
来源：{metadata["source"]}
内容：
{document}"""
        )

    return "\n\n".join(context_parts)


def ask_rag(question):
    results = search_documents(question, top_k=2)
    context = build_context(results)

    prompt = f"""你是公司的制度问答助手。

请严格依据“参考资料”回答用户问题。
不能使用资料之外的知识，不能编造。
如果资料不足以回答，直接说“提供的资料不足以回答这个问题”。
回答后必须单独输出“来源”，注明引用的是哪份文件。

参考资料：
{context}

用户问题：{question}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 400,
            },
        },
        timeout=180,
    )

    response.raise_for_status()

    return {
        "answer": clean_answer(response.json()["response"]),
        "results": results,
    }


if __name__ == "__main__":
    question = "订单折扣超过10%需要谁审批？"

    result = ask_rag(question)

    print(f"\n问题：{question}")
    print("\nAgent 回答：")
    print(result["answer"])

    print("\n--- 本次检索来源 ---")
    for index, metadata in enumerate(result["results"]["metadatas"][0]):
        print(f"{index + 1}. {metadata['source']}，文本块 {metadata['chunk_id']}")