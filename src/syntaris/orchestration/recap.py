from __future__ import annotations

import re

from syntaris.contracts.runtime import (
    ContextSource,
    RecapQueryAction,
    RecapQueryMatch,
    RecapRequest,
    RecapTarget,
    RuntimeContext,
    ThreadContextPack,
    ThreadContextRequest,
    ThreadRecapLine,
    ThreadRecapView,
)
from syntaris.orchestration.context_pack import build_thread_context_view
from syntaris.orchestration.text_normalize import clean_display_text, normalize_text

_CURRENT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recap_current_hol_tartunk", re.compile(r"^hol\s+tartunk\??$", re.IGNORECASE)),
    ("recap_current_hol_tartunk_most", re.compile(r"^hol\s+tartunk\s+most\??$", re.IGNORECASE)),
    ("recap_current_mutasd", re.compile(r"^mutasd\s+a\s+mostani\s+szálat$", re.IGNORECASE)),
    ("recap_current_foglald", re.compile(r"^foglald\s+össze\s+ezt\s+a\s+szálat$", re.IGNORECASE)),
)

_PREVIOUS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recap_previous_mutasd", re.compile(r"^mutasd\s+az\s+előző\s+szálat$", re.IGNORECASE)),
    ("recap_previous_foglald", re.compile(r"^foglald\s+össze\s+az\s+előző\s+szálat$", re.IGNORECASE)),
    ("recap_previous_hol_tartunk", re.compile(r"^hol\s+tartunk\s+az\s+előző\s+szálon\??$", re.IGNORECASE)),
)

_NAMED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recap_named_mutasd", re.compile(r"^mutasd\s+a\s+([a-z0-9_-]+)\s+szálat$", re.IGNORECASE)),
    ("recap_named_foglald", re.compile(r"^foglald\s+össze\s+a\s+([a-z0-9_-]+)\s+szálat$", re.IGNORECASE)),
    ("recap_named_hol_tartunk", re.compile(r"^hol\s+tartunk\s+a\s+([a-z0-9_-]+)\s+szálon\??$", re.IGNORECASE)),
)


def match_recap_query(message: str) -> RecapQueryMatch:
    text = normalize_text(message).canonical_text.strip()
    for pattern_name, pattern in _CURRENT_PATTERNS:
        if pattern.match(text):
            return RecapQueryMatch(action=RecapQueryAction.CURRENT, pattern_name=pattern_name)

    for pattern_name, pattern in _PREVIOUS_PATTERNS:
        if pattern.match(text):
            return RecapQueryMatch(action=RecapQueryAction.PREVIOUS, pattern_name=pattern_name)

    for pattern_name, pattern in _NAMED_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        return RecapQueryMatch(
            action=RecapQueryAction.NAMED,
            thread_key=match.group(1).strip().lower(),
            pattern_name=pattern_name,
        )

    return RecapQueryMatch(action=RecapQueryAction.NONE)


def _build_recap_text(pack: ThreadContextPack, lines: list[ThreadRecapLine]) -> str:
    header = (
        f"Szál recap: {pack.thread_key} (session={pack.session_id}, thread_id={pack.thread_id}, "
        f"turn_count={pack.turn_count}, last_turn_id={pack.last_turn_id})"
    )
    if not lines:
        return f"{header}\nNincs még eltárolt turn ezen a szálon."

    body = [
        f"- #{line.turn_index} user={line.user_message} | assistant={line.assistant_reply}"
        for line in lines
    ]
    return "\n".join([header, *body])


def build_thread_recap_view(context: RuntimeContext, request: RecapRequest) -> ThreadRecapView:
    if request.target == RecapTarget.CURRENT:
        context_request = ThreadContextRequest(source=ContextSource.CURRENT.value, limit=request.limit)
    elif request.target == RecapTarget.PREVIOUS:
        context_request = ThreadContextRequest(source=ContextSource.PREVIOUS.value, limit=request.limit)
    else:
        context_request = ThreadContextRequest(
            source=ContextSource.NAMED.value,
            thread_key=request.thread_key,
            limit=request.limit,
        )

    context_view = build_thread_context_view(context, context_request)
    if not context_view.found or context_view.pack is None:
        return ThreadRecapView(
            request=request,
            found=False,
            session_id=None,
            thread_id=None,
            thread_key=request.thread_key,
            turn_count=None,
            last_turn_id=None,
            mode=None,
            previous_thread_id=None,
            previous_thread_key=None,
            recap_lines=[],
            recap_text="Thread recap not found.",
        )

    pack = context_view.pack
    lines = [
        ThreadRecapLine(
            turn_id=turn.turn_id,
            turn_index=turn.turn_index,
            user_message=clean_display_text(turn.user_message),
            assistant_reply=clean_display_text(turn.assistant_reply),
        )
        for turn in pack.recent_turns
    ]
    return ThreadRecapView(
        request=request,
        found=True,
        session_id=pack.session_id,
        thread_id=pack.thread_id,
        thread_key=pack.thread_key,
        turn_count=pack.turn_count,
        last_turn_id=pack.last_turn_id,
        mode=pack.mode,
        previous_thread_id=pack.previous_thread_id,
        previous_thread_key=pack.previous_thread_key,
        recap_lines=lines,
        recap_text=_build_recap_text(pack, lines),
    )
