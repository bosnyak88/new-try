from pathlib import Path


_TOML_BASIC_ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
}


def toml_basic_string(value: str) -> str:
    """Return a TOML basic string literal with all required escaping applied."""
    escaped = "".join(_TOML_BASIC_ESCAPES.get(char, char) for char in value)
    return f'"{escaped}"'


def toml_path_string(path: str | Path) -> str:
    """Return a TOML-safe string literal for filesystem paths (including Windows paths)."""
    return toml_basic_string(str(path))
