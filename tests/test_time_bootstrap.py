from __future__ import annotations

from pathlib import Path

import tomli

from syntaris.contracts.runtime import SystemClock


def test_pyproject_declares_tzdata_for_windows() -> None:
    pyproject = tomli.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    deps = pyproject["project"]["dependencies"]
    assert any("tzdata" in dep and "Windows" in dep for dep in deps)


def test_system_clock_uses_builtin_utc_tzinfo() -> None:
    now = SystemClock().now()
    assert now.tzinfo is not None
    assert str(now.tzinfo).upper() == "UTC"
