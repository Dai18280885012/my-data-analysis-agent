import pandas as pd
from urllib.request import Request, urlopen
import json

file_path = "sales_demo.xls"

df = pd.read_excel(file_path)

print("数据前 5 行：")
print(df.head())

print("\n字段名称：")
print(df.columns.tolist())
print("\n数据行数：")
print(len(df))
print("\n每列空值数量：")
print(df.isna().sum())

print("\n重复行数量：")
print(df.duplicated().sum())

print("\n每列的数据类型：")
print(df.dtypes)
department_sales = (
    df.groupby("部门")["销售额"]
    .sum()
    .sort_values(ascending=False)
)

print("\n各部门销售额汇总：")
print(department_sales)
df["利润"] = df["销售额"] - df["成本"]

df["利润率"] = df["利润"] / df["销售额"]

print("\n新增利润后的前 5 行：")
print(df[["月份", "部门", "品类", "销售额", "成本", "利润", "利润率"]].head())

department_profit = (
    df.groupby("部门")[["销售额", "成本", "利润"]]
    .sum()
)

department_profit["利润率"] = (
    department_profit["利润"] / department_profit["销售额"]
)

print("\n各部门销售额、成本、利润和利润率：")
print(department_profit)
department_profit["利润率"] = (
    department_profit["利润率"] * 100
).round(2)

print("\n各部门经营汇总（利润率已转换为百分比）：")
print(department_profit)
LOCAL_MODEL = "local-deepseek-data-agent"
LOCAL_CHAT_URL = "http://127.0.0.1:11434/api/chat"


def call_local_model(prompt):
    request_data = {
        "model": LOCAL_MODEL,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": "你是数据分析 Agent 的工具选择器，只返回合法 JSON，不要输出其他文字。",
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
        result = json.loads(response.read().decode("utf-8"))

    return result["message"]["content"].strip()
def analyze_monthly_sales(df):
    monthly_sales = (
        df.groupby("月份")["销售额"]
        .sum()
        .sort_index()
    )

    monthly_report = monthly_sales.to_frame(name="销售额")

    monthly_report["环比变化额"] = monthly_report["销售额"].diff()

    monthly_report["环比变化率"] = (
        monthly_report["销售额"].pct_change() * 100
    ).round(2)

    latest_month = monthly_report.index[-1]
    latest_sales = monthly_report.loc[latest_month, "销售额"]
    change_amount = monthly_report.loc[latest_month, "环比变化额"]
    change_rate = monthly_report.loc[latest_month, "环比变化率"]

    if change_amount > 0:
        trend = "上涨"
    elif change_amount < 0:
        trend = "下降"
    else:
        trend = "持平"

    conclusion = (
        f"{latest_month.strftime('%Y年%m月')}销售额为 {latest_sales:,.0f} 元，"
        f"较上月{trend} {abs(change_amount):,.0f} 元，"
        f"环比变化 {abs(change_rate):.2f}%。"
    )

    return monthly_report, conclusion


monthly_report, conclusion = analyze_monthly_sales(df)

print("\n每月销售额与环比变化：")
print(monthly_report)

print("\n自动生成的业务结论：")
print(conclusion)

def analyze_department_profit(df):
    report = (
        df.groupby("部门")[["销售额", "成本", "利润"]]
        .sum()
    )

    report["利润率"] = (
        report["利润"] / report["销售额"] * 100
    ).round(2)

    report = report.sort_values("销售额", ascending=False)

    best_sales_department = report.index[0]
    best_sales = report.iloc[0]["销售额"]

    best_margin_department = report["利润率"].idxmax()
    best_margin = report.loc[best_margin_department, "利润率"]

    conclusion = (
        f"销售额最高的是{best_sales_department}，"
        f"销售额为 {best_sales:,.0f} 元；"
        f"利润率最高的是{best_margin_department}，"
        f"利润率为 {best_margin:.2f}%。"
    )

    return report, conclusion
tools = {
    "月度销售趋势分析": {
        "description": "用于回答销售额趋势、环比上涨、下降、月度销售情况的问题",
        "function": analyze_monthly_sales,
    },
    "部门经营分析": {
        "description": "用于回答部门销售额、成本、利润、利润率的问题",
        "function": analyze_department_profit,
    },
}
department_report, department_conclusion = analyze_department_profit(df)

print("\n各部门经营分析：")
print(department_report)

print("\n部门经营结论：")
print(department_conclusion)

def answer_question(df, question):
    prompt = f"""
你是数据分析 Agent 的工具选择器。

用户问题：
{question}

你只能从下面两个工具中选择一个：

1. 月度销售趋势分析
适合：销售趋势、环比、月度上涨或下降。

2. 部门经营分析
适合：部门销售额、成本、利润、利润率。

只返回 JSON，不能返回其他文字：

{{"tool_name": "月度销售趋势分析"}}

如果两个工具都不适合，返回：

{{"tool_name": "无法回答"}}
"""

    raw_result = call_local_model(prompt)

    try:
        selection = json.loads(raw_result)
        tool_name = selection["tool_name"]
    except (json.JSONDecodeError, KeyError):
        return f"模型未返回正确的工具选择结果：{raw_result}"

    if tool_name not in tools:
        return "暂时无法回答这个问题。目前只支持销售趋势和部门经营分析。"

    tool = tools[tool_name]
    _, conclusion = tool["function"](df)

    return f"模型选择工具：{tool_name}\n{conclusion}"
user_question = input("\n请输入你的问题：")

answer = answer_question(df, user_question)

print("\nAgent 回答：")
print(answer)