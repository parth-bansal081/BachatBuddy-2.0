from datetime import date
from decimal import Decimal

from bb.data import PAGE, SupabaseDataStore
from bb.policy.models import Policy


class Q:
    def __init__(self, table, db):
        self.t, self.db, self.start, self.end, self.op, self.payload = table, db, 0, 10**9, "select", None

    def select(self, cols): return self
    def eq(self, c, v): self.db.setdefault("eq", []).append((self.t, c, v)); return self
    def order(self, c): return self
    def limit(self, n): return self
    def range(self, a, b): self.start, self.end = a, b; return self
    def update(self, payload): self.op, self.payload = "update", payload; return self
    def insert(self, payload): self.op, self.payload = "insert", payload; return self

    def execute(self):
        if self.op == "update":
            self.db.setdefault("updates", []).append((self.t, self.payload)); return type("R", (), {"data": []})()
        if self.op == "insert":
            self.db.setdefault("inserts", []).append((self.t, self.payload)); return type("R", (), {"data": [{"id": "new-id"}]})()
        return type("R", (), {"data": self.db.get(self.t, [])[self.start : self.end + 1]})()


class C:
    def __init__(self, db): self.db = db
    def table(self, name): return Q(name, self.db)


def test_enriched_transactions_parse_dates_amounts_and_legacy_categories():
    db = {"transactions_enriched": [
        {"date": "2026-01-05T10:00:00+00:00", "amount": -120.5, "merchant": "UPI/x", "enriched_category": "Food"},
        {"date": "2026-01-06", "amount": 50000, "merchant": "SALARY", "enriched_category": "Income"},
        {"date": None, "amount": 1, "merchant": "bad", "enriched_category": "Income"},
    ]}
    txns = SupabaseDataStore(C(db), "u1").enriched_transactions()  # type: ignore[arg-type]
    assert len(txns) == 2
    assert txns[0].day == date(2026, 1, 5) and txns[0].amount == Decimal("-120.5") and txns[0].category == "Food & Dining"
    assert txns[1].category == "Income"


def test_reads_every_page():
    rows = [{"date": "2026-01-01", "amount": -1, "merchant": "m", "enriched_category": "Groceries"} for _ in range(PAGE + 7)]
    assert len(SupabaseDataStore(C({"transactions_enriched": rows}), "u1").enriched_transactions()) == PAGE + 7  # type: ignore[arg-type]


def test_save_policy_deactivates_old_then_inserts_active():
    db: dict = {}
    pol = Policy.model_validate({"name": "p", "rules": [{"type": "save_percent", "percent": 10}]})
    pid = SupabaseDataStore(C(db), "u1").save_policy(pol, "save 10%")  # type: ignore[arg-type]
    assert pid == "new-id"
    assert db["updates"] == [("policies", {"active": False})]
    table, row = db["inserts"][0]
    assert table == "policies" and row["user_id"] == "u1" and row["active"] is True and row["source_text"] == "save 10%"
    assert row["rules"][0]["type"] == "save_percent"


def test_active_policy_roundtrip_and_none():
    rules = [{"type": "category_cap", "category": "Groceries", "monthly_limit": 5000}]
    got = SupabaseDataStore(C({"policies": [{"name": "p", "rules": rules, "source_text": "t"}]}), "u1").active_policy()  # type: ignore[arg-type]
    assert got is not None and got[0].rules[0].type == "category_cap" and got[1] == "t"
    assert SupabaseDataStore(C({}), "u1").active_policy() is None  # type: ignore[arg-type]
