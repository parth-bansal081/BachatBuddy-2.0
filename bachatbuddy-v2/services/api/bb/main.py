from __future__ import annotations

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import env
from .deps import Caller, get_caller, get_llm
from .enrich import enrich_user
from .llm import LlmClient, LlmUnavailable
from .schemas import EnrichResult

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
