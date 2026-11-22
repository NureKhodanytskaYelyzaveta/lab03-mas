"""Мультиагентна система «Команда проєктування страшної сцени» на графі ADK 2.x."""
import os

from google.adk import Workflow
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.models.base_llm import BaseLlm
from google.adk.workflow import JoinNode
from google.genai import types

from .agents import build_agents
from .nodes import gate, intake, link_check, publish, reject, scene_check

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def build_workflow(model: BaseLlm | str) -> Workflow:
    a = build_agents(model)
    plans = JoinNode(name="plans")  # чекає на обидві паралельні гілки
    return Workflow(
        name="horror_team",
        max_concurrency=2,  # не більше двох агентів одночасно
        edges=[
            ("START", intake),
            (intake, {"ok": a["scene"], "reject": reject}),
            (a["scene"], scene_check),
            (scene_check, {"ok": (a["audio"], a["visual"]), "fix": a["scene"]}),
            (a["audio"], plans),
            (a["visual"], plans),
            (plans, link_check),
            (link_check, {"ok": a["director"], "fix": a["scene"]}),
            (a["director"], gate),
            (gate, {"revise": a["scene"], "publish": publish}),
        ],
    )


root_agent = build_workflow(
    Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=6)))
app = App(root_agent=root_agent, name="app")
