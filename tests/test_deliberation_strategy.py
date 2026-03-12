from syntaris.contracts.runtime import (
    RecallResolution,
    RecallTargetKind,
    RuntimeContext,
    AppConfig,
    AppPaths,
    ConversationConfig,
    LLMConfig,
    ReplyConfig,
    TurnInterpretation,
    TurnInterpretationKind,
    FollowupResolution,
)
from syntaris.orchestration.deliberation import assemble_deliberation_input
from syntaris.orchestration.answer_strategy import build_comparison_pack, select_answer_strategy


def _runtime() -> RuntimeContext:
    config = AppConfig(
        name="syntaris",
        environment="test",
        llm=LLMConfig(server_bin_path="", model_path=""),
        paths=AppPaths(data_dir="./.tmp", db_path="./.tmp/runtime.db"),
        reply=ReplyConfig(),
        conversation=ConversationConfig(),
    )
    return RuntimeContext(config=config)


def test_close_candidates_choose_clarification():
    runtime = _runtime()
    item = assemble_deliberation_input(
        message="nem ezt kérdeztem, mi a lényeg és mi legyen a következő?",
        interpretation=TurnInterpretation(kind=TurnInterpretationKind.ORDINARY),
        recall=RecallResolution(target=RecallTargetKind.NONE, resolved=False),
        followup=FollowupResolution(detected=False, resolved=False, ambiguous=False),
        has_focus=False,
        has_previous_thread=True,
    )

    pack = build_comparison_pack(runtime, item)
    selection = select_answer_strategy(runtime, pack)

    assert selection.strategy.value == "clarification"
    assert selection.clarification_need.needed is True


def test_clear_winner_does_not_clarify():
    runtime = _runtime()
    item = assemble_deliberation_input(
        message="mi a lényeg és mi legyen a következő?",
        interpretation=TurnInterpretation(kind=TurnInterpretationKind.ORDINARY),
        recall=RecallResolution(target=RecallTargetKind.NONE, resolved=False),
        followup=FollowupResolution(detected=False, resolved=False, ambiguous=False),
        has_focus=False,
        has_previous_thread=False,
    )

    pack = build_comparison_pack(runtime, item)
    selection = select_answer_strategy(runtime, pack)

    assert selection.strategy.value == "structured_answer"
    assert selection.clarification_need.needed is False
