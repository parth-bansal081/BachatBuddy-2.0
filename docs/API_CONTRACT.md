# BachatBuddy API Contract

## Route Table

| Method | Path | Auth | Source File | Function |
|--------|------|------|-------------|----------|
| GET | /health | No | bb/main.py:32 | health() |
| POST | /enrich | Yes (Bearer) | bb/main.py:37 | enrich() |
| POST | /policy/compile | Yes (Bearer) | bb/main.py:69 | policy_compile() |
| POST | /policy/backtest | Yes (Bearer) | bb/main.py:79 | policy_backtest() |
| POST | /policy | Yes (Bearer) | bb/main.py:84 | policy_save() |
| GET | /policy/active | Yes (Bearer) | bb/main.py:89 | policy_active() |
| GET | /policy/safe-to-spend | Yes (Bearer) | bb/main.py:98 | policy_safe_to_spend() |

---

## Route Details

### GET /health
- **Auth required**: No
- **Request body**: None
- **Response**: `{"status": "ok"}`
- **Error cases**: None

### POST /enrich
- **Auth required**: Yes (Bearer token in `Authorization` header)
- **Request body**: None
- **Response** (`EnrichResult`):
  ```json
  {
    "narrations_seen": 0,
    "new_narrations": 0,
    "new_keys": 0,
    "llm_calls": 0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "fallbacks": 0,
    "needs_review": 0
  }
  ```
- **Error cases**:
  - 401: Missing or invalid bearer token
  - 502: Model API unavailable (LLM call failed)

### POST /policy/compile
- **Auth required**: Yes (Bearer token)
- **Request body** (`CompileRequest`):
  ```json
  {
    "text": "string (1-1000 chars)"
  }
  ```
- **Response** (`CompileResult`):
  ```json
  {
    "ok": true,
    "policy": {
      "name": "string",
      "rules": [
        { "type": "save_percent", "percent": number, "label": "string" } |
        { "type": "category_cap", "category": "string", "monthly_limit": number } |
        { "type": "bill_reserve", "name": "string", "amount": number, "due_day": number }
      ]
    } | null,
    "unsupported": ["string"],
    "message": "string | null",
    "llm_calls": 0,
    "prompt_tokens": 0,
    "completion_tokens": 0
  }
  ```
- **Error cases**:
  - 401: Missing or invalid bearer token
  - 422: Validation error (empty text, text too long)
  - 502: Model API unavailable

### POST /policy/backtest
- **Auth required**: Yes (Bearer token)
- **Request body** (`BacktestRequest`):
  ```json
  {
    "policy": { "name": "string", "rules": [...] }
  }
  ```
- **Response** (`BacktestResult`):
  ```json
  {
    "policy_name": "string",
    "first_day": "YYYY-MM-DD | null",
    "last_day": "YYYY-MM-DD | null",
    "months": [
      {
        "month": "YYYY-MM",
        "income": number,
        "saved": number,
        "spend": number,
        "reserved": number,
        "left_after_policy": number,
        "caps": [
          { "category": "string", "limit": number, "spent": number, "breached": boolean, "over_by": number }
        ]
      }
    ],
    "events": [
      { "day": "YYYY-MM-DD", "kind": "saved | cap_warning | cap_breached | bill_reserved", "rule": "string", "amount": number, "detail": "string" }
    ],
    "total_income": number,
    "total_spend": number,
    "total_saved": number,
    "total_reserved": number,
    "cap_breaches": number,
    "over_cap_total": number,
    "headline": "string",
    "warnings": ["string"]
  }
  ```
- **Error cases**:
  - 401: Missing or invalid bearer token
  - 422: Validation error (invalid policy, e.g., save_percent > 100, duplicate caps)

### POST /policy
- **Auth required**: Yes (Bearer token)
- **Request body** (`SaveRequest`):
  ```json
  {
    "policy": { "name": "string", "rules": [...] },
    "source_text": "string | null (max 1000 chars)"
  }
  ```
- **Response** (`SaveResponse`):
  ```json
  { "id": "string" }
  ```
- **Error cases**:
  - 401: Missing or invalid bearer token
  - 422: Validation error (invalid policy)

### GET /policy/active
- **Auth required**: Yes (Bearer token)
- **Request body**: None
- **Response**:
  ```json
  { "policy": { ... } | null, "source_text": "string | null" }
  ```
  - If no active policy: `{"policy": null, "source_text": null}`
- **Error cases**:
  - 401: Missing or invalid bearer token

### GET /policy/safe-to-spend
- **Auth required**: Yes (Bearer token)
- **Request body**: None
- **Response** (`SafeToSpend`):
  ```json
  {
    "as_of": "YYYY-MM-DD",
    "amount": number,
    "income_used": number,
    "saved": number,
    "spent": number,
    "reserved_upcoming": number,
    "notes": ["string"]
  }
  ```
- **Error cases**:
  - 401: Missing or invalid bearer token
  - 404: No active policy yet

---

## Environment Variables (Names Only)

| Variable | Purpose |
|----------|---------|
| SUPABASE_URL | Supabase project URL |
| SUPABASE_ANON_KEY | Supabase anon/public key for RLS |
| TOKEN_FACTORY_API_KEY | Nebius Token Factory API key |
| TOKEN_FACTORY_BASE_URL | Nebius Token Factory base URL |
| TOKEN_FACTORY_MODEL | Default model ID (fast/cheap) |
| TOKEN_FACTORY_MODEL_SMART | Stronger model ID for policy compilation |
| ALLOWED_ORIGINS | Comma-separated CORS origins (default: http://localhost:5173) |

---

## Local Run Command

```bash
cd services/api
.venv\Scripts\Activate.ps1  # PowerShell
# or: source .venv/bin/activate  # Git Bash
uvicorn bb.main:app --reload --port 8000
```

---

## Routes That Call the LLM

| Route | Model Variable | Purpose |
|-------|----------------|---------|
| POST /enrich | `TOKEN_FACTORY_MODEL` (via `get_llm`) | Classify merchant names into categories |
| POST /policy/compile | `TOKEN_FACTORY_MODEL_SMART` (via `get_smart_llm`) | Compile plain language (English/Hinglish) into policy rules |

---

## Missing for the UI

| Feature | Status | Evidence |
|---------|--------|----------|
| (a) Compile plain-language text (English or Hinglish) into a rule set | **IMPLEMENTED** | `POST /policy/compile` in `bb/main.py:69` calls `compile_policy()` from `bb/policy/compiler.py` |
| (b) Run a backtest on stored transactions | **IMPLEMENTED** | `POST /policy/backtest` in `bb/main.py:79` calls `backtest()` from `bb/policy/engine.py` |
| (c) List proposed actions awaiting approval and record approve/reject | **NOT IMPLEMENTED** | No route exists for listing pending actions or recording approve/reject. `POST /policy` only saves a policy; there is no approval workflow or pending actions table. |
| (d) Trigger enrichment | **IMPLEMENTED** | `POST /enrich` in `bb/main.py:37` calls `enrich_user()` from `bb/enrich.py` |

---

*Generated from code in `services/api/bb/` as of task P3-05. This document is read-only; do not edit the implementation to match it.*