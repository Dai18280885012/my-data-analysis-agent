import sqlite3
from pathlib import Path

import pandas as pd

DATA_FILE = Path(
    r"E:\my-data-analysis-agent\datasets\02_真实零售交易大数据\Online_Retail.xlsx"
)
DB_FILE = Path("retail.db")

print("正在读取 Excel 数据...")
df = pd.read_excel(DATA_FILE)

# 保留有效订单，并创建销售额字段
df = df.dropna(subset=["CustomerID", "Description"])
df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)].copy()
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
df["SalesAmount"] = df["Quantity"] * df["UnitPrice"]

print(f"清洗后数据量：{len(df):,} 行")

conn = sqlite3.connect(DB_FILE)

# 将 DataFrame 写入 SQLite，replace 表示重复运行时覆盖旧表
df.to_sql("retail_orders", conn, if_exists="replace", index=False)

# 给常用筛选字段创建索引，查询会更快
conn.execute(
    "CREATE INDEX IF NOT EXISTS idx_orders_country "
    "ON retail_orders(Country)"
)
conn.execute(
    "CREATE INDEX IF NOT EXISTS idx_orders_date "
    "ON retail_orders(InvoiceDate)"
)

row_count = conn.execute(
    "SELECT COUNT(*) FROM retail_orders"
).fetchone()[0]

conn.close()

print(f"数据库创建成功：{DB_FILE.resolve()}")
print(f"retail_orders 表共有：{row_count:,} 行")