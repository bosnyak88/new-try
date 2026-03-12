from __future__ import annotations

from dataclasses import dataclass
import unicodedata


@dataclass(frozen=True)
class TextNormalizationResult:
    raw_text: str
    canonical_text: str
    display_text: str
    repaired: bool


_DIRECT_MOJIBAKE_MAP = {
    "Ã¡": "á",
    "Ã©": "é",
    "Ã­": "í",
    "Ã³": "ó",
    "Ã¶": "ö",
    "Ãº": "ú",
    "Ã¼": "ü",
    "Å": "ő",
    "Å±": "ű",
    "Ã": "Á",
    "Ã": "É",
    "Ã": "Í",
    "Ã": "Ó",
    "Ã": "Ö",
    "Ã": "Ú",
    "Ã": "Ü",
    "Å": "Ő",
    "Å°": "Ű",
    "Å\x91": "ő",
    "Å\xb1": "ű",
    "Ã\xa1": "á",
    "Ã\xa9": "é",
    "Ã\xad": "í",
    "Ã\xb3": "ó",
    "Ã\xb6": "ö",
    "Ã\xba": "ú",
    "Ã\xbc": "ü",
    "ĂĄ": "á",
    "ĂŠ": "é",
    "Ă­": "í",
    "Ăł": "ó",
    "Ă¶": "ö",
    "Ăş": "ú",
    "ĂĽ": "ü",
    "Ă": "Á",
    "Ă‰": "É",
    "Ă": "Í",
    "Ă“": "Ó",
    "Ă–": "Ö",
    "Ăš": "Ú",
    "Ăś": "Ü",
    "ĺ‘": "ő",
    "ĺ’": "ő",
    "Ĺ": "ő",
    "Ĺ±": "ű",
    "\u0102\u00a9": "é",
    "\u0102\u00ad": "í",
    "\u0102\u00b3": "ó",
    "\u0102\u00b6": "ö",
    "\u0102\u00ba": "ú",
    "\u0102\u00bc": "ü",
}

_DEGRADED_MARKERS = ("Ã", "Å", "Ă", "ĺ", "Ĺ", "�")


def contains_degraded_text(text: str) -> bool:
    return any(marker in text for marker in _DEGRADED_MARKERS)


def _repair_common_mojibake(text: str) -> str:
    repaired_direct = text
    for broken, fixed in _DIRECT_MOJIBAKE_MAP.items():
        repaired_direct = repaired_direct.replace(broken, fixed)
    if repaired_direct != text:
        return repaired_direct

    for encoding in ("latin1", "cp1252"):
        try:
            repaired = text.encode(encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if repaired != text:
            return repaired
    return text


def normalize_text(text: str) -> TextNormalizationResult:
    raw_text = text
    stripped = text.strip()
    repaired = _repair_common_mojibake(stripped)
    canonical = unicodedata.normalize("NFC", repaired)
    return TextNormalizationResult(
        raw_text=raw_text,
        canonical_text=canonical,
        display_text=canonical,
        repaired=canonical != stripped,
    )


def clean_display_text(text: str) -> str:
    return normalize_text(text).display_text


def normalize_hungarian_for_match(text: str) -> str:
    normalized = normalize_text(text).canonical_text.lower()
    folded = "".join(ch for ch in unicodedata.normalize("NFKD", normalized) if not unicodedata.combining(ch))
    cleaned = folded.replace("?", " ").replace("!", " ").replace(".", " ")
    return " ".join(cleaned.split())


def preprocess_turn_message(text: str) -> str:
    return normalize_text(text).canonical_text
