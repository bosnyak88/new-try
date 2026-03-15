from __future__ import annotations

import re
from dataclasses import dataclass

from syntaris.contracts.runtime import (
    AssumptionStatus,
    DecisionState,
    EvidenceGapStatus,
    MissingInfoStatus,
    OpenQuestionStatus,
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
_BLOCKER_EXPLICIT = re.compile(
    r"(?:fo\s+problema\s+hogy|fo\s+problema\s+most\s+az\s+hogy|ebben\s+most\s+az\s+a\s+fo\s+problema\s+hogy|miben\s+akadtunk\s+el\s*:?|elakadtunk\s+abban\s+hogy|a\s+blocker\s+most|blocker\s+most)\s+(?:az\s+)?(.+)$"
)
_BLOCKER_HEDGED = re.compile(r"(?:lehet\s+hogy)\s+(.+?)\s+(?:a\s+blokk|blokkol|a\s+fo\s+problema)")
_NEXT_STEP_HEDGED = re.compile(r"(?:talan\s+az\s+lenne\s+a\s+kovetkezo\s+lepes\s+hogy)\s+(.+)$")
_BLOCKER_REPLACED_CONTEXT = re.compile(r"most\s+mar\s+mas\s+a\s+helyzet\s*:\s*(.+?)\s+megszunt\s*,\s*(?:a\s+)?(.+?)\s+maradt\s+gond$")


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
    asks_missing_info: bool = False
    asks_open_questions: bool = False
    asks_assumptions: bool = False
    asks_decision_state: bool = False
    asks_evidence_gaps: bool = False
    asks_progress_block_reason: bool = False

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
        if any((self.asks_missing_info, self.asks_open_questions, self.asks_assumptions, self.asks_decision_state, self.asks_evidence_gaps, self.asks_progress_block_reason)):
            return "decision_readiness_query"
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
    complex_joint = " es " in n
    asks_blocker_single = any(phrase in n for phrase in ("mi a fo problema", "miben akadtunk el", "mi blokkol", "mi a blocker"))
    asks_next_single = any(phrase in n for phrase in ("mit kell most tenni", "mi a kovetkezo lepes"))
    asks_blocker_mixed = "meg amugy mi a blocker" in n
    return WorkframeQuerySignals(
        asks_blocker=(asks_blocker_single and not complex_joint) or asks_blocker_mixed,
        asks_next_step=(asks_next_single and not complex_joint),
        asks_plan=("irj egy rovid tervet" in n) or (n in {"rovid tervet", "rovid tervet?"}),
        asks_current_objective=n in {"mi a mostani cel", "mi a mostani cel?"},
        asks_current_work=n in {"min dolgozunk most", "min dolgozunk most?", "akkor most min dolgozunk", "akkor most min dolgozunk?"},
        asks_current_posture=n in {"ez most chat vagy munka", "ez most chat vagy munka?"},
        asks_current_blocker=n in {"mi a mostani fo problema", "mi a mostani fo problema?", "mi a blocker most", "mi a blocker most?"},
        asks_current_next_step=n in {"mi a mostani kovetkezo lepes", "mi a mostani kovetkezo lepes?"},
        asks_history_objective=n in {"mi volt az aktiv cel", "mi volt az aktiv cel?"},
        asks_history_blocker=n in {"mi volt a fo problema", "mi volt a fo problema?"},
        asks_history_next_step=n in {"mi volt a kovetkezo lepes", "mi volt a kovetkezo lepes?"},
        asks_certainty_split=("mi biztos ebben" in n and "mi csak feltetelezes" in n),
        asks_next_step_certainty=("kovetkezo lepes biztos" in n and "csak javaslat" in n),
        asks_missing_info=("mi hianyzik" in n) or ("mihez kell meg adat" in n) or ("mihez kell meg informacio" in n),
        asks_open_questions=("milyen nyitott kerdesek" in n) or ("mi maradt nyitva" in n) or ("amire meg nincs valasz" in n),
        asks_assumptions=("mi csak feltetelezes" in n) or ("mi ebben a bizonytalan" in n),
        asks_decision_state=("milyen dontest kell" in n) or ("van most dontesi pont" in n) or ("mihez kell dontes" in n) or ("eldolt mar" in n),
        asks_evidence_gaps=("mihez nincs meg eleg alap" in n) or ("mihez kell meg bizonyitek" in n) or ("mihez nincs meg eleg bizonyitek" in n) or ("mitol lenne ez megalapozott" in n),
        asks_progress_block_reason=("miert nem tudunk meg tovabbmenni" in n),
    )


def detect_update_signals(message: str) -> WorkframeUpdateSignals:
    n = normalize_hungarian_for_match(message).strip()
    return WorkframeUpdateSignals(
        declares_work=any(phrase in n for phrase in ("most ezen dolgozunk", "ezen dolgozunk most", "most ezen a feladaton dolgozunk")) or ("dolgozunk" in n and "?" not in n),
        declares_objective=_OBJECTIVE_ACTIVE.search(n) is not None,
        declares_chat=any(phrase in n for phrase in ("most csak beszelgetunk", "most csak dumalunk", "most inkabb beszelgetunk", "most ne dolgozzunk", "csak reagalj normalisan", "nem kerek listat")),
        declares_blocker_explicit=_BLOCKER_EXPLICIT.search(n) is not None or _BLOCKER_REPLACED_CONTEXT.search(n) is not None,
        resume_here=(n == "folytassuk innen"),
        hedged_blocker=("lehet hogy" in n and "blokk" in n) or (_BLOCKER_HEDGED.search(n) is not None),
        hedged_objective=("jo lenne" in n and "ticket" in n) or ("jo lenne" in n and "cel" in n),
        hedged_next_step=("talan" in n and "kovetkezo lepes" in n) or (_NEXT_STEP_HEDGED.search(n) is not None),
    )


def _detect_workframe(message: str, current: WorkframeKind) -> WorkframeKind:
    n = normalize_hungarian_for_match(message)
    chat_lock_signals = (
        "most ne dolgozzunk", "most ne dolgzunk", "csak beszelgessunk", "nem kerek listat", "csak reagalj normalisan", "most csak beszelgetunk", "csak beszelgetunk", "beszelgessunk", "beszelgesunk", "pls",
    )
    casual_weight = sum(1 for token in ("beszelg", "dumal", "normalisan", "pls", "chat") if token in n)
    if any(phrase in n for phrase in chat_lock_signals) or casual_weight >= 2 or n in {"szia syntaris", "szia"}:
        return WorkframeKind.CHAT
    if current == WorkframeKind.CHAT and any(phrase in n for phrase in ("most", "fontos", "biztos", "emlekszel", "hol tartottunk", "folytassuk innen")):
        strong_work = any(phrase in n for phrase in ("dolgozzunk", "feladat", "ticket", "konkret lepes", "terv kell", "kovetkezo lepes kell"))
        if not strong_work:
            return WorkframeKind.CHAT
    if any(phrase in n for phrase in ("hol tartottunk", "elozo szalon mi volt", "emlekezz")):
        return WorkframeKind.RECALL
    if any(phrase in n for phrase in ("rovid terv", "kovetkezo lepes", "tervezzunk", "mit kell most tenni")):
        return WorkframeKind.PLANNING
    if any(phrase in n for phrase in ("jegyezd meg", "rogzitsd", "irasban hagyjuk", "mentsd el")):
        return WorkframeKind.CAPTURE
    if any(phrase in n for phrase in ("most ezen dolgozunk", "dolgozunk", "ticket", "feladat", "cel most", "a cel most", "blocker most", "maintenance")):
        return WorkframeKind.WORK
    return current


def _trim(value: str) -> str:
    return value.strip(" .!?:;")


def _is_meta_state_query(n: str, query_signals: WorkframeQuerySignals) -> bool:
    return query_signals.family in {"decision_readiness_query", "current_state_query", "historical_state_query", "uncertainty_query"} or (
        n.endswith("?") and ("mi " in n or "milyen " in n or "van most" in n)
    )


def derive_workframe_state(turns: list[ThreadContextTurn], current_message: str) -> WorkframeState:
    workframe = WorkframeKind.CHAT
    objective_status = WorkframeObjectiveStatus.NONE
    objective_text: str | None = None
    blocker_status = WorkframeBlockerStatus.NONE
    blocker_text: str | None = None
    next_step_status = WorkframeNextStepStatus.NONE
    next_step_lines: list[str] = []
    missing_info_status = MissingInfoStatus.NONE
    missing_info_lines: list[str] = []
    open_question_status = OpenQuestionStatus.NONE
    open_question_lines: list[str] = []
    assumption_status = AssumptionStatus.UNKNOWN
    assumption_lines: list[str] = []
    decision_state = DecisionState.NONE
    decision_lines: list[str] = []
    evidence_gap_status = EvidenceGapStatus.UNKNOWN
    evidence_gap_lines: list[str] = []

    seed_turns = [*turns, ThreadContextTurn(turn_id=-1, turn_index=-1, user_message=current_message, assistant_reply="", backend="deterministic", degraded=False)]
    for turn in seed_turns:
        msg = turn.user_message
        n = normalize_hungarian_for_match(msg).strip()
        query_signals = detect_query_signals(msg)
        update_signals = detect_update_signals(msg)
        is_meta_query = _is_meta_state_query(n, query_signals)

        workframe = _detect_workframe(msg, workframe)

        if match := _OBJECTIVE_ACTIVE.search(n):
            objective_status = WorkframeObjectiveStatus.ACTIVE
            objective_text = _trim(match.group(1))
        elif (match := _OBJECTIVE_PROPOSED.search(n)) and objective_status != WorkframeObjectiveStatus.ACTIVE:
            objective_status = WorkframeObjectiveStatus.PROPOSED
            objective_text = _trim(match.group(1))
            assumption_status = AssumptionStatus.ASSUMPTION
            assumption_lines = [f"Cél-javaslatként hangzott el: {objective_text}"]

        if match := _BLOCKER_EXPLICIT.search(n):
            blocker_status = WorkframeBlockerStatus.EXPLICIT
            blocker_text = _trim(match.group(1))
            if "nincs meg" in blocker_text and any(token in blocker_text for token in ("eleg", "adat", "informacio", "bizonyitek", "eros")):
                missing_info_status = MissingInfoStatus.IMPLIED
                missing_info_lines = [f"A fő blokker alapján még hiányzik valami a haladáshoz: {blocker_text}."]
                evidence_gap_status = EvidenceGapStatus.IMPLIED
                evidence_gap_lines = ["A fő blokker alapján további bizonyíték/adat kell a biztos továbblépéshez."]
        elif (replacement := _BLOCKER_REPLACED_CONTEXT.search(n)) is not None:
            blocker_status = WorkframeBlockerStatus.EXPLICIT
            blocker_text = f"{_trim(replacement.group(2))} maradt gond"
            missing_info_status = MissingInfoStatus.NONE
            if blocker_text:
                assumption_status = AssumptionStatus.SUPPORTED
        elif (_BLOCKER_HEDGED.search(n) is not None) and blocker_status == WorkframeBlockerStatus.NONE:
            blocker_status = WorkframeBlockerStatus.IMPLIED
            blocker_text = "Lehetséges blokkerről beszéltünk, de nem biztos állításként."
            assumption_status = AssumptionStatus.INFERRED
            assumption_lines = ["A blokkert csak valószínűsítettük."]
        elif any(phrase in n for phrase in ("nem megy", "elakadt", "hianyos", "nem eleg eros")):
            blocker_status = WorkframeBlockerStatus.IMPLIED
            blocker_text = blocker_text or "Van súrlódás, de nincs teljesen kimondva a fő akadály."


        if any(t in n for t in ("traceback", "exception", "error", "runtimeerror", "valueerror", "exit code", "failed")):
            if blocker_status == WorkframeBlockerStatus.NONE:
                blocker_status = WorkframeBlockerStatus.IMPLIED
            if blocker_text is None:
                blocker_text = "A forrásban hiba/traceback jel látszik, ez valószínűleg blokkolja a továbblépést."
            if assumption_status == AssumptionStatus.UNKNOWN:
                assumption_status = AssumptionStatus.INFERRED
                if not assumption_lines:
                    assumption_lines = ["A blocker részben közvetlen hibajelre, részben következtetésre épül."]

        if update_signals.hedged_blocker or update_signals.hedged_objective or update_signals.hedged_next_step:
            if assumption_status == AssumptionStatus.UNKNOWN:
                assumption_status = AssumptionStatus.ASSUMPTION
            if not assumption_lines:
                assumption_lines = ["Van olyan állítás, ami csak feltételezésként szerepel."]

        if match := _NEXT_STEP_HEDGED.search(n):
            next_step_status = WorkframeNextStepStatus.SUGGESTED
            next_step_lines = [f"Lehetséges következő lépés (még nem biztos): {_trim(match.group(1))}."]
        if "irj egy rovid tervet" in n or "rovid tervet" in n:
            if objective_text:
                next_step_status = WorkframeNextStepStatus.MULTIPLE
                next_step_lines = [
                    "1) Rögzítsük röviden a célt.",
                    "2) Azonosítsuk a fő blokkert.",
                    "3) Pótoljuk a hiányzó adatot és csak utána döntsünk.",
                ]


        # Do not materialize meta state-queries into persistent open/missing/decision state.
        if is_meta_query:
            continue

        if "nincs meg" in n and any(t in n for t in ("adat", "informacio", "bizonyitek", "alap")):
            missing_info_status = MissingInfoStatus.EXPLICIT
            missing_info_lines = ["Hiányzó adat/információ van kimondva."]
            evidence_gap_status = EvidenceGapStatus.EXPLICIT
            evidence_gap_lines = ["A továbblépéshez még nincs elég bizonyíték/adat."]
        elif any(t in n for t in ("nem tudjuk", "nem derult ki", "hianyzik")) and missing_info_status == MissingInfoStatus.NONE:
            missing_info_status = MissingInfoStatus.IMPLIED
            missing_info_lines = ["Valami hiányzik, de nincs teljesen explicit leírva."]

        if any(t in n for t in ("nyitott kerdes", "kerdes hogy", "nincs valasz")):
            open_question_status = OpenQuestionStatus.EXPLICIT
            open_question_lines = ["Van tartalmi nyitott kérdés, ami még nincs lezárva."]
        elif any(t in n for t in ("megvan a valasz", "lezartuk a kerdest")) and open_question_status in {OpenQuestionStatus.EXPLICIT, OpenQuestionStatus.IMPLIED}:
            open_question_status = OpenQuestionStatus.ANSWERED
            open_question_lines = ["A korábban nyitott kérdés lezártnak tűnik."]

        if any(t in n for t in ("dontest kell", "dontesi pont", "mi legyen a kovetkezo")):
            decision_state = DecisionState.NEEDED
            decision_lines = ["Aktív döntési pont van."]
        elif any(t in n for t in ("dontes lett", "ugy dontottunk", "eldolt")) and "?" not in n:
            decision_state = DecisionState.MADE
            decision_lines = ["A döntés lezártnak van jelezve."]

    # Derived relation rules after scanning full turn history.
    if decision_state in {DecisionState.NEEDED, DecisionState.PROPOSED} and missing_info_status in {MissingInfoStatus.EXPLICIT, MissingInfoStatus.IMPLIED}:
        decision_state = DecisionState.BLOCKED_BY_MISSING_INFO
        decision_lines = ["Döntés kellene, de hiányzó információ blokkolja."]

    if next_step_status == WorkframeNextStepStatus.NONE:
        if missing_info_status in {MissingInfoStatus.EXPLICIT, MissingInfoStatus.IMPLIED}:
            next_step_status = WorkframeNextStepStatus.SUGGESTED
            next_step_lines = ["Előbb pótoljuk a hiányzó információt, utána legyen végleges következő lépés."]
        elif blocker_text:
            next_step_status = WorkframeNextStepStatus.SUGGESTED
            next_step_lines = [f"Javaslat: a blokkert bontsuk fel és pontosítsuk ({blocker_text})."]
        elif objective_text:
            next_step_status = WorkframeNextStepStatus.SUGGESTED
            next_step_lines = [f"Javaslat: az aktív célból induljunk ki ({objective_text})."]

    if objective_status == WorkframeObjectiveStatus.NONE and objective_text is None and workframe in {WorkframeKind.WORK, WorkframeKind.PLANNING}:
        objective_status = WorkframeObjectiveStatus.UNRELATED_CONTEXT
    if blocker_status == WorkframeBlockerStatus.NONE and workframe in {WorkframeKind.WORK, WorkframeKind.PLANNING}:
        blocker_status = WorkframeBlockerStatus.UNKNOWN

    if evidence_gap_status == EvidenceGapStatus.UNKNOWN:
        evidence_gap_status = EvidenceGapStatus.SUFFICIENT if missing_info_status == MissingInfoStatus.NONE else EvidenceGapStatus.IMPLIED

    if decision_state == DecisionState.NONE and missing_info_status in {MissingInfoStatus.EXPLICIT, MissingInfoStatus.IMPLIED}:
        decision_state = DecisionState.BLOCKED_BY_MISSING_INFO
        decision_lines = ["A következő döntési pontot hiányzó információ blokkolja."]

    return WorkframeState(
        workframe=workframe,
        objective_status=objective_status,
        objective_text=objective_text,
        blocker_status=blocker_status,
        blocker_text=blocker_text,
        next_step_status=next_step_status,
        next_step_lines=next_step_lines,
        missing_info_status=missing_info_status,
        missing_info_lines=missing_info_lines,
        open_question_status=open_question_status,
        open_question_lines=open_question_lines,
        assumption_status=assumption_status,
        assumption_lines=assumption_lines,
        decision_state=decision_state,
        decision_lines=decision_lines,
        evidence_gap_status=evidence_gap_status,
        evidence_gap_lines=evidence_gap_lines,
    )
