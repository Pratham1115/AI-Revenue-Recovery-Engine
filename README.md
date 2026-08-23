# RevEngine AI — Autonomous Revenue Recovery Engine

<div align="center">

![RevEngine AI](https://img.shields.io/badge/RevEngine-AI-7c3aed?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjEyIi8+PC9zdmc+)
![Phase 1](https://img.shields.io/badge/Phase%201-Live-22c55e?style=for-the-badge)
![Recovery Rate](https://img.shields.io/badge/Recovery%20Rate-43.3%25-a78bfa?style=for-the-badge)

**Closed-Loop Detection, Diagnostic Triage, and Autonomous Intervention for At-Risk Revenue**

[Dashboard](http://localhost:3000) · [API Docs](http://localhost:8000/docs) · [Pitch Deck](./pitch/index.html)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Core Modules](#core-modules)
- [API Reference](#api-reference)
- [Compliance & Guardrails](#compliance--guardrails)
- [Attribution Model](#attribution-model)
- [Demo Results](#demo-results)
- [Team](#team)

---

## Overview

Modern revenue leakage is fragmented across merchant checkout flows, recurring card billing retries, UPI Autopay mandates, and overdue B2B trade receivables. Traditional recovery tools rely on static time-based rules that suffer from poor recovery rates (<18%), high churn degradation, and customer annoyance.

**RevEngine AI** transforms passive payment failures into active recoveries by orchestrating an intelligent, event-driven state machine that:

1. **Ingests** real-time Razorpay webhook events
2. **Diagnoses** the exact root cause of each failure (6 categories)
3. **Enriches** with customer LTV, churn risk, timezone, and language preference
4. **Executes** dynamic intervention cadences (ML-optimised retry, WhatsApp nudges, magic payment links)
5. **Attributes** every recovery with statistical rigour using a 5% holdout group

---

## Key Features

| Feature | Description |
|---|---|
| 🔬 **Diagnostic Classifier** | Deterministic rule engine mapping Razorpay error codes → 6 failure categories |
| 🤖 **ML Retry Sequencer** | RandomForest model predicts optimal retry windows (salary-day peaks) |
| 📊 **Holdout Attribution** | 5% control group proves incremental lift above organic baseline |
| ⚡ **Circuit Breaker** | Stops all dunning within <500ms of dispute/chargeback webhook |
| 🌙 **Compliance Guardrails** | Quiet hours, touchpoint limits, FDCPA/RBI adherence — hard-coded |
| 🗣️ **Hinglish Messaging** | Multilingual WhatsApp templates (Hindi/English) for Indian market |
| 📱 **UPI Autopay Recovery** | Dedicated mandate failure handling with UPI payment link fallback |
| 💳 **Zero-Login Recovery** | Magic payment links via WhatsApp/Email — no re-authentication needed |
| 📄 **B2B AR Chaser** | Autonomous invoice follow-up with Promise-to-Pay commitment capture |
| 📈 **Live Dashboard** | Real-time metrics, attribution donut, trend charts, event feed |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAZORPAY EVENTS                          │
│  payment.failed · subscription.halted · mandate.revoked         │
│  cart.abandoned · payment.dispute.created · payment_link.paid   │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HMAC-SHA256 Verified Webhooks
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MODULE 1: TELEMETRY INGESTION                 │
│  • Webhook normalisation (Razorpay → canonical RevenueAtRiskEvent)
│  • Customer enrichment (LTV, churn risk, timezone, language)    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                MODULE 2: DIAGNOSTIC CLASSIFIER                  │
│  HARD_DECLINE → SOFT_DECLINE → CREDENTIAL_EXPIRY               │
│  MANDATE_FAILURE → CART_ABANDONED → B2B_OVERDUE                │
└──────────┬──────────────┬──────────────┬────────────────────────┘
           │              │              │
           ▼              ▼              ▼
┌──────────────┐  ┌────────────────┐  ┌──────────────────────────┐
│  HOLDOUT     │  │ COMPLIANCE     │  │  MODULE 3: ORCHESTRATOR  │
│  GROUP (5%)  │  │ CHECK          │  │  • ML Retry Sequencer    │
│  No action   │  │ Quiet hours?   │  │  • WhatsApp/SMS dispatch │
│  Baseline    │  │ Touchpoint cap?│  │  • Magic payment links   │
│  measurement │  │ Circuit break? │  │  • B2B AR chaser         │
└──────────────┘  └────────────────┘  └───────────────┬──────────┘
                                                       │
                                                       ▼
                                        ┌──────────────────────────┐
                                        │  MODULE 4: ATTRIBUTION   │
                                        │  AGENT_DRIVEN            │
                                        │  ORGANIC_BASELINE        │
                                        │  HOLDOUT                 │
                                        │  Immutable Ledger        │
                                        └──────────────────────────┘
```

### State Machine

```
DETECTED → TRIAGED → INTERVENTION_SCHEDULED → INTERVENTION_SENT
                                                      │
                    ┌─────────────────────────────────┤
                    ▼         ▼           ▼           ▼
                RECOVERED  FAILED     LAPSED   CIRCUIT_BROKEN
```

---

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| Python 3.12 | Core language |
| FastAPI 0.111 | Async REST API framework |
| SQLAlchemy 2.0 | ORM (SQLite for demo, PostgreSQL-ready) |
| Pydantic 2.7 | Data validation & serialisation |
| scikit-learn 1.5 | RandomForest retry timing model |
| Razorpay Python SDK | Webhook verification, Payment Links API |
| uvicorn | ASGI server |
| pytz | Timezone-aware compliance checking |

### Frontend
| Technology | Purpose |
|---|---|
| Next.js 16 (App Router) | React framework |
| TypeScript | Type safety |
| Tailwind CSS | Utility-first styling |
| Recharts | Recovery trend, category breakdown, attribution charts |
| lucide-react | Icons |

### Pitch Deck
| Technology | Purpose |
|---|---|
| Reveal.js 5.1 (CDN) | Presentation framework |
| Vanilla HTML/CSS | Self-contained, no build needed |

---

## Project Structure

```
AI-Revenue-Recovery-Engine/
├── backend/                          # FastAPI backend
│   ├── main.py                       # App entry point + CORS
│   ├── config.py                     # Settings (Razorpay keys, guardrail constants)
│   ├── requirements.txt              # Python dependencies
│   ├── .env.example                  # Environment variable template
│   ├── core/
│   │   ├── classifier.py             # Diagnostic root-cause classifier
│   │   ├── enrichment.py             # Customer LTV/risk/timezone enrichment
│   │   ├── retry_sequencer.py        # ML retry timing optimizer
│   │   ├── attribution.py            # Holdout-group attribution engine
│   │   └── orchestrator.py           # State machine + compliance guardrails
│   ├── models/
│   │   ├── database.py               # SQLAlchemy ORM models
│   │   └── schemas.py                # Pydantic request/response schemas
│   ├── routers/
│   │   ├── webhooks.py               # Razorpay webhook ingestion
│   │   ├── dashboard.py              # Dashboard stats API
│   │   └── simulator.py              # Demo event simulator
│   └── services/
│       └── notification.py           # Mock notification service (WhatsApp/SMS/Email)
│
├── frontend/                         # Next.js dashboard
│   ├── app/
│   │   ├── page.tsx                  # Dashboard (KPIs, charts, live feed)
│   │   ├── events/page.tsx           # Live event feed (auto-refresh 5s)
│   │   ├── simulator/page.tsx        # Interactive simulator UI
│   │   └── attribution/page.tsx      # Attribution ledger table
│   ├── components/
│   │   ├── Sidebar.tsx               # Navigation sidebar
│   │   ├── KpiBar.tsx                # 4 KPI metric cards
│   │   ├── Charts.tsx                # Recharts (trend, breakdown, donut)
│   │   ├── RecoveryFeed.tsx          # Live event feed component
│   │   └── Badges.tsx                # Category/status/attribution badges
│   └── lib/
│       ├── api.ts                    # Typed API client
│       └── utils.ts                  # Date/currency formatting helpers
│
├── pitch/
│   └── index.html                    # 12-slide Reveal.js pitch deck (self-contained)
│
└── README.md
```

---

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- npm

### 1. Clone & Setup Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Copy environment file (optional — demo works without Razorpay keys)
cp .env.example .env

# Start the backend server
$env:PYTHONUTF8="1"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend starts at **http://localhost:8000**
Swagger docs at **http://localhost:8000/docs**

### 2. Seed Demo Data

```bash
# Fire 25 synthetic events across all 6 failure categories
curl -X POST "http://localhost:8000/simulate/bulk?count=25"
```

### 3. Setup & Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend starts at **http://localhost:3000**

### 4. Open Pitch Deck

Open `pitch/index.html` directly in any browser. No server required.

Use `→` / `←` arrow keys to navigate. Press `F` for fullscreen.

### 5. Configure Razorpay (Optional)

Add your test-mode credentials to `backend/.env`:

```env
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_secret_here
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret_here
```

Without these, the simulator handles all demo flows automatically.

---

## Core Modules

### Module 1 — Diagnostic Classifier

Maps Razorpay error codes to 6 failure categories with recommended actions:

| Category | Error Codes | Action |
|---|---|---|
| `HARD_DECLINE` | `DO_NOT_HONOR`, `STOLEN_CARD`, `PICKUP_CARD` | Stop. Send magic card-swap link. |
| `SOFT_DECLINE` | `INSUFFICIENT_FUNDS`, `TRY_AGAIN_LATER` | ML retry at salary-day peak. |
| `CREDENTIAL_EXPIRY` | `EXPIRED_CARD`, `INVALID_CVV` | Network Token fetch → swap link. |
| `MANDATE_FAILURE` | `MANDATE_REVOKED`, `UPI_PIN_FAILURE` | Hinglish WhatsApp + UPI link. |
| `CART_ABANDONED` | `CART_ABANDONED`, `SESSION_EXPIRED` | Sub-10-min recovery nudge. |
| `B2B_OVERDUE` | `INVOICE_OVERDUE`, `NET30_BREACHED` | AR chaser → PTP commitment. |

### Module 2 — ML Retry Sequencer

**Model**: `RandomForestClassifier` (scikit-learn) trained on synthetic bank clearing data

**Features**: `hour_of_day`, `day_of_month`, `bank_code_hash`, `prev_failure_count`

**Key insight**: Indian bank clearing peaks at 06:00–09:00 IST on salary days (1st and 5th of the month), yielding **+25% success probability** vs off-peak retries.

### Module 3 — Orchestrator State Machine

```python
# Compliance is enforced before every dispatch
if not _passes_compliance(db, customer_id, timezone):
    # Quiet hours (21:00–09:00) or touchpoint limit (3/7 days) hit
    event.status = INTERVENTION_SCHEDULED
    return

# Circuit breaker — instant on dispute webhook
if dispute_received:
    all_active_events.status = CIRCUIT_BROKEN  # < 500ms
```

### Module 4 — Attribution Engine

```
Net_Agent_Recovery = Total_Cohort_Recovered − (Control_Rate × Treatment_Total)
```

- **5% holdout group** — determined by `MD5(recovery_id) % 100 < 5`
- **72-hour attribution window** — recovery within window = `AGENT_DRIVEN`
- **Immutable ledger** — every touchpoint logged with timestamp, channel, template ID, tone confidence score

---

## API Reference

### Webhooks

```http
POST /webhooks/razorpay
X-Razorpay-Signature: <hmac-sha256>
```

Supported events: `payment.failed`, `subscription.halted`, `mandate.revoked`, `cart.abandoned`, `payment.dispute.created`, `payment_link.paid`, `payment.captured`

### Dashboard

```http
GET /dashboard/summary          # KPIs + recent events
GET /dashboard/events           # Paginated event ledger
GET /dashboard/attribution-stats # Attribution breakdown
GET /dashboard/recovery-trend   # 7-day trend data
```

### Simulator

```http
POST /simulate/fire             # Fire single event
POST /simulate/bulk?count=25    # Seed bulk demo data
POST /simulate/recover/{id}     # Mark event as recovered
GET  /simulate/scenarios        # List available scenarios
```

**Available scenarios**: `soft_decline`, `hard_decline`, `expired_card`, `mandate_failure`, `cart_abandoned`, `b2b_overdue`

**Example:**
```bash
curl -X POST http://localhost:8000/simulate/fire \
  -H "Content-Type: application/json" \
  -d '{"scenario": "soft_decline", "amount": 4999}'
```

---

## Compliance & Guardrails

All guardrails are **hard-coded** — they cannot be overridden by configuration.

| Guardrail | Specification |
|---|---|
| **Quiet Hours** | No contact 21:00–09:00 customer local time (IANA timezone DB) |
| **Touchpoint Cap** | Max 3 touchpoints per customer per 7 days |
| **Circuit Breaker** | All dunning halted within <500ms of dispute webhook |
| **Discount Ceiling** | Max 5% incentive only if LTV > ₹2.5L AND churn risk > 85% |
| **DNC Respect** | Instant permanent opt-out on "DO NOT CALL" |
| **Regulatory** | FDCPA + TCPA + RBI Digital Recovery Guidelines enforced |

---

## Attribution Model

The holdout-group model ensures RevEngine AI never claims credit for organic recoveries:

```
Net_Agent_Recovery = Total_Cohort_Recovered − (Control_Rate × Treatment_Total)
```

**How it works:**
1. 5% of events are randomly assigned to the **holdout (control) group** — they receive no intervention
2. Their natural recovery rate becomes the **organic baseline**
3. Any recovery above this baseline is attributed as **agent-driven**
4. The immutable ledger records every intervention with tone confidence score and payer response

**Attribution statuses:**
- `AGENT_DRIVEN` — Recovered within 72h of last intervention
- `ORGANIC_BASELINE` — Recovered without agent action
- `HOLDOUT` — In control group, no intervention applied

---

## Demo Results

Smoke test with 30 synthetic events:

| Metric | Result | PRD Target |
|---|---|---|
| Gross Recovery Rate | **43.3%** | ≥ 42% |
| ML Retry Confidence | **69.6%** | — |
| Net Agent Recovery | **₹75,458** | — |
| Circuit Breaker Response | **< 500ms** | < 500ms |
| Quiet Hours Compliance | **100%** | 100% |
| Holdout Group Rate | **5%** | 5% |

**Category breakdown (30 events):**
- Soft Decline: 9 · Hard Decline: 6 · Cart Abandoned: 6
- Mandate Failure: 4 · Credential Expiry: 3 · B2B Overdue: 2

---

## Team

**Pratham Prasad** — Product Lead, RevOps / AI Core

---

## License

MIT
