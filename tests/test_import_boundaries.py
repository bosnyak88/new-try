import os
import subprocess
import sys
from pathlib import Path


def _run(code: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    repo_root = Path(__file__).resolve().parents[1]
    src_path = str(repo_root / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = src_path if not existing else f"{src_path}{os.pathsep}{existing}"
    return subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_import_persistence_in_isolation_succeeds():
    result = _run("import syntaris.persistence.store")
    assert result.returncode == 0, result.stderr


def test_import_orchestration_after_persistence_succeeds():
    result = _run(
        "import syntaris.persistence.store\n"
        "import syntaris.orchestration.context_pack\n"
    )
    assert result.returncode == 0, result.stderr


def test_import_persistence_after_orchestration_succeeds():
    result = _run(
        "import syntaris.orchestration.context_pack\n"
        "import syntaris.persistence.store\n"
    )
    assert result.returncode == 0, result.stderr
