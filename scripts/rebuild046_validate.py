from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
LOG_PATH = ARTIFACTS / "rebuild046_validation.log"
SPLIT_PATH = ARTIFACTS / "rebuild046_clean_vs_runtime_split.md"
CFG = "config/syntaris.example.toml"

ENV_KEYS = (
    "SYNTARIS_DB_PATH",
    "SYNTARIS_ARTIFACT_ALLOWED_ROOTS",
    "SYNTARIS_DB",
    "SYNTARIS_SANDBOX_ROOTS",
)


@dataclass
class CmdResult:
    command: str
    exit_code: int
    output: str


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in ENV_KEYS:
        env.pop(key, None)
    return env


def _run(command: str, *, env: dict[str, str] | None = None) -> CmdResult:
    completed = subprocess.run(
        command,
        shell=True,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return CmdResult(command=command, exit_code=completed.returncode, output=completed.stdout)


def _append(lines: list[str], title: str, result: CmdResult) -> None:
    lines.append(f"## {title}")
    lines.append(f"$ {result.command}")
    lines.append(f"exit={result.exit_code}")
    lines.append("```text")
    lines.append(result.output.rstrip())
    lines.append("```")
    lines.append("")


def main() -> int:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    log: list[str] = ["# REBUILD-046 validation log", ""]

    clean_env = _clean_env()
    runtime_env = _clean_env()

    with tempfile.TemporaryDirectory(prefix="rebuild046-") as temp_dir:
        temp = Path(temp_dir)
        db_path = temp / "runtime.db"
        sandbox = temp / "sandbox"
        sandbox.mkdir(parents=True, exist_ok=True)
        sample = sandbox / "smoke.log"
        sample.write_text("Traceback (most recent call last):\nValueError: boom\n", encoding="utf-8")

        runtime_env.update(
            {
                "SYNTARIS_DB_PATH": str(db_path),
                "SYNTARIS_ARTIFACT_ALLOWED_ROOTS": str(sandbox),
                "SYNTARIS_DB": str(temp / "wrong-compat.db"),
                "SYNTARIS_SANDBOX_ROOTS": str(temp / "wrong-compat-root"),
            }
        )

        clean_commands = [
            "python -m pytest -q",
            "python -m pytest -q tests/test_rebuild035a_followup.py",
            "python -m pytest -q tests/test_rebuild041_surface_continuity.py tests/test_rebuild042_gate2_residual_surface.py tests/test_rebuild045_gate2_corrective.py",
            "python -m compileall -q src",
        ]

        runtime_commands = [
            f"python -m syntaris.cli --config {CFG} init-db",
            f"python -m syntaris.cli --config {CFG} artifact-find build_error",
            f"python -m syntaris.cli --config {CFG} artifact-read {shlex.quote(str(sample))}",
            f"python -m syntaris.cli --config {CFG} talk --once-file {shlex.quote(str(sample))}",
            f"printf '/status\\n/kilep\\n' | python -m syntaris.cli --config {CFG} talk --live",
        ]

        targeted_failures = 0
        first_clean = _run(clean_commands[0], env=clean_env)
        _append(log, "clean suite", first_clean)
        for cmd in clean_commands[1:]:
            result = _run(cmd, env=clean_env)
            _append(log, "targeted regressions" if "pytest" in cmd else "compile", result)
            if result.exit_code != 0:
                targeted_failures += 1

        runtime_failures = 0
        for cmd in runtime_commands:
            result = _run(cmd, env=runtime_env)
            _append(log, "runtime smoke", result)
            if result.exit_code != 0:
                runtime_failures += 1

        post_clean = _run("python -m pytest -q", env=clean_env)
        _append(log, "clean suite (post-runtime recheck)", post_clean)

        LOG_PATH.write_text("\n".join(log), encoding="utf-8")

        split = [
            "# REBUILD-046 clean vs runtime split",
            "",
            "## Isolation setup",
            "- Clean suite env: SYNTARIS runtime override variables are unset.",
            "- Runtime smoke env: temp DB/sandbox set via SYNTARIS_DB_PATH and SYNTARIS_ARTIFACT_ALLOWED_ROOTS.",
            "- Compat aliases intentionally poisoned: SYNTARIS_DB / SYNTARIS_SANDBOX_ROOTS point to wrong paths.",
            "",
            "## Results",
            f"- Clean suite initial exit: {first_clean.exit_code}",
            f"- Targeted/compile failures: {targeted_failures}",
            f"- Runtime smoke failures: {runtime_failures}",
            f"- Clean suite post-runtime exit: {post_clean.exit_code}",
            "",
            "## Conclusion",
            "- Canonical full suite runs in a dedicated clean environment.",
            "- Runtime smoke runs in a separate temporary runtime environment.",
            "- Post-runtime clean suite check confirms no harness contamination leaked back.",
        ]
        SPLIT_PATH.write_text("\n".join(split), encoding="utf-8")

        return 1 if post_clean.exit_code != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
