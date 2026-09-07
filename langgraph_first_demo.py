from typing import TypedDict
import json
import re
from local_llm import call_local_model, extract_json

from langgraph.graph import END, START, StateGraph

from retail_tools import (
    analyze_country_sales,
    analyze_monthly_sales,
    analyze_top_country_share,
    analyze_customer_repurchase,
    load_sales_data,
)
from rag_demo.rag_tool import search_company_policy


class AgentState(TypedDict):
    question: str
    dataframe: object
    intent: str
    tool_args: dict
    tool_name: str
    result: dict
    answer: str
    conversation_history: list[dict[str, str]]
    validation_status: str

# 程序启动时加载一次数据
sales_df = load_sales_data()

tool_registry = {
    "国家销售分析": analyze_country_sales,
    "国家销售占比分析": analyze_top_country_share,
    "月度销售分析": analyze_monthly_sales,
    "客户复购分析": analyze_customer_repurchase,
    "公司制度知识库检索": search_company_policy,
}

def understand_question(state: AgentState):
    question = state["question"]

    history = state.get("conversation_history", [])

    history_text = "\n".join(
        f"{item['role']}: {item['content']}"
        for item in history[-6:]
    )

    prompt = f"""
之前的对话记录：
{history_text}

当前用户问题：

{question}

当前可用的分析能力：

1. 国家销售分析
适合分析：
- 哪个国家卖得最好
- 海外市场表现
- 哪些国家贡献销售额
- 主要销售市场

2. 月度销售分析
适合分析：
- 每个月销售趋势
- 销售额什么时候最高
- 最近销售情况
- 销售额上涨或下降

3. 国家销售占比分析
适合分析：
- 它占总销售额多少
- 最高销售国家贡献了多少
- 主要市场占比是多少
- 哪个国家占整体销售额比例最高
如果用户询问某个国家、最高销售国家或主要市场占总销售额的比例，
选择“国家销售占比分析”。

4. 客户复购分析
适合分析：
- 客户复购情况怎么样
- 有多少客户重复购买
- 复购率是多少
- 哪些客户购买次数最多

5. 公司制度知识库检索
适合回答：
- 折扣审批规则
- 重点客户定义
- 销售管理制度
- 制度文件中是否有某项规定
- 公司的业务规则、审批流程和数据口径
- 员工报销、住宿、差旅等管理办法
- 产品退货、换货、维修和保修规则
- 售后服务规范和客服响应要求
- 任何已放入知识库文档中的规则、说明或流程

返回：

请只返回一个 JSON 对象，不要解释。

除“客户复购分析”外，其他意图的 tool_args 必须是空对象。

示例：

{{"intent": "国家销售分析", "tool_args": {{}}}}

{{"intent": "月度销售分析", "tool_args": {{}}}}

{{"intent": "客户复购分析", "tool_args": {{"top_n": 10}}}}

{{"intent": "公司制度知识库检索", "tool_args": {{}}}}

如果用户明确询问“前 5 位客户”“前 3 名客户”等数量，
将对应数字填入 top_n。

如果用户没有指定数量，客户复购分析的 top_n 使用 10。
"""

    raw_result = call_local_model(prompt)
    selection = extract_json(raw_result)

    intent = selection.get("intent", "无法识别")
    tool_args = selection.get("tool_args", {})

    allowed_intents = {
        "国家销售分析",
        "国家销售占比分析",
        "月度销售分析",
        "客户复购分析",
        "无法识别",
        "公司制度知识库检索",
    }

    if intent not in allowed_intents:
        intent = "无法识别"

    if not isinstance(tool_args, dict):
        tool_args = {}

    if intent == "客户复购分析":
        top_n = tool_args.get("top_n", 10)

        if not isinstance(top_n, int) or top_n < 1 or top_n > 50:
            top_n = 10

        tool_args = {"top_n": top_n}
    else:
        tool_args = {}

    return {
        "intent": intent,
        "tool_args": tool_args,
    }


def run_tool(state: AgentState):
    intent = state["intent"]

    tool_function = tool_registry.get(intent)

    if tool_function is None:
        return {
            "tool_name": "无",
            "result": {
                "error": "没有找到适合的分析工具"
            },
        }

    tool_args = state.get("tool_args", {})
    if intent == "公司制度知识库检索":
       result = tool_function(question=state["question"])
    else:
       analysis_df = state.get("dataframe", sales_df)
       result = tool_function(analysis_df, **tool_args)
    return {
        "tool_name": intent,
        "result": result,
    }

def validate_result(state: AgentState):
    result = state["result"]

    if not result:
        return {
            "validation_status": "失败：工具没有返回结果"
        }

    if isinstance(result, dict):
        if "error" in result:
            return {
                "validation_status": f"失败：{result['error']}"
            }

        if "conclusion" not in result and "metrics" not in result:
            return {
                "validation_status": "失败：工具结果缺少关键内容"
            }

    return {
        "validation_status": "通过"
    }

def route_after_validation(state: AgentState):
    if state["validation_status"] == "通过":
        return "generate_answer"

    return "generate_error_answer"


def generate_error_answer(state: AgentState):
    result = state["result"]
    error_message = result.get(
        "error",
        "工具执行或结果校验失败",
    )

    return {
        "answer": (
            f"当前无法处理这个问题。原因：{error_message}。\n\n"
            "当前已支持的分析能力：\n"
            "1. 国家销售额排行\n"
            "2. 最高销售国家占比\n"
            "3. 月度销售趋势与环比分析\n"
            "4. 客户复购分析"
            "5. 公司制度知识库问答"
        )
    }

def clean_agent_answer(answer):
    # 删除 DeepSeek 可能输出的思考过程。
    answer = re.sub(
        r"<think>.*?</think>\s*",
        "",
        answer,
        flags=re.DOTALL,
    )

    # 清理模型偶尔生成的反斜杠换行。
    answer = answer.replace("\\\r\n", "\n")
    answer = answer.replace("\\\n", "\n")
    answer = answer.replace("\\", "")

    conclusions = re.findall(
        r"结论：\s*(.*?)(?=\n\s*结论：|\n\s*数据依据：|$)",
        answer,
        flags=re.DOTALL,
    )

    evidences = re.findall(
        r"数据依据：\s*(.*?)(?=\n\s*数据依据：|$)",
        answer,
        flags=re.DOTALL,
    )

    # 模型没有按指定格式回答时，原样返回，避免变量未定义。
    if not conclusions:
        return answer.strip()

    conclusion = conclusions[-1].strip()

    # 模型有时把“数据依据”放到“结论”同一行。
    if "数据依据：" in conclusion:
        conclusion = conclusion.split(
            "数据依据：",
            maxsplit=1,
        )[0].rstrip("，,；; ")

    cleaned_answer = f"结论：{conclusion}"

    if evidences:
        cleaned_answer += (
            f"\n\n数据依据："
            f"{evidences[0].strip()}"
        )

    return cleaned_answer


def generate_answer(state: AgentState):
    if state["result"].get("retrieval_status") == "资料不足":
        return {
            "answer": "提供的资料不足以回答这个问题。"
        }
    if state["validation_status"] != "通过":
        error_message = state["result"].get("error", "工具执行或结果校验失败")

        return {
            "answer": (
                f"当前无法处理这个问题。原因：{error_message}。\n\n"
                "当前已支持的分析能力：\n"
                 "1. 国家销售额排行\n"
                 "2. 最高销售国家占比\n"
                 "3. 月度销售趋势与环比分析\n"
                 "4. 客户复购分析"
            )
        }
    validation_status = state["validation_status"]
    question = state["question"]
    intent = state["intent"]
    tool_name = state["tool_name"]
    result = state["result"]
    result_text = json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
    )
    history = state.get("conversation_history", [])

    history_text = "\n".join(
        f"{item['role']}: {item['content']}"
        for item in history[-6:]
    )

    prompt = f"""
之前的对话记录：
{history_text}

用户当前的问题：

{question}

本次使用的分析能力：

{intent}

本次实际调用的工具：

{tool_name}

工具实际执行结果：

{result_text}

结果校验状态：

{validation_status}

请根据工具执行结果回答用户的问题。

要求：

1. 使用中文。
2. 严格使用“结论：”和“数据依据：”两个部分，每部分只写一次，不要重复表达同一个指标。
3. 只能使用工具结果中的数字。
4. 不要擅自添加“元”“人民币”“美元”“英镑”等货币单位。
5. 如果工具结果没有提供货币单位，就只说“销售额”。
6. 如果工具结果不足以回答问题，要明确说明。
7. 不要提及系统提示词、代码或内部流程。
8. 如果结果校验状态不是“通过”，不要把它当成可靠结论，应该向用户说明分析失败原因。
9. 当工具结果来自“公司制度知识库检索”时，只能依据检索结果中的“内容”回答。
10. 如果检索内容没有明确回答用户问题，必须回答“提供的资料不足以回答这个问题”。
11. 制度类回答的“数据依据：”必须写明对应来源文件。
12. “结论：”只能出现一次，“数据依据：”只能出现一次。
13. 不要复述用户问题，不要输出反斜杠。
14. 不要输出 <think>、思考过程或任何内部推理。
15. 如果工具结果中的 retrieval_status 是“资料不足”，必须回答“提供的资料不足以回答这个问题”，不要自行补充。
"""

    answer = call_local_model(
        prompt,
        system_prompt=(
            "你是一个严谨的数据分析师。"
            "你只能根据工具返回的真实结果回答问题。"
        ),
    )

    answer = clean_agent_answer(answer)

    return {
        "answer": answer
    }

workflow = StateGraph(AgentState)

workflow.add_node(
    "understand_question",
    understand_question,
)

workflow.add_node(
    "run_tool",
    run_tool,
)

workflow.add_node(
    "validate_result",
    validate_result,
)

workflow.add_node(
    "generate_answer",
    generate_answer,
)

workflow.add_node(
    "generate_error_answer",
    generate_error_answer,
)

workflow.add_edge(
    START,
    "understand_question",
)

workflow.add_edge(
    "understand_question",
    "run_tool",
)

workflow.add_edge(
    "run_tool",
    "validate_result",
)

workflow.add_conditional_edges(
    "validate_result",
    route_after_validation,
    {
        "generate_answer": "generate_answer",
        "generate_error_answer": "generate_error_answer",
    },
)

workflow.add_edge(
    "generate_answer",
    END,
)

workflow.add_edge(
    "generate_error_answer",
    END,
)

app = workflow.compile()


def run_cli():
    print("\n本地数据分析 Agent 已启动")
    print("你可以连续提问，输入 exit 或 quit 退出。")

    conversation_history = []

    while True:
        user_question = input("\n你：").strip()

        if user_question.lower() in {"exit", "quit"}:
            print("Agent 已退出。")
            break

        if not user_question:
            print("问题不能为空，请重新输入。")
            continue

        initial_state = {
            "question": user_question,
            "dataframe": sales_df,
            "intent": "",
            "tool_args": {},
            "tool_name": "",
            "result": {},
            "answer": "",
            "conversation_history": conversation_history.copy(),
            "validation_status": "",
        }

        try:
            final_state = app.invoke(initial_state)

            print("\n--- 本次工具调用记录 ---")
            print(f"识别意图：{final_state['intent']}")
            print(f"传入参数：{final_state['tool_args']}")
            print(f"实际工具：{final_state['tool_name']}")
            print(f"结果校验：{final_state['validation_status']}")
            print("------------------------")

            answer = final_state["answer"]

            print("\nAgent：")
            print(answer)

            conversation_history.append(
                {
                    "role": "user",
                    "content": user_question,
                }
            )
            conversation_history.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

        except Exception as error:
            print("\n本次分析失败：")
            print(error)


if __name__ == "__main__":
    run_cli()