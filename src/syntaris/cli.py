import argparse
import json

from syntaris.bootstrap.init_app import build_runtime
from syntaris.orchestration.doctor import run_doctor
from syntaris.trace.events import build_boot_trace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="syntaris")
    parser.add_argument("--config", help="Path to TOML config file", default=None)

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Validate foundation runtime wiring")
    sub.add_parser("trace-boot", help="Emit minimal bootstrap trace event")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    runtime = build_runtime(config_path=args.config)

    if args.command == "doctor":
        result = run_doctor(runtime)
        print(json.dumps({"healthy": result.healthy, "checks": result.checks}, indent=2))
        return 0 if result.healthy else 1

    if args.command == "trace-boot":
        print(json.dumps(build_boot_trace(runtime), indent=2))
        return 0

    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
