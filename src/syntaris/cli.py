import argparse
import json
import sys

from syntaris.bootstrap.env import load_repo_env
from syntaris.bootstrap.init_app import build_runtime
from syntaris.contracts.runtime import TalkRequest
from syntaris.orchestration.doctor import run_doctor
from syntaris.orchestration.live_loop import run_live_loop, run_live_loop_interactive
from syntaris.orchestration.text_normalize import clean_display_text, render_console_text
from syntaris.orchestration.talk import init_db, list_threads, session_status, talk_once, thread_focus_current, thread_focus_named, thread_focus_previous, thread_recap_current, thread_recap_named, thread_recap_previous, thread_snapshot_current, thread_snapshot_named, thread_snapshot_previous, thread_view_current, thread_view_named, thread_view_previous, trace_last
from syntaris.persistence import PersistenceStore
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
    group.add_argument("--once-file", help="Run a single-turn interaction by loading message text from file")
    group.add_argument("--once-stdin", action="store_true", help="Run a single-turn interaction by reading full message text from stdin")
    group.add_argument("--live", action="store_true", help="Run interactive multi-turn loop")
    group.add_argument("--script", help="Run deterministic multi-turn loop from input file")
    talk_parser.add_argument("--thread", dest="thread_key", default=None, help="Open/create and activate thread key")
    talk_parser.add_argument("--mode", default=None, help="Explicit mode metadata persisted on turn")

    sub.add_parser("trace-last", help="Inspect the latest persisted turn and trace events")
    sub.add_parser("session-status", help="Inspect active session/thread/mode")
    sub.add_parser("thread-list", help="List known threads and active thread")
    thread_view_parser = sub.add_parser("thread-view", help="Inspect deterministic thread context pack")
    scope = thread_view_parser.add_mutually_exclusive_group(required=False)
    scope.add_argument("--current", action="store_true", help="View active thread context")
    scope.add_argument("--previous", action="store_true", help="View previous thread context")
    thread_view_parser.add_argument("thread_key", nargs="?", default=None, help="Named thread key")
    thread_view_parser.add_argument("--limit", type=int, default=None, help="Override context turn window")
    thread_recap_parser = sub.add_parser("thread-recap", help="Inspect deterministic thread recap view")
    recap_scope = thread_recap_parser.add_mutually_exclusive_group(required=False)
    recap_scope.add_argument("--current", action="store_true", help="Recap active thread")
    recap_scope.add_argument("--previous", action="store_true", help="Recap previous thread")
    thread_recap_parser.add_argument("thread_key", nargs="?", default=None, help="Named thread key")
    thread_recap_parser.add_argument("--limit", type=int, default=None, help="Override recap turn window")
    thread_focus_parser = sub.add_parser("thread-focus", help="Inspect deterministic thread active-focus pack")
    focus_scope = thread_focus_parser.add_mutually_exclusive_group(required=False)
    focus_scope.add_argument("--current", action="store_true", help="Focus for active thread")
    focus_scope.add_argument("--previous", action="store_true", help="Focus for previous thread")
    thread_focus_parser.add_argument("thread_key", nargs="?", default=None, help="Named thread key")
    thread_focus_parser.add_argument("--limit", type=int, default=None, help="Override focus turn window")
    thread_focus_parser.add_argument("--refresh", action="store_true", help="Rebuild and persist focus before returning it")
    thread_snapshot_parser = sub.add_parser("thread-snapshot", help="Inspect deterministic persisted thread snapshot handoff pack")
    snapshot_scope = thread_snapshot_parser.add_mutually_exclusive_group(required=False)
    snapshot_scope.add_argument("--current", action="store_true", help="Snapshot active thread")
    snapshot_scope.add_argument("--previous", action="store_true", help="Snapshot previous thread")
    thread_snapshot_parser.add_argument("thread_key", nargs="?", default=None, help="Named thread key")
    thread_snapshot_parser.add_argument("--limit", type=int, default=None, help="Override snapshot source window")
    thread_snapshot_parser.add_argument("--refresh", action="store_true", help="Rebuild and persist snapshot before returning it")
    return parser


def _print_turn_result(result) -> None:
    print(
        json.dumps(
            {
                "kind": result.output_kind,
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


def _thread_context_payload(view) -> dict[str, object]:
    if not view.found or view.pack is None:
        return {"request": {"source": view.request.source, "thread_key": view.request.thread_key, "limit": view.request.limit}, "found": False, "pack": None}
    return {
        "request": {
            "source": view.request.source,
            "thread_key": view.request.thread_key,
            "limit": view.request.limit,
        },
        "found": True,
        "pack": {
            "session_id": view.pack.session_id,
            "thread_id": view.pack.thread_id,
            "thread_key": view.pack.thread_key,
            "mode": view.pack.mode,
            "turn_count": view.pack.turn_count,
            "last_turn_id": view.pack.last_turn_id,
            "previous_thread_id": view.pack.previous_thread_id,
            "previous_thread_key": view.pack.previous_thread_key,
            "recent_turns": [
                {
                    "turn_id": turn.turn_id,
                    "turn_index": turn.turn_index,
                    "user_message": turn.user_message,
                    "assistant_reply": turn.assistant_reply,
                    "backend": turn.backend,
                    "degraded": turn.degraded,
                }
                for turn in view.pack.recent_turns
            ],
        },
    }



def _thread_snapshot_payload(view) -> dict[str, object]:
    if not view.found or view.snapshot is None:
        return {
            "request": {
                "target": view.request.target.value,
                "thread_key": view.request.thread_key,
                "limit": view.request.limit,
                "refresh": view.request.refresh,
                "source": view.request.source,
            },
            "found": False,
            "loaded_from_persistence": view.loaded_from_persistence,
            "snapshot": None,
        }
    snapshot = view.snapshot
    return {
        "request": {
            "target": view.request.target.value,
            "thread_key": view.request.thread_key,
            "limit": view.request.limit,
            "refresh": view.request.refresh,
            "source": view.request.source,
        },
        "found": True,
        "loaded_from_persistence": view.loaded_from_persistence,
        "snapshot": {
            "session_id": snapshot.session_id,
            "thread_id": snapshot.thread_id,
            "thread_key": snapshot.thread_key,
            "mode": snapshot.mode,
            "turn_count": snapshot.turn_count,
            "last_turn_id": snapshot.last_turn_id,
            "snapshot_built_at": snapshot.snapshot_built_at.isoformat(),
            "source_metadata": {
                "source_turn_count": snapshot.source_metadata.source_turn_count,
                "included_turn_count": snapshot.source_metadata.included_turn_count,
                "filtered_recap_turn_count": snapshot.source_metadata.filtered_recap_turn_count,
                "filtered_pending_turn_count": snapshot.source_metadata.filtered_pending_turn_count,
                "filtered_control_turn_count": snapshot.source_metadata.filtered_control_turn_count,
            },
            "previous_thread_id": snapshot.previous_thread_id,
            "previous_thread_key": snapshot.previous_thread_key,
            "snapshot_text": snapshot.snapshot_text,
            "workframe_state": {
                "workframe": snapshot.workframe_state.workframe.value,
                "objective_status": snapshot.workframe_state.objective_status.value,
                "objective_text": snapshot.workframe_state.objective_text,
                "blocker_status": snapshot.workframe_state.blocker_status.value,
                "blocker_text": snapshot.workframe_state.blocker_text,
                "next_step_status": snapshot.workframe_state.next_step_status.value,
                "next_step_lines": snapshot.workframe_state.next_step_lines,
            } if snapshot.workframe_state else None,
            "thread_weave_state": {
                "relation": snapshot.thread_weave_state.relation.value,
                "main_thread_key": snapshot.thread_weave_state.main_thread_key,
                "related_thread_key": snapshot.thread_weave_state.related_thread_key,
                "detour_thread_key": snapshot.thread_weave_state.detour_thread_key,
                "conclusion_status": snapshot.thread_weave_state.conclusion_status.value,
                "conclusion_text": snapshot.thread_weave_state.conclusion_text,
                "applicability_status": snapshot.thread_weave_state.applicability_status.value,
                "applicability_reason": snapshot.thread_weave_state.applicability_reason,
            } if snapshot.thread_weave_state else None,
            "snapshot_lines": [
                {
                    "turn_id": line.turn_id,
                    "turn_index": line.turn_index,
                    "user_message": line.user_message,
                    "assistant_reply": line.assistant_reply,
                }
                for line in snapshot.snapshot_lines
            ],
        },
    }

def _thread_recap_payload(view) -> dict[str, object]:
    payload = {
        "request": {
            "target": view.request.target.value,
            "thread_key": view.request.thread_key,
            "limit": view.request.limit,
        },
        "found": view.found,
        "session_id": view.session_id,
        "thread_id": view.thread_id,
        "thread_key": view.thread_key,
        "turn_count": view.turn_count,
        "last_turn_id": view.last_turn_id,
        "mode": view.mode,
        "previous_thread_id": view.previous_thread_id,
        "previous_thread_key": view.previous_thread_key,
        "recap_text": view.recap_text,
        "recap_lines": [
            {
                "turn_id": line.turn_id,
                "turn_index": line.turn_index,
                "user_message": line.user_message,
                "assistant_reply": line.assistant_reply,
            }
            for line in view.recap_lines
        ],
    }
    return payload


def _emit_console_text(text: str) -> tuple[bool, str | None]:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    result = render_console_text(text, encoding=encoding)
    payload = result.text
    try:
        print(payload)
    except UnicodeEncodeError:
        fallback = render_console_text(payload, encoding="ascii")
        payload = fallback.text
        buffer = getattr(sys.stdout, "buffer", None)
        if buffer is not None:
            buffer.write((payload + "\n").encode("ascii", errors="replace"))
            buffer.flush()
        else:
            print(payload)
        reason = fallback.reason or "console_encoding_replace:ascii"
        return True, reason

    return result.degraded, result.reason


def _record_live_output_degraded(runtime, output, reason: str | None) -> None:
    store = PersistenceStore(runtime.config.paths.db_path)
    store.initialize(data_dir=runtime.config.paths.data_dir)
    store.create_trace_events(
        session_id=output.state.session_id,
        thread_id=output.state.thread_id,
        turn_id=output.turn_id or 0,
        mode=output.state.mode,
        backend="loop",
        degraded=True,
        events=[
            {
                "event_name": "live_output_sanitized",
                "payload": {
                    "reason": clean_display_text(reason or "console_encoding_replace"),
                    "kind": output.kind,
                    "turn_id": output.turn_id,
                    "backend": output.backend,
                },
            }
        ],
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

        if args.once_file is not None:
            with open(args.once_file, "r", encoding="utf-8-sig") as f:
                message = f.read()
            request = TalkRequest(message=message, thread_key=args.thread_key, mode=args.mode)
            result = talk_once(runtime, request)
            _print_turn_result(result)
            return 0

        if args.once_stdin:
            message = sys.stdin.read()
            request = TalkRequest(message=message, thread_key=args.thread_key, mode=args.mode)
            result = talk_once(runtime, request)
            _print_turn_result(result)
            return 0

        if args.live:
            result = run_live_loop_interactive(runtime)
            for output in result.outputs:
                degraded, reason = _emit_console_text(output.message)
                if degraded:
                    _record_live_output_degraded(runtime, output, reason)
            return 0

        if args.script:
            with open(args.script, "r", encoding="utf-8-sig") as f:
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

    if args.command == "thread-view":
        if args.current:
            view = thread_view_current(runtime, limit=args.limit)
        elif args.previous:
            view = thread_view_previous(runtime, limit=args.limit)
        elif args.thread_key:
            view = thread_view_named(runtime, thread_key=args.thread_key, limit=args.limit)
        else:
            view = thread_view_current(runtime, limit=args.limit)
        print(json.dumps(_thread_context_payload(view), indent=2))
        return 0

    if args.command == "thread-focus":
        if args.current:
            view = thread_focus_current(runtime, limit=args.limit, refresh=args.refresh)
        elif args.previous:
            view = thread_focus_previous(runtime, limit=args.limit, refresh=args.refresh)
        elif args.thread_key:
            view = thread_focus_named(runtime, thread_key=args.thread_key, limit=args.limit, refresh=args.refresh)
        else:
            view = thread_focus_current(runtime, limit=args.limit, refresh=args.refresh)
        print(json.dumps(_thread_focus_payload(view), indent=2))
        return 0

    if args.command == "thread-snapshot":
        if args.current:
            view = thread_snapshot_current(runtime, limit=args.limit, refresh=args.refresh)
        elif args.previous:
            view = thread_snapshot_previous(runtime, limit=args.limit, refresh=args.refresh)
        elif args.thread_key:
            view = thread_snapshot_named(runtime, thread_key=args.thread_key, limit=args.limit, refresh=args.refresh)
        else:
            view = thread_snapshot_current(runtime, limit=args.limit, refresh=args.refresh)
        print(json.dumps(_thread_snapshot_payload(view), indent=2))
        return 0

    if args.command == "thread-recap":
        if args.current:
            view = thread_recap_current(runtime, limit=args.limit)
        elif args.previous:
            view = thread_recap_previous(runtime, limit=args.limit)
        elif args.thread_key:
            view = thread_recap_named(runtime, thread_key=args.thread_key, limit=args.limit)
        else:
            view = thread_recap_current(runtime, limit=args.limit)
        print(json.dumps(_thread_recap_payload(view), indent=2))
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


def _thread_focus_payload(view):
    payload = {
        "request": {
            "target": view.request.target.value,
            "thread_key": view.request.thread_key,
            "limit": view.request.limit,
            "refresh": view.request.refresh,
            "source": view.request.source,
        },
        "found": view.found,
        "loaded_from_persistence": view.loaded_from_persistence,
        "focus": None,
    }
    if view.focus is None:
        return payload
    payload["focus"] = {
        "session_id": view.focus.session_id,
        "thread_id": view.focus.thread_id,
        "thread_key": view.focus.thread_key,
        "last_turn_id": view.focus.last_turn_id,
        "focus_updated_at": view.focus.focus_updated_at.isoformat(),
        "focus_source_turn_count": view.focus.focus_source_turn_count,
        "source_metadata": {
            "source_turn_count": view.focus.source_metadata.source_turn_count,
            "included_turn_count": view.focus.source_metadata.included_turn_count,
            "filtered_recap_turn_count": view.focus.source_metadata.filtered_recap_turn_count,
            "filtered_pending_turn_count": view.focus.source_metadata.filtered_pending_turn_count,
            "filtered_control_turn_count": view.focus.source_metadata.filtered_control_turn_count,
        },
        "focus_lines": [{"key": line.key, "text": line.text} for line in view.focus.focus_lines],
        "workframe_state": {
            "workframe": view.focus.workframe_state.workframe.value,
            "objective_status": view.focus.workframe_state.objective_status.value,
            "objective_text": view.focus.workframe_state.objective_text,
            "blocker_status": view.focus.workframe_state.blocker_status.value,
            "blocker_text": view.focus.workframe_state.blocker_text,
            "next_step_status": view.focus.workframe_state.next_step_status.value,
            "next_step_lines": view.focus.workframe_state.next_step_lines,
        } if view.focus.workframe_state else None,
        "thread_weave_state": {
            "relation": view.focus.thread_weave_state.relation.value,
            "main_thread_key": view.focus.thread_weave_state.main_thread_key,
            "related_thread_key": view.focus.thread_weave_state.related_thread_key,
            "detour_thread_key": view.focus.thread_weave_state.detour_thread_key,
            "conclusion_status": view.focus.thread_weave_state.conclusion_status.value,
            "conclusion_text": view.focus.thread_weave_state.conclusion_text,
            "applicability_status": view.focus.thread_weave_state.applicability_status.value,
            "applicability_reason": view.focus.thread_weave_state.applicability_reason,
        } if view.focus.thread_weave_state else None,
    }
    return payload



if __name__ == "__main__":
    raise SystemExit(main())
