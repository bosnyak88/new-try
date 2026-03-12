from __future__ import annotations

from syntaris.contracts.runtime import ResponsePlan


def render_response_plan(plan: ResponsePlan) -> str:
    parts: list[str] = []
    for section in plan.sections:
        parts.extend(section.lines)
    if plan.followup_prompt:
        parts.append(plan.followup_prompt)
    return "\n".join([p for p in parts if p]).strip() or "Rendben."
