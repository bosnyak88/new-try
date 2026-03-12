from pathlib import Path

import tomli


def test_pyproject_build_system_declares_editable_prerequisites():
    data = tomli.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    build = data["build-system"]
    requires = build["requires"]
    assert any(req.startswith("setuptools") for req in requires)
    assert "wheel" in requires
    assert build["build-backend"] == "setuptools.build_meta"
