from fastapi.testclient import TestClient

from bb.deps import Caller, get_caller, get_llm
from bb.llm import Usage
from bb.main import app
from test_enrich import ANSWERS, NARR, FakeLlm, FakeStore


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_enrich_requires_a_token():
    assert TestClient(app).post("/enrich").status_code == 401


def test_enrich_happy_path_with_fakes():
    store = FakeStore(NARR)
    app.dependency_overrides[get_caller] = lambda: Caller(user_id="u1", store=store)  # type: ignore[arg-type]
    app.dependency_overrides[get_llm] = lambda: FakeLlm(ANSWERS)
    try:
        res = TestClient(app).post("/enrich")
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 200
    body = res.json()
    assert body["new_keys"] == 2 and body["llm_calls"] == 1 and body["fallbacks"] == 0


def test_enrich_returns_502_when_model_down():
    from bb.llm import LlmUnavailable

    class Down:
        model = "x"

        def complete(self, system, user):
            raise LlmUnavailable("down")

    app.dependency_overrides[get_caller] = lambda: Caller(user_id="u1", store=FakeStore(NARR))  # type: ignore[arg-type]
    app.dependency_overrides[get_llm] = lambda: Down()
    try:
        res = TestClient(app).post("/enrich")
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 502
