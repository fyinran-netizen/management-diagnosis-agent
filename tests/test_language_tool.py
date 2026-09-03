from app.tools.understanding.language import detect_output_language


def test_detect_chinese_from_chinese_description():
    description = "我们公司最近增长放缓，请帮我做管理诊断。"

    result = detect_output_language(description)

    assert result == "zh"


def test_detect_english_from_english_description():
    description = "Our company growth is slowing down. Please diagnose the management problem."

    result = detect_output_language(description)

    assert result == "en"


def test_detect_english_when_user_explicitly_requests_english():
    description = "我们公司最近增长放缓，请用英文回答。"

    result = detect_output_language(description)

    assert result == "en"
