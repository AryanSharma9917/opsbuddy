from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.ai import (
    AIServiceError,
    AIUnavailableError,
    _is_safe_command,
    _sanitize_suggestions,
)
from app.main import app
from app.models import AnalysisResult, IssueType

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
        commands=["docker logs --tail=50 <container-name>"],
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


@pytest.mark.parametrize(
    ("issue_type", "command"),
    [
        ("kubernetes", "kubectl logs --tail=50 <pod-name>"),
        ("kubernetes", "kubectl describe pod <pod-name>"),
        ("kubernetes", "kubectl top pod <pod-name>"),
        ("kubernetes", "kubectl get pods -o wide"),
        ("docker", "docker logs --tail=50 <container-name>"),
        ("docker", "docker ps -a"),
        ("cicd", "gh run list --limit 5"),
        ("cicd", "git status --short"),
    ],
)
def test_read_only_diagnostic_commands_are_allowed(issue_type: IssueType, command: str) -> None:
    assert _is_safe_command(issue_type, command)


@pytest.mark.parametrize(
    ("issue_type", "command"),
    [
        ("kubernetes", "kubectl rollout restart deployment/api"),
        ("kubernetes", "kubectl delete pod api"),
        ("kubernetes", "kubectl logs -f api --tail=50"),
        ("kubernetes", "kubectl logs --tail=500 api"),
        ("kubernetes", "kubectl describe secret credentials"),
        ("kubernetes", "kubectl get pods -o yaml"),
        ("kubernetes", "kubectl get --raw /api/v1/secrets"),
        ("docker", "docker rm api"),
        ("docker", "docker logs -f api --tail=50"),
        ("cicd", "gh run rerun 123"),
        ("cicd", "git status; rm -rf /"),
    ],
)
def test_system_changing_commands_are_rejected(issue_type: IssueType, command: str) -> None:
    assert not _is_safe_command(issue_type, command)


def test_unsafe_model_step_is_removed() -> None:
    result = AnalysisResult(
        summary="The pod is restarting.",
        likely_causes=["The cause is not clear from the provided details."],
        next_steps=["Restart the pod and check whether it recovers."],
        commands=["kubectl describe pod <pod-name>"],
        safety_note="Review commands before running them.",
    )

    sanitized = _sanitize_suggestions("kubernetes", result)

    assert all("restart" not in step.lower() for step in sanitized.next_steps)
    assert "omitted or replaced suggestions" in sanitized.safety_note


def test_cause_cannot_claim_logs_were_seen_when_none_were_provided() -> None:
    result = AnalysisResult(
        summary="The pod is in CrashLoopBackOff.",
        likely_causes=["Pod logs indicate errors."],
        next_steps=["Review the pod's recent output."],
        commands=["kubectl logs --tail=50 <pod-name>"],
        safety_note="Review commands before running them.",
    )

    sanitized = _sanitize_suggestions(
        "kubernetes",
        result,
        "The payments-api pod is in CrashLoopBackOff and restarted 6 times.",
    )

    assert sanitized.likely_causes == [
        "The provided details identify a failure, but not its underlying cause."
    ]
    assert "evidence checks" in sanitized.safety_note


def test_concrete_log_evidence_can_support_a_possible_cause() -> None:
    result = AnalysisResult(
        summary="The application cannot connect to its database.",
        likely_causes=["The database endpoint may be unavailable."],
        next_steps=["Check the database endpoint and service configuration."],
        commands=["kubectl get pods"],
        safety_note="Review commands before running them.",
    )

    sanitized = _sanitize_suggestions(
        "kubernetes",
        result,
        "Application logs: connection refused while connecting to the database.",
    )

    assert sanitized.likely_causes == ["The database endpoint may be unavailable."]


def test_unsafe_summary_and_safety_note_are_replaced() -> None:
    result = AnalysisResult(
        summary="Check the logs and restart the pod.",
        likely_causes=["Restart the pod to see if it recovers."],
        next_steps=["Review the recent pod logs."],
        commands=["kubectl logs --tail=50 <pod-name>"],
        safety_note="Review logs and restart only if the problem persists.",
    )

    sanitized = _sanitize_suggestions("kubernetes", result)

    assert "restart" not in sanitized.summary.lower()
    assert "restart" not in sanitized.safety_note.lower()
    assert all("restart" not in cause.lower() for cause in sanitized.likely_causes)
    assert "does not execute commands" in sanitized.safety_note


def test_unapproved_command_is_omitted_from_next_steps_and_commands() -> None:
    result = AnalysisResult(
        summary="The container exited.",
        likely_causes=["The process may have stopped after an error."],
        next_steps=["docker inspect <container-name>"],
        commands=["docker ps -a"],
        safety_note="Review commands before running them.",
    )

    sanitized = _sanitize_suggestions("docker", result)

    assert all("docker" not in step.lower() for step in sanitized.next_steps)
    assert sanitized.commands == ["docker ps -a"]
    assert "omitted or replaced suggestions" in sanitized.safety_note


def test_unapproved_shell_command_in_next_step_is_omitted() -> None:
    result = AnalysisResult(
        summary="The Docker image may have a configuration issue.",
        likely_causes=["The container startup configuration may not match expectations."],
        next_steps=["cat Dockerfile"],
        commands=["docker ps -a"],
        safety_note="Review commands before running them.",
    )

    sanitized = _sanitize_suggestions("docker", result)

    assert sanitized.next_steps != ["cat Dockerfile"]
    assert "omitted or replaced suggestions" in sanitized.safety_note


def test_ci_rerun_suggestion_is_omitted() -> None:
    result = AnalysisResult(
        summary="The CI test stage failed.",
        likely_causes=["A test may have failed."],
        next_steps=["Run the test stage manually in GitHub Actions to isolate the issue."],
        commands=["gh run list --limit 5"],
        safety_note="Review commands before running them.",
    )

    sanitized = _sanitize_suggestions("cicd", result)

    assert all("run the test stage" not in step.lower() for step in sanitized.next_steps)
    assert "omitted or replaced suggestions" in sanitized.safety_note


def test_approved_commands_are_kept_and_not_repeated_as_next_steps() -> None:
    result = AnalysisResult(
        summary="The container exited.",
        likely_causes=["The process may have stopped after an error."],
        next_steps=["docker ps -a to check the container status."],
        commands=["docker ps -a"],
        safety_note="Review commands before running them.",
    )

    sanitized = _sanitize_suggestions("docker", result)

    assert sanitized.next_steps == [
        "Review the container's recent logs and exit status.",
        "Compare the startup command and configuration with the expected behavior.",
    ]
    assert sanitized.commands == ["docker ps -a"]


def test_vague_input_gets_request_for_more_details_without_model_call() -> None:
    response = client.post(
        "/api/analyze",
        json={
            "issue_type": "kubernetes",
            "details": "My Kubernetes application isn't working. What is wrong?",
        },
    )

    assert response.status_code == 200
    assert "isn't enough detail" in response.json()["summary"]
    assert response.json()["commands"] == ["kubectl get pods", "kubectl get events"]


def test_api_withholds_analysis_with_unsafe_model_suggestions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_analyze = AsyncMock(
        side_effect=AIServiceError(
            "Ollama suggested a potentially system-changing action. OpsBuddy withheld the analysis."
        )
    )
    monkeypatch.setattr("app.main.analyze_issue", mock_analyze)

    response = client.post(
        "/api/analyze",
        json={"issue_type": "kubernetes", "details": "The pod is in CrashLoopBackOff."},
    )

    assert response.status_code == 502
    assert "withheld the analysis" in response.json()["detail"]
