from __future__ import annotations

import re

from syntaris.contracts.runtime import (
    ChunkDisposition,
    ConversationConfig,
    EvidenceChunk,
    EvidenceIngestResult,
    EvidenceIngestStatus,
    EvidenceSourceReference,
)
from syntaris.orchestration.text_normalize import clean_display_text

_ERROR_RE = re.compile(r"\b(error|runtimeerror|valueerror|typeerror|exception|traceback|failed|failure|fatal|nem sikerult|hiba)\b", re.IGNORECASE)
_WARNING_RE = re.compile(r"\b(warn(?:ing)?|figyelmeztetes)\b", re.IGNORECASE)
_PATH_RE = re.compile(r"([\w./\\-]+\.(?:py|ts|js|go|java|rs|c|cpp|cs))(?:[:](\d+))?", re.IGNORECASE)


def _chunk_lines(lines: list[str], size: int, max_chunks: int) -> list[list[str]]:
    chunks: list[list[str]] = []
    for start in range(0, len(lines), size):
        if len(chunks) >= max_chunks:
            break
        chunks.append(lines[start : start + size])
    return chunks


def _extract_key_lines(lines: list[str]) -> tuple[list[str], list[str]]:
    key: list[str] = []
    unresolved: list[str] = []
    for line in lines:
        text = line.strip()
        if not text:
            continue
        if _ERROR_RE.search(text) or _WARNING_RE.search(text) or _PATH_RE.search(text):
            key.append(clean_display_text(text))
        elif text.startswith("Caused by") or text.startswith("File ") or "exit code" in text.lower():
            key.append(clean_display_text(text))
    if not key and lines:
        unresolved.append("A forrásban nem találtam egyértelmű error/warning mintát.")
    return key[:12], unresolved


def ingest_text_evidence(message: str, config: ConversationConfig) -> EvidenceIngestResult:
    raw = message.strip()
    lines = [line.rstrip() for line in raw.splitlines()]
    long_text = len(lines) >= 6 or len(raw) >= 350
    if not long_text:
        return EvidenceIngestResult(ingest_status=EvidenceIngestStatus.NO_EVIDENCE_INGESTED)

    chunk_size = max(4, config.evidence_chunk_line_limit)
    max_chunks = max(1, config.evidence_max_chunks)
    chunks = _chunk_lines(lines, chunk_size, max_chunks)

    chunked: list[EvidenceChunk] = []
    kept_lines: list[str] = []
    refs: list[EvidenceSourceReference] = []
    unresolved: list[str] = []
    for idx, chunk_lines in enumerate(chunks, start=1):
        key_lines, unresolved_lines = _extract_key_lines(chunk_lines)
        if key_lines:
            disposition = ChunkDisposition.KEPT_CHUNK
            kept_lines.extend(key_lines)
            refs.extend(
                EvidenceSourceReference(source_label=f"chunk_{idx}", excerpt=line)
                for line in key_lines[:2]
            )
        else:
            disposition = ChunkDisposition.DROPPED_NOISE
        unresolved.extend(unresolved_lines)
        chunked.append(
            EvidenceChunk(
                chunk_id=f"chunk_{idx}",
                raw_chunk="\n".join(chunk_lines),
                disposition=disposition,
                extracted_key_lines=key_lines,
            )
        )

    if len(lines) > chunk_size * max_chunks:
        unresolved.append("A nyers szöveg vége nincs teljesen feldolgozva a chunk-limit miatt.")

    summary: list[str] = []
    errors = [line for line in kept_lines if _ERROR_RE.search(line)]
    warnings = [line for line in kept_lines if _WARNING_RE.search(line)]
    paths = [line for line in kept_lines if _PATH_RE.search(line)]
    if errors:
        summary.append(f"Hiba-jel: {errors[0]}")
    if warnings:
        summary.append(f"Figyelmeztetés: {warnings[0]}")
    if paths:
        summary.append(f"Érintett fájl/modul jel: {paths[0]}")
    if not summary:
        summary.append("A bemenet nagy szövegként be lett emelve, de erős kulcsjel nem látszik.")

    return EvidenceIngestResult(
        ingest_status=EvidenceIngestStatus.RAW_TEXT_EVIDENCE,
        raw_text_evidence=raw,
        chunked_evidence=chunked,
        extracted_key_lines=kept_lines[:20],
        evidence_summary=summary[: max(1, config.evidence_summary_line_limit)],
        evidence_source_references=refs[:8],
        unresolved_evidence=unresolved[:4],
    )
