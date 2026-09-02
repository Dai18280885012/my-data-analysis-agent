from retail_tools import (
    load_sales_data,
    analyze_country_sales,
    analyze_top_country_share,
    analyze_monthly_sales,
    analyze_customer_repurchase,
)


def check_tool_result(tool_name, result):
    required_keys = {"tool_name", "table", "metrics", "conclusion"}

    assert isinstance(result, dict), f"{tool_name} 返回的不是字典"
    assert required_keys.issubset(result.keys()), (
        f"{tool_name} 缺少字段："
        f"{required_keys - result.keys()}"
    )
    assert result["tool_name"] == tool_name, (
        f"工具名称不一致：{result['tool_name']}"
    )
    assert isinstance(result["table"], list), "table 必须是列表"
    assert isinstance(result["metrics"], dict), "metrics 必须是字典"
    assert isinstance(result["conclusion"], str), "conclusion 必须是字符串"

    print(f"通过：{tool_name}")


sales_df = load_sales_data()

country_result = analyze_country_sales(sales_df)
check_tool_result("国家销售分析", country_result)

share_result = analyze_top_country_share(sales_df)
check_tool_result("国家销售占比分析", share_result)

monthly_result = analyze_monthly_sales(sales_df)
check_tool_result("月度销售分析", monthly_result)

repurchase_result = analyze_customer_repurchase(sales_df)
check_tool_result("客户复购分析", repurchase_result)

print("\n全部工具契约检查通过。")