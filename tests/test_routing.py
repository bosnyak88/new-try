from syntaris.contracts.runtime import ActiveConversationState, ThreadSummaryView
from syntaris.orchestration.routing import resolve_route_decision


def _active() -> ActiveConversationState:
    return ActiveConversationState(
        session_id=1,
        thread_id=1,
        thread_key="default",
        mode="chat",
        turn_count=0,
        last_turn_id=None,
    )


def test_resolve_route_create_phrase():
    decision = resolve_route_decision(
        "új szál: Work",
        _active(),
        [ThreadSummaryView(thread_id=1, thread_key="default", turn_count=0, last_turn_id=None, is_active=True)],
    )
    assert decision.action.value == "create_and_switch"
    assert decision.thread_key == "work"


def test_resolve_route_return_existing():
    decision = resolve_route_decision(
        "vissza a work szálra",
        _active(),
        [
            ThreadSummaryView(thread_id=1, thread_key="default", turn_count=0, last_turn_id=None, is_active=True),
            ThreadSummaryView(thread_id=2, thread_key="work", turn_count=0, last_turn_id=None, is_active=False),
        ],
    )
    assert decision.action.value == "switch_existing"
    assert decision.thread_key == "work"


def test_resolve_route_non_matching_defaults_continue():
    decision = resolve_route_decision(
        "beszéljünk valami másról",
        _active(),
        [ThreadSummaryView(thread_id=1, thread_key="default", turn_count=0, last_turn_id=None, is_active=True)],
    )
    assert decision.action.value == "continue_active"
    assert decision.thread_key == "default"
