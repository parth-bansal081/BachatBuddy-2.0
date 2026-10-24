from __future__ import annotations

from datetime import date

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from supabase import Client
from .config import env
from .deps import Caller, get_caller, get_llm, get_smart_llm
from .enrich import enrich_user
from .llm import LlmClient, LlmUnavailable
from .policy.compiler import CompileResult, compile_policy
from .policy.engine import BacktestResult, SafeToSpend, backtest, safe_to_spend
from .policy.models import Policy
from .schemas import EnrichResult
from .actions import generate_actions, get_pending_actions, decide_action

load_dotenv()

app = FastAPI(title="BachatBuddy API")

_origins = [o.strip() for o in env("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/enrich", response_model=EnrichResult)
def enrich(caller: Caller = Depends(get_caller), llm: LlmClient = Depends(get_llm)) -> EnrichResult:
    model_name = getattr(llm, "model", "unknown")
    try:
        return enrich_user(caller.store, llm, model_name)
    except LlmUnavailable as exc:
        raise HTTPException(status_code=502, detail=f"Model API unavailable: {exc}") from exc


class CompileRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class BacktestRequest(BaseModel):
    policy: Policy


class SaveRequest(BaseModel):
    policy: Policy
    source_text: str | None = Field(default=None, max_length=1000)


class SaveResponse(BaseModel):
    id: str


class ActionDecision(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")


class ActionOut(BaseModel):
    id: str
    user_id: str
    kind: str
    label: str
    amount: str
    month: str
    status: str
    created_at: str
    decided_at: str | None = None


class GenerateResponse(BaseModel):
    month: str
    actions: list[ActionOut]


def _data(caller: Caller):  # the data store is always set outside of tests
    if caller.data is None:
        raise HTTPException(status_code=500, detail="Data store not available")
    return caller.data


@app.post("/policy/compile", response_model=CompileResult)
def policy_compile(
    body: CompileRequest, caller: Caller = Depends(get_caller), llm: LlmClient = Depends(get_smart_llm)
) -> CompileResult:
    try:
        return compile_policy(body.text, llm)
    except LlmUnavailable as exc:
        raise HTTPException(status_code=502, detail=f"Model API unavailable: {exc}") from exc


@app.post("/policy/backtest", response_model=BacktestResult)
def policy_backtest(body: BacktestRequest, caller: Caller = Depends(get_caller)) -> BacktestResult:
    return backtest(body.policy, _data(caller).enriched_transactions())


@app.post("/policy", response_model=SaveResponse)
def policy_save(body: SaveRequest, caller: Caller = Depends(get_caller)) -> SaveResponse:
    return SaveResponse(id=_data(caller).save_policy(body.policy, body.source_text))


@app.get("/policy/active")
def policy_active(caller: Caller = Depends(get_caller)) -> dict[str, object]:
    found = _data(caller).active_policy()
    if found is None:
        return {"policy": None, "source_text": None}
    policy, source_text = found
    return {"policy": policy.model_dump(), "source_text": source_text}


@app.get("/policy/safe-to-spend", response_model=SafeToSpend)
def policy_safe_to_spend(caller: Caller = Depends(get_caller)) -> SafeToSpend:
    data = _data(caller)
    found = data.active_policy()
    if found is None:
        raise HTTPException(status_code=404, detail="No active policy yet")
    return safe_to_spend(found[0], data.enriched_transactions(), date.today())


def _data_client(caller: Caller) -> Client:
    if caller.data is None:
        raise HTTPException(status_code=500, detail="Data store not available")
    return caller.data.client


@app.post("/actions/generate", response_model=GenerateResponse)
async def actions_generate(caller: Caller = Depends(get_caller)) -> GenerateResponse:
    actions = await generate_actions(_data_client(caller), caller.user_id)
    month = actions[0]["month"] if actions else ""
    return GenerateResponse(month=month, actions=[ActionOut.model_validate(a) for a in actions])


@app.get("/actions/pending", response_model=list[ActionOut])
async def actions_pending(caller: Caller = Depends(get_caller)) -> list[ActionOut]:
    actions = await get_pending_actions(_data_client(caller), caller.user_id)
    return [ActionOut.model_validate(a) for a in actions]


@app.post("/actions/{action_id}/decision", response_model=ActionOut)
async def actions_decide(
    action_id: str,
    body: ActionDecision,
    caller: Caller = Depends(get_caller),
) -> ActionOut:
    try:
        action = await decide_action(_data_client(caller), caller.user_id, action_id, body.decision)
    except ValueError as exc:
        if str(exc) == "already_decided":
            raise HTTPException(status_code=409, detail="Action already decided")
        raise HTTPException(status_code=400, detail=str(exc))
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")
    return ActionOut.model_validate(action)
