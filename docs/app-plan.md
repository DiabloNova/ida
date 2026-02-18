# Mobile Safety Reporting App (Android-first, iOS-ready)

## Goal
Build an **offline-capable, safety-focused incident reporting app** for civilians in Iran that helps people:
- See nearby danger reports on a map.
- Submit incident reports (location, direction of movement, observed equipment/vehicles, approximate group size, severity).
- Attach media evidence (photo/video/audio) when safe.
- Receive nearby danger alerts even under restricted internet conditions.

> This document is focused on **civilian safety and situational awareness**.

---

## 1) Product scope (MVP)

### Core features
1. **Map view (Iran) with zoom/pan**
   - Android map SDK with clustering of reports.
   - Custom markers by severity/type.

2. **Create a report**
   - Tap map to place marker or use current GPS.
   - Fields:
     - Incident type
     - Severity level
     - Observed movement direction
     - Observed equipment/vehicle type
     - Approximate count
     - Estimated injured / killed (optional)
     - Free text notes
   - Optional attachments: image/video/audio.

3. **Local-first operation**
   - App fully usable without internet.
   - Save pending reports locally, encrypt on device, sync when possible.

4. **Area alerts**
   - Geo-fenced push/local alerts for high-severity incidents near the user.
   - TTL-based expiration so stale alerts disappear.

5. **Safety UX**
   - Quick-exit mode (disguised UI option).
   - Optional passcode/biometric app lock.
   - Minimal personally identifying data collection.

---

## 2) Suggested architecture

## Client (Android first)
- **Framework**: Kotlin + Jetpack Compose.
- **Pattern**: Clean Architecture + MVVM.
- **Storage**:
  - Room DB for reports/attachments metadata.
  - SQLCipher (or encrypted storage) for at-rest encryption.
- **Background sync**:
  - WorkManager for retry/sync when network becomes available.
- **Maps**:
  - Abstraction layer `MapProvider` to avoid vendor lock-in.

## Server
- **API**: REST/GraphQL over HTTPS.
- **Backend stack**: FastAPI or Node.js + PostgreSQL/PostGIS.
- **Media storage**: object store compatible with resumable uploads.
- **Queue**: Redis/RabbitMQ/Kafka for alert fan-out and processing.
- **Alerting service**:
  - Compute nearby users by geohash.
  - Send local push notifications and maintain in-app alert feed.

## Data flow
1. User creates report offline.
2. Report encrypted + stored locally.
3. Background worker syncs report when network path available.
4. Server validates, assigns risk score, stores, then emits area alerts.
5. Nearby clients receive alert + map update.

---

## 3) Operating under internet blocking

Use a **multi-path transport strategy**:

1. **Primary path**: standard HTTPS API.
2. **Fallback path A**: domain fronting/CDN where legally and technically possible.
3. **Fallback path B**: peer-to-peer local relay (Wi‑Fi Direct / Bluetooth) for delayed delivery.
4. **Fallback path C**: store-and-forward through trusted bridge nodes when any path becomes available.

### Sync strategy
- Durable local queue with per-item retry/backoff.
- Conflict resolution by timestamp + server reconciliation.
- Compressed media upload and chunked resumable transfer.

### Internal network considerations
- Operate on local-only mesh mode when WAN is unavailable.
- Propagate critical alerts hop-by-hop with TTL to reduce stale/false spread.

---

## 4) Data model (MVP)

## `IncidentReport`
- `id`
- `created_at`, `observed_at`
- `lat`, `lng`, `accuracy_m`
- `severity` (1..5)
- `incident_type`
- `movement_direction` (N, NE, E, ...)
- `vehicle_type` (optional)
- `weapon_type` (optional)
- `estimated_count` (optional)
- `estimated_injured` (optional)
- `estimated_killed` (optional)
- `notes` (optional)
- `attachments[]`
- `verification_status` (unverified / corroborated / disputed)
- `risk_score`
- `expires_at`

## `Alert`
- `id`
- `report_id`
- `center_lat`, `center_lng`
- `radius_m`
- `priority`
- `message`
- `expires_at`

---

## 5) Trust, verification, abuse prevention

Because crowdsourced reports can be manipulated:
- Multi-report corroboration before broad alerts.
- Trust scoring based on historical accuracy (privacy-preserving).
- Rate limits and anomaly detection.
- Human moderation workflows for high-impact incidents.
- Clear “unverified” labels in UI.

---

## 6) Security and privacy requirements

- End-to-end encryption for sensitive payloads where possible.
- At-rest encryption for DB + media cache.
- Ephemeral identifiers instead of real identity.
- Metadata minimization (collect only what is required).
- Secure key management and certificate pinning.
- Tamper-evident logging on server side.
- Data retention policy with automatic purge.

---

## 7) Android → iOS expansion path

Create shared domain contracts now:
- Shared API schema (OpenAPI/Proto).
- Shared event and risk model.
- Map abstraction interface.

Then build iOS with SwiftUI replicating:
- offline queue,
- map rendering,
- report workflow,
- alert geofencing,
- security controls.

---

## 8) MVP milestone plan (8–12 weeks)

1. **Weeks 1–2**: Product spec, threat model, wireframes.
2. **Weeks 3–4**: Android skeleton + map + local DB.
3. **Weeks 5–6**: Report form + attachments + offline queue.
4. **Weeks 7–8**: Backend ingestion + map feed + alert engine.
5. **Weeks 9–10**: Security hardening + moderation + QA.
6. **Weeks 11–12**: Pilot deployment + monitoring + incident response playbook.

---

## 9) Immediate next actions

1. Decide map provider strategy (Google Maps + fallback provider).
2. Define exact report taxonomy and severity scoring rules.
3. Produce threat model and secure-by-default UX requirements.
4. Build Android proof-of-concept with offline report queue and local alerts.
5. Stand up minimal backend with PostGIS and alert fan-out.

