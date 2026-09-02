from langgraph_first_demo import app, sales_df as default_sales_df


def run_agent_question(
    question,
    conversation_history=None,
    dataframe=None,
):
    if conversation_history is None:
        conversation_history = []

    if dataframe is None:
        dataframe = default_sales_df

    initial_state = {
        "question": question,
        "dataframe": dataframe,
        "intent": "",
        "tool_args": {},
        "tool_name": "",
        "result": {},
        "answer": "",
        "conversation_history": conversation_history.copy(),
        "validation_status": "",
    }

    return app.invoke(initial_state)