from functools import lru_cache

from app.config import get_settings

settings = get_settings()


@lru_cache
def get_persona_system_prompt() -> str:
    brief_path = settings.data_dir / "persona_brief.md"
    return brief_path.read_text(encoding="utf-8")


@lru_cache
def get_all_policy_snippets() -> tuple[tuple[str, str], ...]:
    snippets_dir = settings.data_dir / "policy_snippets"
    return tuple(
        (path.stem, path.read_text(encoding="utf-8")) for path in sorted(snippets_dir.glob("*.md"))
    )


def clear_persona_cache() -> None:
    """Invalida la caché en memoria del perfil y fragmentos de conocimiento."""
    get_persona_system_prompt.cache_clear()
    get_all_policy_snippets.cache_clear()

