from __future__ import annotations

from syntaris.orchestration.text_normalize import clean_display_text
from syntaris.contracts.runtime import (
    AnswerStrategy,
    ClaimKind,
    AnswerStrategySelection,
    ComparisonPack,
    DecompositionPlan,
    EvidencePack,
    ObjectiveFrame,
    OwnerIdentityProfile,
    PersonalMemoryView,
    MemoryQueryKind,
    ScopedStateStatus,
    PersonalEntryKind,
    RecallResolution,
    ResponsePlan,
    ResponsePlanKind,
    ResponsePlanSection,
    RuntimeContext,
    SynthesisPlan,
    ThreadFocusPack,
    TimeContext,
    TurnInterpretation,
    WorkframeState,
    ThreadWeaveState,
)


def _synthesis_sections(synthesis: SynthesisPlan) -> list[ResponsePlanSection]:
    return [
        ResponsePlanSection(title=section.key, lines=section.lines)
        for section in synthesis.sections
        if section.lines
    ]


def _direct_should_use_synthesis(objective: ObjectiveFrame, decomposition: DecompositionPlan, synthesis: SynthesisPlan) -> bool:
    _ = synthesis
    if objective.kind.value in {"mixed_multi_part", "status_check", "diagnose", "compare", "next_step"}:
        return True
    if decomposition.multi_part:
        return True
    target_kinds = {"status_check", "diagnose", "compare", "next_step"}
    return any(unit.objective_kind.value in target_kinds for unit in decomposition.units)


def _daypart_greeting(daypart: str) -> str:
    mapping = {
        "reggel": "Jó reggelt",
        "delelott": "Szép délelőttöt",
        "delutan": "Szép délutánt",
        "este": "Jó estét",
        "ejjel": "Jó estét",
    }
    return mapping.get(daypart, "Szia")


def _gap_phrase(gap_kind: str, gap_minutes: int | None) -> str | None:
    if gap_kind == "short":
        return "Pár perce beszéltünk utoljára."
    if gap_kind == "same_day_long":
        if gap_minutes is not None and gap_minutes >= 120:
            return "Eltelt pár óra a legutóbbi üzenet óta."
        return "Eltelt egy kis idő a legutóbbi üzenet óta."
    if gap_kind == "cross_day":
        return "Tegnap óta nem folytattuk."
    return None


def _continuity_resume_line(gap_kind: str) -> str:
    if gap_kind in {"immediate", "short"}:
        return "Látom a mostani irányt, onnan folytathatjuk."
    if gap_kind == "same_day_long":
        return "A mai előzmény még megvan, de megerősítheted, maradjon-e ez az irány."
    if gap_kind == "cross_day":
        return "A tegnapi irányt nem kezelem automatikusan aktívnak, de vissza tudjuk venni, ha kéred."
    return "Innen tudunk továbblépni."


def _personal_entry_lines(signal: PersonalEntryKind, display_name: str, focus: str | None, direction: str | None, time_context: TimeContext | None = None, workframe_state: WorkframeState | None = None) -> list[str]:
    if signal == PersonalEntryKind.GREETING:
        greet = _daypart_greeting(time_context.daypart.value) if time_context is not None else "Szia"
        return [f"{greet}{display_name}. Miben segítsek most?"]
    if signal == PersonalEntryKind.SELF_INTRO:
        return [f"Szia{display_name}. Örülök, hogy így mutatkoztál be — miben induljunk el most?"]
    if signal == PersonalEntryKind.OWNER_FRAMING:
        return [f"Szia{display_name}. Értem, hogy te tervezed és fejleszted a rendszert. Mi legyen a mai konkrét fókusz?"]
    if signal == PersonalEntryKind.PERSONAL_CHAT_INTAKE:
        return [f"Rendben{display_name}, most beszélgető módra váltunk. Mi az, ami most leginkább foglalkoztat?"]
    if signal == PersonalEntryKind.CONCRETE_HELP_INTAKE:
        return ["Rendben, menjünk konkrétan ezen: írd le röviden, hol akadtál el, és onnan lépünk tovább."]
    if signal == PersonalEntryKind.FOCUS_SETTING_INTAKE:
        if focus:
            return [f"Jó irány, a mai fókusz legyen {clean_display_text(focus)}. Mi legyen az első konkrét lépés?"]
        if direction:
            return [f"Rendben, most a {clean_display_text(direction)} irányra állunk rá. Melyik konkrét ponttal kezdjük?"]
        return ["Rendben, fókuszra álltunk. Melyik konkrét ponttal kezdjük?"]
    if signal == PersonalEntryKind.RESUME_INTAKE:
        lead = _continuity_resume_line(time_context.gap_kind.value) if time_context is not None else "Innen tudunk továbblépni."
        if workframe_state is not None and workframe_state.objective_status.value == "active" and workframe_state.objective_text:
            return [f"Oké, vegyük fel innen a fonalat. {lead} Aktív célként ezt látom: {clean_display_text(workframe_state.objective_text)}."]
        return [f"Oké, vegyük fel innen a fonalat. {lead}"]
    if signal == PersonalEntryKind.RETURN_ENTRY:
        gap = _gap_phrase(time_context.gap_kind.value, time_context.gap_minutes) if time_context is not None else None
        base = f"Jó újra itt{display_name}."
        if workframe_state is not None and workframe_state.objective_status.value == "active" and workframe_state.objective_text:
            objective = clean_display_text(workframe_state.objective_text)
            blocker = f" Fő blokkernél ezt látom: {clean_display_text(workframe_state.blocker_text)}." if workframe_state.blocker_text else ""
            if gap:
                return [f"{base} {gap} Folytathatjuk a korábbi munkát: {objective}.{blocker}"]
            return [f"{base} Folytathatjuk a korábbi munkát: {objective}.{blocker}"]
        if gap:
            return [f"{base} {gap} Mivel folytassuk?"]
        return [f"{base} Mivel folytassuk?"]
    return ["Rendben, visszakapcsoltam ide. Folytassuk innen — most beszélgessünk, vagy oldjunk meg egy konkrét feladatot?"]


def _memory_query_lines(query: MemoryQueryKind, memory: PersonalMemoryView) -> list[str]:
    def status_label(status: ScopedStateStatus | None) -> str:
        if status == ScopedStateStatus.ACTIVE:
            return "aktív"
        if status == ScopedStateStatus.STALE:
            return "már csak részben aktív"
        return "lejárt"

    if query == MemoryQueryKind.WHO_AM_I:
        if memory.owner_name:
            return [f"A megadott adataid alapján {memory.owner_name} vagy."]
        return ["Ezt még nem tudom biztosan, mert nem mondtad ki egyértelműen a neved."]
    if query == MemoryQueryKind.RELATIONSHIP:
        if memory.owner_relation == "creator":
            return ["Amit biztosan tudok: azt mondtad, hogy te tervezted ezt a rendszert."]
        return ["A kapcsolatunkról még csak annyit tudok biztosan, amit explicit mondtál — ezt még nem rögzítettük."]
    if query == MemoryQueryKind.SYSTEM_ROLE:
        if memory.system_role:
            return [f"A kimondott szerepem: {memory.system_role}."]
        return ["A szerepemről még nincs egyértelmű, explicit állításod eltárolva."]
    if query == MemoryQueryKind.CURRENT_FOCUS:
        if memory.current_focus and memory.current_focus_status == ScopedStateStatus.ACTIVE:
            return [f"A mostani fókusz aktívan: {clean_display_text(memory.current_focus)}."]
        if memory.current_direction and memory.current_direction_status == ScopedStateStatus.ACTIVE:
            return [f"A mostani irány aktívan: {clean_display_text(memory.current_direction)}."]
        if memory.current_focus:
            return [f"A legutóbbi fókusz: {clean_display_text(memory.current_focus)}, de ez most {status_label(memory.current_focus_status)}."]
        if memory.current_direction:
            return [f"A legutóbbi irány: {clean_display_text(memory.current_direction)}, de ez most {status_label(memory.current_direction_status)}."]
        return ["Mostani fókuszt még nem állítottál be explicit módon."]
    if query == MemoryQueryKind.CURRENT_DIRECTION:
        if memory.current_direction and memory.current_direction_status == ScopedStateStatus.ACTIVE:
            return [f"Most erről akartál beszélni: {clean_display_text(memory.current_direction)}."]
        if memory.current_direction:
            return [f"Legutóbb erről akartál beszélni: {clean_display_text(memory.current_direction)}, de ez most {status_label(memory.current_direction_status)}."]
        return ["Mostani beszélgetési irányt még nem adtál meg explicit módon."]
    if query == MemoryQueryKind.ACTIVE_STATE:
        relevant = memory.scoped_state.recent_items
        if relevant:
            lines = ["Mostanról ennyi maradt releváns:"]
            for item in relevant[:3]:
                lines.append(
                    f"• {item.kind.value.replace('_', ' ')}: {clean_display_text(item.value)} ({status_label(item.status)})"
                )
            return lines
        if memory.scoped_state.items:
            latest = memory.scoped_state.items[0]
            return [f"A legutóbbi ideiglenes állapot ({clean_display_text(latest.value)}) már nem aktív."]
        return ["Most nincs aktív ideiglenes fókusz vagy irány rögzítve."]
    if query == MemoryQueryKind.WHAT_INFERRED:
        return ["Rólad jelenleg nem tartok fenn külön, bizonyított következtetés-listát; amit biztosnak mondok, az explicit állításból jön."]
    if query == MemoryQueryKind.TEMPORARY_VS_CERTAIN:
        lines: list[str] = ["Szétválasztva:"]
        if memory.owner_name or memory.owner_relation or memory.system_role:
            lines.append("• Biztos (stabil, explicit):")
            if memory.owner_name:
                lines.append(f"  - név: {memory.owner_name}")
            if memory.owner_relation:
                lines.append(f"  - kapcsolat: {memory.owner_relation}")
            if memory.system_role:
                lines.append(f"  - szerep: {memory.system_role}")
        else:
            lines.append("• Biztos (stabil, explicit): még nincs.")

        if memory.scoped_state.recent_items:
            lines.append("• Ideiglenes (idővel elévül):")
            for item in memory.scoped_state.recent_items[:3]:
                lines.append(f"  - {item.kind.value.replace('_', ' ')}: {clean_display_text(item.value)} ({status_label(item.status)})")
        elif memory.scoped_state.items:
            lines.append("• Ideiglenes: volt ilyen, de már lejárt.")
        else:
            lines.append("• Ideiglenes: jelenleg nincs.")
        lines.append("• Feltételezés/inferencia: nincs külön biztosként kezelt tétel.")
        return lines

    lines: list[str] = []
    if memory.owner_name:
        lines.append(f"• Név (explicit): {memory.owner_name}")
    if memory.owner_relation:
        relation = "creator" if memory.owner_relation == "creator" else memory.owner_relation
        lines.append(f"• Kapcsolat (explicit): {relation}")
    if memory.system_role:
        lines.append(f"• Szerep (explicit): {memory.system_role}")
    if memory.current_focus:
        lines.append(f"• Mostani fókusz ({status_label(memory.current_focus_status)}): {clean_display_text(memory.current_focus)}")
    elif memory.current_direction:
        lines.append(f"• Mostani irány ({status_label(memory.current_direction_status)}): {clean_display_text(memory.current_direction)}")
    return lines or ["Még nincs olyan explicit állításod eltárolva, amit biztos tényként vissza tudok mondani."]


def _claim_capture_lines(interpretation: TurnInterpretation) -> list[str]:
    captures = interpretation.claim_capture
    by_kind = {item.kind: item.value for item in captures}

    if interpretation.pattern_name == "claim_correction" and ClaimKind.OWNER_NAME in by_kind:
        return [f"Köszönöm a javítást, a nevedet {clean_display_text(by_kind[ClaimKind.OWNER_NAME])} néven rögzítettem."]

    if ClaimKind.SYSTEM_ROLE in by_kind:
        return [f"Rögzítettem: a szerepemnek ezt mondtad — {clean_display_text(by_kind[ClaimKind.SYSTEM_ROLE])}."]
    if ClaimKind.OWNER_NAME in by_kind:
        return [f"Rendben, rögzítettem a nevedet: {clean_display_text(by_kind[ClaimKind.OWNER_NAME])}."]
    if ClaimKind.OWNER_RELATION in by_kind and by_kind[ClaimKind.OWNER_RELATION] == "creator":
        return ["Rögzítettem: azt mondtad, hogy te tervezted a rendszeremet."]
    if ClaimKind.CURRENT_FOCUS in by_kind:
        return [f"Rögzítettem a mostani fókuszt: {clean_display_text(by_kind[ClaimKind.CURRENT_FOCUS])}."]
    if ClaimKind.CURRENT_DIRECTION in by_kind:
        direction_value = by_kind[ClaimKind.CURRENT_DIRECTION]
        if direction_value.startswith("állapot:"):
            return [f"Jelezted az ideiglenes állapotodat, ezt most így kezelem: {clean_display_text(direction_value)}."]
        return [f"Rögzítettem a mostani irányt: {clean_display_text(direction_value)}."]

    return ["Rögzítettem az explicit állításodat."]



def _workframe_lines(workframe_state: WorkframeState) -> list[str]:
    lines: list[str] = [f"Munkakeret: {workframe_state.workframe.value}."]
    if workframe_state.objective_status.value == "active" and workframe_state.objective_text:
        lines.append(f"Aktív cél: {clean_display_text(workframe_state.objective_text)}.")
    elif workframe_state.objective_status.value == "proposed" and workframe_state.objective_text:
        lines.append(f"Javasolt cél: {clean_display_text(workframe_state.objective_text)} (még nem végleges).")
    elif workframe_state.objective_status.value in {"none", "related_context"}:
        lines.append("Aktív cél: nincs még egyértelműen rögzítve.")

    if workframe_state.blocker_status.value in {"explicit", "implied"} and workframe_state.blocker_text:
        prefix = "Fő blokkert" if workframe_state.blocker_status.value == "explicit" else "Lehetséges blokkert"
        lines.append(f"{prefix} látok: {clean_display_text(workframe_state.blocker_text)}.")
    elif workframe_state.blocker_status.value in {"uncertainty_or_missing_info", "none"}:
        lines.append("Fő blokkert nem látok biztosan rögzítve.")

    if workframe_state.next_step_lines:
        lines.append("Következő lépés:")
        for step in workframe_state.next_step_lines:
            lines.append(f"- {clean_display_text(step)}")
    elif workframe_state.next_step_status.value == "none":
        lines.append("Következő lépés: még nincs megalapozottan rögzítve.")
    lines.append(f"Hiányzó információ: {workframe_state.missing_info_status.value}.")
    lines.append(f"Nyitott kérdés: {workframe_state.open_question_status.value}.")
    lines.append(f"Döntési állapot: {workframe_state.decision_state.value}.")
    return lines





def _decision_readiness_lines(state: WorkframeState) -> list[str]:
    return [
        f"Hiányzó információ állapot: {state.missing_info_status.value}.",
        *(f"- {clean_display_text(line)}" for line in state.missing_info_lines),
        f"Nyitott kérdés állapot: {state.open_question_status.value}.",
        *(f"- {clean_display_text(line)}" for line in state.open_question_lines),
        f"Feltételezés/evidencia állapot: {state.assumption_status.value}.",
        *(f"- {clean_display_text(line)}" for line in state.assumption_lines),
        f"Döntési állapot: {state.decision_state.value}.",
        *(f"- {clean_display_text(line)}" for line in state.decision_lines),
        f"Bizonyíték-rés állapot: {state.evidence_gap_status.value}.",
        *(f"- {clean_display_text(line)}" for line in state.evidence_gap_lines),
    ]

def _history_lines(state: WorkframeState) -> list[str]:
    lines: list[str] = ["Korábbi állapot alapján:"]
    if state.objective_status.value == "active" and state.objective_text:
        lines.append(f"- Aktív cél: {clean_display_text(state.objective_text)}")
    else:
        lines.append("- Aktív cél: korábban sem volt biztosan rögzítve.")
    if state.blocker_text:
        lines.append(f"- Fő probléma: {clean_display_text(state.blocker_text)}")
    else:
        lines.append("- Fő probléma: nem volt egyértelműen rögzítve.")
    if state.next_step_lines:
        lines.append(f"- Következő lépés: {clean_display_text(state.next_step_lines[0])}")
    else:
        lines.append("- Következő lépés: nem volt megalapozottan rögzítve.")
    return lines


def _certainty_lines(state: WorkframeState) -> list[str]:
    sure: list[str] = []
    uncertain: list[str] = []
    if state.objective_status.value == "active" and state.objective_text:
        sure.append(f"Aktív cél: {clean_display_text(state.objective_text)}")
    elif state.objective_status.value == "proposed" and state.objective_text:
        uncertain.append(f"Cél-javaslat: {clean_display_text(state.objective_text)}")

    if state.blocker_status.value == "explicit" and state.blocker_text:
        sure.append(f"Blokker: {clean_display_text(state.blocker_text)}")
    elif state.blocker_text:
        uncertain.append(f"Lehetséges blokker: {clean_display_text(state.blocker_text)}")

    if state.next_step_status.value in {"grounded"} and state.next_step_lines:
        sure.append(f"Következő lépés: {clean_display_text(state.next_step_lines[0])}")
    elif state.next_step_lines:
        uncertain.append(f"Javasolt következő lépés: {clean_display_text(state.next_step_lines[0])}")

    lines = ["Ami biztos:"]
    lines.extend([f"• {item}" for item in sure] or ["• Nincs biztosan rögzített állítás."])
    lines.append("Ami nyitott:")
    lines.append("Ami inkább javaslat/feltételezés:")
    lines.extend([f"• {item}" for item in uncertain] or ["• Jelenleg nincs külön javaslatként megjelölt tétel."])
    return lines

def build_response_plan(
    context: RuntimeContext,
    interpretation: TurnInterpretation,
    recall: RecallResolution,
    strategy: AnswerStrategySelection,
    comparison_pack: ComparisonPack,
    objective: ObjectiveFrame,
    decomposition: DecompositionPlan,
    evidence_pack: EvidencePack,
    synthesis: SynthesisPlan,
    focus: ThreadFocusPack | None = None,
    followup_target: str | None = None,
    owner_identity: OwnerIdentityProfile | None = None,
    personal_memory: PersonalMemoryView | None = None,
    time_context: TimeContext | None = None,
    has_previous_thread: bool = False,
    workframe_state: WorkframeState | None = None,
    workframe_queries: object | None = None,
    workframe_updates: object | None = None,
    historical_workframe_state: WorkframeState | None = None,
    thread_weave_state: ThreadWeaveState | None = None,
    thread_weave_query_family: str | None = None,
) -> ResponsePlan:

    if thread_weave_state is not None and thread_weave_query_family is not None:
        if thread_weave_query_family == "thread_relation_query":
            lines = [f"Szál-kapcsolat: {thread_weave_state.relation.value}."]
            if thread_weave_state.main_thread_key:
                lines.append(f"Főszál: {clean_display_text(thread_weave_state.main_thread_key)}")
            if thread_weave_state.related_thread_key:
                lines.append(f"Kapcsolt szál: {clean_display_text(thread_weave_state.related_thread_key)}")
            if thread_weave_state.detour_thread_key:
                lines.append(f"Kitérő szál: {clean_display_text(thread_weave_state.detour_thread_key)}")
            return ResponsePlan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="thread_relation", lines=lines)], focus_used=focus is not None)

        if thread_weave_query_family == "conclusion_query":
            lines = [f"Konklúzió állapot: {thread_weave_state.conclusion_status.value}."]
            if thread_weave_state.conclusion_text:
                lines.append(f"Levonható tanulság: {clean_display_text(thread_weave_state.conclusion_text)}")
            else:
                lines.append("Még nincs elég erős, megalapozott konklúzió rögzítve.")
            return ResponsePlan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="conclusion", lines=lines)], focus_used=focus is not None)

        if thread_weave_query_family == "applicability_query":
            lines = [f"Alkalmazhatóság: {thread_weave_state.applicability_status.value}."]
            if thread_weave_state.conclusion_text:
                lines.append(f"Kiinduló konklúzió: {clean_display_text(thread_weave_state.conclusion_text)}")
            if thread_weave_state.applicability_reason:
                lines.append(clean_display_text(thread_weave_state.applicability_reason))
            return ResponsePlan(kind=ResponsePlanKind.UNCERTAINTY_LABELED, sections=[ResponsePlanSection(title="applicability", lines=lines)], focus_used=focus is not None)
    if interpretation.memory_query is not None and personal_memory is not None:
        return ResponsePlan(
            kind=ResponsePlanKind.STRUCTURED,
            sections=[ResponsePlanSection(title="explicit_memory", lines=_memory_query_lines(interpretation.memory_query, personal_memory))],
            focus_used=focus is not None,
        )

    if workframe_state is not None and workframe_queries is not None:
        if getattr(workframe_queries, "asks_current_objective", False):
            lines = [f"A mostani cél: {clean_display_text(workframe_state.objective_text)}."] if workframe_state.objective_status.value == "active" and workframe_state.objective_text else ["Most nincs egyértelműen rögzített aktív cél."]
            return ResponsePlan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="current_objective", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_queries, "asks_current_work", False):
            lines = [f"Mostani munkakeret: {workframe_state.workframe.value}."]
            if workframe_state.objective_status.value == "active" and workframe_state.objective_text:
                lines.append(f"Aktív cél: {clean_display_text(workframe_state.objective_text)}.")
            else:
                lines.append("Aktív cél még nincs egyértelműen rögzítve.")
            return ResponsePlan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="current_work", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_queries, "asks_current_posture", False):
            return ResponsePlan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="current_posture", lines=[f"Mostani munkakeret: {workframe_state.workframe.value}."])], focus_used=focus is not None)
        if getattr(workframe_queries, "asks_current_blocker", False):
            lines = [f"Mostani fő probléma: {clean_display_text(workframe_state.blocker_text)}."] if workframe_state.blocker_text else ["Most nincs egyértelműen rögzített fő probléma."]
            return ResponsePlan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="current_blocker", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_queries, "asks_current_next_step", False):
            lines = [f"Mostani következő lépés: {clean_display_text(workframe_state.next_step_lines[0])}"] if workframe_state.next_step_lines else ["Most nincs megalapozottan rögzített következő lépés."]
            return ResponsePlan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="current_next_step", lines=lines)], focus_used=focus is not None)
        if any((getattr(workframe_queries, "asks_history_objective", False), getattr(workframe_queries, "asks_history_blocker", False), getattr(workframe_queries, "asks_history_next_step", False))):
            state = historical_workframe_state or workframe_state
            return ResponsePlan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="historical_state", lines=_history_lines(state))], focus_used=focus is not None)
        if getattr(workframe_queries, "asks_certainty_split", False) or getattr(workframe_queries, "asks_next_step_certainty", False):
            return ResponsePlan(kind=ResponsePlanKind.UNCERTAINTY_LABELED, sections=[ResponsePlanSection(title="certainty_split", lines=_certainty_lines(workframe_state))], focus_used=focus is not None)
        if any((
            getattr(workframe_queries, "asks_missing_info", False),
            getattr(workframe_queries, "asks_open_questions", False),
            getattr(workframe_queries, "asks_assumptions", False),
            getattr(workframe_queries, "asks_decision_state", False),
            getattr(workframe_queries, "asks_evidence_gaps", False),
            getattr(workframe_queries, "asks_progress_block_reason", False),
        )):
            return ResponsePlan(kind=ResponsePlanKind.UNCERTAINTY_LABELED, sections=[ResponsePlanSection(title="decision_readiness", lines=_decision_readiness_lines(workframe_state))], focus_used=focus is not None)

    if interpretation.kind.value == "personal_entry" and interpretation.personal_entry is not None:
        signal = interpretation.personal_entry
        name = signal.owner_name or (owner_identity.owner_name if owner_identity is not None else None)
        display_name = f" {name}" if name else ""
        lines = _personal_entry_lines(signal.kind, display_name, signal.declared_focus, signal.declared_direction, time_context, workframe_state)
        return ResponsePlan(
            kind=ResponsePlanKind.PERSONAL_ENTRY,
            sections=[ResponsePlanSection(title="personal_entry", lines=lines)],
            focus_used=focus is not None,
        )


    if workframe_state is not None and workframe_updates is not None:
        if getattr(workframe_updates, "declares_work", False):
            lines = ["Rendben, ezt most aktív munkaszálként kezelem."]
            if workframe_state.objective_status.value == "active" and workframe_state.objective_text:
                lines.append(f"Aktív cél: {clean_display_text(workframe_state.objective_text)}.")
            else:
                lines.append("Aktív cél még nincs kimondva, ezt pontosíthatjuk.")
            return ResponsePlan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="workframe_update", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_updates, "declares_objective", False):
            if workframe_state.objective_status.value == "active" and workframe_state.objective_text:
                lines = [f"Rendben, az aktív célt rögzítem: {clean_display_text(workframe_state.objective_text)}."]
            else:
                lines = ["Értettem, célról beszélünk, de még pontosítás kell az aktív cél rögzítéséhez."]
            return ResponsePlan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="objective_update", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_updates, "declares_chat", False):
            lines = ["Rendben, most beszélgető módra váltunk."]
            if workframe_state.objective_status.value == "active" and workframe_state.objective_text:
                lines.append(f"A korábbi aktív célt megőrzöm háttér-kontinuitásnak: {clean_display_text(workframe_state.objective_text)}.")
            return ResponsePlan(kind=ResponsePlanKind.PERSONAL_ENTRY, sections=[ResponsePlanSection(title="chat_update", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_updates, "declares_blocker_explicit", False):
            lines = ["Rendben, ezt explicit fő blokkert állításként rögzítem."]
            if workframe_state.blocker_text:
                lines.append(f"Fő blokker: {clean_display_text(workframe_state.blocker_text)}.")
            if workframe_state.objective_status.value == "active" and workframe_state.objective_text:
                lines.append(f"Aktív cél változatlanul: {clean_display_text(workframe_state.objective_text)}.")
            return ResponsePlan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="blocker_update", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_updates, "hedged_blocker", False):
            lines = ["Ezt lehetséges blokkerként kezelem, még nem biztos állításként."]
            if workframe_state.blocker_text:
                lines.append(f"Jelölt blokker: {clean_display_text(workframe_state.blocker_text)}.")
            return ResponsePlan(kind=ResponsePlanKind.UNCERTAINTY_LABELED, sections=[ResponsePlanSection(title="hedged_blocker", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_updates, "hedged_objective", False):
            lines = ["Értem, ez egy lehetséges cél-javaslat, még nem végleges aktív cél."]
            if workframe_state.objective_text:
                lines.append(f"Javasolt cél: {clean_display_text(workframe_state.objective_text)}.")
            return ResponsePlan(kind=ResponsePlanKind.UNCERTAINTY_LABELED, sections=[ResponsePlanSection(title="hedged_objective", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_updates, "hedged_next_step", False):
            lines = ["Ezt javasolt következő lépésként kezelem, nem biztos döntésként."]
            if workframe_state.next_step_lines:
                lines.append(f"Lehetséges következő lépés: {clean_display_text(workframe_state.next_step_lines[0])}")
            return ResponsePlan(kind=ResponsePlanKind.UNCERTAINTY_LABELED, sections=[ResponsePlanSection(title="hedged_next_step", lines=lines)], focus_used=focus is not None)

    if interpretation.claim_capture:
        return ResponsePlan(
            kind=ResponsePlanKind.ORDINARY,
            sections=[ResponsePlanSection(title="claim_capture", lines=_claim_capture_lines(interpretation))],
            focus_used=focus is not None,
        )
    if workframe_state is not None and workframe_queries is not None and (getattr(workframe_queries, "asks_blocker", False) or getattr(workframe_queries, "asks_next_step", False) or getattr(workframe_queries, "asks_plan", False)):
        return ResponsePlan(
            kind=ResponsePlanKind.STRUCTURED,
            sections=[ResponsePlanSection(title="workframe", lines=_workframe_lines(workframe_state))],
            focus_used=focus is not None,
        )


    if interpretation.kind.value == "compare_previous" and not has_previous_thread:
        return ResponsePlan(
            kind=ResponsePlanKind.CLARIFICATION,
            sections=[ResponsePlanSection(title="compare_previous_missing", lines=["Még nincs előző szál, ezért nem tudok megalapozott összehasonlítást adni."])],
            focus_used=focus is not None,
        )

    if strategy.strategy == AnswerStrategy.CLARIFICATION:
        question = strategy.clarification_question.question if strategy.clarification_question else (recall.clarification_message or "Pontosíts kérlek.")
        return ResponsePlan(
            kind=ResponsePlanKind.CLARIFICATION,
            sections=[ResponsePlanSection(title="clarification", lines=[question])],
            focus_used=focus is not None,
        )

    if objective.kind.value == "clarify":
        return ResponsePlan(
            kind=ResponsePlanKind.CLARIFICATION,
            sections=[ResponsePlanSection(title="clarification", lines=["Pontosíts kérlek röviden, mit hasonlítsak vagy melyik szálra gondolsz."])],
            focus_used=focus is not None,
        )

    if strategy.strategy in {AnswerStrategy.RECALL_ANSWER, AnswerStrategy.RESUME_ANSWER} and recall.resolved and recall.snapshot is not None:
        limit = max(1, context.config.conversation.recall_line_limit)
        selected = recall.snapshot.snapshot_lines[-limit:]
        lead = "Röviden itt tartottunk:" if interpretation.kind.value.startswith("recall") else f"Visszahoztam a(z) {recall.snapshot.thread_key} szálat."
        lines = [lead]
        for line in selected:
            lines.append(f"• #{line.turn_index}: {clean_display_text(line.user_message)} → {clean_display_text(line.assistant_reply)}")
        followup = "Innen menjünk tovább?" if context.config.conversation.response_followup_enabled else None
        return ResponsePlan(
            kind=ResponsePlanKind.RECALL if interpretation.kind.value.startswith("recall") else ResponsePlanKind.RESUME,
            sections=[ResponsePlanSection(title="recall_summary", lines=lines)],
            followup_prompt=followup,
            focus_used=focus is not None,
        )

    if strategy.strategy in {AnswerStrategy.STRUCTURED_ANSWER, AnswerStrategy.UNCERTAINTY_LABELED_ANSWER}:
        sections = _synthesis_sections(synthesis)
        if not sections:
            sections = [ResponsePlanSection(title="ordinary", lines=["Rendben."])]
        kind = ResponsePlanKind.STRUCTURED if strategy.strategy != AnswerStrategy.UNCERTAINTY_LABELED_ANSWER else ResponsePlanKind.UNCERTAINTY_LABELED
        return ResponsePlan(kind=kind, sections=sections, focus_used=focus is not None)

    if strategy.strategy == AnswerStrategy.DIRECT_ANSWER:
        if _direct_should_use_synthesis(objective, decomposition, synthesis):
            sections = _synthesis_sections(synthesis)
            if sections:
                return ResponsePlan(
                    kind=ResponsePlanKind.STRUCTURED,
                    sections=sections,
                    focus_used=focus is not None,
                )
        if followup_target:
            lines = [f"Rendben, innen folytatjuk: {clean_display_text(followup_target)}"]
        elif interpretation.relative_time_terms:
            joined = ", ".join(interpretation.relative_time_terms)
            lines = [f"Értem az időhivatkozásokat ({clean_display_text(joined)}). Mondd, pontosan mire fókuszáljunk."]
        else:
            lines = ["Rendben."]
        return ResponsePlan(
            kind=ResponsePlanKind.ORDINARY,
            sections=[ResponsePlanSection(title="ordinary", lines=lines)],
            focus_used=focus is not None,
        )

    if strategy.strategy == AnswerStrategy.CORRECTION_REDIRECT:
        lines = ["Rendben, korrigálok és átirányítom a választ a kért irányra."]
        if "előző" in interpretation.kind.value or comparison_pack.winner_kind.value in {"correction_redirect", "resume"}:
            lines.append("Az előző szálhoz igazodva folytatom.")
        return ResponsePlan(
            kind=ResponsePlanKind.CORRECTION_REDIRECT,
            sections=[ResponsePlanSection(title="correction_redirect", lines=lines)],
            focus_used=focus is not None,
        )

    ordinary_lines: list[str] = []
    if followup_target:
        ordinary_lines.append(f"Rendben, innen folytatjuk: {clean_display_text(followup_target)}")
    return ResponsePlan(
        kind=ResponsePlanKind.ORDINARY,
        sections=[ResponsePlanSection(title="ordinary", lines=ordinary_lines)],
        focus_used=focus is not None,
    )
