import pandas as pd


import os
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent

DEFAULT_DATA_FILE = (
    PROJECT_DIR
    / "datasets"
    / "02_真实零售交易大数据"
    / "Online_Retail.xlsx"
)

DATA_FILE = Path(
    os.getenv(
        "SALES_DATA_FILE",
        str(DEFAULT_DATA_FILE),
    )
)

def prepare_sales_data(df):
    required_columns = {
        "InvoiceNo",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        missing_text = "、".join(sorted(missing_columns))
        raise ValueError(
            f"上传的数据缺少必要字段：{missing_text}"
        )

    df = df.copy()

    df = df.dropna(subset=["CustomerID"]).copy()

    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"],
        errors="coerce",
    )
    df["Quantity"] = pd.to_numeric(
        df["Quantity"],
        errors="coerce",
    )
    df["UnitPrice"] = pd.to_numeric(
        df["UnitPrice"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["InvoiceDate", "Quantity", "UnitPrice"]
    ).copy()

    df["SalesAmount"] = df["Quantity"] * df["UnitPrice"]

    df["IsCancelled"] = (
        df["InvoiceNo"]
        .astype(str)
        .str.startswith("C")
    )

    sales_df = df[
        (~df["IsCancelled"])
        & (df["Quantity"] > 0)
        & (df["UnitPrice"] > 0)
    ].copy()

    if sales_df.empty:
        raise ValueError(
            "清洗后没有有效销售数据，请检查上传文件。"
        )

    return sales_df

def load_sales_data():
    print("正在读取零售数据，请等待...")
    df = pd.read_excel(DATA_FILE)

    return prepare_sales_data(df)


def analyze_country_sales(df, top_n=10):
    result = (
        df.groupby("Country")["SalesAmount"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .round(2)
    )

    total_sales = df["SalesAmount"].sum()
    top_country = result.index[0]
    top_sales = result.iloc[0]
    top_country_share = top_sales / total_sales * 100

    table = [
        {
            "国家": country,
            "销售额": float(sales),
        }
        for country, sales in result.items()
    ]

    return {
        "tool_name": "国家销售分析",
        "table": table,
        "metrics": {
            "总销售额": round(float(total_sales), 2),
            "最高销售国家": top_country,
            "最高国家销售额": round(float(top_sales), 2),
            "最高国家销售占比": round(float(top_country_share), 2),
        },
        "conclusion": (
            f"销售额最高的国家是 {top_country}，"
            f"销售额为 {top_sales:,.2f}，"
            f"占全部销售额的 {top_country_share:.2f}%。"
        ),
    }

def analyze_top_country_share(df):
    country_sales = (
        df.groupby("Country")["SalesAmount"]
        .sum()
        .sort_values(ascending=False)
        .round(2)
    )

    total_sales = country_sales.sum()
    top_country = country_sales.index[0]
    top_country_sales = country_sales.iloc[0]
    share = top_country_sales / total_sales * 100

    return {
        "tool_name": "国家销售占比分析",
        "table": [
            {
                "国家": top_country,
                "销售额": float(top_country_sales),
                "销售额占比": round(float(share), 2),
            }
        ],
        "metrics": {
            "总销售额": round(float(total_sales), 2),
            "最高销售国家": top_country,
            "最高国家销售额": round(float(top_country_sales), 2),
            "最高国家销售占比": round(float(share), 2),
        },
        "conclusion": (
            f"{top_country}是销售额最高的国家，"
            f"销售额为 {top_country_sales:,.2f}，"
            f"占全部销售额的 {share:.2f}%。"
        ),
    }


def analyze_monthly_sales(df):
    monthly_sales = (
        df.groupby(df["InvoiceDate"].dt.to_period("M"))["SalesAmount"]
        .sum()
        .sort_index()
        .round(2)
    )

    latest_month = str(monthly_sales.index[-1])
    latest_sales = monthly_sales.iloc[-1]

    if len(monthly_sales) >= 2:
        previous_sales = monthly_sales.iloc[-2]
        change_amount = latest_sales - previous_sales
        change_rate = change_amount / previous_sales * 100
    else:
        previous_sales = 0
        change_amount = 0
        change_rate = 0

    table = [
        {
            "月份": str(month),
            "销售额": float(sales),
        }
        for month, sales in monthly_sales.items()
    ]

    return {
        "tool_name": "月度销售分析",
        "table": table,
        "metrics": {
            "最新月份": latest_month,
            "最新月份销售额": round(float(latest_sales), 2),
            "上月销售额": round(float(previous_sales), 2),
            "环比变化额": round(float(change_amount), 2),
            "环比变化率": round(float(change_rate), 2),
        },
        "conclusion": (
            f"最新月份为 {latest_month}，销售额为 {latest_sales:,.2f}；"
            f"较上月变化 {change_amount:,.2f}，环比 {change_rate:.2f}%。"
        ),
    }



def analyze_customer_repurchase(df, top_n=10):
    customer_orders = (
        df.groupby("CustomerID")["InvoiceNo"]
        .nunique()
        .sort_values(ascending=False)
    )

    customer_sales = (
        df.groupby("CustomerID")["SalesAmount"]
        .sum()
        .round(2)
    )

    total_customers = len(customer_orders)
    repeat_customers = (customer_orders >= 2).sum()
    repeat_rate = repeat_customers / total_customers * 100

    top_customers = customer_orders.head(top_n)

    table = [
        {
            "客户ID": str(int(customer_id)),
            "订单数": int(order_count),
            "销售额": float(customer_sales.loc[customer_id]),
        }
        for customer_id, order_count in top_customers.items()
    ]

    top_customer_id = top_customers.index[0]
    top_customer_orders = top_customers.iloc[0]

    return {
        "tool_name": "客户复购分析",
        "table": table,
        "metrics": {
            "总客户数": int(total_customers),
            "复购客户数": int(repeat_customers),
            "客户复购率": round(float(repeat_rate), 2),
            "最高复购客户ID": str(int(top_customer_id)),
            "最高复购客户订单数": int(top_customer_orders),
        },
        "conclusion": (
            f"共有 {total_customers:,} 位客户，"
            f"其中 {repeat_customers:,} 位客户至少复购过一次，"
            f"客户复购率为 {repeat_rate:.2f}%。"
        ),
    }