"""Detect when an agent addresses someone other than the expected caller."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

# Words that look like names in Title Case but are not a person on the call.
NOT_A_PERSON = frozenset(
    """
    Monday Tuesday Wednesday Thursday Friday Saturday Sunday
    January February March April May June July August September October November December
    Hi Hello Hey Thanks Thank Okay Ok Sure Yes No Please Sorry
    Doctor Dr Mister Miss Mrs Ms
    Dental Dentistry Office Clinic Hospital
    Northside Southside Eastside Westside
    I I'll I'm I've
    Let Look Book Cleaning Appointment Insurance
    You Your You're
    """.split()
)

# Prefix is case-insensitive. The captured name is not — (?i) would make
# [A-Z] match "let" in "Okay, let me look".
VOCATIVE_PREFIX = re.compile(
    r"(?i)\b(?:"
    r"hi|hello|hey|thanks|thank you|you(?:'re| are) all set|"
    r"okay|ok|sure|got it|perfect|alright"
    r")\s*,\s+"
)
PROPER_NAME = re.compile(r"^([A-Z][a-z]+)\b")
# Honorifics are not the addressee. "You're all set, Dr. Smith." addresses Smith.
TITLE_PREFIX = re.compile(r"(?:Doctor|Dr|Mister|Miss|Mrs|Ms)\.?\s+")
NAME_THEN_YOU = re.compile(
    r"\b([A-Z][a-z]+),\s+(?:you're|you are|your)\b"
)


@dataclass(frozen=True)
class Finding:
    name: str
    snippet: str
    line: int


def _norm(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def _aliases(expected: str, extra: list[str] | None) -> set[str]:
    allowed = {_norm(expected)}
    for part in expected.replace("-", " ").split():
        if len(part) > 1:
            allowed.add(_norm(part))
    for a in extra or []:
        allowed.add(_norm(a))
        for part in a.replace("-", " ").split():
            if len(part) > 1:
                allowed.add(_norm(part))
    return {x for x in allowed if x}


def _person_after(tail: str) -> tuple[str, int] | None:
    """Return the person named at the start of tail, skipping one honorific."""
    offset = 0
    title = TITLE_PREFIX.match(tail)
    if title:
        offset = title.end()
    name_match = PROPER_NAME.match(tail[offset:])
    if not name_match:
        return None
    name = name_match.group(1)
    if name in NOT_A_PERSON:
        return None
    return name, offset + name_match.end()


def _vocatives(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for match in VOCATIVE_PREFIX.finditer(text):
        person = _person_after(text[match.end() :])
        if person is None:
            continue
        name, consumed = person
        end = match.end() + consumed
        snippet = text[max(0, match.start()) : end].strip()
        found.append((name, snippet))
    for match in NAME_THEN_YOU.finditer(text):
        name = match.group(1)
        if name in NOT_A_PERSON:
            continue
        found.append((name, match.group(0).strip()))
    return found


def check_text(text: str, expected: str, aliases: list[str] | None = None) -> list[Finding]:
    """Return vocative names that are not the expected caller."""
    allowed = _aliases(expected, aliases)
    findings: list[Finding] = []
    for i, line in enumerate(text.splitlines() or [text], start=1):
        for name, snippet in _vocatives(line):
            if _norm(name) not in allowed:
                findings.append(Finding(name=name, snippet=snippet, line=i))
    return findings


def load_transcript(path: str | Path) -> str:
    """Plain text, or JSON with turns[].text / turns[].speaker."""
    raw = Path(path).read_text(encoding="utf-8")
    stripped = raw.lstrip()
    if not stripped.startswith("{") and not stripped.startswith("["):
        return raw
    data = json.loads(raw)
    if isinstance(data, dict) and "turns" in data:
        bits = []
        for turn in data["turns"]:
            speaker = str(turn.get("speaker", "")).lower()
            text = turn.get("text") or turn.get("content") or ""
            if speaker and speaker not in {"agent", "assistant", "bot", "ai"}:
                continue
            bits.append(str(text))
        return "\n".join(bits)
    if isinstance(data, dict) and "text" in data:
        return str(data["text"])
    raise ValueError("unrecognized transcript JSON")
