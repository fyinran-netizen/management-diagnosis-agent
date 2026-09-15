from __future__ import annotations

from pathlib import Path

from app.tools.ingestion.schemas import Document


def parse_front_matter(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    if not lines or lines[0].strip() != "---":
        return {}, lines
    metadata: dict[str, str] = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return metadata, lines[index + 1 :]
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return {}, lines


class MarkdownLoader:
    def load(self, path: Path, *, root_dir: Path | None = None) -> Document:
        text = path.read_text(encoding="utf-8").strip()
        front_matter, body_lines = parse_front_matter(text.splitlines())
        source = path.name if root_dir is None else path.relative_to(root_dir).as_posix()
        return Document(source=source, text="\n".join(body_lines), metadata=front_matter)

    def load_many(self, paths: list[Path], *, root_dir: Path | None = None) -> list[Document]:
        return [self.load(path, root_dir=root_dir) for path in paths]
