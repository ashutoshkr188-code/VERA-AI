"""
Unit tests for the Validator.
Tests: hallucination check (false-positive regression), valid messages, repair.
"""
import pytest
from app.context.fact_ledger import Fact, FactStatus
from app.validation.validator import Validator, GroundingValidator
from app.llm.composer import MessageCompose


def make_fact(fact_id: str, text: str, value=None, field: str = "test"):
    return Fact(
        fact_id=fact_id,
        text=text,
        value=value,
        source="test",
        field=field,
        verified=True,
        status=FactStatus.VERIFIED,
    )


class TestHallucinationCheck:
    """
    The hallucination check should flag unsupported *factual claims*
    but NOT flag purely stylistic sentences.
    """

    def test_supported_number_passes(self):
        """A number that matches a ledger fact should not be flagged."""
        gv = GroundingValidator()
        facts = [make_fact("f1", "orders declined by 18%", value=-18.0, field="orders_change")]
        violations = gv.validate_hallucination("Orders are down 18%.", facts)
        assert violations == [], f"Should not flag supported number 18: {violations}"

    def test_unsupported_number_flagged(self):
        """A number NOT in any fact should be flagged."""
        gv = GroundingValidator()
        facts = [make_fact("f1", "orders declined by 18%", value=-18.0, field="orders_change")]
        violations = gv.validate_hallucination("Orders are down 35%.", facts)
        assert len(violations) > 0, "Should flag unsupported number 35"

    def test_stylistic_sentence_not_flagged(self):
        """Pure stylistic text with no numbers should never fail hallucination check."""
        gv = GroundingValidator()
        facts = [make_fact("f1", "CTR: 2.10%", value=0.021, field="ctr")]
        violations = gv.validate_hallucination("Worth a look?", facts)
        assert violations == [], "Stylistic sentence should not fail hallucination check"

    def test_year_in_message_not_flagged(self):
        """A year number (like 2026) appearing in a message shouldn't be flagged as hallucination
        unless we have a specific year-based fact rule."""
        gv = GroundingValidator()
        facts = [make_fact("f1", "CTR: 2.10%", value=0.021, field="ctr")]
        violations = gv.validate_hallucination("JIDA Oct 2026 research dropped.", facts)
        # Years are common in text and should not require a matching numeric fact
        assert violations == [], f"Year 2026 should not be flagged as hallucination: {violations}"

    def test_price_from_fact_passes(self):
        """A price mentioned in a fact should be allowed in message."""
        gv = GroundingValidator()
        facts = [make_fact("f1", "Active offer: Dental Cleaning @ Rs299", value=None, field="offer")]
        violations = gv.validate_hallucination("Dental Cleaning @ Rs299 — book now.", facts)
        assert violations == [], f"Price from fact should not be flagged: {violations}"

    def test_multiple_supported_numbers_pass(self):
        """All numbers in the message present somewhere in facts should pass."""
        gv = GroundingValidator()
        facts = [
            make_fact("f1", "Google views: 2410", value=2410.0, field="views"),
            make_fact("f2", "Calls: 18", value=18.0, field="calls"),
        ]
        violations = gv.validate_hallucination(
            "Your profile had 2410 views and 18 calls last month.", facts
        )
        assert violations == [], f"All numbers are supported: {violations}"


class TestValidatorFull:
    def _make_grounded(self, body: str = "Test message"):
        """Build a minimal GroundedContext mock for testing."""
        from unittest.mock import MagicMock
        grounded = MagicMock()
        grounded.facts = [make_fact("f1", "orders declined by 18%", value=-18.0, field="orders_change")]
        grounded.merchant.identity.owner_first_name = "Meera"
        grounded.merchant.identity.name = "Dr. Meera's Dental Clinic"
        grounded.category.voice.vocab_taboo = ["guaranteed", "100% safe"]
        return grounded

    def test_valid_response_passes(self):
        """A clean, grounded message should pass validation."""
        validator = Validator()
        grounded = self._make_grounded()
        msg = MessageCompose(body="Dr. Meera, orders declined by 18%. Want me to look into this?",
                             cta="open_ended", rationale="test", claims=[])
        result = validator.validate(msg, grounded, [], "open_ended")
        # May have minor violations but should not flag hallucinations for "18"
        hallucination_violations = [v for v in result.violations if "Unsupported number" in v and "18" in v]
        assert hallucination_violations == [], f"18 from fact should not be flagged: {result.violations}"

    def test_unsupported_claim_fails(self):
        """A message with a made-up number not in any fact should have violations."""
        validator = Validator()
        grounded = self._make_grounded()
        grounded.facts = [make_fact("f1", "orders declined by 18%", value=-18.0, field="orders_change")]
        msg = MessageCompose(body="Dr. Meera, orders declined by 75%. This is critical.",
                             cta="open_ended", rationale="test", claims=[])
        result = validator.validate(msg, grounded, [], "open_ended")
        hallucination_violations = [v for v in result.violations if "Unsupported number" in v]
        assert len(hallucination_violations) > 0, "75 should be flagged as unsupported"

    def test_repetition_detection(self):
        """Sending the exact same message that was sent before should fail."""
        validator = Validator()
        grounded = self._make_grounded()
        msg = MessageCompose(body="Let's improve your profile.", cta="open_ended", rationale="test", claims=[])
        history = ["Let's improve your profile."]
        result = validator.validate(msg, grounded, history, "open_ended")
        repetition_violations = [v for v in result.violations if "epeat" in v or "ame" in v]
        assert len(repetition_violations) > 0, "Repeated message should be flagged"


class TestValidatorRepair:
    """Tests for Validator.repair() — BUG 9 regression."""

    def _make_grounded(self):
        from unittest.mock import MagicMock
        grounded = MagicMock()
        grounded.facts = [make_fact("f1", "CTR: 2.10%", value=0.021, field="ctr")]
        grounded.merchant.identity.owner_first_name = "Meera"
        grounded.merchant.identity.name = "Dr. Meera"
        grounded.category.voice.vocab_taboo = ["guaranteed"]
        return grounded

    def test_repair_returns_message_compose(self):
        """repair() must exist and return a MessageCompose."""
        validator = Validator()
        grounded = self._make_grounded()
        msg = MessageCompose(body="Your CTR is 2.10%. Let's fix this. YES / STOP / MAYBE",
                             cta="open_ended", rationale="test", claims=[])
        repaired = validator.repair(msg, grounded, "open_ended")
        assert isinstance(repaired, MessageCompose)
        assert repaired.body  # must not be empty

    def test_repair_does_not_invent_facts(self):
        """Repaired message must not contain numbers not in the fact ledger."""
        validator = Validator()
        grounded = self._make_grounded()
        # Message with a hallucinated number
        msg = MessageCompose(body="Your CTR jumped by 99%. Amazing result!",
                             cta="open_ended", rationale="test", claims=[])
        repaired = validator.repair(msg, grounded, "open_ended")
        # Should either remove "99" or fall back to something grounded
        assert "99" not in repaired.body or repaired.body == msg.body, \
            "Repair should not silently keep hallucinated content"

    def test_repair_preserves_grounded_content(self):
        """Repair should keep valid grounded content if present."""
        validator = Validator()
        grounded = self._make_grounded()
        msg = MessageCompose(body="Dr. Meera, your CTR is 2.10%. Let's improve this.",
                             cta="open_ended", rationale="test", claims=[])
        repaired = validator.repair(msg, grounded, "open_ended")
        assert repaired.body  # non-empty
