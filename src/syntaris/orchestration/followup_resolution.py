from __future__ import annotations

from syntaris.contracts.runtime import FollowupResolution, ThreadFocusPack

_PHRASES = (
    "erről beszéljünk tovább",
    "és abból mi következik",
    "folytassuk innen",
    "erről",
    "arról",
    "ebből",
    "abból",
    "ezt",
    "azt",
    "és akkor",
    "térjünk vissza rá",
    "a másikra",
)


def resolve_followup_reference(message: str, focus: ThreadFocusPack | None) -> FollowupResolution:
    normalized = message.strip().lower().rstrip("?!.")
    phrase = next((candidate for candidate in _PHRASES if normalized == candidate or normalized.startswith(candidate)), None)
    if phrase is None:
        return FollowupResolution(detected=False, resolved=False, ambiguous=False)

    if focus is None or not focus.focus_lines:
        return FollowupResolution(
            detected=True,
            resolved=False,
            ambiguous=True,
            phrase=phrase,
            clarification_message="Pontosan mire utalsz? Írd le egy rövid főnévvel vagy szálnévvel.",
        )

    topic = next((line.text for line in focus.focus_lines if line.key == "active_topic_line"), None)
    if not topic:
        return FollowupResolution(
            detected=True,
            resolved=False,
            ambiguous=True,
            phrase=phrase,
            clarification_message="Pontosan mire utalsz? Írd le röviden, mire térjünk vissza.",
        )

    return FollowupResolution(
        detected=True,
        resolved=True,
        ambiguous=False,
        phrase=phrase,
        target_line=topic,
    )
