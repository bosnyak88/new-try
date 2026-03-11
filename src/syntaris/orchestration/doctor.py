from syntaris.contracts.runtime import DoctorResult, RuntimeContext
from syntaris.core.health import required_path_present


def run_doctor(context: RuntimeContext) -> DoctorResult:
    checks = {
        "llm_server_bin_exists": required_path_present(context.config.llm.server_bin_path),
        "llm_model_exists": required_path_present(context.config.llm.model_path),
        "llm_port_valid": context.config.llm.port > 0,
    }
    return DoctorResult(checks=checks)
