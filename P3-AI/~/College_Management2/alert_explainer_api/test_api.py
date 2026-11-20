"""Tests for the alert explainer service."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from services.explainer import generate_explanation


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine)

    def override_get_db():
        with test_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


@pytest.mark.parametrize("value,comparison", [(86.0, "exceeded"), (84.0, "fell below"), (85.0, "reached")])
@pytest.mark.parametrize("severity,next_step", [
    ("critical", "Investigate immediately and take corrective action."),
    ("warning", "Review the affected system and monitor the metric closely."),
    ("info", "Review the metric and confirm whether any action is needed."),
])
def test_explanation_comparison_and_severity(value, comparison, severity, next_step):
    alert = SimpleNamespace(title="CPU alert", severity=severity, source="gateway", metric_name="cpu", metric_value=value, threshold=85.0)
    assert generate_explanation(alert) == (
        f'This {severity} alert from gateway is titled "CPU alert". '
        f"The cpu metric {comparison} its threshold: the current value is {value}, "
        f"compared with a threshold of 85.0. Recommended next step: {next_step}"
    )


def test_api_workflow(client):
    assert client.get("/").status_code == 200
    assert client.get("/docs").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths["/alerts/"]) >= {"get", "post"}
    assert "get" in paths["/alerts/{alert_id}"]
    assert "post" in paths["/alerts/{alert_id}/explain"]
    inputs = [
        {"title": "High CPU utilization on api-gateway-prod-3", "severity": "critical", "source": "api-gateway", "metric_name": "cpu_utilization", "metric_value": 96.5, "threshold": 85.0},
        {"title": "Elevated response latency on network-monitor", "severity": "warning", "source": "network-monitor", "metric_name": "p95_latency_ms", "metric_value": 812, "threshold": 500},
    ]
    for index, data in enumerate(inputs, start=1):
        response = client.post("/alerts/", json=data)
        assert response.status_code == 201
        created = response.json()
        assert created["id"] == index
        assert all(created[key] == value for key, value in data.items())
        assert datetime.fromisoformat(created["created_at"]).utcoffset() == timezone.utc.utcoffset(None)
        assert client.get(f"/alerts/{index}").json() == created
        explanation = client.post(f"/alerts/{index}/explain").json()
        assert explanation["alert_id"] == index
        assert explanation["explanation"] == generate_explanation(SimpleNamespace(**created))
        assert datetime.fromisoformat(explanation["generated_at"]).utcoffset() == timezone.utc.utcoffset(None)
    assert len(client.get("/alerts/").json()) == 2
    for method, path in ((client.get, "/alerts/999"), (client.post, "/alerts/999/explain")):
        response = method(path)
        assert response.status_code == 404
        assert response.json() == {"detail": "Alert not found"}
    assert client.post("/alerts/", json={**inputs[0], "severity": "high"}).status_code == 422