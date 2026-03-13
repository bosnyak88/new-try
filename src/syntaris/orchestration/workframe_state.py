from __future__ import annotations

import re
from dataclasses import dataclass

from syntaris.contracts.runtime import ThreadContextTurn, WorkframeBlockerStatus, WorkframeKind, WorkframeNextStepStatus, WorkframeObjectiveStatus, WorkframeState
from syntaris.orchestration.text_normalize import normalize_hungarian_for_match


_OBJECTIVE_ACTIVE = re.compile(r"(?:a\s+cel\s+most|celunk\s+most|mostani\s+cel(?:unk)?)\s+(?:az\s+)?(.+)$")
_OBJECTIVE_PROPOSED = re.compile(r"(?:lehet\s+a\s+cel|javasolt\s+cel|talan\s+a\s+cel)\s+(?:az\s+)?(.+)$")
_BLOCKER_EXPLICIT = re.compile(r"(?:fo\s+problema\s+hogy|ebben\s+most\s+az\s+a\s+fo\s+problema\s+hogy|miben\s+akadtunk\s+el\s*:?|elakadtunk\s+abban\s+hogy)\s+(.+)$")


@dataclass(frozen=True)
class WorkframeQuerySignals:
    asks_blocker: bool = False
    asks_next_step: bool = False
    asks_plan: bool = False


def detect_query_signals(message: str) -> WorkframeQuerySignals:
    n = normalize_hungarian_for_match(message).strip()
    simple = " es " not in n and "," not in n
    return WorkframeQuerySignals(
        asks_blocker=simple and n in {"mi a fo problema", "mi a fo problema?", "miben akadtunk el", "miben akadtunk el?", "mi blokkol most", "mi blokkol most?"},
        asks_next_step=simple and n in {"mit kell most tenni", "mit kell most tenni?", "mi a kovetkezo lepes", "mi a kovetkezo lepes?"},
        asks_plan=simple and n in {"irj egy rovid tervet", "irj egy rovid tervet?", "rovid tervet", "rovid tervet?"},
    )


def _detect_workframe(message: str, current: WorkframeKind) -> WorkframeKind:
    n = normalize_hungarian_for_match(message)
    if any(phrase in n for phrase in ("hol tartottunk", "elozo szalon mi volt", "emlekezz")):
        return WorkframeKind.RECALL
    if any(phrase in n for phrase in ("rovid terv", "kovetkezo lepes", "tervezzunk", "mit kell most tenni")):
        return WorkframeKind.PLANNING
    if any(phrase in n for phrase in ("jegyezd meg", "rogzitsd", "irasban hagyjuk", "mentsd el")):
        return WorkframeKind.CAPTURE
    if any(phrase in n for phrase in ("csak beszelgetunk", "beszelgessunk", "szia syntaris", "szia")):
        return WorkframeKind.CHAT
    if any(phrase in n for phrase in ("dolgozunk", "ticket", "feladat", "c el", "cel most")):
        return WorkframeKind.WORK
    return current


def _trim(value: str) -> str:
    return value.strip(" .!?:;")


def derive_workframe_state(turns: list[ThreadContextTurn], current_message: str) -> WorkframeState:
    workframe = WorkframeKind.CHAT
    objective_status = WorkframeObjectiveStatus.NONE
    objective_text: str | None = None
    blocker_status = WorkframeBlockerStatus.NONE
    blocker_text: str | None = None
    next_step_status = WorkframeNextStepStatus.NONE
    next_step_lines: list[str] = []

    for turn in [*turns, ThreadContextTurn(turn_id=-1, turn_index=-1, user_message=current_message, assistant_reply="", backend="deterministic", degraded=False)]:
        msg = turn.user_message
        n = normalize_hungarian_for_match(msg)
        workframe = _detect_workframe(msg, workframe)

        if match := _OBJECTIVE_ACTIVE.search(n):
            objective_status = WorkframeObjectiveStatus.ACTIVE
            objective_text = _trim(match.group(1))
        elif match := _OBJECTIVE_PROPOSED.search(n):
            objective_status = WorkframeObjectiveStatus.PROPOSED
            objective_text = _trim(match.group(1))

        if match := _BLOCKER_EXPLICIT.search(n):
            blocker_status = WorkframeBlockerStatus.EXPLICIT
            blocker_text = _trim(match.group(1))
        elif any(phrase in n for phrase in ("nem megy", "elakadt", "hianyos", "nem eleg eros")):
            blocker_status = WorkframeBlockerStatus.IMPLIED
            blocker_text = blocker_text or "Van súrlódás, de nincs teljesen kimondva a fő akadály."

        if "kovetkezo lepes" in n or "mit kell most tenni" in n:
            if blocker_text:
                next_step_status = WorkframeNextStepStatus.SUGGESTED
                next_step_lines = [f"Javaslat: a blokkert bontsuk fel és pontosítsuk ({blocker_text})."]
            elif objective_text:
                next_step_status = WorkframeNextStepStatus.SUGGESTED
                next_step_lines = [f"Javaslat: az aktív célból induljunk ki ({objective_text})."]
            else:
                next_step_status = WorkframeNextStepStatus.NONE
                next_step_lines = []
        if "irj egy rovid tervet" in n or "rovid tervet" in n:
            if objective_text:
                next_step_status = WorkframeNextStepStatus.MULTIPLE
                next_step_lines = [
                    "1) Rögzítsük röviden a célt.",
                    "2) Azonosítsuk a fő blokkert.",
                    "3) Válasszunk egy konkrét következő lépést.",
                ]
            else:
                next_step_status = WorkframeNextStepStatus.NONE
                next_step_lines = []

    if objective_status == WorkframeObjectiveStatus.NONE and objective_text is None and workframe in {WorkframeKind.WORK, WorkframeKind.PLANNING}:
        objective_status = WorkframeObjectiveStatus.UNRELATED_CONTEXT
    if blocker_status == WorkframeBlockerStatus.NONE and workframe in {WorkframeKind.WORK, WorkframeKind.PLANNING}:
        blocker_status = WorkframeBlockerStatus.UNKNOWN

    return WorkframeState(
        workframe=workframe,
        objective_status=objective_status,
        objective_text=objective_text,
        blocker_status=blocker_status,
        blocker_text=blocker_text,
        next_step_status=next_step_status,
        next_step_lines=next_step_lines,
    )
