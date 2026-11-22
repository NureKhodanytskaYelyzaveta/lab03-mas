"""Просунуто: координатор сам вирішує, кого з експертів залучити.

На відміну від графа маршрут тут обирає LLM під час виконання.
"""
from google.adk import Agent
from google.adk.models.base_llm import BaseLlm

from .agents import LANGUAGE


def build_coordinator(model: BaseLlm | str) -> Agent:
    def expert(name: str, description: str, focus: str) -> Agent:
        return Agent(
            name=name, model=model, description=description, mode="single_turn",
            instruction=f"You are a {focus}. Answer the delegated request briefly "
                        f"and concretely, max 8 bullet points. {LANGUAGE}")

    experts = [
        expert("level_expert", "Designs scene structure, pacing and the fear curve.",
               "horror level designer"),
        expert("sound_expert", "Designs sound: ambience, silence, stingers, whispers.",
               "horror sound designer"),
        expert("vfx_expert", "Designs lighting and screen effects in Unity.",
               "Unity visual effects artist"),
    ]
    return Agent(
        name="coordinator",
        model=model,
        instruction=f"""
You coordinate a team of experts: level_expert, sound_expert, vfx_expert.
For the user's request call only the experts whose competence is needed,
pass each of them a focused request, then merge their answers into one
consistent reply. Do not answer expert questions yourself. Call each expert at most once.
{LANGUAGE}
""",
        sub_agents=experts,
    )
