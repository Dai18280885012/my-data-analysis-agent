from rag_demo.rag_tool import search_company_policy
import re

test_cases = [
    {
        "question": "订单折扣超过10%需要谁审批？",
        "expected_source": "公司销售管理制度.txt",
        "expected_keyword": "销售副总裁",
    },
    {
        "question": "一线城市住宿最多报销多少？",
        "expected_source": "员工报销管理办法.docx",
        "expected_keyword": "800元",
    },
    {
        "question": "软件服务可以无理由退货吗？",
        "expected_source": "产品售后服务规范.pdf",
        "expected_keyword": "不支持无理由退货",
    },
    {
        "question": "产品免费保修多久？",
        "expected_source": "产品售后服务规范.pdf",
        "expected_keyword": "12个月",
    },
        {
        "question": "折扣打到九折需要谁批准？",
        "expected_source": "公司销售管理制度.txt",
        "expected_keyword": "区域总监",
    },
    {
        "question": "住宿报销标准是多少？",
        "expected_source": "员工报销管理办法.docx",
        "expected_keyword": "800元",
    },
    {
        "question": "产品保修期限是多久？",
        "expected_source": "产品售后服务规范.pdf",
        "expected_keyword": "12个月",
    },
    {
        "question": "软件购买后能不能退？",
        "expected_source": "产品售后服务规范.pdf",
        "expected_keyword": "不支持无理由退货",
    },
    {
        "question": "重点客户的标准是什么？",
        "expected_source": "公司销售管理制度.txt",
        "expected_keyword": "10万元",
    },
    {
        "question": "公司年假有多少天？",
        "expected_source": None,
        "expected_keyword": None,
        "expect_no_result": True,
    },
]

def normalize_text(text):
    return re.sub(
        r"\s+",
        "",
        text,
    )


def run_evaluation():
    passed_count = 0

    for index, case in enumerate(test_cases, start=1):
        result = search_company_policy(case["question"])

        chunks = result["table"]
        sources = [chunk["来源"] for chunk in chunks]
        content = "\n".join(
            chunk["内容"]
            for chunk in chunks
        )

        if case.get("expect_no_result"):
            source_passed = len(sources) == 0
            keyword_passed = result.get("retrieval_status") == "资料不足"
            passed = source_passed and keyword_passed
        else:
            source_passed = case["expected_source"] in sources
            keyword_passed = (
                normalize_text(case["expected_keyword"])
                in normalize_text(content)
            )
            passed = source_passed and keyword_passed

        if passed:
            passed_count += 1
            status = "通过"
        else:
            status = "失败"

        print("\n" + "=" * 60)
        print(f"测试题 {index}：{case['question']}")
        print(f"测试结果：{status}")
        if case.get("expect_no_result"):
            print("期望行为：没有召回相关资料并拒答")
            print(f"实际状态：{result.get('retrieval_status')}")
            print(f"实际来源：{sources}")
        else:
            print(f"期望来源：{case['expected_source']}")
            print(f"实际来源：{sources}")
            print(f"期望关键词：{case['expected_keyword']}")
            print(f"是否召回关键词：{keyword_passed}")

    print("\n" + "=" * 60)
    print(
        f"检索评估完成："
        f"{passed_count}/{len(test_cases)} 题通过"
    )


if __name__ == "__main__":
    run_evaluation()