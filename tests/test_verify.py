from app.tools.verify_tool import verify_report_quality


def test_verify_passes_good_report():
    report = (
        "1. 核心诊断：企业当前存在顾客价值偏离的问题。管理层过度关注内部效率、流程和成本，"
        "但没有充分说明这些工作如何创造顾客价值。团队虽然每天都很忙，但新客户减少，说明企业可能正在把内部效率误认为经营目标。"
        "这一判断基于用户描述，并参考来源：01_customer_value.md。\n\n"
        "2. 实践建议：建议管理层先重新定义核心顾客，梳理顾客真正愿意付费或持续使用的价值。"
        "同时，检查现有会议、流程和指标，删除不创造顾客价值的内部管理动作。"
        "下一步可以安排客户访谈，并把关键指标重新连接到顾客价值。\n\n"
        "3. 缺失信息与假设：目前缺少具体客户画像、客户流失数据和现有指标体系。"
        "因此，以上判断基于用户对增长放缓、团队忙碌和新客户减少的描述。"
    )

    retrieved_chunks = [
        {
            "source": "01_customer_value.md",
            "title": "Common Symptoms",
            "content": "团队每天都很忙，但新客户越来越少。",
            "score": 10,
        }
    ]

    result = verify_report_quality(report, retrieved_chunks)

    assert result["passed"] is True
    assert result["needs_revision"] is False
    assert result["issues"] == []

def test_verify_fails_empty_report():
    result = verify_report_quality("", [])

    assert result["passed"] is False
    assert result["needs_revision"] is True
    assert "The report is empty." in result["issues"]


def test_verify_fails_without_recommendations():
    report = (
        "这份报告主要说明企业存在顾客价值问题。"
        "来源：01_customer_value.md。"
        "缺失信息与假设：目前缺少客户画像。"
    )

    retrieved_chunks = [
        {
            "source": "01_customer_value.md",
            "title": "Core Idea",
            "content": "企业存在的目的是创造顾客。",
            "score": 8,
        }
    ]

    result = verify_report_quality(report, retrieved_chunks)

    assert result["passed"] is False
    assert result["needs_revision"] is True
    assert any("practical recommendations" in issue for issue in result["issues"])


def test_verify_fails_truncated_report():
    report = "这是一份不完整的报告，最后一句没有结束（"

    result = verify_report_quality(report, [])

    assert result["passed"] is False
    assert result["needs_revision"] is True
    assert any("truncated" in issue or "unmatched" in issue for issue in result["issues"])