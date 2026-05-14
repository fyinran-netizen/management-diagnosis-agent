from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


SOURCE_PATH = Path("source_docs/raw_converted.md")
OUTPUT_DIR = Path("data/private_knowledge_base")
TARGET_CHARS = 900
MAX_CHARS = 1200
OVERLAP_CHARS = 180

H1_RE = re.compile(r"^# (.+?)\s*$")
H2_RE = re.compile(r"^## (.+?)\s*$")
H3_RE = re.compile(r"^### (.+?)\s*$")
TOC_LINK_RE = re.compile(r"\[\d+\]\([^)]*\)\s*$")
DOT_LEADER_RE = re.compile(r".*\.{2,}\s*\d+\s*$")
SENTENCE_RE = re.compile(r"([^.!?\u3002\uff01\uff1f\uff1b;]+[.!?\u3002\uff01\uff1f\uff1b;]?)")
CHAPTER_NUMBER_RE = re.compile(r"^\s*\u7b2c([0-9\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u767e]+)\u7ae0")

CHINESE_NUMBERS = {
    "\u96f6": 0,
    "\u4e00": 1,
    "\u4e8c": 2,
    "\u4e09": 3,
    "\u56db": 4,
    "\u4e94": 5,
    "\u516d": 6,
    "\u4e03": 7,
    "\u516b": 8,
    "\u4e5d": 9,
}


@dataclass
class SourceSection:
    chapter_id: str
    section_id: str
    chapter_title: str
    section_title: str
    body_lines: list[str]


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def trim_blank_lines(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def is_toc_line(line: str) -> bool:
    stripped = line.strip()
    return bool(TOC_LINK_RE.search(stripped) or DOT_LEADER_RE.match(stripped))


def strip_front_toc(text: str) -> list[str]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for index, line in enumerate(lines):
        if H1_RE.match(line):
            return lines[index:]
    return lines


def chinese_number_to_int(value: str) -> int:
    if value.isdigit():
        return int(value)
    if value == "\u5341":
        return 10
    if "\u5341" in value:
        left, _, right = value.partition("\u5341")
        tens = CHINESE_NUMBERS.get(left, 1 if not left else 0)
        ones = CHINESE_NUMBERS.get(right, 0 if not right else 0)
        return tens * 10 + ones
    return CHINESE_NUMBERS.get(value, 0)


def build_chapter_id(title: str, fallback_index: int) -> str:
    match = CHAPTER_NUMBER_RE.match(title)
    if match:
        number = chinese_number_to_int(match.group(1))
        if number:
            return f"ch{number:02d}"
    if fallback_index == 0:
        return "ch00"
    return f"ch{fallback_index:02d}"


def parse_sections(lines: list[str]) -> list[SourceSection]:
    sections: list[SourceSection] = []
    chapter_title: str | None = None
    chapter_id: str | None = None
    chapter_index = 0
    section_index = 0
    section_title = ""
    body_lines: list[str] = []

    def flush() -> None:
        nonlocal body_lines
        if chapter_title is None or chapter_id is None:
            return
        trimmed = trim_blank_lines(body_lines)
        if not trimmed:
            return
        current_section_id = f"s{max(section_index, 1):02d}"
        sections.append(
            SourceSection(
                chapter_id=chapter_id,
                section_id=current_section_id,
                chapter_title=chapter_title,
                section_title=section_title,
                body_lines=trimmed,
            )
        )
        body_lines = []

    for raw_line in lines:
        line = raw_line.rstrip()
        h1_match = H1_RE.match(line)
        if h1_match:
            flush()
            chapter_title = h1_match.group(1).strip()
            chapter_id = build_chapter_id(chapter_title, chapter_index)
            chapter_index += 1
            section_index = 0
            section_title = ""
            body_lines = []
            continue

        h2_match = H2_RE.match(line)
        if h2_match and chapter_title is not None:
            flush()
            section_index += 1
            section_title = h2_match.group(1).strip()
            body_lines = []
            continue

        h3_match = H3_RE.match(line)
        if h3_match and chapter_title is not None:
            body_lines.append("")
            body_lines.append(f"### {h3_match.group(1).strip()}")
            body_lines.append("")
            continue

        if chapter_title is None or is_toc_line(line):
            continue
        body_lines.append(line)

    flush()
    return sections


def split_paragraphs(lines: list[str]) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []

    for line in lines:
        if line.strip():
            current.append(line)
            continue
        if current:
            paragraphs.append("\n".join(current).strip())
            current = []

    if current:
        paragraphs.append("\n".join(current).strip())

    return paragraphs


def split_long_text(text: str, max_chars: int) -> list[str]:
    sentences = [match.group(1).strip() for match in SENTENCE_RE.finditer(text)]
    if not sentences:
        sentences = [text[index : index + max_chars] for index in range(0, len(text), max_chars)]

    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        candidate = f"{current}{sentence}" if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            pieces.append(current)
        if len(sentence) <= max_chars:
            current = sentence
        else:
            pieces.extend(sentence[index : index + max_chars] for index in range(0, len(sentence), max_chars))
            current = ""
    if current:
        pieces.append(current)
    return pieces


def maybe_overlap(previous_chunk: str) -> str:
    if not previous_chunk or OVERLAP_CHARS <= 0:
        return ""
    paragraphs = split_paragraphs(previous_chunk.splitlines())
    if not paragraphs:
        return ""
    last = paragraphs[-1]
    if len(last) <= OVERLAP_CHARS:
        return last
    return last[-OVERLAP_CHARS:]


def split_section_body(body_lines: list[str]) -> list[str]:
    paragraphs: list[str] = []
    for paragraph in split_paragraphs(body_lines):
        if len(paragraph) <= MAX_CHARS:
            paragraphs.append(paragraph)
        else:
            paragraphs.extend(split_long_text(paragraph, MAX_CHARS))

    chunks: list[str] = []
    current_parts: list[str] = []

    def current_text() -> str:
        return "\n\n".join(current_parts).strip()

    for paragraph in paragraphs:
        candidate_parts = current_parts + [paragraph]
        candidate = "\n\n".join(candidate_parts).strip()
        if len(candidate) <= MAX_CHARS and (len(candidate) <= TARGET_CHARS or not current_parts):
            current_parts = candidate_parts
            continue

        if current_parts:
            chunks.append(current_text())
            overlap = maybe_overlap(chunks[-1])
            current_parts = [overlap, paragraph] if overlap else [paragraph]
            if len(current_text()) > MAX_CHARS:
                current_parts = [paragraph]
        else:
            chunks.append(paragraph)
            current_parts = []

    if current_parts:
        chunks.append(current_text())

    return [chunk for chunk in chunks if chunk]


def extract_keywords(*titles: str) -> list[str]:
    keywords: list[str] = []
    seen: set[str] = set()
    for title in titles:
        for token in re.split(r"[\s,.;:!?()\[\]\-_/|\u3000\uff0c\u3002\uff1a\uff1b\uff01\uff1f\u3001]+", title):
            token = token.strip(" \"'")
            if len(token) < 2 or token in seen:
                continue
            seen.add(token)
            keywords.append(token)
    return keywords[:8]


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_chunk(section: SourceSection, chunk_text: str, chunk_index: int, chunk_count: int) -> str:
    source_id = f"{section.chapter_id}_{section.section_id}_chunk_{chunk_index:02d}"
    title = section.section_title or section.chapter_title
    keywords = extract_keywords(section.chapter_title, section.section_title)
    lines = [
        "---",
        f"source_id: {source_id}",
        f"chapter_id: {section.chapter_id}",
        f"section_id: {section.section_id}",
        f"chunk_index: {chunk_index}",
        f"chunk_count: {chunk_count}",
        f"chapter_title: {yaml_quote(section.chapter_title)}",
        f"section_title: {yaml_quote(section.section_title)}",
        f"title: {yaml_quote(title)}",
        "keywords:",
    ]
    lines.extend(f"  - {yaml_quote(keyword)}" for keyword in keywords)
    lines.extend(["---", "", f"# {section.chapter_title}"])
    if section.section_title:
        lines.extend(["", f"## {section.section_title}"])
    lines.extend(["", chunk_text.strip(), ""])
    return "\n".join(lines)


def cleanup_generated_outputs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in output_dir.iterdir():
        if path.is_dir() and re.fullmatch(r"ch\d{2}", path.name):
            shutil.rmtree(path)
        elif path.is_file() and path.name in {"_index.json", "_index.md", "_chunk_stats.json", "_chunk_stats.md", "_chunk_stats.csv"}:
            path.unlink()


def write_chunks(sections: list[SourceSection], output_dir: Path) -> list[dict[str, object]]:
    cleanup_generated_outputs(output_dir)
    index_entries: list[dict[str, object]] = []

    for section in sections:
        chunk_texts = split_section_body(section.body_lines)
        chapter_dir = output_dir / section.chapter_id
        chapter_dir.mkdir(parents=True, exist_ok=True)

        for chunk_index, chunk_text in enumerate(chunk_texts, start=1):
            filename = f"{section.section_id}.md"
            if len(chunk_texts) > 1:
                filename = f"{section.section_id}_chunk_{chunk_index:02d}.md"
            output_path = chapter_dir / filename
            output_path.write_text(
                render_chunk(section, chunk_text, chunk_index, len(chunk_texts)),
                encoding="utf-8",
                newline="\n",
            )
            index_entries.append(
                {
                    "source_id": f"{section.chapter_id}_{section.section_id}_chunk_{chunk_index:02d}",
                    "path": output_path.relative_to(output_dir).as_posix(),
                    "chapter_id": section.chapter_id,
                    "section_id": section.section_id,
                    "chunk_index": chunk_index,
                    "chunk_count": len(chunk_texts),
                    "chapter_title": section.chapter_title,
                    "section_title": section.section_title,
                    "title": section.section_title or section.chapter_title,
                    "char_count": len(chunk_text),
                    "keywords": extract_keywords(section.chapter_title, section.section_title),
                }
            )

    return index_entries


def write_index_json(output_dir: Path, entries: list[dict[str, object]]) -> Path:
    path = output_dir / "_index.json"
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def write_index_md(output_dir: Path, entries: list[dict[str, object]]) -> Path:
    lines = [
        "# Knowledge Base Index",
        "",
        "| source_id | path | title | chunk | chars | keywords |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        keywords = ", ".join(entry["keywords"])
        lines.append(
            f"| {entry['source_id']} | {entry['path']} | {entry['title']} | "
            f"{entry['chunk_index']}/{entry['chunk_count']} | {entry['char_count']} | {keywords} |"
        )
    path = output_dir / "_index.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Split markdown source into structured RAG chunks.")
    parser.add_argument("--source", type=Path, default=SOURCE_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    lines = strip_front_toc(read_source(args.source))
    sections = parse_sections(lines)
    entries = write_chunks(sections, args.output_dir)
    index_json = write_index_json(args.output_dir, entries)
    index_md = write_index_md(args.output_dir, entries)

    print(f"source: {args.source}")
    print(f"output_dir: {args.output_dir}")
    print(f"sections: {len(sections)}")
    print(f"chunks: {len(entries)}")
    print(f"index_json: {index_json}")
    print(f"index_md: {index_md}")


if __name__ == "__main__":
    main()
