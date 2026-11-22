"""Базова лінія: один агент виконує роботу всієї команди за один виклик."""
from google.adk import Agent
from google.adk.models.base_llm import BaseLlm
from pydantic import BaseModel

from .agents import LANGUAGE
from .schemas import AudioPlan, SceneDesign, VisualPlan


class SoloResult(BaseModel):
    scene: SceneDesign
    audio_plan: AudioPlan
    visual_plan: VisualPlan


def build_solo_agent(model: BaseLlm | str) -> Agent:
    return Agent(
        name="solo",
        model=model,
        instruction=f"""
You are a whole game-design team in one person, working on a psychological
horror game in Unity. For the scene request:
1) design ONE scene with 4-8 beats (ids B1, B2, ...): it starts calm
   (fear_target <= 30), peaks at >= 70, then a later beat is at least 15 lower;
   add 2-4 inner voice lines;
2) as a sound designer write 1-2 cues per beat (volume 0.0-1.0);
3) as a visual effects artist plan 1-2 effects per beat (intensity 0.0-1.0).
{LANGUAGE}
""",
        output_schema=SoloResult,
        output_key="solo",
    )
