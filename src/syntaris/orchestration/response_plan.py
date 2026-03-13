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


def _personal_entry_lines(signal: PersonalEntryKind, display_name: str, focus: str | None, direction: str | None, time_context: TimeContext | None = None) -> list[str]:
    if signal == PersonalEntryKind.GREETING:
        greet = _daypart_greeting(time_context.daypart.value) if time_context is not None else "Szia"
        return [f"{greet}{display_name}. Miben segítsek most?"]
    if signal == PersonalEntryKind.SELF_INTRO:
        return [f"Szia{display_name}. Örülök, hogy így mutatkoztál be — miben induljunk el most?"]
    if signal == PersonalEntryKind.OWNER_FRAMING:
        return [f"Szia{display_name}. Értem, hogy te tervezed és fejleszted a rendszert. Mi legyen a mai konkrét fókusz?"]
    if signal == PersonalEntryKind.PERSONAL_CHAT_INTAKE:
        return [f"Rendben{display_name}, beszélgessünk. Mi az, ami most leginkább foglalkoztat?"]
    if signal == PersonalEntryKind.CONCRETE_HELP_INTAKE:
        return ["Rendben, menjünk konkrétan ezen: írd le röviden, hol akadtál el, és onnan lépünk tovább."]
    if signal == PersonalEntryKind.FOCUS_SETTING_INTAKE:
        if focus:
            return [f"Jó irány, a mai fókusz legyen {clean_display_text(focus)}. Mi legyen az első konkrét lépés?"]
        if direction:
            return [f"Rendben, most a {clean_display_text(direction)} irányra állunk rá. Melyik konkrét ponttal kezdjük?"]
        return ["Rendben, fókuszra álltunk. Melyik konkrét ponttal kezdjük?"]
    if signal == PersonalEntryKind.RESUME_INTAKE:
        return ["Oké, vegyük fel innen a fonalat. Melyik részről folytassuk először?"]
    if signal == PersonalEntryKind.RETURN_ENTRY:
        gap = _gap_phrase(time_context.gap_kind.value, time_context.gap_minutes) if time_context is not None else None
        base = f"Jó újra itt{display_name}."
        if gap:
            return [f"{base} {gap} Mivel folytassuk?"]
        return [f"{base} Mivel folytassuk?"]
    return ["Rendben, visszakapcsoltam ide. Folytassuk innen — most beszélgessünk, vagy oldjunk meg egy konkrét feladatot?"]


def _memory_query_lines(query: MemoryQueryKind, memory: PersonalMemoryView) -> list[str]:
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
        if memory.current_focus:
            return [f"A mostani fókusznak ezt mondtad: {clean_display_text(memory.current_focus)}."]
        if memory.current_direction:
            return [f"Most erre az irányra álltunk: {clean_display_text(memory.current_direction)}."]
        return ["Mostani fókuszt még nem állítottál be explicit módon."]

    lines: list[str] = []
    if memory.owner_name:
        lines.append(f"• Név (explicit): {memory.owner_name}")
    if memory.owner_relation:
        relation = "creator" if memory.owner_relation == "creator" else memory.owner_relation
        lines.append(f"• Kapcsolat (explicit): {relation}")
    if memory.system_role:
        lines.append(f"• Szerep (explicit): {memory.system_role}")
    if memory.current_focus:
        lines.append(f"• Mostani fókusz (szál-szintű): {clean_display_text(memory.current_focus)}")
    elif memory.current_direction:
        lines.append(f"• Mostani irány (szál-szintű): {clean_display_text(memory.current_direction)}")
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
        return [f"Rögzítettem a mostani irányt: {clean_display_text(by_kind[ClaimKind.CURRENT_DIRECTION])}."]

    return ["Rögzítettem az explicit állításodat."]


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
) -> ResponsePlan:
    if interpretation.memory_query is not None and personal_memory is not None:
        return ResponsePlan(
            kind=ResponsePlanKind.STRUCTURED,
            sections=[ResponsePlanSection(title="explicit_memory", lines=_memory_query_lines(interpretation.memory_query, personal_memory))],
            focus_used=focus is not None,
        )

    if interpretation.kind.value == "personal_entry" and interpretation.personal_entry is not None:
        signal = interpretation.personal_entry
        name = signal.owner_name or (owner_identity.owner_name if owner_identity is not None else None)
        display_name = f" {name}" if name else ""
        lines = _personal_entry_lines(signal.kind, display_name, signal.declared_focus, signal.declared_direction, time_context)
        return ResponsePlan(
            kind=ResponsePlanKind.PERSONAL_ENTRY,
            sections=[ResponsePlanSection(title="personal_entry", lines=lines)],
            focus_used=focus is not None,
        )

    if interpretation.claim_capture:
        return ResponsePlan(
            kind=ResponsePlanKind.ORDINARY,
            sections=[ResponsePlanSection(title="claim_capture", lines=_claim_capture_lines(interpretation))],
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
