"""Deterministic review-tier policy shared by plan review tools.

The policy decides required evidence. It deliberately does not invoke a model
or invent provider usage data that the current runtime cannot collect.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


CLASSIFIER_VERSION = "review-policy/v1"
REVIEWERS_BY_TIER = {
    "simple": (),
    "standard": ("plan-reviewer",),
    "high-risk": ("plan-reviewer", "principle-auditor"),
}

_PATH_RE = re.compile(r"^\s*-\s*(?:생성|수정|삭제):\s*`?([^`\s]+)", re.MULTILINE)
_PROTECTED_RE = re.compile(r"(?:^|[\s`])(?:AGENTS\.md|\.agents/|\.codex/|\.claude/)", re.IGNORECASE)
_RISK_RE = re.compile(
    r"credential|secret|token|auth|security|privacy|delete|drop table|migration|"
    r"external service|network|mcp|plugin|webhook|deploy|database|데이터 삭제|보안|인증|"
    r"외부 서비스|네트워크|마이그레이션|배포",
    re.IGNORECASE,
)
_USER_INTERACTION_RE = re.compile(
    r"\bcli\b|setup|install|onboarding|wizard|error message|command output|"
    r"사용자 안내|오류 메시지|설치|온보딩|명령 출력|대화형",
    re.IGNORECASE,
)
_USABILITY_RE = re.compile(
    r"(?:usability_review_required:\s*true|>\s*\*\*usability_review_required:\*\*\s*true)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ReviewPolicy:
    tier: str
    review_required: bool
    reviewers: tuple[str, ...]
    model_class: str
    max_tokens: int
    max_seconds: int
    max_attempts: int
    reason: str
    classifier_version: str = CLASSIFIER_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "tier": self.tier,
            "review_required": self.review_required,
            "reviewers": list(self.reviewers),
            "model_class": self.model_class,
            "max_tokens": self.max_tokens,
            "max_seconds": self.max_seconds,
            "max_attempts": self.max_attempts,
            "reason": self.reason,
            "classifier_version": self.classifier_version,
        }


def classify_plan(text: str) -> ReviewPolicy:
    """Classify declared plan scope; user-declared tier cannot lower safety."""
    paths = _PATH_RE.findall(text)
    protected = bool(_PROTECTED_RE.search(text))
    risky = bool(_RISK_RE.search(text))
    user_interaction = bool(_USER_INTERACTION_RE.search(text))
    usability = bool(_USABILITY_RE.search(text))

    if protected or risky or user_interaction:
        reviewers = list(REVIEWERS_BY_TIER["high-risk"])
        if usability or user_interaction:
            reviewers.append("usability-reviewer")
        reasons = []
        if protected:
            reasons.append("protected-path")
        if risky:
            reasons.append("risk-signal")
        if user_interaction:
            reasons.append("user-interaction")
        return ReviewPolicy("high-risk", True, tuple(reviewers), "capable", 8000, 300, 2, ",".join(reasons))

    markdown_only = bool(paths) and all(path.lower().endswith(".md") for path in paths)
    if markdown_only and len(paths) <= 2:
        return ReviewPolicy("simple", False, (), "none", 0, 0, 0, "two-or-fewer-non-sensitive-markdown-files")

    return ReviewPolicy("standard", True, REVIEWERS_BY_TIER["standard"], "economy", 3000, 120, 1, "default-code-or-multi-surface-change")
