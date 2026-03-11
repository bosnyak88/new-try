from syntaris.contracts.runtime import ReplyConfig
from syntaris.reply.adapters import (
    DeterministicReplyAdapter,
    LlamaHttpReplyAdapter,
    ReplyAdapter,
    SafeReplyAdapter,
)


def build_reply_adapter(config: ReplyConfig) -> ReplyAdapter:
    fallback = DeterministicReplyAdapter()
    if config.backend == "llama-http" and config.live_url and config.live_model:
        return SafeReplyAdapter(preferred=LlamaHttpReplyAdapter(config), fallback=fallback)
    return fallback
