from rag_step4_rag_answer import ask_rag


print("本地 RAG 制度问答已启动。")
print("输入 exit 或 quit 退出。")

while True:
    question = input("\n你：").strip()

    if question.lower() in ["exit", "quit"]:
        print("已退出。")
        break

    if not question:
        continue

    try:
        result = ask_rag(question)

        print("\nAgent：")
        print(result["answer"])

        print("\n--- 本次检索来源 ---")
        for index, metadata in enumerate(result["results"]["metadatas"][0]):
            print(
                f"{index + 1}. "
                f"{metadata['source']}，"
                f"文本块 {metadata['chunk_id']}"
            )

    except Exception as error:
        print(f"\n本次问答失败：{error}")