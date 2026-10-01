from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RecoveryResult:
    value: Any | None
    success: bool
    method: str | None = None
    actions: list[str] | None = None


class DuplicateJSONKeyError(ValueError):
    """Raised when a JSON object repeats a key instead of silently overwriting it."""


def loads_rejecting_duplicate_keys(text: str) -> Any:
    def object_pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise DuplicateJSONKeyError(key)
            value[key] = item
        return value

    return json.loads(text, object_pairs_hook=object_pairs_hook)


def _balanced_json_objects(text: str) -> list[str]:
    """Return complete object candidates without repairing their contents."""
    candidates: list[str] = []

    for start, char in enumerate(text):
        if char != "{":
            continue

        depth = 0
        in_string = False
        escaped = False

        for index in range(start, len(text)):
            current = text[index]

            if in_string:
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == '"':
                    in_string = False
                continue

            if current == '"':
                in_string = True
            elif current == "{":
                depth += 1
            elif current == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start:index + 1])
                    break

    return candidates


def _repair_stray_object_boundary_quotes(text: str) -> tuple[str, list[str]]:
    """Remove only an unambiguous stray quote between JSON array objects.

    Example:
        ... "source_items":[1,2]},"{"text":"next" ...
    becomes:
        ... "source_items":[1,2]},{"text":"next" ...

    The quote is removed only when:
    - we are currently outside a JSON string;
    - the previous non-whitespace structure is `},`;
    - the next non-whitespace character is `{`.

    No content inside JSON strings is modified.
    """
    output: list[str] = []
    actions: list[str] = []

    in_string = False
    escaped = False
    index = 0

    while index < len(text):
        current = text[index]

        if in_string:
            output.append(current)

            if escaped:
                escaped = False
            elif current == "\\":
                escaped = True
            elif current == '"':
                in_string = False

            index += 1
            continue

        if current == '"':
            previous = "".join(output).rstrip()

            next_index = index + 1
            while next_index < len(text) and text[next_index].isspace():
                next_index += 1

            if (
                previous.endswith("},")
                and next_index < len(text)
                and text[next_index] == "{"
            ):
                actions.append("remove_stray_object_boundary_quote")
                index += 1
                continue

            in_string = True
            output.append(current)
            index += 1
            continue

        output.append(current)
        index += 1

    return "".join(output), actions


def _normalize(value: Any) -> tuple[Any, list[str]] | None:
    """Normalize only unambiguous container/scalar representations."""
    if not isinstance(value, dict) or set(value) != {"sentences"}:
        return None

    sentences = value["sentences"]
    if not isinstance(sentences, list) or not sentences:
        return None

    normalized: list[dict[str, Any]] = []
    actions: list[str] = []

    for sentence in sentences:
        if (
            not isinstance(sentence, dict)
            or set(sentence) != {"text", "source_items"}
        ):
            return None

        text = sentence["text"]
        source_items = sentence["source_items"]

        if not isinstance(text, str) or not text.strip():
            return None

        if isinstance(source_items, int) and not isinstance(source_items, bool):
            source_items = [source_items]
            actions.append("source_items_scalar_to_list")
        elif isinstance(source_items, str) and source_items.strip().isdigit():
            source_items = [int(source_items.strip())]
            actions.append("source_items_numeric_string_to_list")

        if not isinstance(source_items, list):
            return None

        converted: list[int] = []

        for item in source_items:
            if isinstance(item, int) and not isinstance(item, bool):
                converted.append(item)
            elif isinstance(item, str) and item.strip().isdigit():
                converted.append(int(item.strip()))
                actions.append("source_item_numeric_string_to_int")
            else:
                return None

        normalized.append(
            {
                "text": text,
                "source_items": converted,
            }
        )

    return {"sentences": normalized}, actions


def recover_section_json(raw: str) -> RecoveryResult:
    """Recover a section only through deterministic structural repairs.

    This deliberately does not:
    - add missing semantic fields;
    - complete truncated JSON;
    - infer missing content;
    - invent citations.
    """
    if not isinstance(raw, str):
        return RecoveryResult(None, False)

    text = raw.strip()
    base_actions: list[str] = []

    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()

        if (
            len(lines) >= 3
            and lines[0].lstrip().startswith("```")
            and lines[-1].strip() == "```"
        ):
            text = "\n".join(lines[1:-1]).strip()
            base_actions.append("strip_code_fence")

    repaired_text, repair_actions = _repair_stray_object_boundary_quotes(text)

    candidate_specs: list[tuple[str, list[str]]] = [
        (text, list(base_actions)),
    ]

    if repaired_text != text:
        candidate_specs.append(
            (
                repaired_text,
                base_actions + repair_actions,
            )
        )

    for source_text, source_actions in list(candidate_specs):
        for candidate in _balanced_json_objects(source_text):
            if candidate == source_text:
                continue

            candidate_specs.append(
                (
                    candidate,
                    source_actions + ["extract_json_object"],
                )
            )

    seen: set[str] = set()

    for candidate, candidate_actions in candidate_specs:
        if candidate in seen:
            continue

        seen.add(candidate)

        try:
            parsed = loads_rejecting_duplicate_keys(candidate)
        except (TypeError, ValueError):
            continue

        normalized = _normalize(parsed)
        if normalized is None:
            continue

        value, normalize_actions = normalized

        return RecoveryResult(
            value=value,
            success=True,
            method="programmatic_json_recovery",
            actions=candidate_actions + normalize_actions,
        )

    return RecoveryResult(
        value=None,
        success=False,
        method="programmatic_json_recovery",
        actions=base_actions,
    )
