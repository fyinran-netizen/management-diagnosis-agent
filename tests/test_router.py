from app.tools.problem_router_tool import route_problem


def test_route_customer_value_and_metrics_problem():
    description = (
        "我们公司最近增长放缓，新客户越来越少。"
        "管理层现在主要在抓成本和效率，员工觉得目标越来越乱，很多人只是在完成KPI。"
    )

    result = route_problem(description)

    assert "customer_value_misalignment" in result
    assert "metrics_misalignment" in result


def test_route_opportunity_problem():
    description = (
        "团队每天都在处理问题，但是很少讨论未来机会。"
        "公司缺少新产品和新市场探索。"
    )

    result = route_problem(description)

    assert "opportunity_neglect" in result


def test_route_general_problem_when_no_keywords_match():
    description = "公司最近有一些复杂情况，需要做一次整体管理诊断。"

    result = route_problem(description)

    assert result == ["general_management_diagnosis"]