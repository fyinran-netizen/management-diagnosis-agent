from __future__ import annotations

import re


def detect_output_language(description: str) -> str:
    """
    Detect the preferred output language from the user's raw description.

    Rules:
    1. If the user explicitly asks for English or Chinese, follow that.
    2. Otherwise, infer from the dominant language in the description.
    """
    text = description.lower()

    english_markers = [
        "answer in english",
        "reply in english",
        "respond in english",
        "use english",
        "用英文",
        "英文回答",
        "英语回答",
    ]

    chinese_markers = [
        "用中文",
        "中文回答",
        "用汉语",
        "汉语回答",
        "answer in chinese",
        "reply in chinese",
    ]

    if any(marker in text for marker in english_markers):
        return "en"

    if any(marker in text for marker in chinese_markers):
        return "zh"

    chinese_chars = re.findall(r"[\u4e00-\u9fff]", description)
    english_words = re.findall(r"[a-zA-Z]{2,}", description)

    if len(chinese_chars) >= len(english_words):
        return "zh"

    return "en"