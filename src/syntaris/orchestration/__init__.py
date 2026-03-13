"""Orchestration package marker.

Intentionally avoids eager re-exports to keep import boundaries acyclic:
- persistence modules may import orchestration submodules (e.g. text normalization)
- orchestration modules may import persistence store

Keeping package import side-effect free prevents import-time cycles between
`syntaris.persistence` and `syntaris.orchestration` during isolated module loading.
"""

__all__: list[str] = []
