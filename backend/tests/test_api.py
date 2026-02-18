from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import ALERTS, REPORTS, SUBSCRIPTIONS, app


client = TestClient(app)


def setup_function() -> None:
    REPORTS.clear()
    ALERTS.clear()
    SUBSCRIPTIONS.clear()


def sample_payload(severity: int = 3) -> dict:
    return {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "lat": 35.6892,
        "lng": 51.389,
        "accuracy_m": 20,
        "incident_type": "CROWD_CONTROL",
        "severity": severity,
        "movement_direction": "NE",
        "vehicle_type": "VAN",
        "estimated_count": 12,
        "notes": "Observed movement toward the square.",
        "attachments": [],
    }


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_report_and_fetch() -> None:
    create_response = client.post("/v1/reports", json=sample_payload())
    assert create_response.status_code == 200
    report = create_response.json()

    fetch_response = client.get(f"/v1/reports/{report['id']}")
    assert fetch_response.status_code == 200
    assert fetch_response.json()["id"] == report["id"]


def test_high_severity_creates_alert() -> None:
    create_response = client.post("/v1/reports", json=sample_payload(severity=5))
    assert create_response.status_code == 200

    alerts_response = client.get("/v1/alerts")
    assert alerts_response.status_code == 200
    alerts = alerts_response.json()
    assert len(alerts) == 1
    assert alerts[0]["priority"] == "critical"


def test_list_reports_by_radius() -> None:
    client.post("/v1/reports", json=sample_payload())

    far_payload = sample_payload()
    far_payload["lat"] = 34.6416
    far_payload["lng"] = 50.8746
    far_payload["observed_at"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    client.post("/v1/reports", json=far_payload)

    nearby_response = client.get("/v1/reports?lat=35.6892&lng=51.389&radius_m=500")
    assert nearby_response.status_code == 200
    assert len(nearby_response.json()) == 1


def test_subscription_alerts_are_filtered_by_area_and_severity() -> None:
    sub_response = client.post(
        "/v1/subscriptions",
        json={
            "lat": 35.6892,
            "lng": 51.389,
            "radius_m": 2000,
            "min_severity": 4,
        },
    )
    assert sub_response.status_code == 200
    subscription = sub_response.json()

    high_report = client.post("/v1/reports", json=sample_payload(severity=4))
    assert high_report.status_code == 200

    far_payload = sample_payload(severity=5)
    far_payload["lat"] = 36.2605
    far_payload["lng"] = 59.6168
    far_response = client.post("/v1/reports", json=far_payload)
    assert far_response.status_code == 200

    alerts_response = client.get(f"/v1/subscriptions/{subscription['id']}/alerts")
    assert alerts_response.status_code == 200

    alerts = alerts_response.json()
    assert len(alerts) == 1
    assert alerts[0]["priority"] == "high"


def test_subscription_not_found() -> None:
    response = client.get("/v1/subscriptions/6fa459ea-ee8a-3ca4-894e-db77e160355e/alerts")
    assert response.status_code == 404
    assert response.json()["detail"] == "subscription_not_found"
