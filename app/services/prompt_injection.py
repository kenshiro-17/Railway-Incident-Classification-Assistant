from __future__ import annotations

import re
from dataclasses import dataclass


INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+the\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"reveal\s+(the\s+)?(prompt|api\s*key|secret|credentials?)", re.IGNORECASE),
    re.compile(r"print\s+the\s+full\s+conversation", re.IGNORECASE),
    re.compile(r"developer\s+message", re.IGNORECASE),
    re.compile(r"tool\s+output", re.IGNORECASE),
    re.compile(r"execute\s+(code|command)", re.IGNORECASE),
]


@dataclass
class GuardResult:
    blocked: bool
    risk_score: int
    sanitized_text: str
    reasons: list[str]


def sanitize_untrusted_text(text: str) -> str:
    # Remove common instruction-like wrappers while preserving incident substance.
    cleaned = text.replace("```", "").replace("<system>", "").replace("</system>", "").replace("\x00", "")
    cleaned = re.sub(r"(?im)^\s*(system|assistant|developer)\s*:\s*", "", cleaned)
    return cleaned.strip()


def detect_prompt_injection(*segments: str) -> GuardResult:
    reasons: list[str] = []
    risk_score = 0
    combined = "\n".join(s for s in segments if s)
    sanitized = sanitize_untrusted_text(combined)

    for pattern in INJECTION_PATTERNS:
        if pattern.search(combined):
            reasons.append(pattern.pattern)
            risk_score += 2

    # Long instruction-heavy payloads are treated as higher risk.
    lowered = combined.lower()
    suspicious_tokens = ["ignore", "override", "prompt", "secret", "instruction", "policy"]
    token_hits = sum(1 for t in suspicious_tokens if t in lowered)
    if token_hits >= 3:
        risk_score += 2

    blocked = risk_score >= 3
    return GuardResult(blocked=blocked, risk_score=risk_score, sanitized_text=sanitized, reasons=reasons)
