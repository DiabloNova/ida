from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Dict
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query

from .models import (
    Alert,
    AlertSubscription,
    AlertSubscriptionCreate,
    IncidentCreate,
    IncidentReport,
    Severity,
)

app = FastAPI(title="IDA Safety API", version="0.1.0")

REPORTS: Dict[UUID, IncidentReport] = {}
ALERTS: Dict[UUID, Alert] = {}
SUBSCRIPTIONS: Dict[UUID, AlertSubscription] = {}


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius_m = 6371000
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    c = 2 * asin(sqrt(a))
    return earth_radius_m * c


def build_alert(report: IncidentReport) -> Alert | None:
    if report.severity.value < Severity.high.value:
        return None

    radius_m = 2000 if report.severity == Severity.high else 5000
    return Alert(
        report_id=report.id,
        center_lat=report.lat,
        center_lng=report.lng,
        radius_m=radius_m,
        priority="high" if report.severity == Severity.high else "critical",
        message=f"Safety alert near your area ({report.incident_type.value}).",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/reports", response_model=IncidentReport)
def create_report(payload: IncidentCreate) -> IncidentReport:
    report = IncidentReport(**payload.model_dump())
    REPORTS[report.id] = report

    alert = build_alert(report)
    if alert:
        ALERTS[alert.id] = alert

    return report


@app.get("/v1/reports", response_model=list[IncidentReport])
def list_reports(
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    radius_m: int = Query(default=3000, ge=100, le=50000),
) -> list[IncidentReport]:
    if lat is None or lng is None:
        return sorted(REPORTS.values(), key=lambda x: x.created_at, reverse=True)

    nearby = [
        report
        for report in REPORTS.values()
        if haversine_m(lat, lng, report.lat, report.lng) <= radius_m
    ]
    return sorted(nearby, key=lambda x: x.created_at, reverse=True)


@app.get("/v1/reports/{report_id}", response_model=IncidentReport)
def get_report(report_id: UUID) -> IncidentReport:
    report = REPORTS.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="report_not_found")
    return report


@app.get("/v1/alerts", response_model=list[Alert])
def list_alerts(
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
) -> list[Alert]:
    now = datetime.now(timezone.utc)
    active_alerts = [a for a in ALERTS.values() if a.expires_at > now]

    if lat is None or lng is None:
        return active_alerts

    return [
        alert
        for alert in active_alerts
        if haversine_m(lat, lng, alert.center_lat, alert.center_lng) <= alert.radius_m
    ]


@app.post("/v1/subscriptions", response_model=AlertSubscription)
def create_subscription(payload: AlertSubscriptionCreate) -> AlertSubscription:
    subscription = AlertSubscription(**payload.model_dump())
    SUBSCRIPTIONS[subscription.id] = subscription
    return subscription


@app.get("/v1/subscriptions/{subscription_id}/alerts", response_model=list[Alert])
def list_subscription_alerts(subscription_id: UUID) -> list[Alert]:
    subscription = SUBSCRIPTIONS.get(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="subscription_not_found")

    now = datetime.now(timezone.utc)
    return [
        alert
        for alert in ALERTS.values()
        if alert.expires_at > now
        and haversine_m(
            subscription.lat,
            subscription.lng,
            alert.center_lat,
            alert.center_lng,
        )
        <= min(subscription.radius_m, alert.radius_m)
        and (
            (alert.priority == "critical" and subscription.min_severity.value <= Severity.critical.value)
            or (alert.priority == "high" and subscription.min_severity.value <= Severity.high.value)
        )
    ]
