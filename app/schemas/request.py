from pydantic import BaseModel, Field


class DiagnosisRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "description": (
                    "我们公司最近增长放缓，团队每天都很忙，但新客户越来越少。"
                    "管理层现在主要在抓成本和效率，员工觉得目标越来越乱，很多人只是在完成KPI。"
                    "请帮我判断主要管理问题，并给出下一步建议。"
                )
            }
        }
    }

    description: str = Field(
        ...,
        min_length=10,
        title="Company Situation Description",
        description=(
            "The user's raw description of the company's situation, problem, "
            "and expected analysis goal. It can be informal or unstructured."
        ),
    )
