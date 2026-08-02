from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.llm.ollama_client import get_ollama_config


KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "private_knowledge_base"
INDEX_PATH = KNOWLEDGE_DIR / "_index.json"
OUTPUT_PATH = KNOWLEDGE_DIR / "semantic_metadata.jsonl"

DIAGNOSIS_TAGS = [
    "customer_value_misalignment",
    "opportunity_neglect",
    "strategy_execution_gap",
    "metrics_misalignment",
    "control_over_self_drive",
    "short_term_decision_bias",
    "entrepreneurial_leadership_gap",
    "general_management_diagnosis",
]

MAX_LIST_ITEMS = 8
MAX_ANCHORS = 4


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_existing_source_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()

    source_ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        source_id = item.get("source_id")
        if isinstance(source_id, str):
            source_ids.add(source_id)
    return source_ids


def strip_front_matter(markdown: str) -> str:
    text = markdown.replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---\n"):
        return text.strip()

    end = text.find("\n---", 4)
    if end == -1:
        return text.strip()

    return text[end + len("\n---") :].strip()


def clean_content(markdown_body: str) -> str:
    text = markdown_body.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]

    cleaned_lines: list[str] = []
    blank = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not blank:
                cleaned_lines.append("")
            blank = True
            continue
        blank = False
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def build_prompt(entry: dict[str, Any], cleaned_content: str) -> list[dict[str, str]]:
    schema = {
        "summary": "80-150 Chinese characters. Explain the management idea in this chunk.",
        "extracted": {
            "concept_keywords": ["terms explicitly supported by the chunk"],
            "method_keywords": ["methods or frameworks explicitly supported by the chunk"],
            "named_entities": ["people, companies, books, or named frameworks explicitly mentioned"],
        },
        "inferred": {
            "symptom_keywords": ["management symptoms reasonably inferred from the chunk"],
            "diagnosis_tags": DIAGNOSIS_TAGS,
            "recommended_methods": ["practical methods reasonably inferred from the chunk"],
        },
        "evidence_anchors": [
            {
                "label": "short label for the evidence",
                "anchor_text": "short exact substring copied from cleaned_content",
            }
        ],
        "metadata_confidence": 0.0,
    }

    return [
        {
            "role": "system",
            "content": (
                "You extract structured semantic metadata for a Chinese management knowledge base. "
                "Return valid JSON only. Do not include markdown fences or explanations. "
                "Separate extracted facts from inferred diagnosis information. "
                "Use concise, domain-specific Chinese keywords. "
                "Do not invent company facts. "
                "For evidence_anchors, anchor_text must be an exact short substring from cleaned_content."
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"source_id: {entry.get('source_id')}\n"
                f"chapter_title: {entry.get('chapter_title')}\n"
                f"section_title: {entry.get('section_title')}\n"
                f"title: {entry.get('title')}\n\n"
                f"Allowed diagnosis_tags:\n{DIAGNOSIS_TAGS}\n\n"
                f"Output JSON schema example:\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n\n"
                "Rules:\n"
                "- summary must be specific to this chunk, not generic.\n"
                "- extracted.concept_keywords and extracted.method_keywords must be directly supported by the text.\n"
                "- inferred.symptom_keywords and inferred.recommended_methods may be inferred, but must stay grounded.\n"
                "- inferred.diagnosis_tags must only use allowed tags.\n"
                f"- Use at most {MAX_LIST_ITEMS} items per keyword list.\n"
                f"- Use at most {MAX_ANCHORS} evidence anchors.\n"
                "- evidence_anchors.anchor_text must be copied exactly from cleaned_content and should be short.\n"
                "- If unsure, use an empty array.\n\n"
                f"cleaned_content:\n{cleaned_content}"
            ),
        },
    ]


def call_ollama(messages: list[dict[str, str]], model: str | None, timeout: int) -> str:
    base_url, default_model = get_ollama_config()
    payload = {
        "model": model or default_model,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "num_predict": 1200,
            "num_ctx": 8192,
        },
    }
    response = requests.post(f"{base_url}/api/chat", json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    content = data.get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError(f"Ollama response did not contain message content: {data}")
    return content.strip()


def parse_json_content(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.S)
        if not match:
            raise
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise ValueError("LLM output JSON is not an object.")
    return parsed


def ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value[:MAX_LIST_ITEMS]
    return []


def ensure_string_list(value: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in ensure_list(value):
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def normalize_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    extracted = raw.get("extracted") if isinstance(raw.get("extracted"), dict) else {}
    inferred = raw.get("inferred") if isinstance(raw.get("inferred"), dict) else {}

    tags = [
        tag
        for tag in ensure_string_list(inferred.get("diagnosis_tags"))
        if tag in DIAGNOSIS_TAGS
    ]

    confidence = raw.get("metadata_confidence", 0.0)
    try:
        confidence_float = float(confidence)
    except (TypeError, ValueError):
        confidence_float = 0.0
    confidence_float = max(0.0, min(1.0, confidence_float))

    return {
        "summary": str(raw.get("summary", "")).strip(),
        "extracted": {
            "concept_keywords": ensure_string_list(extracted.get("concept_keywords")),
            "method_keywords": ensure_string_list(extracted.get("method_keywords")),
            "named_entities": ensure_string_list(extracted.get("named_entities")),
        },
        "inferred": {
            "symptom_keywords": ensure_string_list(inferred.get("symptom_keywords")),
            "diagnosis_tags": tags,
            "recommended_methods": ensure_string_list(inferred.get("recommended_methods")),
        },
        "evidence_anchors": ensure_list(raw.get("evidence_anchors"))[:MAX_ANCHORS],
        "metadata_confidence": confidence_float,
    }


def anchors_to_spans(anchors: list[Any], content: str) -> tuple[list[dict[str, Any]], list[str]]:
    spans: list[dict[str, Any]] = []
    issues: list[str] = []
    cursor = 0

    for anchor in anchors:
        if not isinstance(anchor, dict):
            issues.append("evidence anchor is not an object")
            continue
        label = str(anchor.get("label", "")).strip()
        anchor_text = str(anchor.get("anchor_text", "")).strip()
        if not label or not anchor_text:
            issues.append("evidence anchor missing label or anchor_text")
            continue
        index = content.find(anchor_text, cursor)
        if index == -1:
            index = content.find(anchor_text)
        if index == -1:
            issues.append(f"anchor not found: {label}")
            continue
        end = index + len(anchor_text)
        spans.append(
            {
                "label": label,
                "start": index,
                "end": end,
            }
        )
        cursor = end

    return spans, issues


def build_record(
    entry: dict[str, Any],
    metadata: dict[str, Any],
    cleaned_content: str,
    model_name: str,
) -> dict[str, Any]:
    evidence_spans, evidence_issues = anchors_to_spans(
        metadata.pop("evidence_anchors", []),
        cleaned_content,
    )

    validation_issues: list[str] = []
    if not metadata["summary"]:
        validation_issues.append("summary is empty")
    if not metadata["inferred"]["diagnosis_tags"]:
        validation_issues.append("diagnosis_tags is empty")
    validation_issues.extend(evidence_issues)

    status = "pending" if not validation_issues else "needs_edit"
    confidence = metadata.pop("metadata_confidence", 0.0)

    return {
        "source_id": entry["source_id"],
        "summary": metadata["summary"],
        "extracted": metadata["extracted"],
        "inferred": metadata["inferred"],
        "evidence_spans": evidence_spans,
        "quality": {
            "cleaned": True,
            "encoding_ok": True,
            "has_evidence": bool(evidence_spans),
            "metadata_confidence": confidence,
            "validation_issues": validation_issues,
        },
        "review": {
            "status": status,
            "notes": "",
        },
        "generation": {
            "model": model_name,
            "created_at": datetime.now(UTC).isoformat(),
            "content_char_count": len(cleaned_content),
        },
    }


def select_entries(
    entries: list[dict[str, Any]],
    *,
    source_id: str | None,
    limit: int | None,
    include_preface: bool,
    existing_source_ids: set[str],
    overwrite: bool,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []

    for entry in entries:
        current_source_id = entry.get("source_id")
        if not isinstance(current_source_id, str):
            continue
        if source_id and current_source_id != source_id:
            continue
        if not include_preface and entry.get("chapter_id") == "ch00":
            continue
        if not overwrite and current_source_id in existing_source_ids:
            continue
        selected.append(entry)
        if limit is not None and len(selected) >= limit:
            break

    return selected


def print_review(records: list[dict[str, Any]]) -> None:
    for record in records:
        extracted = record["extracted"]
        inferred = record["inferred"]
        quality = record["quality"]
        print("=" * 80)
        print(f"source_id: {record['source_id']}")
        print(f"review: {record['review']['status']} | confidence: {quality['metadata_confidence']:.2f}")
        if quality["validation_issues"]:
            print(f"issues: {quality['validation_issues']}")
        print(f"summary: {record['summary']}")
        print(f"concept_keywords: {', '.join(extracted['concept_keywords'])}")
        print(f"method_keywords: {', '.join(extracted['method_keywords'])}")
        print(f"symptom_keywords: {', '.join(inferred['symptom_keywords'])}")
        print(f"diagnosis_tags: {', '.join(inferred['diagnosis_tags'])}")
        print(f"recommended_methods: {', '.join(inferred['recommended_methods'])}")
        print(f"evidence_spans: {len(record['evidence_spans'])}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate semantic metadata for private RAG chunks.")
    parser.add_argument("--index", type=Path, default=INDEX_PATH)
    parser.add_argument("--knowledge-dir", type=Path, default=KNOWLEDGE_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--source-id")
    parser.add_argument("--model")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--include-preface", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()

    entries = read_json(args.index)
    if not isinstance(entries, list):
        raise ValueError(f"Index must contain a list: {args.index}")

    existing_source_ids = set() if args.overwrite else load_existing_source_ids(args.output)
    selected = select_entries(
        entries,
        source_id=args.source_id,
        limit=args.limit,
        include_preface=args.include_preface,
        existing_source_ids=existing_source_ids,
        overwrite=args.overwrite,
    )

    if not selected:
        print("No entries selected.")
        return

    _, default_model = get_ollama_config()
    model_name = args.model or default_model
    records: list[dict[str, Any]] = []

    for index, entry in enumerate(selected, start=1):
        source_id = entry["source_id"]
        chunk_path = args.knowledge_dir / entry["path"]
        markdown = chunk_path.read_text(encoding="utf-8")
        cleaned_content = clean_content(strip_front_matter(markdown))
        print(f"[{index}/{len(selected)}] generating {source_id} ...", flush=True)

        messages = build_prompt(entry, cleaned_content)
        try:
            content = call_ollama(messages, args.model, args.timeout)
            raw = parse_json_content(content)
            metadata = normalize_metadata(raw)
            record = build_record(entry, metadata, cleaned_content, model_name)
        except Exception as exc:
            record = {
                "source_id": source_id,
                "summary": "",
                "extracted": {
                    "concept_keywords": [],
                    "method_keywords": [],
                    "named_entities": [],
                },
                "inferred": {
                    "symptom_keywords": [],
                    "diagnosis_tags": [],
                    "recommended_methods": [],
                },
                "evidence_spans": [],
                "quality": {
                    "cleaned": True,
                    "encoding_ok": True,
                    "has_evidence": False,
                    "metadata_confidence": 0.0,
                    "validation_issues": [f"{type(exc).__name__}: {exc}"],
                },
                "review": {
                    "status": "needs_edit",
                    "notes": "",
                },
                "generation": {
                    "model": model_name,
                    "created_at": datetime.now(UTC).isoformat(),
                    "content_char_count": len(cleaned_content),
                },
            }
        records.append(record)

    if not args.no_write:
        if args.overwrite:
            retained: list[dict[str, Any]] = []
            if args.output.exists():
                selected_ids = {record["source_id"] for record in records}
                for line in args.output.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    if item.get("source_id") not in selected_ids:
                        retained.append(item)
            write_jsonl(args.output, retained + records)
        else:
            append_jsonl(args.output, records)
        print(f"wrote: {args.output}")

    print_review(records)


if __name__ == "__main__":
    main()
