"""
Unit tests for the FactLedger.
Tests: isolation, singleton bug detection, per-request scoping.
"""
import pytest
from app.context.fact_ledger import FactLedger, FactStatus


def make_ledger():
    """Create a fresh per-request FactLedger instance."""
    return FactLedger()


class TestFactLedgerIsolation:
    def test_fresh_ledger_is_empty(self):
        ledger = make_ledger()
        assert ledger.get_verified_facts() == []

    def test_add_fact_stores_it(self):
        ledger = make_ledger()
        fid = ledger.add_fact("orders declined by 18%", -18.0, "merchant.performance", "orders_change",
                              verified=True, status=FactStatus.VERIFIED)
        assert ledger.get_fact(fid) is not None
        assert ledger.get_fact(fid).value == -18.0

    def test_merchant_a_facts_not_in_merchant_b_ledger(self):
        """Core isolation test — BUG 1 regression."""
        ledger_a = make_ledger()
        ledger_b = make_ledger()

        ledger_a.add_fact("merchant A views: 2410", 2410.0, "merchant.performance", "views",
                          verified=True, status=FactStatus.VERIFIED)

        # Merchant B's ledger must not see merchant A's facts
        facts_b = ledger_b.get_verified_facts()
        assert len(facts_b) == 0, "Merchant B ledger should be empty (isolation failure)"

    def test_global_singleton_isolation_check(self):
        """
        Verify that the module-level singleton (fact_ledger) IS shared — documenting
        the bug — and that our per-request pattern (make_ledger()) is safe.
        This test EXPECTS the singleton to accumulate, confirming the bug exists.
        """
        from app.context.fact_ledger import fact_ledger as singleton
        initial_count = len(singleton._facts)
        singleton.add_fact("singleton test fact", 999.0, "test", "test",
                           verified=True, status=FactStatus.VERIFIED)
        assert len(singleton._facts) == initial_count + 1, "Singleton accumulates across calls (BUG 1)"

    def test_independent_ledgers_have_separate_fact_ids(self):
        ledger_a = make_ledger()
        ledger_b = make_ledger()
        fid_a = ledger_a.add_fact("A fact", 1.0, "src", "field", verified=True, status=FactStatus.VERIFIED)
        fid_b = ledger_b.add_fact("B fact", 2.0, "src", "field", verified=True, status=FactStatus.VERIFIED)
        # They may coincidentally have same ID (fact_0) — that's OK because they're separate objects
        assert ledger_a.get_fact(fid_a).text == "A fact"
        assert ledger_b.get_fact(fid_b).text == "B fact"
        # B cannot retrieve A's fact by ID
        assert ledger_b.get_fact(fid_a) is None or ledger_b.get_fact(fid_a).text == "B fact"


class TestFactLedgerExtraction:
    def test_extract_from_context_populates_facts(self):
        """extract_from_context should populate numeric performance facts."""
        from app.context.normalizer import ContextNormalizer
        import json

        ledger = make_ledger()
        normalizer = ContextNormalizer()
        cat = json.load(open("dataset/categories/dentists.json"))
        m_raw = json.load(open("dataset/merchants_seed.json"))["merchants"][0]
        t_raw = json.load(open("dataset/triggers_seed.json"))["triggers"][0]

        normalized = normalizer.normalize(cat, m_raw, t_raw)
        facts = ledger.extract_from_context(normalized)
        assert len(facts) > 0

        # Should contain at least views fact
        view_facts = [f for f in facts.values() if "views" in f.field.lower() or "views" in f.text.lower()]
        assert len(view_facts) > 0, "Should have a views fact from merchant performance"

    def test_ctr_fact_is_float_not_string(self):
        """CTR fact value must be stored as float for validator comparisons."""
        from app.context.normalizer import ContextNormalizer
        import json

        ledger = make_ledger()
        normalizer = ContextNormalizer()
        cat = json.load(open("dataset/categories/dentists.json"))
        m_raw = json.load(open("dataset/merchants_seed.json"))["merchants"][0]
        t_raw = json.load(open("dataset/triggers_seed.json"))["triggers"][0]

        normalized = normalizer.normalize(cat, m_raw, t_raw)
        ledger.extract_from_context(normalized)

        ctr_facts = [f for f in ledger._facts.values() if f.field == "ctr"]
        if ctr_facts:
            assert isinstance(ctr_facts[0].value, float)
