from __future__ import annotations

import re
from dataclasses import dataclass

from syntaris.contracts.runtime import (
    ThreadContextTurn,
    WorkframeBlockerStatus,
    WorkframeKind,
    WorkframeNextStepStatus,
    WorkframeObjectiveStatus,
    WorkframeState,
)
from syntaris.orchestration.text_normalize import normalize_hungarian_for_match

_OBJECTIVE_ACTIVE = re.compile(r"(?:a\s+cel\s+most|celunk\s+most|mostani\s+cel(?:unk)?)\s+(?:az\s+)?(.+)$")
_OBJECTIVE_PROPOSED = re.compile(r"(?:lehet\s+a\s+cel|javasolt\s+cel|talan\s+a\s+cel|jo\s+lenne)\s+(?:az\s+)?(.+)$")
_BLOCKER_EXPLICIT = re.compile(r"(?:fo\s+problema\s+hogy|ebben\s+most\s+az\s+a\s+fo\s+problema\s+hogy|miben\s+akadtunk\s+el\s*:?|elakadtunk\s+abban\s+hogy)\s+(.+)$")
_BLOCKER_HEDGED = re.compile(r"(?:lehet\s+hogy)\s+(.+?)\s+(?:a\s+blokk|blokkol|a\s+fo\s+problema)")
_NEXT_STEP_HEDGED = re.compile(r"(?:talan\s+az\s+lenne\s+a\s+kovetkezo\s+lepes\s+hogy)\s+(.+)$")


@dataclass(frozen=True)
class WorkframeQuerySignals:
    asks_blocker: bool = False
    asks_next_step: bool = False
    asks_plan: bool = False
    asks_current_objective: bool = False
    asks_current_work: bool = False
    asks_current_posture: bool = False
    asks_current_blocker: bool = False
    asks_current_next_step: bool = False
    asks_history_objective: bool = False
    asks_history_blocker: bool = False
    asks_history_next_step: bool = False
    asks_certainty_split: bool = False
    asks_next_step_certainty: bool = False

    @property
    def family(self) -> str | None:
        if any((self.asks_history_objective, self.asks_history_blocker, self.asks_history_next_step)):
            return "historical_state_query"
        if any((self.asks_current_objective, self.asks_current_work, self.asks_current_posture, self.asks_current_blocker, self.asks_current_next_step)):
            return "current_state_query"
        if any((self.asks_blocker, self.asks_next_step, self.asks_plan)):
            return "workframe_action_query"
        if any((self.asks_certainty_split, self.asks_next_step_certainty)):
            return "uncertainty_query"
        return None


@dataclass(frozen=True)
class WorkframeUpdateSignals:
    declares_work: bool = False
    declares_objective: bool = False
    declares_chat: bool = False
    declares_blocker_explicit: bool = False
    resume_here: bool = False
    hedged_blocker: bool = False
    hedged_objective: bool = False
    hedged_next_step: bool = False

    @property
    def uncertainty_marked(self) -> bool:
        return self.hedged_blocker or self.hedged_objective or self.hedged_next_step


def detect_query_signals(message: str) -> WorkframeQuerySignals:
    n = normalize_hungarian_for_match(message).strip()
    simple = " es " not in n and "," not in n
    return WorkframeQuerySignals(
        asks_blocker=simple and n in {"mi a fo problema", "mi a fo problema?", "miben akadtunk el", "miben akadtunk el?", "mi blokkol most", "mi blokkol most?"},
        asks_next_step=simple and n in {"mit kell most tenni", "mit kell most tenni?", "mi a kovetkezo lepes", "mi a kovetkezo lepes?"},
        asks_plan=simple and n in {"irj egy rovid tervet", "irj egy rovid tervet?", "rovid tervet", "rovid tervet?"},
        asks_current_objective=n in {"mi a mostani cel", "mi a mostani cel?"},
        asks_current_work=n in {"min dolgozunk most", "min dolgozunk most?", "akkor most min dolgozunk", "akkor most min dolgozunk?"},
        asks_current_posture=n in {"ez most chat vagy munka", "ez most chat vagy munka?"},
        asks_current_blocker=n in {"mi a mostani fo problema", "mi a mostani fo problema?"},
        asks_current_next_step=n in {"mi a mostani kovetkezo lepes", "mi a mostani kovetkezo lepes?"},
        asks_history_objective=n in {"mi volt az aktiv cel", "mi volt az aktiv cel?"},
        asks_history_blocker=n in {"mi volt a fo problema", "mi volt a fo problema?"},
        asks_history_next_step=n in {"mi volt a kovetkezo lepes", "mi volt a kovetkezo lepes?"},
        asks_certainty_split=("mi biztos ebben" in n and "mi csak feltetelezes" in n),
        asks_next_step_certainty=("kovetkezo lepes biztos" in n and "csak javaslat" in n),
    )


def detect_update_signals(message: str) -> WorkframeUpdateSignals:
    n = normalize_hungarian_for_match(message).strip()
    return WorkframeUpdateSignals(
        declares_work=any(phrase in n for phrase in ("most ezen dolgozunk", "ezen dolgozunk most", "most ezen a feladaton dolgozunk")),
        declares_objective=_OBJECTIVE_ACTIVE.search(n) is not None,
        declares_chat=any(phrase in n for phrase in ("most csak beszelgetunk", "most csak dumalunk", "most inkabb beszelgetunk")),
        declares_blocker_explicit=_BLOCKER_EXPLICIT.search(n) is not None,
        resume_here=(n == "folytassuk innen"),
        hedged_blocker=("lehet hogy" in n and "blokk" in n) or (_BLOCKER_HEDGED.search(n) is not None),
        hedged_objective=("jo lenne" in n and "ticket" in n) or ("jo lenne" in n and "cel" in n),
        hedged_next_step=("talan" in n and "kovetkezo lepes" in n) or (_NEXT_STEP_HEDGED.search(n) is not None),
    )


def _detect_workframe(message: str, current: WorkframeKind) -> WorkframeKind:
    n = normalize_hungarian_for_match(message)
    if any(phrase in n for phrase in ("most csak beszelgetunk", "csak beszelgetunk", "beszelgessunk", "szia syntaris", "szia")):
        return WorkframeKind.CHAT
    if any(phrase in n for phrase in ("hol tartottunk", "elozo szalon mi volt", "emlekezz")):
        return WorkframeKind.RECALL
    if any(phrase in n for phrase in ("rovid terv", "kovetkezo lepes", "tervezzunk", "mit kell most tenni")):
        return WorkframeKind.PLANNING
    if any(phrase in n for phrase in ("jegyezd meg", "rogzitsd", "irasban hagyjuk", "mentsd el")):
        return WorkframeKind.CAPTURE
    if any(phrase in n for phrase in ("most ezen dolgozunk", "dolgozunk", "ticket", "feladat", "cel most", "a cel most")):
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
        elif (match := _OBJECTIVE_PROPOSED.search(n)) and objective_status != WorkframeObjectiveStatus.ACTIVE:
            objective_status = WorkframeObjectiveStatus.PROPOSED
            objective_text = _trim(match.group(1))

        if match := _BLOCKER_EXPLICIT.search(n):
            blocker_status = WorkframeBlockerStatus.EXPLICIT
            blocker_text = _trim(match.group(1))
        elif (_BLOCKER_HEDGED.search(n) is not None) and blocker_status == WorkframeBlockerStatus.NONE:
            blocker_status = WorkframeBlockerStatus.IMPLIED
            blocker_text = "Lehetséges blokkerről beszéltünk, de nem biztos állításként."
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
        if match := _NEXT_STEP_HEDGED.search(n):
            next_step_status = WorkframeNextStepStatus.SUGGESTED
            next_step_lines = [f"Lehetséges következő lépés (még nem biztos): {_trim(match.group(1))}."]
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
