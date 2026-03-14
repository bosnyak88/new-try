from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
from syntaris.orchestration.talk import talk_once


def _runtime(tmp_path) -> RuntimeContext:
    return RuntimeContext(
        config=AppConfig(
            name="syntaris",
            environment="test",
            llm=LLMConfig(server_bin_path="", model_path=""),
            paths=AppPaths(data_dir=str(tmp_path / "data"), db_path=str(tmp_path / "data" / "runtime.db")),
            reply=ReplyConfig(),
            conversation=ConversationConfig(),
        )
    )


def test_entry_and_continue_prompts_are_not_cold_fallback(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="az én nevem Árpi"))
    talk_once(runtime, TalkRequest(message="a mai fókusz a jelenlét baseline"))

    for prompt in ["folytassuk innen", "na folytassuk", "vissza syntaris", "hol tartottunk?"]:
        out = talk_once(runtime, TalkRequest(message=prompt))
        text = out.turn.assistant_reply.lower()
        assert out.turn.assistant_reply.strip() != "Rendben."
        assert any(term in text for term in ("folyt", "tart", "szál", "irány", "fókusz"))
