"""
Unit tests for OpportunityEngine, SignalExtractor, CTAEngine, and SuppressionEngine.
"""
import pytest
from app.core.opportunity_engine import OpportunityEngine, OpportunityType, Opportunity
from app.core.signal_extractor import SignalExtractor, Signal, SignalType
from app.core.cta_engine import CTAEngine
from app.core.suppression import SuppressionEngine
from app.models.enums import CTA
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_normalized(trigger_kind="research_digest", trigger_urgency=2,
                     signals=None, merchant_id="m_test"):
    """Minimal NormalizedContext-like object for testing."""
    norm = MagicMock()
    norm.merchant.merchant_id = merchant_id
    norm.merchant.signals = signals or []
    norm.merchant.performance.delta_7d = {}
    norm.merchant.performance.ctr = 0.021
    norm.merchant.performance.views = 2410
    norm.trigger.id = f"trg_{trigger_kind}"
    norm.trigger.kind = trigger_kind
    norm.trigger.urgency = trigger_urgency
    norm.trigger.expires_at = "2026-05-03T00:00:00Z"
    return norm


def _make_suppression():
    return SuppressionEngine()


# ---------------------------------------------------------------------------
# Opportunity Engine Tests
# ---------------------------------------------------------------------------

class TestOpportunityEngine:
    def test_research_digest_trigger_maps_to_research_opportunity(self):
        engine = OpportunityEngine()
        suppression = _make_suppression()
        normalized = _make_normalized(trigger_kind="research_digest")
        signals = SignalExtractor().extract_signals(normalized)
        result = engine.select_best_opportunity(normalized, signals, suppression, "research_digest")
        assert result == OpportunityType.RESEARCH_DIGEST

    def test_perf_dip_trigger_maps_correctly(self):
        engine = OpportunityEngine()
        suppression = _make_suppression()
        normalized = _make_normalized(trigger_kind="perf_dip")
        signals = SignalExtractor().extract_signals(normalized)
        result = engine.select_best_opportunity(normalized, signals, suppression, "perf_dip")
        assert result == OpportunityType.PERF_DIP

    def test_recall_due_trigger_maps_correctly(self):
        engine = OpportunityEngine()
        suppression = _make_suppression()
        normalized = _make_normalized(trigger_kind="recall_due")
        signals = SignalExtractor().extract_signals(normalized)
        result = engine.select_best_opportunity(normalized, signals, suppression, "recall_due")
        assert result == OpportunityType.RECALL_DUE

    def test_unknown_trigger_returns_informational_or_none(self):
        """Unknown trigger kind should not crash — return None or a fallback type."""
        engine = OpportunityEngine()
        suppression = _make_suppression()
        normalized = _make_normalized(trigger_kind="totally_unknown_kind")
        signals = SignalExtractor().extract_signals(normalized)
        result = engine.select_best_opportunity(normalized, signals, suppression, "totally_unknown_kind")
        # Either None or INFORMATIONAL_OPPORTUNITY is acceptable
        assert result is None or result == OpportunityType.INFORMATIONAL_OPPORTUNITY

    def test_suppressed_opportunity_not_returned(self):
        """If an opportunity is suppressed it should not be returned."""
        engine = OpportunityEngine()
        suppression = _make_suppression()
        normalized = _make_normalized(trigger_kind="research_digest")
        # Pre-suppress this combination
        suppression.record_send("m_test", "trg_research_digest", "research_digest", "some message body")
        signals = SignalExtractor().extract_signals(normalized)
        # After cooldown is active the same opportunity should be suppressed
        result = engine.select_best_opportunity(normalized, signals, suppression, "research_digest")
        # Either None (fully suppressed) or a different opportunity
        assert result != OpportunityType.RESEARCH_DIGEST or result is None

    def test_festival_trigger_maps_to_seasonal(self):
        engine = OpportunityEngine()
        suppression = _make_suppression()
        normalized = _make_normalized(trigger_kind="festival_upcoming")
        signals = SignalExtractor().extract_signals(normalized)
        result = engine.select_best_opportunity(normalized, signals, suppression, "festival_upcoming")
        assert result == OpportunityType.SEASONAL_OPPORTUNITY

    def test_competitor_opened_maps_correctly(self):
        engine = OpportunityEngine()
        suppression = _make_suppression()
        normalized = _make_normalized(trigger_kind="competitor_opened")
        signals = SignalExtractor().extract_signals(normalized)
        result = engine.select_best_opportunity(normalized, signals, suppression, "competitor_opened")
        assert result == OpportunityType.COMPETITOR_CONTEXT


# ---------------------------------------------------------------------------
# CTA Engine Tests
# ---------------------------------------------------------------------------

class TestCTAEngine:
    def test_research_digest_returns_open_ended(self):
        engine = CTAEngine()
        assert engine.select_cta(OpportunityType.RESEARCH_DIGEST, "merchant") == CTA.OPEN_ENDED

    def test_perf_dip_returns_binary_yes_stop(self):
        engine = CTAEngine()
        assert engine.select_cta(OpportunityType.PERF_DIP, "merchant") == CTA.BINARY_YES_STOP

    def test_recall_due_customer_scope_returns_multi_choice(self):
        engine = CTAEngine()
        assert engine.select_cta(OpportunityType.RECALL_DUE, "customer") == CTA.MULTI_CHOICE_SLOT

    def test_renewal_due_returns_binary(self):
        engine = CTAEngine()
        assert engine.select_cta(OpportunityType.RENEWAL_DUE, "merchant") == CTA.BINARY_YES_STOP

    def test_informational_returns_none(self):
        engine = CTAEngine()
        assert engine.select_cta(OpportunityType.INFORMATIONAL_OPPORTUNITY, "merchant") == CTA.NONE


# ---------------------------------------------------------------------------
# Suppression Engine Tests
# ---------------------------------------------------------------------------

class TestSuppressionEngine:
    def test_first_send_not_suppressed(self):
        engine = SuppressionEngine()
        suppressed, reason = engine.should_suppress("m1", "trg1", "perf_dip", "some message")
        assert not suppressed

    def test_cooldown_suppresses_second_send(self):
        engine = SuppressionEngine()
        engine.record_send("m1", "trg1", "perf_dip", "some message")
        suppressed, reason = engine.should_suppress("m1", "trg1", "perf_dip", "some message")
        assert suppressed
        assert "Cooldown" in reason or "cooldown" in reason.lower()

    def test_different_merchant_not_suppressed(self):
        """Suppression is per merchant — m2 should not be suppressed because m1 was."""
        engine = SuppressionEngine()
        engine.record_send("m1", "trg1", "perf_dip", "some message")
        suppressed, _ = engine.should_suppress("m2", "trg1", "perf_dip", "some message")
        assert not suppressed

    def test_duplicate_body_suppressed(self):
        """Same body hash should be suppressed."""
        engine = SuppressionEngine({"cooldown_hours": 0})  # zero cooldown
        engine.record_send("m1", "trg1", "perf_dip", "exact same message body")
        suppressed, reason = engine.should_suppress("m1", "trg1", "perf_dip", "exact same message body")
        # Either cooldown or duplicate
        assert suppressed

    def test_max_nudges_suppresses(self):
        """After max nudges exceeded, further sends should be suppressed."""
        engine = SuppressionEngine({"cooldown_hours": 0, "max_nudges": 2})
        engine.record_send("m1", "trg1", "perf_dip", "msg1")
        engine.record_send("m1", "trg1", "perf_dip", "msg2")
        # 2 sends, max_nudges=2 — next should be suppressed
        engine._store["m1:trg1:perf_dip"].nudge_count = 3  # force over limit
        suppressed, reason = engine.should_suppress("m1", "trg1", "perf_dip", "msg3")
        assert suppressed


# ---------------------------------------------------------------------------
# Signal Extractor Tests
# ---------------------------------------------------------------------------

class TestSignalExtractor:
    def test_research_digest_trigger_produces_signal(self):
        extractor = SignalExtractor()
        normalized = _make_normalized(trigger_kind="research_digest")
        signals = extractor.extract_signals(normalized)
        types = [s.type for s in signals]
        assert SignalType.RESEARCH_DIGEST in types

    def test_perf_dip_trigger_produces_signal(self):
        extractor = SignalExtractor()
        normalized = _make_normalized(trigger_kind="perf_dip")
        signals = extractor.extract_signals(normalized)
        types = [s.type for s in signals]
        assert SignalType.PERF_DIP in types

    def test_merchant_ctr_below_threshold_produces_signal(self):
        extractor = SignalExtractor()
        normalized = _make_normalized()
        normalized.merchant.performance.ctr = 0.01  # below 0.02 threshold
        normalized.merchant.performance.delta_7d = {}
        signals = extractor.extract_signals(normalized)
        types = [s.type for s in signals]
        assert SignalType.PERF_DIP in types

    def test_merchant_views_spike_produces_signal(self):
        extractor = SignalExtractor()
        normalized = _make_normalized()
        normalized.merchant.performance.delta_7d = {"views_pct": 0.35}  # >0.2
        signals = extractor.extract_signals(normalized)
        types = [s.type for s in signals]
        assert SignalType.PERF_SPIKE in types

    def test_unknown_trigger_produces_no_crash(self):
        """Unknown trigger kind should not crash the extractor."""
        extractor = SignalExtractor()
        normalized = _make_normalized(trigger_kind="unknown_future_trigger_kind")
        signals = extractor.extract_signals(normalized)
        # Should return list (possibly empty) without error
        assert isinstance(signals, list)
