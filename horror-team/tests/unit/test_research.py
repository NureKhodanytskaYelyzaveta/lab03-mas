"""Крок 13: дослідник з search_knowledge і база знань із ЛР 2 (без API)."""
import asyncio
import shutil
from pathlib import Path

import chromadb

from app.agent import build_workflow
from app.knowledge import make_search_tool
from kb.embedder import HashEmbedder
from kb.indexer import index_vault
from kb.store import KnowledgeStore
from kb.tools import KnowledgeTools
from run_cli import run_once
from tests.fixtures import (APPROVE, AUDIO, AUDIO_M, DIRECTOR, GOOD, REQUEST, RESEARCHER, SCENE,
                            VISUAL, VISUAL_M)
from tests.scripted import ToolCallingLlm

VAULT = Path(__file__).parent.parent / "kb_vault"


def real_search(tmp_path):
    """Справжній KnowledgeTools із ЛР 2: Chroma + HashEmbedder (без мережі)."""
    vault = tmp_path / "vault"
    shutil.copytree(VAULT, vault)
    store = KnowledgeStore(HashEmbedder(), "test_kb",
                           client=chromadb.PersistentClient(path=str(tmp_path / "chroma")))
    index_vault(vault, store)
    return make_search_tool(KnowledgeTools(store, vault, top_k=3, max_distance=0.95))


def script(notes):
    return {RESEARCHER: [notes], SCENE: [GOOD], AUDIO_M: [AUDIO], VISUAL_M: [VISUAL],
            DIRECTOR: [APPROVE]}


def test_researcher_calls_tool_and_shares_notes_through_state():
    queries = []

    def search_knowledge(query: str) -> str:
        """Search the knowledge base."""
        queries.append(query)
        return '<fragment source="[[Страх#Тиша]]">Тиша перед піком підсилює страх</fragment>'

    model = ToolCallingLlm(model="scripted", script=script("- Тиша підсилює страх [[Страх#Тиша]]"))
    result = asyncio.run(run_once(build_workflow(model, search_tool=search_knowledge), REQUEST))
    assert queries == [model.tool_query]
    state = result["state"]
    assert "[[Страх#Тиша]]" in state["kb_notes"]
    assert "## Нотатки з бази знань" in state["report"] and state["stop_reason"] == "approved"
    assert model.calls[0] == RESEARCHER  # дослідник працює першим, один раз


def test_researcher_runs_once_even_with_revise_loop():
    model = ToolCallingLlm(model="scripted", script={
        **script("- нотатка"), SCENE: [GOOD, GOOD],
        DIRECTOR: [{"decision": "REVISE", "comments": ["ще"]}, APPROVE]})
    def search_knowledge(query: str) -> str:
        """Search the knowledge base."""
        return "x"

    result = asyncio.run(run_once(build_workflow(model, search_tool=search_knowledge), REQUEST))
    nodes = [t["node"] for t in result["trace"]]
    assert "researcher@1" in nodes and "researcher@2" not in nodes   # вузол виконано один раз
    assert model.calls.count(RESEARCHER) == 2   # але це 2 виклики моделі: запит інструмента + підсумок
    assert model.calls.count(SCENE) == 2


def test_graph_without_search_tool_has_no_researcher():
    model = ToolCallingLlm(model="scripted", script=script("не потрібно"))
    asyncio.run(run_once(build_workflow(model), REQUEST))
    assert RESEARCHER not in model.calls


def test_real_knowledge_base_from_lab02_through_the_tool(tmp_path):
    search = real_search(tmp_path)
    found = search("Для чого потрібен Raycast")
    assert "<fragment" in found and "Raycast" in found


def test_researcher_with_real_knowledge_base(tmp_path):
    model = ToolCallingLlm(model="scripted", script=script("- Raycast [[Raycast#Що це]]"))
    model.tool_query = "Raycast"
    result = asyncio.run(run_once(build_workflow(model, search_tool=real_search(tmp_path)), REQUEST))
    assert result["state"]["stop_reason"] == "approved"
    assert RESEARCHER in model.calls
