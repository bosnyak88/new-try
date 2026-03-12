from __future__ import annotations

from syntaris.contracts.runtime import AnswerStrategySelection, ObjectiveFrame, ObjectiveKind


_KEYWORD_MAP: list[tuple[tuple[str, ...], ObjectiveKind]] = [
    (("hasonlítsd", "összehasonl", "különbség"), ObjectiveKind.COMPARE),
    (("lényeg", "röviden", "összefoglal"), ObjectiveKind.SUMMARIZE),
    (("következő", "mit tegyek", "most teendő", "mit kell most"), ObjectiveKind.NEXT_STEP),
    (("fő probléma", "mi a probléma", "mi gond"), ObjectiveKind.DIAGNOSE),
    (("mi biztos", "feltételezés", "bizonytalan"), ObjectiveKind.STATUS_CHECK),
    (("dönts", "melyik", "válassz"), ObjectiveKind.DECIDE),
    (("magyarázd", "miért"), ObjectiveKind.EXPLAIN),
]


def frame_objective(message: str, strategy: AnswerStrategySelection) -> ObjectiveFrame:
    lowered = message.strip().lower()
    matched: list[ObjectiveKind] = []

    for keywords, kind in _KEYWORD_MAP:
        if any(keyword in lowered for keyword in keywords):
            matched.append(kind)

    unique = list(dict.fromkeys(matched))
    is_multi_part = " és " in lowered or len(unique) > 1

    if strategy.strategy.value == "clarification":
        return ObjectiveFrame(
            kind=ObjectiveKind.CLARIFY,
            is_multi_part=False,
            objective_text="A kérés nem elég egyértelmű, rövid pontosítás szükséges.",
            secondary_kinds=[],
        )

    if ("hasonlítsd össze" in lowered or "összehasonl" in lowered) and ("előző" not in lowered and "mostani" not in lowered):
        return ObjectiveFrame(
            kind=ObjectiveKind.CLARIFY,
            is_multi_part=False,
            objective_text="Az összehasonlítás célpontja nem egyértelmű.",
            secondary_kinds=[],
        )

    if is_multi_part or strategy.strategy.value == "structured_answer":
        primary = unique[0] if unique else ObjectiveKind.MIXED_MULTI_PART
        secondary = unique[1:] if len(unique) > 1 else ([ObjectiveKind.NEXT_STEP] if " és " in lowered else [])
        return ObjectiveFrame(
            kind=ObjectiveKind.MIXED_MULTI_PART,
            is_multi_part=True,
            objective_text="A kérés több részből áll, rendezett bontás szükséges.",
            secondary_kinds=[primary, *secondary],
        )

    if unique:
        return ObjectiveFrame(
            kind=unique[0],
            is_multi_part=False,
            objective_text="A felhasználó egy fő célt kér.",
            secondary_kinds=unique[1:],
        )

    return ObjectiveFrame(
        kind=ObjectiveKind.EXPLAIN,
        is_multi_part=False,
        objective_text="Általános magyarázó válasz szükséges.",
        secondary_kinds=[],
    )
