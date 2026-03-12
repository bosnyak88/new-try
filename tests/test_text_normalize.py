from syntaris.orchestration.text_normalize import normalize_hungarian_for_match, normalize_text


def test_normalize_text_repairs_mojibake_and_marks_repaired():
    result = normalize_text("az elÅzÅ szÃ¡l")
    assert result.canonical_text == "az előző szál"
    assert result.display_text == "az előző szál"
    assert result.repaired is True


def test_normalize_hungarian_for_match_keeps_clean_hungarian_stable():
    assert normalize_hungarian_for_match("hasonlítsd össze") == "hasonlitsd ossze"
    assert normalize_hungarian_for_match("hasonlÃ­tsd Ã¶ssze") == "hasonlitsd ossze"
