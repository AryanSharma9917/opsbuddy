from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.ai import AIUnavailableError
from app.main import app
from app.models import AnalysisResult

client = TestClient(app)


def test_health_reports_service_status() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_homepage_is_served() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Stuck on an error?" in response.text


def test_static_stylesheet_is_served() -> None:
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "--green: #375a46" in response.text


def test_analyze_returns_structured_guidance(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = AnalysisResult(
        summary="The container is restarting after it exits.",
        likely_causes=["The application may be failing during startup."],
        next_steps=["Check the container logs for the first error."],
        commands=["docker logs <container-name>"],
        safety_note="Review commands before running them.",
    )
    mock_analyze = AsyncMock(return_value=expected)
    monkeypatch.setattr("app.main.analyze_issue", mock_analyze)

    response = client.post(
        "/api/analyze",
        json={"issue_type": "docker", "details": "The container exits after starting."},
    )

    assert response.status_code == 200
    assert response.json() == expected.model_dump()
    mock_analyze.assert_awaited_once_with("docker", "The container exits after starting.")


def test_analyze_rejects_short_diagnostic_text() -> None:
    response = client.post(
        "/api/analyze",
        json={"issue_type": "kubernetes", "details": "short"},
    )

    assert response.status_code == 422


def test_analyze_reports_unavailable_local_model(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_analyze = AsyncMock(
        side_effect=AIUnavailableError("Could not reach Ollama. Make sure it is running.")
    )
    monkeypatch.setattr("app.main.analyze_issue", mock_analyze)

    response = client.post(
        "/api/analyze",
        json={"issue_type": "cicd", "details": "The workflow failed during the test step."},
    )

    assert response.status_code == 503
    assert "Could not reach Ollama" in response.json()["detail"]
