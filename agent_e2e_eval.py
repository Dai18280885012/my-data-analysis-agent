import re

from agent_service import run_agent_question


test_cases = [
    {
        "question": "订单折扣超过10%需要谁审批？",
        "expected_intent": "公司制度知识库检索",
        "expected_keywords": ["销售副总裁"],
    },
    {
        "question": "一线城市住宿最多报销多少？",
        "expected_intent": "公司制度知识库检索",
        "expected_keywords": ["800"],
    },
    {
        "question": "产品免费保修多久？",
        "expected_intent": "公司制度知识库检索",
        "expected_keywords": ["12"],
    },
    {
        "question": "公司年假有多少天？",
        "expected_intent": "公司制度知识库检索",
        "expected_keywords": ["资料不足"],
    },
    {
        "question": "哪个国家卖得最好？",
        "expected_intent": "国家销售分析",
        "expected_keywords": ["英国"],
    },
]


def normalize_text(text):
    return re.sub(r"\s+", "", text)


def run_evaluation():
    passed_count = 0

    for index, case in enumerate(test_cases, start=1):
        final_state = run_agent_question(
            question=case["question"],
            conversation_history=[],
        )

        answer = final_state["answer"]
        actual_intent = final_state["intent"]

        intent_passed = (
            actual_intent == case["expected_intent"]
        )

        normalized_answer = normalize_text(answer)

        answer_passed = all(
            normalize_text(keyword) in normalized_answer
            for keyword in case["expected_keywords"]
        )

        passed = intent_passed and answer_passed

        if passed:
            passed_count += 1
            status = "通过"
        else:
            status = "失败"

        print("\n" + "=" * 60)
        print(f"测试题 {index}：{case['question']}")
        print(f"测试结果：{status}")
        print(f"期望意图：{case['expected_intent']}")
        print(f"实际意图：{actual_intent}")
        print(f"意图是否正确：{intent_passed}")
        print(f"回答是否包含预期关键词：{answer_passed}")
        print(f"Agent 回答：{answer}")

    print("\n" + "=" * 60)
    print(
        f"端到端评估完成："
        f"{passed_count}/{len(test_cases)} 题通过"
    )


if __name__ == "__main__":
    run_evaluation()