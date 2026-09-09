from app.tools.understanding import understand_query


def test_detects_english_from_raw_query():
    result = understand_query("Our company growth is slowing down.")

    assert result["language"] == "en"


def test_explicit_english_request_is_preserved():
    result = understand_query("Please answer in English.")

    assert result["language"] == "en"
