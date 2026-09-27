"""
Validator for composed messages.
Checks grounding, category fit, merchant fit, CTA, hallucinations, and repetition.
Includes repair() to produce a safe cleaned message when validation fails.
"""
from typing import Optional, List, TYPE_CHECKING
import re
from pydantic import BaseModel, Field
from app.context.fact_ledger import Fact, FactStatus

if TYPE_CHECKING:
    from app.llm.composer import MessageCompose
    from app.retrieval.structured_retriever import GroundedContext


class ValidationResult(BaseModel):
    valid: bool
    violations: List[str] = []
    corrected_message: Optional[str] = None
    fallback_used: bool = False


class GroundingValidator:
    """Deterministic checks for each validation dimension."""

    # 4-digit years (1900-2099) are always allowed — they are context, not invented data.
    _YEAR_RE = re.compile(r"^(19|20)\d{2}$")

    def validate_grounding(self, message: str, grounded_facts: List[Fact]) -> List[str]:
        """Currently lenient — hallucination check handles numeric grounding."""
        return []

    def validate_merchant_fit(self, message: str, merchant) -> List[str]:
        """Verify some form of merchant name appears in the message."""
        violations = []
        owner = (merchant.identity.owner_first_name or "").lower().strip()
        biz_name = merchant.identity.name.lower()
        msg_lower = message.lower()

        # Accept if owner first name present
        if owner and owner in msg_lower:
            return []
        # Accept if any significant word from biz name present (>3 chars)
        if any(part in msg_lower for part in biz_name.split() if len(part) > 3):
            return []
        violations.append("Merchant name not mentioned")
        return violations

    def validate_category_fit(self, message: str, category) -> List[str]:
        """Check that no taboo words appear in the message."""
        violations = []
        try:
            taboos = getattr(category.voice, "vocab_taboo", [])
        except Exception:
            return []
        msg_lower = message.lower()
        for taboo in taboos:
            if taboo.lower() in msg_lower:
                violations.append(f"Taboo word used: '{taboo}'")
        return violations

    def validate_cta(self, message: str, expected_cta: str) -> List[str]:
        """Validate CTA is a known type."""
        valid_ctas = ["binary_yes_stop", "binary_confirm_cancel", "open_ended",
                      "multi_choice_slot", "none"]
        if expected_cta not in valid_ctas:
            return [f"Unknown CTA type: {expected_cta}"]
        return []

    def _build_allowed_numbers(self, grounded_facts: List[Fact]) -> set:
        """
        Build the set of number strings that are permitted in a composed message.

        A number N is allowed if:
          - N appears as a digit sequence anywhere in any fact's text string, OR
          - N matches the integer or float string representation of any fact's value, OR
          - N looks like a percentage of a decimal fact value (e.g. 0.021 -> "2" for 2.1%)
        """
        allowed: set = set()
        for f in grounded_facts:
            # All digit substrings in the fact text
            if f.text:
                for m in re.findall(r"\d+", f.text):
                    allowed.add(m)
            # Numeric value representations
            if f.value is not None:
                v = f.value
                # Integer form
                try:
                    allowed.add(str(int(v)))
                except (ValueError, TypeError):
                    pass
                # Float form (without trailing zeros)
                allowed.add(str(v))
                # Percentage: if value is a decimal (e.g. 0.021 -> 2 or 3)
                if 0 < abs(v) < 1:
                    pct = abs(v) * 100
                    allowed.add(str(int(round(pct))))
                    allowed.add(str(int(pct)))
        return allowed

    def validate_hallucination(self, message: str, grounded_facts: List[Fact]) -> List[str]:
        """
        Flag integers in the message body that are NOT supported by grounded facts.

        Exempt:
          - 4-digit years (1900-2099) — contextual references, not invented data
          - Any number that appears (as digit sequence) in any fact text
          - Any number matching a fact's numeric value (integer or percentage form)
        """
        violations = []
        nums_in_msg = re.findall(r"\d+", message)
        if not nums_in_msg:
            return []

        allowed = self._build_allowed_numbers(grounded_facts)

        for n in nums_in_msg:
            if self._YEAR_RE.match(n):
                continue  # Years are always allowed
            if n not in allowed:
                violations.append(f"Unsupported number: {n}")
        return violations

    def validate_repetition(self, message: str, history: List[str]) -> List[str]:
        """Flag verbatim message repetition."""
        for h in history:
            if h == message:
                return ["Repeated message verbatim"]
        return []


class Validator:
    def __init__(self):
        self.grounding = GroundingValidator()

    def validate(self,
                 message: "MessageCompose",
                 grounded: "GroundedContext",
                 history: List[str] = [],
                 expected_cta: str = "open_ended") -> ValidationResult:
        all_violations: List[str] = []
        all_violations.extend(self.grounding.validate_grounding(message.body, grounded.facts))
        all_violations.extend(self.grounding.validate_merchant_fit(message.body, grounded.merchant))
        all_violations.extend(self.grounding.validate_category_fit(message.body, grounded.category))
        all_violations.extend(self.grounding.validate_cta(message.body, expected_cta))
        all_violations.extend(self.grounding.validate_hallucination(message.body, grounded.facts))
        all_violations.extend(self.grounding.validate_repetition(message.body, history))

        return ValidationResult(
            valid=len(all_violations) == 0,
            violations=all_violations,
            corrected_message=None,
            fallback_used=False,
        )

    def repair(self,
               message: "MessageCompose",
               grounded: "GroundedContext",
               expected_cta: str = "open_ended") -> "MessageCompose":
        """
        Deterministic repair of a message that failed validation.

        Steps:
        1. Remove sentences that contain unsupported numbers.
        2. Remove taboo words.
        3. If the cleaned body is viable (>=20 chars), return it.
        4. Otherwise, generate a deterministic safe fallback from grounded facts.

        IMPORTANT: repair() NEVER invents new facts. It only:
          - Removes problematic content
          - Uses text directly from grounded.facts
        """
        from app.llm.composer import MessageCompose

        body = message.body or ""
        allowed_numbers = self.grounding._build_allowed_numbers(grounded.facts)
        year_re = self.grounding._YEAR_RE

        # --- Step 1: Remove sentences with unsupported numbers ---
        sentences = re.split(r"(?<=[.!?])\s+", body.strip())
        clean_sentences = []
        for sent in sentences:
            nums = re.findall(r"\d+", sent)
            unsupported = [n for n in nums
                           if not year_re.match(n) and n not in allowed_numbers]
            if not unsupported:
                clean_sentences.append(sent)

        repaired_body = " ".join(clean_sentences).strip()

        # --- Step 2: Remove taboo words ---
        try:
            taboos = getattr(grounded.category.voice, "vocab_taboo", [])
            for taboo in taboos:
                repaired_body = re.sub(
                    re.escape(taboo), "", repaired_body, flags=re.IGNORECASE
                ).strip()
        except Exception:
            pass

        # --- Step 3: If cleaned body is viable, return it ---
        if repaired_body and len(repaired_body) >= 20:
            return MessageCompose(
                body=repaired_body,
                cta=expected_cta,
                rationale=message.rationale + " [repaired: removed unsupported claims]",
                claims=[c for c in message.claims if self._claim_is_clean(c, allowed_numbers, year_re)],
            )

        # --- Step 4: Safe deterministic fallback from grounded facts ---
        safe_body = self._build_safe_fallback(grounded)
        return MessageCompose(
            body=safe_body,
            cta=expected_cta,
            rationale="Deterministic safe fallback after validation repair",
            claims=[],
        )

    def _claim_is_clean(self, claim: dict, allowed_numbers: set, year_re) -> bool:
        """Return True if a claim's text contains no unsupported numbers."""
        text = claim.get("text", "")
        for n in re.findall(r"\d+", text):
            if not year_re.match(n) and n not in allowed_numbers:
                return False
        return True

    def _build_safe_fallback(self, grounded: "GroundedContext") -> str:
        """Build a minimal safe message from grounded facts. No invented numbers."""
        try:
            merchant_name = (
                grounded.merchant.identity.owner_first_name
                or grounded.merchant.identity.name
            )
            trigger_kind = grounded.trigger.kind if grounded.trigger else "update"
            # Use first text-only fact as anchor (prefer non-numeric text)
            hook = next(
                (f.text for f in grounded.facts
                 if f.text and not re.search(r"\d{4,}", f.text or "")),
                grounded.facts[0].text if grounded.facts else None,
            )
            if hook:
                return f"{merchant_name}, {hook}. Want me to share more details?"
            return f"{merchant_name}, I have an update relevant to your business. Shall I share?"
        except Exception:
            return "There's an update relevant to your business. Want me to share the details?"
