import argparse
import json

from syntaris.bootstrap.env import load_repo_env
from syntaris.bootstrap.init_app import build_runtime
from syntaris.orchestration.doctor import run_doctor
from syntaris.orchestration.talk import init_db, talk_once, trace_last
from syntaris.trace.events import build_boot_trace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="syntaris")
    parser.add_argument("--config", help="Path to TOML config file", default=None)

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Validate foundation runtime wiring")
    sub.add_parser("trace-boot", help="Emit minimal bootstrap trace event")
    sub.add_parser("init-db", help="Initialize persistence directories and schema")

    talk_parser = sub.add_parser("talk", help="Execute talk flows")
    talk_parser.add_argument("--once", required=True, help="Run a single-turn interaction")

    sub.add_parser("trace-last", help="Inspect the latest persisted turn and trace events")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    load_repo_env()
    runtime = build_runtime(config_path=args.config)

    if args.command == "doctor":
        result = run_doctor(runtime)
        print(json.dumps({"healthy": result.healthy, "checks": result.checks}, indent=2))
        return 0 if result.healthy else 1

    if args.command == "trace-boot":
        print(json.dumps(build_boot_trace(runtime), indent=2))
        return 0

    if args.command == "init-db":
        print(json.dumps(init_db(runtime), indent=2))
        return 0

    if args.command == "talk":
        result = talk_once(runtime, args.once)
        print(
            json.dumps(
                {
                    "reply": result.turn.assistant_reply,
                    "session_id": result.turn.session_id,
                    "turn_id": result.turn.turn_id,
                    "backend": result.turn.reply_backend,
                    "degraded": result.turn.degraded,
                },
                indent=2,
            )
        )
        return 0

    if args.command == "trace-last":
        last = trace_last(runtime)
        if last.turn is None:
            print(json.dumps({"turn": None, "trace_events": []}, indent=2))
            return 0
        print(
            json.dumps(
                {
                    "turn": {
                        "turn_id": last.turn.turn_id,
                        "session_id": last.turn.session_id,
                        "user_message": last.turn.user_message,
                        "assistant_reply": last.turn.assistant_reply,
                        "backend": last.turn.reply_backend,
                        "degraded": last.turn.degraded,
                    },
                    "trace_events": [
                        {
                            "trace_id": event.trace_id,
                            "event_name": event.event_name,
                            "backend": event.backend,
                            "degraded": event.degraded,
                            "payload": event.payload,
                        }
                        for event in last.trace_events
                    ],
                },
                indent=2,
            )
        )
        return 0

    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
