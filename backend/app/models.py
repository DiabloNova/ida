from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Severity(int, Enum):
    low = 1
    guarded = 2
    elevated = 3
    high = 4
    critical = 5


class Direction(str, Enum):
    n = "N"
    ne = "NE"
    e = "E"
    se = "SE"
    s = "S"
    sw = "SW"
    w = "W"
    nw = "NW"
    unknown = "UNKNOWN"


class IncidentType(str, Enum):
    armed_presence = "ARMED_PRESENCE"
    road_block = "ROAD_BLOCK"
    crowd_control = "CROWD_CONTROL"
    detention_activity = "DETENTION_ACTIVITY"
    medical_emergency = "MEDICAL_EMERGENCY"
    other = "OTHER"


class AttachmentType(str, Enum):
    image = "IMAGE"
    video = "VIDEO"
    audio = "AUDIO"


class Attachment(BaseModel):
    type: AttachmentType
    uri: str = Field(description="Encrypted local or remote object reference")


class IncidentCreate(BaseModel):
    observed_at: datetime
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    accuracy_m: float = Field(ge=0, le=5000)
    incident_type: IncidentType
    severity: Severity
    movement_direction: Direction = Direction.unknown
    vehicle_type: Optional[str] = None
    weapon_type: Optional[str] = None
    estimated_count: Optional[int] = Field(default=None, ge=0, le=5000)
    estimated_injured: Optional[int] = Field(default=None, ge=0, le=10000)
    estimated_killed: Optional[int] = Field(default=None, ge=0, le=10000)
    notes: Optional[str] = Field(default=None, max_length=3000)
    attachments: list[Attachment] = Field(default_factory=list)


class IncidentReport(IncidentCreate):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    verification_status: str = "unverified"


class Alert(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    report_id: UUID
    center_lat: float
    center_lng: float
    radius_m: int
    priority: str
    message: str
    expires_at: datetime
