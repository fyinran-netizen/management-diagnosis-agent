from app.tools.validation.report import verify_report_quality


def test_verify_passes_good_report():
    report = (
        "1. 核心诊断：企业当前存在顾客价值偏离的问题。管理层过度关注内部效率、流程和成本，"
        "但没有充分说明这些工作如何创造顾客价值。团队虽然每天都很忙，但新客户减少，说明企业可能正在把内部效率误认为经营目标。"
        "这一判断基于用户描述，并以知识库中关于创造顾客与顾客价值偏离的内容作为分析依据。\n\n"
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

    report += "\nKnowledge item 1."
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
        "其判断依据来自知识库中关于企业存在目的是创造顾客的观点。"
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


def test_verify_fails_when_report_exposes_raw_source_name():
    report = (
        "1. 核心诊断：企业当前存在顾客价值偏离。\n\n"
        "2. 知识库依据：参考 ch04/s06.md 可以看出企业家的行动重点。\n\n"
        "3. 实践建议：建议先调整指标与顾客价值的连接关系。\n\n"
        "4. 缺失信息与假设：目前缺少客户流失数据。"
    )

    report += "\n知识项1"

    retrieved_chunks = [
        {
            "source": "ch04/s06.md",
            "title": "第六节 企业家能做什么",
            "content": "企业家需要做关键取舍。",
            "score": 8,
        }
    ]

    result = verify_report_quality(report, retrieved_chunks)

    assert result["passed"] is False
    assert result["needs_revision"] is True
    assert any("should not expose raw source file paths" in issue for issue in result["issues"])


def test_verify_fails_truncated_report():
    report = "这是一份不完整的报告，最后一句没有结束（"

    result = verify_report_quality(report, [])

    assert result["passed"] is False
    assert result["needs_revision"] is True
    assert any("truncated" in issue or "unmatched" in issue for issue in result["issues"])


def test_verify_accepts_required_item_citation_without_basis_keyword():
    report = (
        "Core diagnosis: the operating model is not creating enough customer value. "
        "Knowledge item 1 supports this diagnosis through the retrieved management concept. "
        "Practical recommendations: interview customers, review the value proposition, and connect "
        "the leading indicator to the team decision process. Missing information: customer-level "
        "retention data and the current measurement definitions are not available."
    )
    result = verify_report_quality(report, [{"source": "kb.md", "title": "Value", "content": "Evidence", "score": 1}])

    assert result["passed"] is True
    assert result["issues"] == []


def test_verify_requires_retrieved_item_citation():
    report = (
        "Core diagnosis: the operating model is not creating enough customer value. "
        "Practical recommendations: interview customers and review the value proposition. "
        "Missing information: customer-level retention data is not available."
    )
    result = verify_report_quality(report, [{"source": "kb.md", "title": "Value", "content": "Evidence", "score": 1}])

    assert result["passed"] is False
    assert "The report does not cite retrieved knowledge items using the required format." in result["issues"]
