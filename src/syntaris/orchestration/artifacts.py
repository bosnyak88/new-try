from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from syntaris.contracts.runtime import ArtifactSourceKind

_TEXT_EXTENSIONS = {
    ".txt", ".md", ".log", ".json", ".toml", ".yaml", ".yml", ".ini", ".csv",
    ".py", ".ts", ".js", ".go", ".java", ".rs", ".c", ".cpp", ".h", ".hpp", ".env", ".conf",
}


@dataclass(frozen=True)
class ArtifactReadResult:
    ok: bool
    path: str
    content: str | None = None
    media_type: str | None = None
    size_bytes: int | None = None
    digest: str | None = None
    reason: str | None = None


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_artifact_id(source_kind: ArtifactSourceKind, source_origin: str | None, digest: str | None) -> str:
    seed = f"{source_kind.value}|{source_origin or ''}|{digest or ''}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _resolve_allowed_roots(roots: tuple[str, ...]) -> list[Path]:
    return [Path(root).expanduser().resolve() for root in roots if root.strip()]


def is_within_allowed_roots(path: Path, roots: tuple[str, ...]) -> bool:
    resolved = path.expanduser().resolve()
    for root in _resolve_allowed_roots(roots):
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def read_local_text_file(path_text: str, *, allowed_roots: tuple[str, ...], max_read_bytes: int) -> ArtifactReadResult:
    path = Path(path_text).expanduser().resolve()
    if not path.exists() or not path.is_file():
        return ArtifactReadResult(ok=False, path=str(path), reason="file_not_found")
    if not is_within_allowed_roots(path, allowed_roots):
        return ArtifactReadResult(ok=False, path=str(path), reason="outside_allowed_roots")
    if path.suffix.lower() not in _TEXT_EXTENSIONS:
        return ArtifactReadResult(ok=False, path=str(path), reason="unsupported_file_type")

    size = path.stat().st_size
    if size > max_read_bytes:
        return ArtifactReadResult(ok=False, path=str(path), reason="file_too_large")

    try:
        content = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return ArtifactReadResult(ok=False, path=str(path), reason="binary_or_non_utf8")
    digest = digest_text(content)
    return ArtifactReadResult(
        ok=True,
        path=str(path),
        content=content,
        media_type="text/plain",
        size_bytes=size,
        digest=digest,
    )


def find_files(pattern: str, *, allowed_roots: tuple[str, ...], limit: int = 20) -> list[str]:
    needle = pattern.lower().strip()
    results: list[str] = []
    for root in _resolve_allowed_roots(allowed_roots):
        if not root.exists() or not root.is_dir():
            continue
        for candidate in root.rglob("*"):
            if not candidate.is_file():
                continue
            rel = str(candidate).lower()
            if needle in rel:
                results.append(str(candidate.resolve()))
                if len(results) >= limit:
                    return results
    return results
