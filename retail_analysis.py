import json
import re
from urllib.request import Request, urlopen

import pandas as pd

file_path = r"E:\my-data-analysis-agent\datasets\02_真实零售交易大数据\Online_Retail.xlsx"

print("正在读取零售交易数据，请等待...")
df = pd.read_excel(file_path)

print("\n原始数据规模：")
print(f"行数：{len(df):,}")
print(f"字段：{df.columns.tolist()}")

# 删除没有客户编号的记录
df = df.dropna(subset=["CustomerID"]).copy()

# 转换日期字段
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

# 计算销售额
df["SalesAmount"] = df["Quantity"] * df["UnitPrice"]

# C 开头的订单通常代表取消订单
df["IsCancelled"] = df["InvoiceNo"].astype(str).str.startswith("C")

# 只保留正常销售记录
sales_df = df[
    (~df["IsCancelled"])
    & (df["Quantity"] > 0)
    & (df["UnitPrice"] > 0)
].copy()

print("\n清洗后数据规模：")
print(f"行数：{len(sales_df):,}")
print(f"客户数：{sales_df['CustomerID'].nunique():,}")
print(f"国家数：{sales_df['Country'].nunique():,}")
print(f"商品数：{sales_df['StockCode'].nunique():,}")

def analyze_country_sales(df, top_n=10):
    result = (
        df.groupby("Country")["SalesAmount"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .round(2)
    )

    top_country = result.index[0]
    top_sales = result.iloc[0]

    conclusion = (
        f"销售额最高的国家是 {top_country}，"
        f"销售额为 {top_sales:,.2f}。"
    )

    return result, conclusion


country_sales, country_conclusion = analyze_country_sales(sales_df)

print("\n销售额最高的 10 个国家：")
print(country_sales)

print("\n国家销售分析结论：")
print(country_conclusion)

monthly_sales = (
    sales_df
    .assign(Month=sales_df["InvoiceDate"].dt.to_period("M").astype(str))
    .groupby("Month")["SalesAmount"]
    .sum()
    .sort_index()
)

print("\n每月销售额：")
print(monthly_sales)

LOCAL_MODEL = "local-deepseek-data-agent"
LOCAL_CHAT_URL = "http://127.0.0.1:11434/api/chat"


def call_local_model(prompt):
    request_data = {
        "model": LOCAL_MODEL,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是数据分析 Agent。"
                    "你只能从工具列表中选择工具。"
                    "必须返回 JSON，不要输出 Markdown。"
                ),
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


def select_tool(question):
    prompt = f"""
用户问题：
{question}

当前只有一个可用工具：

工具名称：国家销售分析
工具用途：统计各国家销售额，并返回销售额最高的国家。

如果用户的问题与国家、地区、哪个地方卖得最好有关，
只返回：

{{"tool_name": "国家销售分析"}}

如果不相关，只返回：

{{"tool_name": "无法回答"}}
"""

    raw_result = call_local_model(prompt)

    # DeepSeek R1 可能会先输出思考内容，这里只提取 JSON
    json_match = re.search(r"\{.*\}", raw_result, re.DOTALL)

    if not json_match:
        return "模型没有返回有效的 JSON：" + raw_result

    try:
        selection = json.loads(json_match.group())
    except json.JSONDecodeError:
        return "模型返回的 JSON 无法解析：" + raw_result

    if selection.get("tool_name") == "国家销售分析":
        _, conclusion = analyze_country_sales(sales_df)
        return f"模型选择工具：国家销售分析\n{conclusion}"

    return "暂时无法回答这个问题。"


user_question = input("\n请输入你的问题：")

print("\nAgent 回答：")
print(select_tool(user_question))