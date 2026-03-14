from syntaris.contracts.runtime import ConversationConfig
from syntaris.orchestration.evidence_ingest import ingest_text_evidence


def test_ingest_large_console_text_extracts_error_warning_and_paths():
    message = """$ pytest -q
E   Traceback (most recent call last):
E     File \"src/app/main.py\", line 42, in <module>
E       raise RuntimeError('boom')
E   RuntimeError: boom
WARNING: deprecated flag used
exit code 1
"""
    ingest = ingest_text_evidence(message, ConversationConfig())

    assert ingest.ingest_status.value == "raw_text_evidence"
    assert ingest.chunked_evidence
    assert any(chunk.disposition.value == "kept_chunk" for chunk in ingest.chunked_evidence)
    assert any("RuntimeError" in line for line in ingest.extracted_key_lines)
    assert any("WARNING" in line for line in ingest.extracted_key_lines)
    assert ingest.evidence_summary


def test_ingest_short_text_keeps_no_evidence_state():
    ingest = ingest_text_evidence("rövid üzenet", ConversationConfig())
    assert ingest.ingest_status.value == "no_evidence_ingested"
    assert ingest.chunked_evidence == []
