from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


SOURCE_PATH = Path("source_docs/raw_converted.md")
OUTPUT_DIR = Path("data/private_knowledge_base")
MAX_CHARS = 8000

H1_RE = re.compile(r"^# (.+?)\s*$")
H2_RE = re.compile(r"^## (.+?)\s*$")
TOC_LINE_RE = re.compile(
    r"""
    ^\s*
    [^#\s].*?
    (?:
        \[\d+\]\([^)]*\)
        |
        \.{2,}\s*\d+
        |
        …{2,}\s*\d+
        |
        [·•。．]{2,}\s*\d+
    )
    \s*$
    """,
    re.VERBOSE,
)
KEYWORD_SPLIT_RE = re.compile(r"[：:，,、。；;（）()\[\]【】“”‘’《》\-\s]+")
CHAPTER_PREFIX_RE = re.compile(r"^第[一二三四五六七八九十百零\d]+章\s*")
SECTION_PREFIX_RE = re.compile(
    r"^(?:第[一二三四五六七八九十百零\d]+节|第[一二三四五六七八九十百零\d]+部分)\s*"
)
NUMBERED_CHAPTER_RE = re.compile(r"^第([一二三四五六七八九十百零\d]+)章")

CHINESE_DIGITS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


@dataclass
class SectionDocument:
    chapter_id: str
    section_id: str
    chapter_title: str
    section_title: str
    body_lines: list[str]


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def strip_front_toc(text: str) -> list[str]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    start_index = 0
    for index, line in enumerate(lines):
        if H1_RE.match(line):
            start_index = index
            break
    return lines[start_index:]


def is_toc_line(line: str) -> bool:
    return bool(TOC_LINE_RE.match(line.strip()))


def trim_blank_lines(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def chinese_number_to_int(text: str) -> int:
    if text.isdigit():
        return int(text)
    if text == "十":
        return 10
    if "十" in text:
        left, _, right = text.partition("十")
        tens = CHINESE_DIGITS.get(left, 1 if left == "" else 0)
        ones = CHINESE_DIGITS.get(right, 0 if right == "" else 0)
        return tens * 10 + ones
    return CHINESE_DIGITS[text]


def build_chapter_id(title: str, last_numbered_chapter: int, trailing_extra_count: int) -> tuple[str, int, int]:
    match = NUMBERED_CHAPTER_RE.match(title)
    if match:
        chapter_number = chinese_number_to_int(match.group(1))
        return f"ch{chapter_number:02d}", chapter_number, trailing_extra_count
    if last_numbered_chapter == 0:
        return "ch00", last_numbered_chapter, trailing_extra_count
    trailing_extra_count += 1
    return f"ch{last_numbered_chapter + trailing_extra_count:02d}", last_numbered_chapter, trailing_extra_count


def build_documents(lines: list[str]) -> list[SectionDocument]:
    documents: list[SectionDocument] = []
    chapter_title: str | None = None
    chapter_id: str | None = None
    last_numbered_chapter = 0
    trailing_extra_count = 0
    section_index = 0
    chapter_body: list[str] = []
    section_title: str | None = None
    section_body: list[str] = []

    def flush_section() -> None:
        nonlocal section_title, section_body, section_index
        if chapter_title is None or chapter_id is None or section_title is None:
            return
        body_lines = trim_blank_lines(section_body)
        documents.append(
            SectionDocument(
                chapter_id=chapter_id,
                section_id=f"s{section_index:02d}",
                chapter_title=chapter_title,
                section_title=section_title,
                body_lines=body_lines,
            )
        )
        section_title = None
        section_body = []

    def flush_chapter_without_sections() -> None:
        nonlocal section_index, chapter_body
        if chapter_title is None or chapter_id is None:
            return
        body_lines = trim_blank_lines(chapter_body)
        if not body_lines:
            return
        section_index = 1
        documents.append(
            SectionDocument(
                chapter_id=chapter_id,
                section_id="s01",
                chapter_title=chapter_title,
                section_title="",
                body_lines=body_lines,
            )
        )
        chapter_body = []

    for raw_line in lines:
        line = raw_line.rstrip()
        h1_match = H1_RE.match(line)
        if h1_match:
            if section_title is not None:
                flush_section()
            elif chapter_title is not None:
                flush_chapter_without_sections()
            section_index = 0
            chapter_title = h1_match.group(1).strip()
            chapter_id, last_numbered_chapter, trailing_extra_count = build_chapter_id(
                chapter_title,
                last_numbered_chapter,
                trailing_extra_count,
            )
            chapter_body = []
            section_title = None
            section_body = []
            continue

        h2_match = H2_RE.match(line)
        if h2_match and chapter_title is not None:
            if section_title is not None:
                flush_section()
            section_index += 1
            section_title = h2_match.group(1).strip()
            section_body = []
            continue

        if chapter_title is None:
            continue

        if section_title is None:
            if not is_toc_line(line):
                chapter_body.append(line)
        else:
            section_body.append(line)

    if section_title is not None:
        flush_section()
    elif chapter_title is not None:
        flush_chapter_without_sections()

    return documents


def extract_keywords(chapter_title: str, section_title: str) -> list[str]:
    candidates = [chapter_title, section_title]
    keywords: list[str] = []
    seen: set[str] = set()
    for title in candidates:
        if not title:
            continue
        normalized = title.replace("　", " ").strip()
        pieces = KEYWORD_SPLIT_RE.split(normalized)
        for piece in pieces:
            token = piece.strip()
            token = CHAPTER_PREFIX_RE.sub("", token)
            token = SECTION_PREFIX_RE.sub("", token)
            if not token or token in seen:
                continue
            seen.add(token)
            keywords.append(token)
    return keywords


def render_metadata(source_id: str, doc: SectionDocument, keywords: list[str]) -> str:
    lines = [
        "---",
        f"source_id: {source_id}",
        f"chapter_id: {doc.chapter_id}",
        f"section_id: {doc.section_id}",
        f'chapter_title: "{doc.chapter_title}"',
        f'section_title: "{doc.section_title}"',
        "keywords:",
    ]
    for keyword in keywords:
        lines.append(f'  - "{keyword}"')
    lines.append("---")
    return "\n".join(lines)


def render_document(
    source_id: str,
    doc: SectionDocument,
    body_lines: list[str],
    keywords: list[str],
) -> str:
    parts = [render_metadata(source_id, doc, keywords), "", f"# {doc.chapter_title}"]
    if doc.section_title:
        parts.extend(["", f"## {doc.section_title}"])
    if body_lines:
        parts.extend(["", "\n".join(body_lines)])
    return "\n".join(parts).strip() + "\n"


def split_long_line(doc: SectionDocument, line: str, limit: int, keywords: list[str]) -> list[str]:
    if not line.strip():
        return [line]

    pieces: list[str] = []
    current = ""
    for char in line:
        candidate = current + char
        if len(render_document("tmp", doc, [candidate], keywords)) <= limit:
            current = candidate
            continue
        if current:
            pieces.append(current)
            current = char
        else:
            pieces.append(char)
            current = ""
    if current:
        pieces.append(current)
    return pieces


def split_body_lines(doc: SectionDocument, limit: int, keywords: list[str]) -> list[list[str]]:
    if len(render_document("tmp", doc, doc.body_lines, keywords)) <= limit:
        return [doc.body_lines]

    chunks: list[list[str]] = []
    current: list[str] = []

    def flush_current() -> None:
        nonlocal current
        if current:
            chunks.append(trim_blank_lines(current))
            current = []

    for line in doc.body_lines:
        candidate = current + [line]
        if len(render_document("tmp", doc, candidate, keywords)) <= limit:
            current = candidate
            continue

        if current:
            flush_current()

        if len(render_document("tmp", doc, [line], keywords)) <= limit:
            current = [line]
            continue

        for piece in split_long_line(doc, line, limit, keywords):
            if len(render_document("tmp", doc, [piece], keywords)) > limit:
                raise ValueError("A line is too long to split within the configured limit.")
            chunks.append([piece])

    flush_current()
    return [chunk for chunk in chunks if chunk]


def cleanup_generated_outputs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in output_dir.iterdir():
        if path.is_dir() and re.fullmatch(r"ch\d{2}", path.name):
            shutil.rmtree(path)
        elif path.is_file() and path.name in {"_index.json", "_index.md"}:
            path.unlink()


def write_documents(documents: list[SectionDocument], output_dir: Path, limit: int) -> list[dict[str, object]]:
    cleanup_generated_outputs(output_dir)
    index_entries: list[dict[str, object]] = []

    for doc in documents:
        chapter_dir = output_dir / doc.chapter_id
        chapter_dir.mkdir(parents=True, exist_ok=True)
        keywords = extract_keywords(doc.chapter_title, doc.section_title)
        parts = split_body_lines(doc, limit, keywords)

        for part_index, body_lines in enumerate(parts, start=1):
            source_id = f"{doc.chapter_id}_{doc.section_id}"
            filename = f"{doc.section_id}.md"
            if len(parts) > 1:
                source_id = f"{source_id}_part_{part_index:02d}"
                filename = f"{doc.section_id}_part_{part_index:02d}.md"

            output_path = chapter_dir / filename
            content = render_document(source_id, doc, body_lines, keywords)
            output_path.write_text(content, encoding="utf-8", newline="\n")

            index_entries.append(
                {
                    "source_id": source_id,
                    "path": output_path.relative_to(output_dir).as_posix(),
                    "chapter_id": doc.chapter_id,
                    "section_id": doc.section_id,
                    "chapter_title": doc.chapter_title,
                    "section_title": doc.section_title,
                    "keywords": keywords,
                }
            )

    return index_entries


def write_index_json(output_dir: Path, index_entries: list[dict[str, object]]) -> Path:
    index_path = output_dir / "_index.json"
    index_path.write_text(
        json.dumps(index_entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return index_path


def write_index_md(output_dir: Path, index_entries: list[dict[str, object]]) -> Path:
    lines = [
        "# Knowledge Base Index",
        "",
        "| source_id | path | chapter_title | section_title | keywords |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in index_entries:
        keywords = "、".join(entry["keywords"])
        section_title = entry["section_title"] or "-"
        lines.append(
            f"| {entry['source_id']} | {entry['path']} | {entry['chapter_title']} | {section_title} | {keywords} |"
        )
    index_path = output_dir / "_index.md"
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return index_path


def main() -> None:
    text = read_source(SOURCE_PATH)
    lines = strip_front_toc(text)
    documents = build_documents(lines)
    index_entries = write_documents(documents, OUTPUT_DIR, MAX_CHARS)
    index_json_path = write_index_json(OUTPUT_DIR, index_entries)
    index_md_path = write_index_md(OUTPUT_DIR, index_entries)

    print(f"source: {SOURCE_PATH}")
    print(f"output_dir: {OUTPUT_DIR}")
    print(f"documents: {len(documents)}")
    print(f"files_written: {len(index_entries)}")
    print(index_json_path.as_posix())
    print(index_md_path.as_posix())
    for entry in index_entries:
        print(entry["path"])


if __name__ == "__main__":
    main()
