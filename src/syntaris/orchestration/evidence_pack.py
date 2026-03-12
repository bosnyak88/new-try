from __future__ import annotations

from syntaris.orchestration.text_normalize import clean_display_text
from syntaris.contracts.runtime import (
    DecompositionPlan,
    EvidenceItem,
    EvidencePack,
    FollowupResolution,
    RecallResolution,
    SupportLabel,
    ThreadFocusPack,
)


def build_evidence_pack(
    message: str,
    decomposition: DecompositionPlan,
    recall: RecallResolution,
    focus: ThreadFocusPack | None,
    followup: FollowupResolution,
    current_thread_summary: str | None = None,
    previous_thread_summary: str | None = None,
) -> EvidencePack:
    items: list[EvidenceItem] = []

    for unit in decomposition.units:
        unit_items: list[EvidenceItem] = [
            EvidenceItem(
                unit_id=unit.unit_id,
                source="current_message",
                detail=clean_display_text(message),
                support=SupportLabel.SUPPORTED,
            )
        ]

        if focus and focus.focus_lines:
            unit_items.append(
                EvidenceItem(
                    unit_id=unit.unit_id,
                    source="focus_pack",
                    detail=clean_display_text(focus.focus_lines[0].text),
                    support=SupportLabel.WEAK_SUPPORT,
                )
            )

        if recall.resolved and recall.snapshot and recall.snapshot.snapshot_lines:
            line = recall.snapshot.snapshot_lines[-1]
            unit_items.append(
                EvidenceItem(
                    unit_id=unit.unit_id,
                    source="recall_snapshot",
                    detail=f"#{line.turn_index}: {clean_display_text(line.user_message)} → {clean_display_text(line.assistant_reply)}",
                    support=SupportLabel.SUPPORTED,
                )
            )

        if followup.resolved and followup.target_line:
            unit_items.append(
                EvidenceItem(
                    unit_id=unit.unit_id,
                    source="followup_target",
                    detail=clean_display_text(followup.target_line),
                    support=SupportLabel.SUPPORTED,
                )
            )

        if unit.objective_kind.value == "compare":
            unit_items.append(
                EvidenceItem(
                    unit_id=unit.unit_id,
                    source="current_thread",
                    detail=f"Mostani szál: {clean_display_text(current_thread_summary) if current_thread_summary else 'nincs stabil előzmény'}",
                    support=SupportLabel.SUPPORTED if current_thread_summary else SupportLabel.WEAK_SUPPORT,
                )
            )
            unit_items.append(
                EvidenceItem(
                    unit_id=unit.unit_id,
                    source="previous_thread",
                    detail=f"Előző szál: {clean_display_text(previous_thread_summary) if previous_thread_summary else 'nincs stabil előzmény'}",
                    support=SupportLabel.SUPPORTED if previous_thread_summary else SupportLabel.WEAK_SUPPORT,
                )
            )
            if not current_thread_summary or not previous_thread_summary:
                unit_items.append(
                    EvidenceItem(
                        unit_id=unit.unit_id,
                        source="support_gap",
                        detail="Az összehasonlításhoz hiányzik az egyik szál stabil kontextusa.",
                        support=SupportLabel.UNRESOLVED,
                    )
                )

        if unit.objective_kind.value in {"status_check", "diagnose", "next_step"} and len(unit_items) <= 2:
            unit_items.append(
                EvidenceItem(
                    unit_id=unit.unit_id,
                    source="support_gap",
                    detail="Nincs elég célzott kontextus ehhez a részhez.",
                    support=SupportLabel.UNRESOLVED,
                )
            )

        items.extend(unit_items)

    return EvidencePack(items=items)
