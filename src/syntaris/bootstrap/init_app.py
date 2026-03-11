from syntaris.config.loader import load_app_config
from syntaris.contracts.runtime import RuntimeContext


def build_runtime(config_path: str | None = None) -> RuntimeContext:
    config = load_app_config(config_path=config_path)
    return RuntimeContext(config=config)
