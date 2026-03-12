from __future__ import annotations

from collections import Counter

from syntaris.contracts.runtime import (
    DecompositionPlan,
    EvidencePack,
    ObjectiveFrame,
    SupportLabel,
    SynthesisPlan,
    SynthesisSection,
)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def build_synthesis_plan(
    objective: ObjectiveFrame,
    decomposition: DecompositionPlan,
    evidence: EvidencePack,
) -> SynthesisPlan:
    if objective.kind.value == "clarify":
        return SynthesisPlan(
            sections=[SynthesisSection(key="clarification_need", lines=["Pontosítás kell a folytatáshoz."])],
            partial=True,
            support_distribution={"unresolved": 1},
        )

    unit_lines = [f"• {unit.prompt}" for unit in decomposition.units]
    sections = [
        SynthesisSection(
            key="core_point",
            lines=["Lényeg:", *unit_lines],
        )
    ]

    supported = _unique([i.detail for i in evidence.items if i.support == SupportLabel.SUPPORTED])
    weak = _unique([i.detail for i in evidence.items if i.support == SupportLabel.WEAK_SUPPORT])
    unresolved = _unique([i.detail for i in evidence.items if i.support == SupportLabel.UNRESOLVED])

    if supported:
        sections.append(SynthesisSection(key="supported_facts", lines=["Ami biztos:", *[f"• {item}" for item in supported[:3]]]))
    if weak:
        sections.append(SynthesisSection(key="uncertain_parts", lines=["Ami bizonytalanabb:", *[f"• {item}" for item in weak[:2]]]))
    if unresolved:
        sections.append(SynthesisSection(key="unresolved_parts", lines=["Ami nyitott:", *[f"• {item}" for item in unresolved[:2]]]))

    if any(unit.objective_kind.value == "compare" for unit in decomposition.units):
        current = next((item.detail for item in evidence.items if item.source == "current_thread"), "Mostani szál: nincs stabil előzmény")
        previous = next((item.detail for item in evidence.items if item.source == "previous_thread"), "Előző szál: nincs stabil előzmény")
        sections.append(
            SynthesisSection(
                key="comparison_result",
                lines=[
                    "Összevetés:",
                    f"• {current}",
                    f"• {previous}",
                ],
            )
        )

    if any(unit.objective_kind.value == "next_step" for unit in decomposition.units):
        sections.append(
            SynthesisSection(
                key="next_step",
                lines=["Következő lépés:", "• Röviden pontosítsd a hiányzó adatot, utána mehet az egyértelmű végrehajtás."],
            )
        )

    distribution = Counter(item.support.value for item in evidence.items)
    return SynthesisPlan(
        sections=sections,
        partial=bool(unresolved),
        support_distribution=dict(distribution),
    )
