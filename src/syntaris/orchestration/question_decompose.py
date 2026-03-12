from __future__ import annotations
from syntaris.orchestration.text_normalize import normalize_hungarian_for_match

from syntaris.contracts.runtime import DecompositionPlan, ObjectiveFrame, ObjectiveKind, ReasoningUnit


def _unit(unit_id: str, prompt: str, kind: ObjectiveKind, priority: int) -> ReasoningUnit:
    return ReasoningUnit(unit_id=unit_id, prompt=prompt, objective_kind=kind, priority=priority)


def build_decomposition_plan(message: str, objective: ObjectiveFrame) -> DecompositionPlan:
    lowered = message.strip().lower()
    normalized_hu = normalize_hungarian_for_match(message)

    if objective.kind == ObjectiveKind.CLARIFY:
        return DecompositionPlan(units=[_unit("u1", "Pontosítandó cél", ObjectiveKind.CLARIFY, 1)], multi_part=False)

    units: list[ReasoningUnit] = []

    if "lényeg" in lowered:
        units.append(_unit("u1", "Mi a kérés lényege?", ObjectiveKind.SUMMARIZE, 1))
    if "következő" in lowered or "mit kell most" in lowered or "mit tegy" in lowered:
        units.append(_unit(f"u{len(units)+1}", "Mi legyen a következő lépés?", ObjectiveKind.NEXT_STEP, len(units) + 1))
    if "biztos" in lowered or "feltételezés" in lowered:
        units.append(_unit(f"u{len(units)+1}", "Mi támasztható alá biztosan?", ObjectiveKind.STATUS_CHECK, len(units) + 1))
        units.append(_unit(f"u{len(units)+1}", "Mi marad feltételezés vagy nyitott pont?", ObjectiveKind.STATUS_CHECK, len(units) + 1))
    if "fő probléma" in lowered or "mi a probléma" in lowered:
        units.append(_unit(f"u{len(units)+1}", "Mi a fő probléma?", ObjectiveKind.DIAGNOSE, len(units) + 1))
    if (
        "hasonlítsd össze" in lowered
        or "össze" in lowered
        or "hasonlitsd ossze" in normalized_hu
        or ("hasonlã" in lowered and "ssze" in lowered)
    ):
        units.append(_unit(f"u{len(units)+1}", "Miben egyezik és tér el a két célzott szál?", ObjectiveKind.COMPARE, len(units) + 1))

    if not units:
        units.append(_unit("u1", "Közvetlen válasz a kérésre", objective.kind, 1))

    return DecompositionPlan(units=units, multi_part=len(units) > 1)
