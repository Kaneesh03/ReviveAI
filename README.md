# ReviveAI — AI Revenue Recovery Intelligence Platform

[![Razorpay Buildathon](https://img.shields.io/badge/Razorpay%20Buildathon-Track%2003%3A%20AI%20Revenue%20Recovery-blue.svg)](https://razorpay.com)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2019%20%7C%20Vite%208-61DAFB.svg)](https://react.dev/)
[![Tests](https://img.shields.io/badge/Tests-84%2F84%20Passing-brightgreen.svg)]()
[![Model ROC-AUC](https://img.shields.io/badge/Model%20ROC--AUC-0.6960-orange.svg)]()
[![Throughput](https://img.shields.io/badge/Throughput-10.97%20payments%2Fsec-purple.svg)]()

> **ReviveAI** is an AI-powered revenue recovery intelligence platform designed for merchants using Razorpay. It detects revenue at risk from failed payments, diagnoses the root causes, predicts recovery probability using machine learning, ranks recovery opportunities, validates actions against deterministic financial safety policies, executes bounded simulations, drafts personalized customer outreach, and provides transparent, auditable recovery metrics.

---

## 📌 Product North Star

```
DETECT → DIAGNOSE → DECIDE → VALIDATE → ACT → MEASURE
```

> *"ReviveAI identifies recoverable revenue, prioritizes the highest-value opportunities, determines the safest intervention, executes strictly within deterministic policy boundaries, and proves revenue recovered with transparent audit trails."*

---

## 🏛️ Core Architectural Principle: Financial Safety First

### **THE LLM NEVER TOUCHES MONEY-MOVING APIs DIRECTLY**

```
┌─────────────────────────────────┐
│        AI Agent / LLM           │  Investigates evidence, diagnoses failure cause,
│ (NVIDIA NIM or Mock Provider)   │  explains reasoning, & drafts outreach emails
└────────────────┬────────────────┘
                 │ Structured Recommendation Only
                 ▼
┌─────────────────────────────────┐
│   Deterministic Policy Engine   │  Hardcoded financial guardrails:
│   & Guardrail Validator         │  - Max 2 retries (MAX_RETRY_COUNT=2)
└────────────────┬────────────────┘  - Max transaction limit ₹50,000
                 │ Approved Actions Only  - Permanent failure blocking
                 ▼
┌─────────────────────────────────┐
│      Recovery Orchestrator      │  Loop-safety ceiling (MAX_WORKFLOW_STEPS=3)
│   (Bounded Execution Engine)    │  Enforces idempotency & workflow states
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Simulation Gateway / Razorpay  │  Bounded simulated execution (Zero live money)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   Immutable Audit & Metrics     │  Every decision recorded & explainable
└─────────────────────────────────┘
```

1. **AI Investigates & Recommends:** The AI agent analyzes payment history, customer lifetime value, and bank response codes to produce structured recommendations.
2. **Deterministic Policies Govern:** Ineligible payments (permanent payment method failures, cancelled/halted subscriptions, exceeded retry counters) are strictly locked to `DO_NOT_RETRY` with **zero** gateway calls.
3. **Bounded Execution:** Only the `RecoveryOrchestrator` can invoke payment retries within simulation mode.

---

## 🚀 Key Features

- **🔍 Automated Failure Diagnosis:** Identifies whether failures are transient (bank downtime, network timeouts) or permanent (invalid cards, expired instruments, repeated fraud blocks).
- **📊 ML-Powered Recovery Probability:** Scikit-learn Random Forest model trained on eligible payment profiles computes recovery likelihood (`ROC-AUC = 0.6960`, `Accuracy = 81.88%` on 712 holdout samples).
- **💎 Opportunity Ranking:** Evaluates `Expected Recovery Value = Revenue at Risk × Recovery Probability` to prioritize high-yield recoveries.
- **⚡ High-Throughput Batch Processing:** Evaluates and processes payment batches at **~10.97 payments/second** sustained throughput with per-item fault isolation.
- **🛡️ Deterministic Guardrails:** Strict threshold enforcement:
  - `MAX_RETRY_COUNT = 2`
  - `MAX_RECOVERY_AMOUNT = ₹50,000`
  - `MAX_WORKFLOW_STEPS = 3`
- **🧠 100% Read-Only Explainability Engine:** `POST /api/v1/recovery/explain` delivers factor-by-factor decision traces and confidence bands with zero state mutation or side effects.
- **✉️ AI-Assisted Customer Outreach:** The `OutreachAgent` drafts empathetic, customized payment reminder emails for customer-actionable errors (insufficient funds, expired cards).
- **👤 Human-in-the-Loop Escalation Hub:** Centralized interface for merchants to review escalated edge cases, approve email drafts, or manually resolve blocked payments.
- **📈 Comprehensive Executive Dashboard:** Interactive Command Center displaying Revenue at Risk, Total Recovered, Recovery Rates, Funnel Conversions, and Decision Timelines.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Vite 8, Tailwind-inspired Vanilla CSS, Responsive Grid (1280px–1920px) |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, Uvicorn |
| **Machine Learning** | scikit-learn, joblib, NumPy, Pandas |
| **AI / LLM Layer** | NVIDIA NIM API (`minimaxai/minimax-m3`) with automated deterministic `MockProvider` fallback |
| **Testing & Quality** | pytest, pytest-asyncio, flake8 |

---

## 📡 API Reference

| Method | Endpoint | Description | Execution Authority |
|---|---|---|---|
| `GET` | `/health` | API health check & status | Public |
| `POST` | `/api/v1/recovery/analyze` | Single payment investigation, ML prediction & AI narrative | AI Agent + ML |
| `POST` | `/api/v1/recovery/execute` | Bounded deterministic recovery execution in simulation mode | Orchestrator (No LLM) |
| `POST` | `/api/v1/recovery/batch` | Batch recovery execution with aggregate metrics | Orchestrator (No LLM) |
| `POST` | `/api/v1/recovery/opportunities` | Ranked queue of recovery opportunities | Deterministic Ranker |
| `POST` | `/api/v1/recovery/explain` | Factor breakdown, probability bands, and chronological decision trace | Read-Only Engine |
| `POST` | `/api/v1/recovery/draft_reminder` | AI-generated empathetic email reminder draft | Outreach Agent |
| `GET` | `/api/v1/recovery/escalated` | List all escalated cases and outreach requests | Audit Trail |

---

## 📊 Benchmark 9-Payment Validation Suite

ReviveAI is validated against an authoritative 9-payment benchmark representing real merchant lifecycle scenarios:

| Payment ID | Eligible | Failure Reason | Action | Gateway Result | Recovered |
|---|---|---|---|---|---|
| `pay_002610` | **YES** | Temporary bank failure (High Amount) | `RETRY_PAYMENT` | Success | **₹28,100.45** |
| `pay_000041` | **YES** | Temporary bank failure (Low Amount) | `RETRY_WITH_CAUTION` | Success | **₹4,274.20** |
| `pay_000039` | **YES** | Network timeout error | `DEFER_RECOVERY` | Success | **₹2,580.63** |
| `pay_000012` | **YES** | Insufficient funds | `SEND_PAYMENT_REMINDER` | Outreach Drafted | ₹0.00 |
| `pay_000016` | **NO** | Payment method issue (Card stolen/closed) | `DO_NOT_RETRY` | Blocked (0 retries) | ₹0.00 |
| `pay_000049` | **NO** | Repeated bank failure | `DO_NOT_RETRY` | Blocked (0 retries) | ₹0.00 |
| `pay_000116` | **NO** | Unknown unclassified error | `DO_NOT_RETRY` | Blocked (0 retries) | ₹0.00 |
| `pay_000040` | **NO** | Subscription status: Halted | `DO_NOT_RETRY` | Blocked (0 retries) | ₹0.00 |
| `pay_000062` | **NO** | Retry count exceeded (>2) | `DO_NOT_RETRY` | Blocked (0 retries) | ₹0.00 |

### Benchmark Results:
- **Total Revenue at Risk:** ₹52,305.78
- **Total Revenue Recovered:** **₹34,955.28**
- **Recovery Rate (Revenue):** **66.83%**
- **Safety Violation Count:** **0** (All 5 ineligible payments made 0 gateway attempts)

---

## ⚡ Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Kaneesh03/ReviveAI.git
cd ReviveAI
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
```

#### Configure Environment Variables
Copy `.env.example` to `backend/.env`:
```bash
cp .env.example backend/.env
```
*(Optional)* Add your `NVIDIA_API_KEY` to enable live NVIDIA NIM inference. If left empty, ReviveAI runs with the built-in deterministic `MockProvider` seamlessly.

#### Run Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```
Backend API will be live at `http://localhost:8000` (Interactive Swagger docs at `http://localhost:8000/docs`).

### 3. Frontend Setup
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Verification & Testing Suite

### 1. Run Complete Backend Test Suite
```bash
cd backend
python -m pytest tests -v
```
✅ **84 / 84 tests pass** across API endpoints, tools, decision engines, explainability, and orchestrator boundaries.

### 2. Run Benchmark Scenario Validation
```bash
cd backend
python scripts/validate_scenarios.py
```
✅ **78 / 78 validation checks pass** verifying financial formulas, probability mappings, and guardrails.

### 3. Measure ML Model Quality
```bash
cd backend
python scripts/evaluate_model.py
```
✅ Evaluates holdout test data (712 samples):
- **ROC-AUC Score:** `0.6960`
- **Model Accuracy:** `81.88%`

### 4. Run Throughput Benchmark
```bash
cd backend
python scripts/benchmark_throughput.py
```
✅ Evaluates single-batch and multi-iteration sustained throughput:
- **Single Batch:** `~8.95 payments/second`
- **Sustained (15 iterations, 135 evaluations):** `~10.97 payments/second`

### 5. Frontend Production Build
```bash
cd frontend
npm run build
```
✅ Compiles cleanly with zero errors in `< 300ms`.

---

## 🔒 Exceptions, Boundaries & Limitations

For transparent documentation on dataset constraints, model limitations, simulation parameters, and the complete 12-scenario exception matrix, refer to:
📄 [docs/EXCEPTIONS_AND_LIMITATIONS.md](docs/EXCEPTIONS_AND_LIMITATIONS.md)

---

## 👥 Contributors

- **Kaneesh** — Project Creator & Lead Developer ([GitHub](https://github.com/Kaneesh03))

---

## 📄 License & Attribution

Built for the **Razorpay Buildathon — Track 03: AI Revenue Recovery**.  
Licensed under the [MIT License](LICENSE).
