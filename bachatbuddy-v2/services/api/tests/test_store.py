from bb.schemas import CacheRow
from bb.store import PAGE, SupabaseStore


class FakeQuery:
    def __init__(self, table, db):
        self.table_name, self.db = table, db
        self.start = 0
        self.end = 10**9

    def select(self, cols):
        return self

    def eq(self, col, value):
        assert col == "user_id" and value == "u1"
        return self

    def range(self, start, end):
        self.start, self.end = start, end
        return self

    def upsert(self, payload, on_conflict):
        self.db.setdefault("upserts", []).append((self.table_name, on_conflict, payload))
        return self

    def execute(self):
        rows = self.db.get(self.table_name, [])[self.start : self.end + 1]
        return type("R", (), {"data": rows})()


class FakeClient:
    def __init__(self, db):
        self.db = db

    def table(self, name):
        return FakeQuery(name, self.db)


def test_reads_all_pages_and_dedupes_narrations():
    rows = [{"merchant": f"M{i % 1500}"} for i in range(PAGE + 500)]  # forces 2 pages
    store = SupabaseStore(FakeClient({"transactions": rows}), "u1")  # type: ignore[arg-type]
    assert len(store.distinct_narrations()) == 1500


def test_cached_keys_excludes_fallback():
    db = {"merchant_cache": [{"key": "a", "source": "llm"}, {"key": "b", "source": "fallback"}, {"key": "c", "source": "user"}]}
    assert SupabaseStore(FakeClient(db), "u1").cached_keys() == {"a", "c"}  # type: ignore[arg-type]


def test_mapped_returns_narration_to_key():
    db = {"narration_map": [{"raw_narration": "n1", "key": "k1"}]}
    assert SupabaseStore(FakeClient(db), "u1").mapped() == {"n1": "k1"}  # type: ignore[arg-type]


def test_upserts_carry_user_id_and_conflict_target():
    db: dict = {}
    store = SupabaseStore(FakeClient(db), "u1")  # type: ignore[arg-type]
    store.upsert_cache([CacheRow(key="k", clean_name="K", category="Shopping", confidence=0.9, needs_review=False, source="llm")])
    store.upsert_map([("raw", "k")])
    (t1, c1, p1), (t2, c2, p2) = db["upserts"]
    assert (t1, c1) == ("merchant_cache", "user_id,key") and p1[0]["user_id"] == "u1"
    assert (t2, c2) == ("narration_map", "user_id,raw_narration") and p2[0] == {"user_id": "u1", "raw_narration": "raw", "key": "k"}
