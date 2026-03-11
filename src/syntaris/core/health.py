from pathlib import Path


def required_path_present(path_value: str) -> bool:
    if not path_value:
        return False
    return Path(path_value).exists()
