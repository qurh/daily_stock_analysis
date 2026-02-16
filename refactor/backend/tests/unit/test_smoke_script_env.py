from pathlib import Path


def test_smoke_script_defaults_to_backend_env_file() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    script_path = backend_root / "scripts" / "smoke-real-llm.sh"
    script_content = script_path.read_text(encoding="utf-8")
    assert 'ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"' in script_content


def test_smoke_script_uses_key_whitelist_loader() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    script_path = backend_root / "scripts" / "smoke-real-llm.sh"
    script_content = script_path.read_text(encoding="utf-8")
    assert "ALLOWED_ENV_KEYS=" in script_content
