import re


PII_PATTERNS = [
    re.compile(r"\b\d{10,16}\b"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
]


def redact_text(value: str) -> str:
    redacted = value
    for pattern in PII_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted
