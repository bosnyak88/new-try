from syntaris.contracts.runtime import ActiveConversationState, ThreadSummaryView
from syntaris.orchestration.routing import resolve_route_decision


def _active(previous_thread_key: str | None = None) -> ActiveConversationState:
    return ActiveConversationState(
        session_id=1,
        thread_id=1,
        thread_key="default",
        mode="chat",
        turn_count=0,
        last_turn_id=None,
        previous_thread_id=2 if previous_thread_key else None,
        previous_thread_key=previous_thread_key,
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


def test_resolve_route_previous_thread_phrase():
    decision = resolve_route_decision(
        "folytassuk az előzőt",
        _active(previous_thread_key="work"),
        [
            ThreadSummaryView(thread_id=1, thread_key="default", turn_count=0, last_turn_id=None, is_active=True),
            ThreadSummaryView(thread_id=2, thread_key="work", turn_count=0, last_turn_id=None, is_active=False),
        ],
    )
    assert decision.action.value == "switch_previous"
    assert decision.thread_key == "work"


def test_resolve_route_topic_shift_phrase():
    decision = resolve_route_decision(
        "más téma: admin",
        _active(),
        [ThreadSummaryView(thread_id=1, thread_key="default", turn_count=0, last_turn_id=None, is_active=True)],
    )
    assert decision.action.value == "create_and_switch"
    assert decision.thread_key == "admin"


def test_resolve_route_non_matching_defaults_continue():
    decision = resolve_route_decision(
        "beszéljünk valami másról",
        _active(),
        [ThreadSummaryView(thread_id=1, thread_key="default", turn_count=0, last_turn_id=None, is_active=True)],
    )
    assert decision.action.value == "continue_active"
    assert decision.thread_key == "default"


def test_resolve_route_suggestive_named_creates_pending():
    decision = resolve_route_decision(
        "folytassuk a worköt",
        _active(),
        [
            ThreadSummaryView(thread_id=1, thread_key="default", turn_count=0, last_turn_id=None, is_active=True),
            ThreadSummaryView(thread_id=2, thread_key="work", turn_count=0, last_turn_id=None, is_active=False),
        ],
    )
    assert decision.action.value == "propose_switch_existing"
    assert decision.pending_proposal is not None
    assert decision.pending_proposal.proposed_thread_key == "work"


def test_resolve_route_suggestive_previous_creates_pending():
    decision = resolve_route_decision(
        "mi volt az előző témában",
        _active(previous_thread_key="work"),
        [
            ThreadSummaryView(thread_id=1, thread_key="default", turn_count=0, last_turn_id=None, is_active=True),
            ThreadSummaryView(thread_id=2, thread_key="work", turn_count=0, last_turn_id=None, is_active=False),
        ],
    )
    assert decision.action.value == "propose_switch_previous"
    assert decision.pending_proposal is not None
    assert decision.pending_proposal.proposed_thread_key == "work"
