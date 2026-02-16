from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    section_path: str
    content: str
    token_count: int


def normalize_markdown(markdown: str) -> str:
    normalized = markdown.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    cleaned_lines: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = line.strip() == ""
        if is_blank and previous_blank:
            continue
        cleaned_lines.append(line)
        previous_blank = is_blank
    return "\n".join(cleaned_lines).strip()


def chunk_markdown(markdown: str, max_chars: int = 500) -> list[Chunk]:
    text = normalize_markdown(markdown)
    if not text:
        return []

    lines = text.split("\n")
    section_name = "ROOT"
    current_lines: list[str] = []
    chunks: list[Chunk] = []

    def flush_buffer() -> None:
        nonlocal current_lines
        if not current_lines:
            return
        section_text = "\n".join(current_lines).strip()
        current_lines = []
        if not section_text:
            return
        chunks.extend(_split_large_block(section_name=section_name, block=section_text, max_chars=max_chars))

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            flush_buffer()
            heading = stripped.lstrip("#").strip()
            section_name = heading if heading else "UNTITLED"
            continue
        current_lines.append(line)
    flush_buffer()

    if not chunks:
        return _split_large_block(section_name="ROOT", block=text, max_chars=max_chars)
    return chunks


def _split_large_block(section_name: str, block: str, max_chars: int) -> list[Chunk]:
    if len(block) <= max_chars:
        return [Chunk(section_path=section_name, content=block, token_count=_count_tokens(block))]

    paragraphs = [part.strip() for part in block.split("\n\n") if part.strip()]
    if not paragraphs:
        return [Chunk(section_path=section_name, content=block, token_count=_count_tokens(block))]

    pieces: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if not current:
            current = paragraph
            continue
        candidate = f"{current}\n\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            pieces.append(current)
            current = paragraph
    if current:
        pieces.append(current)

    split_chunks: list[Chunk] = []
    for piece in pieces:
        if len(piece) <= max_chars:
            split_chunks.append(Chunk(section_path=section_name, content=piece, token_count=_count_tokens(piece)))
            continue
        start = 0
        while start < len(piece):
            segment = piece[start : start + max_chars]
            split_chunks.append(Chunk(section_path=section_name, content=segment, token_count=_count_tokens(segment)))
            start += max_chars
    return split_chunks


def _count_tokens(text: str) -> int:
    if not text:
        return 0
    word_tokens = [token for token in text.replace("\n", " ").split(" ") if token]
    return max(len(text), len(word_tokens))
