import argparse
import json

from syntaris.bootstrap.env import load_repo_env
from syntaris.bootstrap.init_app import build_runtime
from syntaris.contracts.runtime import TalkRequest
from syntaris.orchestration.doctor import run_doctor
from syntaris.orchestration.live_loop import run_live_loop, run_live_loop_interactive
from syntaris.orchestration.talk import init_db, list_threads, session_status, talk_once, trace_last
from syntaris.trace.events import build_boot_trace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="syntaris")
    parser.add_argument("--config", help="Path to TOML config file", default=None)

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Validate foundation runtime wiring")
    sub.add_parser("trace-boot", help="Emit minimal bootstrap trace event")
    sub.add_parser("init-db", help="Initialize persistence directories and schema")

    talk_parser = sub.add_parser("talk", help="Execute talk flows")
    group = talk_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once", help="Run a single-turn interaction")
    group.add_argument("--live", action="store_true", help="Run interactive multi-turn loop")
    group.add_argument("--script", help="Run deterministic multi-turn loop from input file")
    talk_parser.add_argument("--thread", dest="thread_key", default=None, help="Open/create and activate thread key")
    talk_parser.add_argument("--mode", default=None, help="Explicit mode metadata persisted on turn")

    sub.add_parser("trace-last", help="Inspect the latest persisted turn and trace events")
    sub.add_parser("session-status", help="Inspect active session/thread/mode")
    sub.add_parser("thread-list", help="List known threads and active thread")
    return parser


def _print_turn_result(result) -> None:
    print(
        json.dumps(
            {
                "reply": result.turn.assistant_reply,
                "session_id": result.turn.session_id,
                "thread_id": result.turn.thread_id,
                "thread_key": result.turn.thread_key,
                "mode": result.turn.mode,
                "turn_id": result.turn.turn_id,
                "backend": result.turn.reply_backend,
                "degraded": result.turn.degraded,
                "route": {
                    "action": result.route.action.value,
                    "reason": result.route.reason,
                    "thread_key": result.route.thread_key,
                    "created_thread": result.route.created_thread,
                    "pending_resolution": result.route.pending_resolution.value,
                    "execution_message": result.route.execution_message,
                    "transition": {
                        "before_thread_id": result.route.transition.before_thread_id,
                        "before_thread_key": result.route.transition.before_thread_key,
                        "before_previous_thread_id": result.route.transition.before_previous_thread_id,
                        "before_previous_thread_key": result.route.transition.before_previous_thread_key,
                        "after_thread_id": result.route.transition.after_thread_id,
                        "after_thread_key": result.route.transition.after_thread_key,
                        "after_previous_thread_id": result.route.transition.after_previous_thread_id,
                        "after_previous_thread_key": result.route.transition.after_previous_thread_key,
                    }
                    if result.route.transition
                    else None,
                    "pending_proposal": {
                        "proposed_thread_key": result.route.pending_proposal.proposed_thread_key,
                        "current_thread_key": result.route.pending_proposal.current_thread_key,
                        "reason": result.route.pending_proposal.reason,
                        "held_user_message": result.route.pending_proposal.held_user_message,
                    } if result.route.pending_proposal else None,
                },
            },
            indent=2,
        )
    )


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
        if args.once is not None:
            request = TalkRequest(message=args.once, thread_key=args.thread_key, mode=args.mode)
            result = talk_once(runtime, request)
            _print_turn_result(result)
            return 0

        if args.live:
            result = run_live_loop_interactive(runtime)
            for output in result.outputs:
                print(output.message)
            return 0

        if args.script:
            with open(args.script, "r", encoding="utf-8") as f:
                lines = [line.rstrip("\n") for line in f]
            result = run_live_loop(runtime, lines)
            for output in result.outputs:
                print(
                    json.dumps(
                        {
                            "kind": output.kind,
                            "message": output.message,
                            "session_id": output.state.session_id,
                            "thread_id": output.state.thread_id,
                            "thread_key": output.state.thread_key,
                            "mode": output.state.mode,
                            "turn_count": output.state.turn_count,
                            "last_turn_id": output.state.last_turn_id,
                            "turn_id": output.turn_id,
                            "backend": output.backend,
                            "degraded": output.degraded,
                            "pending_route": {
                                "pending_action": output.state.pending_route.pending_action,
                                "pending_thread_key": output.state.pending_route.pending_thread_key,
                                "pending_reason": output.state.pending_route.pending_reason,
                                "pending_original_message": output.state.pending_route.pending_original_message,
                            } if output.state.pending_route else None,
                        },
                        sort_keys=True,
                    )
                )
            return 0

    if args.command == "session-status":
        state = session_status(runtime)
        print(
            json.dumps(
                {
                    "session_id": state.session_id,
                    "thread_id": state.thread_id,
                    "thread_key": state.thread_key,
                    "mode": state.mode,
                    "turn_count": state.turn_count,
                    "last_turn_id": state.last_turn_id,
                    "previous_thread_id": state.previous_thread_id,
                    "previous_thread_key": state.previous_thread_key,
                    "pending_route": {
                        "pending_action": state.pending_route.pending_action,
                        "pending_thread_key": state.pending_route.pending_thread_key,
                        "pending_reason": state.pending_route.pending_reason,
                        "pending_original_message": state.pending_route.pending_original_message,
                        "match_pattern": state.pending_route.match_pattern,
                        "source": state.pending_route.source,
                        "proposed_at": state.pending_route.proposed_at,
                    } if state.pending_route else None,
                },
                indent=2,
            )
        )
        return 0

    if args.command == "thread-list":
        view = list_threads(runtime)
        print(
            json.dumps(
                {
                    "session_id": view.session_id,
                    "active_thread_id": view.active_thread_id,
                    "active_thread_key": view.active_thread_key,
                    "previous_thread_id": view.previous_thread_id,
                    "previous_thread_key": view.previous_thread_key,
                    "threads": [
                        {
                            "thread_id": thread.thread_id,
                            "thread_key": thread.thread_key,
                            "turn_count": thread.turn_count,
                            "last_turn_id": thread.last_turn_id,
                            "is_active": thread.is_active,
                            "is_previous": thread.is_previous,
                        }
                        for thread in view.threads
                    ],
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
                        "thread_id": last.turn.thread_id,
                        "thread_key": last.turn.thread_key,
                        "mode": last.turn.mode,
                        "turn_index": last.turn.turn_index,
                        "user_message": last.turn.user_message,
                        "assistant_reply": last.turn.assistant_reply,
                        "backend": last.turn.reply_backend,
                        "degraded": last.turn.degraded,
                    },
                    "trace_events": [
                        {
                            "trace_id": event.trace_id,
                            "session_id": event.session_id,
                            "thread_id": event.thread_id,
                            "mode": event.mode,
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
