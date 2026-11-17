# ReviveAI Live Demo Checklist & Judge Walkthrough Guide

This checklist ensures ReviveAI is ready for live demonstrations and provides an exact 3–5 minute script tailored for judges to showcase the product loop, intelligence layer, deterministic safety, bounded execution, and verified revenue recovery.

---

## 1. Pre-Demo Setup Checklist

### Environment & Credentials
- [ ] Backend running on `http://localhost:8000` (`uvicorn app.main:app --reload --port 8000` in `backend/`)
- [ ] Health check responding: `curl http://localhost:8000/health` → `{"status":"healthy"}`
- [ ] Frontend running on `http://localhost:5173` (`npm run dev` in `frontend/`)
- [ ] Tests and validation verified:
  - `python -m pytest tests -v` (80/80 passed)
  - `python scripts/validate_scenarios.py` (78/78 checks passed)

---

## 2. 3–5 Minute Hackathon Demo Flow

### ⏱ 00:00 — Problem & Architecture
- **Pitch:** "Merchants using Razorpay lose substantial revenue through failed payments and subscription disruptions. Retrying blindly wastes money, alienates customers, and degrades bank acceptance rates. ReviveAI is an intelligent, bounded revenue recovery operations system."
- **Core Loop:** `DETECT → DIAGNOSE → DECIDE → VALIDATE → ACT → MEASURE`
- **Key Safety Guardrail:** "The AI investigates and explains; deterministic policy controls what is allowed; the Recovery Orchestrator executes bounded actions."

---

### ⏱ 00:30 — Merchant Intelligence Queue & Top Opportunities
- **Show:** The **Top Recovery Opportunities** card and **Recovery Queue** sections on the dashboard.
- **Talking Points:**
  - "Notice how the system ranks opportunities deterministically: **pay_002610** is ranked #1 because it has the highest expected recovery value (₹24,941.96) and high probability (88.76%)."
  - "Blocked payments like **pay_000016** (payment method issue) and **pay_000040** (halted subscription) are strictly grouped into the **Recovery Blocked** tier and never outrank eligible payments."

---

### ⏱ 01:30 — Single Payment Deep-Dive & AI Investigation (`pay_002610`)
- **Action:** Enter `pay_002610` in the Search bar and click **Analyze Payment**.
- **Talking Points:**
  - "The **Executive Summary** shows ₹28,100.45 at risk with 88.76% probability and HIGH priority."
  - "In the **AI Agent Activity**, the AI agent autonomously executed tools to gather evidence and generated a clear narrative explanation of the failure (temporary bank failure)."
  - "Look at the **Decision Evidence** and **Revenue Intelligence**: the expected recovery value is probability-weighted, separating *potential* from *realized* cash."

---

### ⏱ 02:15 — Bounded Simulated Execution & Audit Trail
- **Action:** Click **Execute Bounded Recovery** in the Recovery Workflow.
- **Talking Points:**
  - "The orchestrator validates the guardrail rules and passes the request to the deterministic simulation gateway."
  - "Outcome: **SUCCESS** — **₹28,100.45 recovered**."
  - "Inspect the **Audit Trail**: every event (timestamp, decision, attempt #1, outcome, amount recovered) is immutably logged for total compliance."

---

### ⏱ 03:00 — Batch Revenue Intelligence & Conversion Funnel
- **Action:** Click **Run Demo Batch (9 payments)** in the Batch section.
- **Talking Points:**
  - "Watch the **Revenue Command Center** update with authoritative aggregate metrics:"
    - **Total Revenue Recovered:** **₹34,955.28** from **₹52,305.78** at risk (**66.83% recovery rate**)
    - **Successful Recoveries:** 3 of 4 attempts (75% attempt success rate)
    - **Guardrail Protected:** 5 payments safely blocked (0 wasted retries)
  - "Look at the **Revenue Recovery Funnel**: it traces conversion from Failed Payments → Policy Eligible → Attempts → Success → Realized Revenue."
  - "The **Opportunity Value Bar** makes clear the difference between *Revenue at Risk*, *Expected Potential*, and *Actually Recovered*."

---

### ⏱ 04:15 — Deterministic Safety on Ineligible Payments (`pay_000016`)
- **Action:** Enter `pay_000016` in the Search bar and analyze.
- **Talking Points:**
  - "The system detects a `payment_method_issue` (permanent failure)."
  - "The policy engine immediately locks the decision to **Recovery Blocked (DO NOT RETRY)**."
  - "The execute button is disabled. No gateway attempts are made. Guardrails are absolute."

---

### ⏱ 04:45 — Conclusion & Summary
- "ReviveAI gives merchants autonomous recovery intelligence while guaranteeing absolute financial safety through deterministic guardrails."

---

## 3. Contingency & Failure Fallbacks

### Contingency A: External LLM Rate-Limit or Outage
- Set `LLM_PROVIDER=mock` in `backend/.env`.
- The backend immediately hot-reloads and provides local deterministic responses with identical business metrics and full tool trace fidelity.

### Contingency B: Restarting Services
- Backend: `uvicorn app.main:app --reload --port 8000` (in `backend/`)
- Frontend: `npm run dev` (in `frontend/`)
