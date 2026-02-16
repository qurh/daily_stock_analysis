from __future__ import annotations


def summarize_chunk(content: str, max_length: int = 160) -> str:
    compact = " ".join(content.replace("\n", " ").split())
    if len(compact) <= max_length:
        return compact
    return f"{compact[: max_length - 3]}..."
