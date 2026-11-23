"""Крок 13: підключення бази знань із ЛР 2 (Obsidian + Chroma) через search_knowledge.

Агент зі схемою output_schema не може викликати інструменти, тому пошук виконує
окремий агент-дослідник (app/agents.py), а результат передається далі через стан.
"""
import os
from collections.abc import Callable

SearchFn = Callable[[str], str]


def make_search_tool(tools) -> SearchFn:
    """Обгортає KnowledgeTools.search_knowledge простою функцією для ADK.

    Ім'я і docstring функції потрапляють до моделі як опис інструмента.
    """
    def search_knowledge(query: str) -> str:
        """Search the game-design knowledge base (Obsidian notes about Unity,
        horror mechanics, sound, lighting, fear scale). Returns fragments with
        sources like [[Note#Section]], or NOT_FOUND if nothing is relevant.

        Args:
            query: a natural-language question, e.g. "How does silence affect fear?"
        """
        return tools.search_knowledge(query)

    return search_knowledge


def build_search_tool() -> SearchFn | None:
    """Робочий інструмент із параметрів .env або None, якщо базу не налаштовано."""
    if not os.getenv("OBSIDIAN_VAULT"):
        return None
    from kb.tools import build_tools  # імпорт тут: chromadb потрібен лише з базою знань
    return make_search_tool(build_tools())
