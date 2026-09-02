import hashlib
import io
import pandas as pd
import streamlit as st

from agent_service import default_sales_df, run_agent_question
from retail_tools import prepare_sales_data

def clear_current_session():
    st.session_state.conversation_history = []
    st.session_state.messages = []

def format_metric_value(metric_name, value):
    if isinstance(value, float):
        formatted_value = f"{value:,.2f}"
    else:
        formatted_value = str(value)

    if "率" in metric_name or "占比" in metric_name:
        return f"{formatted_value}%"

    return formatted_value

def show_rag_sources(table_data):
    st.subheader("回答依据")

    for chunk in table_data:
        rank = chunk.get("排名", "-")
        source = chunk.get("来源", "未知来源")
        chunk_id = chunk.get("文本块编号", "-")
        distance = chunk.get("距离", "-")
        content = chunk.get("内容", "")

        with st.expander(
            f"资料 {rank} · {source}",
            expanded=(rank == 1),
        ):
            st.caption(
                f"文本块：{chunk_id}｜"
                f"向量距离：{distance}"
            )
            st.write(content)


def show_analysis_details(analysis):
    result = analysis["result"]
    table_data = result.get("table", [])
    metrics = result.get("metrics", {})
    tool_name = analysis["tool_name"]

    if metrics:
        st.subheader("核心指标")
        metric_columns = st.columns(3)

        for index, (metric_name, value) in enumerate(
            metrics.items()
        ):
            with metric_columns[index % 3]:
                st.metric(
                    label=metric_name,
                    value=format_metric_value(
                        metric_name,
                        value,
                    ),
                )

    if tool_name == "公司制度知识库检索":
        retrieval_status = result.get(
            "retrieval_status",
            "",
        )

        if retrieval_status == "资料不足":
            st.info("知识库未检索到足够的相关资料。")

        elif table_data:
            show_rag_sources(table_data)

    elif table_data:
        st.subheader("分析明细")
        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
        )

    if tool_name == "国家销售分析" and table_data:
        chart_df = pd.DataFrame(table_data).set_index("国家")

        st.subheader("国家销售额排行")
        st.bar_chart(chart_df["销售额"])

    elif tool_name == "月度销售分析" and table_data:
        chart_df = pd.DataFrame(table_data).set_index("月份")

        st.subheader("月度销售趋势")
        st.line_chart(chart_df["销售额"])

    with st.expander("查看本次工具调用记录"):
        st.write(f"识别意图：{analysis['intent']}")
        st.write(f"传入参数：{analysis['tool_args']}")
        st.write(f"实际工具：{tool_name}")
        st.write(
            f"结果校验："
            f"{analysis['validation_status']}"
        )

        if tool_name == "公司制度知识库检索":
            st.write(
                "检索状态："
                f"{result.get('retrieval_status', '未知')}"
            )
st.set_page_config(
    page_title="本地数据分析 Agent",
    page_icon="📊",
    layout="wide",
)

@st.cache_data(show_spinner="正在读取并清洗上传数据...")
def load_uploaded_sales_data(file_bytes):
    raw_df = pd.read_excel(io.BytesIO(file_bytes))
    return prepare_sales_data(raw_df)

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_sales_df" not in st.session_state:
    st.session_state.active_sales_df = default_sales_df

if "data_source_name" not in st.session_state:
    st.session_state.data_source_name = "默认 Online Retail 数据"

st.title("本地数据分析 Agent")
st.caption(
    "本地 DeepSeek + LangGraph + Pandas + Chroma RAG"
)

with st.sidebar:
    st.subheader("当前数据源")
    st.caption(st.session_state.data_source_name)

    uploaded_file = st.file_uploader(
        "上传零售交易 Excel",
        type=["xlsx"],
    )

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    if st.session_state.get("data_source_hash") != file_hash:
        try:
            uploaded_df = load_uploaded_sales_data(file_bytes)

            st.session_state.active_sales_df = uploaded_df
            st.session_state.data_source_name = uploaded_file.name
            st.session_state.data_source_hash = file_hash

            clear_current_session()

            st.success(
                f"已加载 {len(uploaded_df):,} 行有效销售数据"
            )
            st.info("数据源已切换，历史会话已自动清空。")

        except ValueError as error:
            st.error(f"文件无法使用：{error}")

        except Exception as error:
            st.error(f"读取文件失败：{error}")

    if st.button("恢复默认数据"):
     if st.session_state.get("data_source_hash") != "default":
        st.session_state.active_sales_df = default_sales_df
        st.session_state.data_source_name = "默认 Online Retail 数据"
        st.session_state.data_source_hash = "default"

        clear_current_session()
        st.rerun()

    current_df = st.session_state.active_sales_df

    st.caption("数据概览")

    data_col_1, data_col_2 = st.columns(2)

    with data_col_1:
        st.metric(
            "有效交易行数",
            f"{len(current_df):,}",
        )

    with data_col_2:
        st.metric(
            "客户数",
            f"{current_df['CustomerID'].nunique():,}",
        )

    st.metric(
        "国家数",
        f"{current_df['Country'].nunique():,}",
    )

    st.divider()

    st.subheader("当前分析能力")
    st.write("1. 国家销售额排行")
    st.write("2. 最高销售国家占比")
    st.write("3. 月度销售趋势与环比")
    st.write("4. 客户复购分析")

    if st.button("清空当前会话"):
        clear_current_session()
        st.rerun()


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if (
            message["role"] == "assistant"
            and "analysis" in message
        ):
            show_analysis_details(message["analysis"])


user_question = st.chat_input(
    "例如：客户复购率是多少？或订单折扣超过10%需要谁审批？"
)

if user_question:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_question,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_question)


    with st.chat_message("assistant"):
        with st.spinner("正在分析数据..."):
            try:
                final_state = run_agent_question(
                 question=user_question,
                 conversation_history=st.session_state.conversation_history,
                 dataframe=st.session_state.active_sales_df,
                )
                answer = final_state["answer"]
                result = final_state["result"]
                table_data = result.get("table", [])
                tool_name = final_state["tool_name"]

                analysis = {
                "intent": final_state["intent"],
                "tool_args": final_state["tool_args"],
                "tool_name": final_state["tool_name"],
                "result": final_state["result"],
                "validation_status": final_state["validation_status"],
}
                st.markdown(answer)
                show_analysis_details(analysis)
                st.session_state.messages.append(
                   {
                       "role": "assistant",
                       "content": answer,
                       "analysis": analysis,
                    }
               )
                st.session_state.conversation_history.append(
                    {
                        "role": "user",
                        "content": user_question,
                    }
                )
                st.session_state.conversation_history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            except Exception as error:
                error_message = f"本次分析失败：{error}"
                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )
