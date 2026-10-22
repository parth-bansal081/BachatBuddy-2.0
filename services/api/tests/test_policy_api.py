from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from bb.deps import Caller, get_caller, get_smart_llm
from bb.main import app
from bb.policy.engine import Txn
from bb.policy.models import Policy
from test_compiler import GOOD, Scripted
from test_enrich import FakeStore

POLICY = {"name": "p", "rules": [{"type": "save_percent", "percent": 10}, {"type": "bill_reserve", "name": "Rent", "amount": 6000, "due_day": 1}]}


class FakeData:
    def __init__(self):
        self.saved = None
        self.active = None

    def enriched_transactions(self):
        return [Txn(date(2026, 1, 5), Decimal("50000"), "Income"), Txn(date(2026, 1, 9), Decimal("-100"), "Groceries")]

    def save_policy(self, policy, source_text):
        self.saved = (policy, source_text)
        self.active = (policy, source_text)
        return "pid-1"

    def active_policy(self):
        return self.active


def client(data, llm=None):
    app.dependency_overrides[get_caller] = lambda: Caller(user_id="u1", store=FakeStore([]), data=data)  # type: ignore[arg-type]
    if llm is not None:
        app.dependency_overrides[get_smart_llm] = lambda: llm
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_policy_endpoints_require_a_token():
    for method, path in [("post", "/policy/compile"), ("post", "/policy/backtest"), ("post", "/policy"), ("get", "/policy/active"), ("get", "/policy/safe-to-spend")]:
        assert getattr(TestClient(app), method)(path).status_code in (401, 422), path


def test_compile_endpoint():
    res = client(FakeData(), Scripted(GOOD)).post("/policy/compile", json={"text": "save 10%"})
    assert res.status_code == 200 and res.json()["ok"] is True and len(res.json()["policy"]["rules"]) == 2


def test_compile_endpoint_rejects_empty_text():
    assert client(FakeData(), Scripted()).post("/policy/compile", json={"text": ""}).status_code == 422


def test_compile_endpoint_502_when_model_down():
    from bb.llm import LlmUnavailable

    class Down:
        def complete(self, system, user):
            raise LlmUnavailable("down")

    assert client(FakeData(), Down()).post("/policy/compile", json={"text": "save 10%"}).status_code == 502


def test_backtest_endpoint_uses_the_users_transactions():
    res = client(FakeData()).post("/policy/backtest", json={"policy": POLICY})
    body = res.json()
    assert res.status_code == 200 and body["total_saved"] == 5000.0 and body["total_reserved"] == 6000.0


def test_backtest_endpoint_rejects_invalid_policy():
    bad = {"name": "p", "rules": [{"type": "save_percent", "percent": 500}]}
    assert client(FakeData()).post("/policy/backtest", json={"policy": bad}).status_code == 422


def test_save_then_active_then_safe_to_spend():
    data = FakeData()
    c = client(data)
    assert c.get("/policy/active").json() == {"policy": None, "source_text": None}
    assert c.get("/policy/safe-to-spend").status_code == 404
    res = c.post("/policy", json={"policy": POLICY, "source_text": "save 10%"})
    assert res.json() == {"id": "pid-1"} and data.saved[1] == "save 10%"
    assert c.get("/policy/active").json()["policy"]["name"] == "p"
    assert c.get("/policy/safe-to-spend").status_code == 200
