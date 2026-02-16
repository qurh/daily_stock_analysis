from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    db_file = tmp_path / "test_refactor.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("QUEUE_AUTO_PROCESS", "true")
    monkeypatch.setenv("CHROMA_PATH", str(tmp_path / "chroma"))
    monkeypatch.setenv("CHROMA_COLLECTION", "test_knowledge")
    monkeypatch.setenv("MEMORY_COLLECTION", "test_memory")
    monkeypatch.setenv("LLM_PROVIDER", "mock-llm")
    monkeypatch.setenv("LLM_MODEL", "mock-v1")
    return db_file
