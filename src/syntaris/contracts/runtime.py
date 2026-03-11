from dataclasses import dataclass, field


@dataclass(frozen=True)
class LLMConfig:
    server_bin_path: str
    model_path: str
    host: str = "127.0.0.1"
    port: int = 8080


@dataclass(frozen=True)
class AppConfig:
    name: str
    environment: str
    llm: LLMConfig
    trace_enabled: bool = True
    trace_level: str = "info"


@dataclass(frozen=True)
class RuntimeContext:
    config: AppConfig


@dataclass(frozen=True)
class DoctorResult:
    checks: dict[str, bool] = field(default_factory=dict)

    @property
    def healthy(self) -> bool:
        return all(self.checks.values())
