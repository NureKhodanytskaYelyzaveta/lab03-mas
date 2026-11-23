"""Мультиагентна система «Команда проєктування страшної сцени» на графі ADK 2.x."""
import os

from google.adk import Workflow
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.models.base_llm import BaseLlm
from google.adk.workflow import JoinNode
from google.genai import types

from .agents import build_agents, build_researcher
from .nodes import (gate, human_decision, human_review, intake, link_check, publish, reject,
                    risk_check, scene_check)

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def build_workflow(model: BaseLlm | str, search_tool=None) -> Workflow:
    """search_tool: функція search_knowledge (крок 13). Без неї дослідника в графі немає."""
    a = build_agents(model)
    plans = JoinNode(name="plans")  # чекає на обидві паралельні гілки
    if search_tool is None:
        start = [(intake, {"ok": a["scene"], "reject": reject})]
    else:
        researcher = build_researcher(model, search_tool)
        start = [(intake, {"ok": researcher, "reject": reject}), (researcher, a["scene"])]
    return Workflow(
        name="horror_team",
        max_concurrency=2,  # не більше двох агентів одночасно
        edges=[
            ("START", intake),
            *start,
            (a["scene"], scene_check),
            (scene_check, {"ok": (a["audio"], a["visual"]), "fix": a["scene"]}),
            (a["audio"], plans),
            (a["visual"], plans),
            (plans, link_check),
            (link_check, {"ok": a["director"], "fix": a["scene"]}),
            (a["director"], gate),
            (gate, {"revise": a["scene"], "publish": risk_check}),
            # крок 14: людина в циклі для ризикових сцен
            (risk_check, {"safe": publish, "risky": human_review}),
            (human_review, human_decision),
            (human_decision, {"approved": publish, "revise": a["scene"], "rejected": publish}),
        ],
    )


def _search_tool_from_env():
    from .knowledge import build_search_tool
    return build_search_tool()  # None, якщо OBSIDIAN_VAULT не задано


root_agent = build_workflow(
    Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=6)),
    search_tool=_search_tool_from_env())
app = App(root_agent=root_agent, name="app")
