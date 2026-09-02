import sqlite3
from pathlib import Path

from fastapi import FastAPI
from fastapi import Query

app = FastAPI(title="SQL 数据分析服务")

DB_FILE = Path(r"E:\my-data-analysis-agent\retail.db")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "database_exists": DB_FILE.exists(),
    }


@app.get("/sql/country-sales")
def country_sales(
    country: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    top_n: int = Query(default=10, ge=1, le=100),
):
    sql = """
    SELECT
        Country,
        ROUND(SUM(SalesAmount), 2) AS total_sales
    FROM retail_orders
    WHERE 1 = 1
    """

    params = []

    if country:
        sql += " AND Country = ?"
        params.append(country)

    if start_date:
        sql += " AND InvoiceDate >= ?"
        params.append(start_date)

    if end_date:
        sql += " AND InvoiceDate < ?"
        params.append(end_date)

    sql += """
    GROUP BY Country
    ORDER BY total_sales DESC
    LIMIT ?
    """

    params.append(top_n)

    conn = sqlite3.connect(DB_FILE)
    coverage_sql = """
    SELECT
        MIN(InvoiceDate),
        MAX(InvoiceDate)
    FROM retail_orders
    """
    coverage = conn.execute(coverage_sql).fetchone()
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    data_min_date = coverage[0][:10] if coverage and coverage[0] else None
    data_max_date = coverage[1][:10] if coverage and coverage[1] else None

    data = [
        {
            "rank": rank,
            "country": country_name,
            "total_sales": total_sales,
        }
        for rank, (country_name, total_sales) in enumerate(rows, start=1)
    ]

    return {
        "analysis_type": "国家销售额排行",
        "filters": {
            "country": country,
            "start_date": start_date,
            "end_date": end_date,
            "top_n": top_n,
        },
        "data_coverage": {
            "min_date": data_min_date,
            "max_date": data_max_date,
        },
        "data": data,
    }
