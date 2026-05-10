from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_route_returns_basic_service_info():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Management Diagnosis Agent",
        "status": "ok",
        "docs_url": "/docs",
        "health_url": "/health",
    }


def test_openapi_includes_request_example_for_description():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    example = schema["components"]["schemas"]["DiagnosisRequest"]["example"]

    assert "description" in example
    assert "增长放缓" in example["description"]


def test_public_diagnose_returns_only_source_location_fields(monkeypatch):
    def fake_build_diagnosis_result(request):
        return (
            {
                "model": "qwen3:8b",
                "diagnosis_report": "公开报告",
                "retrieved_sources": [
                    {
                        "source": "ch04/s06.md",
                        "title": "第六节 企业家能做什么",
                        "score": 9,
                    }
                ],
                "verification": {
                    "passed": True,
                    "issues": [],
                    "needs_revision": False,
                },
                "revision_count": 0,
                "project_id": "p1",
            },
            {
                "model": "qwen3:8b",
                "diagnosis_report": "公开报告",
                "retrieved_sources": [
                    {
                        "source": "ch04/s06.md",
                        "title": "第六节 企业家能做什么",
                        "content": "企业家需要做关键取舍。",
                        "score": 9,
                    }
                ],
                "verification": {
                    "passed": True,
                    "issues": [],
                    "needs_revision": False,
                },
                "revision_count": 0,
                "project_id": "p1",
            },
        )

    monkeypatch.setattr("app.main.build_diagnosis_result", fake_build_diagnosis_result)

    response = client.post("/diagnose", json={"description": "我们公司最近增长放缓，需要建议。"})

    assert response.status_code == 200
    assert response.json()["diagnosis_report"] == "公开报告"
    assert response.json()["retrieved_sources"][0]["source"] == "ch04/s06.md"
    assert response.json()["retrieved_sources"][0]["title"] == "第六节 企业家能做什么"
    assert response.json()["retrieved_sources"][0]["score"] == 9
    assert "content" not in response.json()["retrieved_sources"][0]


def test_admin_diagnose_keeps_retrieved_sources(monkeypatch):
    def fake_build_diagnosis_result(request):
        return (
            {
                "model": "qwen3:8b",
                "diagnosis_report": "公开报告",
                "verification": {
                    "passed": True,
                    "issues": [],
                    "needs_revision": False,
                },
                "revision_count": 0,
                "project_id": "p1",
            },
            {
                "model": "qwen3:8b",
                "diagnosis_report": "公开报告",
                "retrieved_sources": [
                    {
                        "source": "ch04/s06.md",
                        "title": "第六节 企业家能做什么",
                        "content": "企业家需要做关键取舍。",
                        "score": 9,
                    }
                ],
                "verification": {
                    "passed": True,
                    "issues": [],
                    "needs_revision": False,
                },
                "revision_count": 0,
                "project_id": "p1",
            },
        )

    monkeypatch.setattr("app.main.build_diagnosis_result", fake_build_diagnosis_result)

    response = client.post("/admin/diagnose", json={"description": "我们公司最近增长放缓，需要建议。"})

    assert response.status_code == 200
    assert response.json()["retrieved_sources"][0]["source"] == "ch04/s06.md"
