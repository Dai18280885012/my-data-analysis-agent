from rag_demo.rag_step3_retrieve import search_documents


MAX_DISTANCE = 0.70

QUERY_ALIASES = {
    "折扣打到九折": "订单折扣达到10%，折扣审批",
    "打九折": "订单折扣达到10%，折扣审批",
    "重点客户的标准": "重点客户定义 近12个月累计销售额",
    "重点客户标准": "重点客户定义 近12个月累计销售额",
    "产品保修期限": "产品免费保修期",
    "住宿报销标准": "住宿报销上限",
    
}

KEYWORD_GROUPS = {
    "折扣审批": ["折扣", "审批", "销售副总裁", "区域总监"],
    "重点客户": ["重点客户", "12个月", "10万元"],
    "住宿报销": ["住宿", "报销", "800元"],
    "产品保修": ["保修", "免费保修", "12个月"],
    "软件退货": ["软件", "退货", "无理由"],
}

def keyword_score(question, content):
    score = 0

    for keywords in KEYWORD_GROUPS.values():
        matched_question_words = [
            word for word in keywords
            if word in question
        ]

        matched_content_words = [
            word for word in keywords
            if word in content
        ]

        score += len(
            set(matched_question_words)
            & set(matched_content_words)
        )

    return score

def normalize_query(question):
    normalized_question = question

    for source, target in QUERY_ALIASES.items():
        normalized_question = normalized_question.replace(source, target)

    return normalized_question


def search_company_policy(question, top_k=2):
    normalized_question = normalize_query(question)
    results = search_documents(normalized_question, top_k=top_k)

    retrieved_chunks = []

    for index, document in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][index]
        distance = float(results["distances"][0][index])

        if distance <= MAX_DISTANCE:
            score = keyword_score(
                normalized_question,
                document,
            )
            retrieved_chunks.append(
                {
                    "排名": index + 1,
                    "来源": metadata["source"],
                    "文本块编号": metadata["chunk_id"],
                    "距离": round(distance, 4),
                    "关键词得分": score,
                    "内容": document,
                }
            )

    retrieved_chunks.sort(
        key=lambda item: (
            -item["关键词得分"],
            item["距离"],
        )
    )
    for rank, item in enumerate(retrieved_chunks, start=1):
        item["排名"] = rank
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
