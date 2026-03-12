from __future__ import annotations

import unicodedata


def _repair_common_mojibake(text: str) -> str:
    direct_map = {
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
    }
    repaired_direct = text
    for broken, fixed in direct_map.items():
        repaired_direct = repaired_direct.replace(broken, fixed)
    if repaired_direct != text:
        return repaired_direct

    # Best-effort repair when UTF-8 bytes were decoded as latin-1/cp1252.
    # If conversion is not applicable, keep the original text.
    for encoding in ("latin1", "cp1252"):
        try:
            repaired = text.encode(encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if repaired != text:
            return repaired
    return text


def normalize_hungarian_for_match(text: str) -> str:
    repaired = _repair_common_mojibake(text.strip().lower())
    folded = "".join(
        ch for ch in unicodedata.normalize("NFKD", repaired) if not unicodedata.combining(ch)
    )
    cleaned = folded.replace("?", " ").replace("!", " ").replace(".", " ")
    return " ".join(cleaned.split())
