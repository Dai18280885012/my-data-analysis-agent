from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from agent_service import run_agent_question
from retail_tools import (
    analyze_country_sales,
    analyze_customer_repurchase,
    analyze_monthly_sales,
    load_sales_data,
)


app = FastAPI(
    title="本地数据分析 Agent API",
    description="为 Dify 提供零售销售数据分析工具。",
    version="1.1.0",
)


class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=500,
        description="用户的问题",
    )

    conversation_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="历史对话记录",
    )


@lru_cache(maxsize=1)
def get_sales_data():
    """首次调用时读取 Excel，之后复用内存中的清洗后数据。"""
    return load_sales_data()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "本地数据分析 Agent 服务正常",
    }


@app.get(
    "/tools/country-sales",
    summary="按国家分析销售额",
)
def country_sales(
    top_n: int = Query(
        default=10,
        ge=1,
        le=20,
        description="返回销售额排名前几的国家",
    ),
):
    try:
        return analyze_country_sales(
            get_sales_data(),
            top_n=top_n,
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"国家销售分析失败：{error}",
        )


@app.get(
    "/tools/monthly-sales",
    summary="分析月度销售趋势",
)
def monthly_sales():
    try:
        return analyze_monthly_sales(
            get_sales_data(),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"月度销售分析失败：{error}",
        )


@app.get(
    "/tools/customer-repurchase",
    summary="分析客户复购情况",
)
def customer_repurchase(
    top_n: int = Query(
        default=10,
        ge=1,
        le=20,
        description="返回订单数排名前几的客户",
    ),
):
    try:
        return analyze_customer_repurchase(
            get_sales_data(),
            top_n=top_n,
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"客户复购分析失败：{error}",
        )


@app.post("/chat")
def chat(request: ChatRequest):
    try:
        final_state = run_agent_question(
            question=request.question,
            conversation_history=request.conversation_history,
        )

        return {
            "answer": final_state["answer"],
            "trace": {
                "intent": final_state["intent"],
                "tool_name": final_state["tool_name"],
                "tool_args": final_state["tool_args"],
                "validation_status": final_state[
                    "validation_status"
                ],
            },
            "result": final_state["result"],
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Agent 执行失败：{error}",
        )