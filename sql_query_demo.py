import sqlite3
from pathlib import Path

DB_FILE = Path(r"E:\my-data-analysis-agent\retail.db")

conn = sqlite3.connect(DB_FILE)

sql = """
SELECT
    Country,
    ROUND(SUM(SalesAmount), 2) AS total_sales
FROM retail_orders
GROUP BY Country
ORDER BY total_sales DESC
LIMIT 10;
"""

rows = conn.execute(sql).fetchall()
conn.close()

print("销售额最高的 10 个国家：")
for rank, (country, total_sales) in enumerate(rows, start=1):
    print(f"{rank}. {country}: {total_sales:,.2f}")