from __future__ import annotations

from dataclasses import dataclass
import unicodedata


@dataclass(frozen=True)
class TextNormalizationResult:
    raw_text: str
    canonical_text: str
    display_text: str
    repaired: bool


@dataclass(frozen=True)
class ConsoleTextResult:
    text: str
    degraded: bool
    reason: str | None = None


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


def flatten_generated_summary_text(text: str) -> str:
    cleaned = clean_display_text(text)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if not lines:
        return cleaned

    lines = [line for line in lines if line != "Innen menjünk tovább?"]
    if not lines:
        return ""

    header = lines[0]
    if header.startswith("Röviden itt tartottunk:") or header.startswith("Szál recap:"):
        bullets = [line for line in lines[1:] if line.startswith("• #")]
        if bullets:
            return f"{header} {bullets[-1]}"
        return header
    if len(lines) > 2 and header in {"Lényeg:", "Összevetés:", "Ami biztos:", "Következő lépés:"}:
        bullet = next((line for line in lines[1:] if line.startswith("•")), None)
        return f"{header} {bullet}" if bullet is not None else header
    if len(lines) > 2:
        return " ".join(lines[:2])
    return "\n".join(lines)


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


def _replace_surrogates(text: str) -> tuple[str, bool]:
    if not text:
        return text, False
    changed = False
    chars: list[str] = []
    for ch in text:
        codepoint = ord(ch)
        if 0xD800 <= codepoint <= 0xDFFF:
            chars.append("\uFFFD")
            changed = True
        else:
            chars.append(ch)
    return "".join(chars), changed


def normalize_text(text: str) -> TextNormalizationResult:
    safe_raw, surrogate_replaced = _replace_surrogates(text)
    raw_text = safe_raw
    stripped = safe_raw.strip()
    repaired = _repair_common_mojibake(stripped)
    canonical = unicodedata.normalize("NFC", repaired)
    return TextNormalizationResult(
        raw_text=raw_text,
        canonical_text=canonical,
        display_text=canonical,
        repaired=canonical != stripped or surrogate_replaced,
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


def render_console_text(text: str, encoding: str | None) -> ConsoleTextResult:
    normalized = clean_display_text(text)
    target_encoding = encoding or "utf-8"
    try:
        normalized.encode(target_encoding)
        return ConsoleTextResult(text=normalized, degraded=False)
    except UnicodeEncodeError:
        encoded = normalized.encode(target_encoding, errors="replace")
        safe_text = encoded.decode(target_encoding, errors="replace")
        return ConsoleTextResult(text=safe_text, degraded=True, reason=f"console_encoding_replace:{target_encoding}")
