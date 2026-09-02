from rag_demo.rag_step3_retrieve import search_documents


MAX_DISTANCE = 0.70


def search_company_policy(question, top_k=2):
    results = search_documents(question, top_k=top_k)

    retrieved_chunks = []

    for index, document in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][index]
        distance = float(results["distances"][0][index])

        # 距离越小，问题和资料的语义越接近。
        if distance <= MAX_DISTANCE:
            retrieved_chunks.append(
                {
                    "排名": index + 1,
                    "来源": metadata["source"],
                    "文本块编号": metadata["chunk_id"],
                    "距离": round(distance, 4),
                    "内容": document,
                }
            )

    if not retrieved_chunks:
        return {
            "tool_name": "公司制度知识库检索",
            "table": [],
            "metrics": {
                "召回片段数": 0,
            },
            "retrieval_status": "资料不足",
        }

    return {
        "tool_name": "公司制度知识库检索",
        "table": retrieved_chunks,
        "metrics": {
            "召回片段数": len(retrieved_chunks),
        },
        "retrieval_status": "已找到相关资料",
    }