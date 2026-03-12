from syntaris.orchestration.text_normalize import (
    contains_degraded_text,
    flatten_generated_summary_text,
    normalize_hungarian_for_match,
    normalize_text,
)


def test_normalize_text_repairs_mojibake_and_marks_repaired():
    result = normalize_text("az elÅzÅ szÃ¡l")
    assert result.canonical_text == "az előző szál"
    assert result.display_text == "az előző szál"
    assert result.repaired is True


def test_normalize_hungarian_for_match_keeps_clean_hungarian_stable():
    assert normalize_hungarian_for_match("hasonlítsd össze") == "hasonlitsd ossze"
    assert normalize_hungarian_for_match("hasonlÃ­tsd Ã¶ssze") == "hasonlitsd ossze"


def test_normalize_text_repairs_observed_runtime_degraded_patterns():
    assert normalize_text("errĺ‘l").canonical_text == "erről"
    assert normalize_text("beszĂ©ljĂĽnk").canonical_text == "beszéljünk"
    assert normalize_text("elĺ‘zĺ‘").canonical_text == "előző"
    assert normalize_text("hasonlĂ­tsd").canonical_text == "hasonlítsd"


def test_contains_degraded_text_detects_observed_runtime_markers():
    assert contains_degraded_text("errĺ‘l") is True
    assert contains_degraded_text("beszĂ©ljĂĽnk") is True
    assert contains_degraded_text("elĺ‘zĺ‘") is True
    assert contains_degraded_text("hasonlĂ­tsd") is True
    assert contains_degraded_text("hasonlítsd") is False


def test_flatten_generated_summary_text_collapses_recursive_recall_lines():
    text = "Röviden itt tartottunk:\n• #1: hol tartottunk? → Röviden itt tartottunk:\nInnen menjünk tovább?"
    flattened = flatten_generated_summary_text(text)
    assert flattened.startswith("Röviden itt tartottunk:")
    assert "Innen menjünk tovább?" not in flattened
