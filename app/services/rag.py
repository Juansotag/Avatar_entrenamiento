from app.services.persona import get_all_policy_snippets


def get_relevant_context(query: str) -> list[str]:
    """RAG-lite: el corpus actual (unos pocos snippets de politica publica) cabe
    entero en la ventana de contexto, asi que no hace falta busqueda vectorial
    para el viernes. Se deja un filtro simple por palabras clave del nombre del
    archivo como demostracion de "retrieval"; si nada matchea, se devuelve todo
    el corpus para no perder contexto relevante.

    Esta funcion es el unico punto de acceso a los snippets desde los servicios
    de LLM (nunca tocan el disco directamente), para poder reemplazarla despues
    por una busqueda vectorial real (chromadb, pgvector, etc.) sin tocar el
    resto del codigo.
    """
    all_snippets = get_all_policy_snippets()
    if not query:
        return [content for _, content in all_snippets]

    query_lower = query.lower()
    matched = [
        content
        for name, content in all_snippets
        if any(word in query_lower for word in name.split("_"))
    ]
    return matched if matched else [content for _, content in all_snippets]
