"""LLM-агенти команди. Модель передається параметром: у тестах її підміняють."""
from google.adk import Agent
from google.adk.models.base_llm import BaseLlm

from .schemas import AudioPlan, SceneDesign, Verdict, VisualPlan

LANGUAGE = ("Write all text values in Ukrainian; keep enum values and beat ids "
            "(B1, B2, ...) exactly as specified.")


def build_researcher(model: BaseLlm | str, search_tool) -> Agent:
    """Дослідник: єдиний агент з інструментом. Без output_schema, бо їх не можна поєднувати."""
    return Agent(
        name="researcher",
        model=model,
        description="Finds relevant facts in the knowledge base for the scene request.",
        instruction=f"""
You are a game-design researcher with access to the project knowledge base.
Scene request: {{request}}
Call search_knowledge 1-3 times with focused questions (fear scale, sound, light,
horror techniques). Then write at most 6 short bullet points with facts that help
to design the scene, each ending with its source like [[Note#Section]].
If the tool returns NOT_FOUND, write exactly: no relevant notes.
Never invent facts and never cite sources that the tool did not return.
{LANGUAGE}
""",
        tools=[search_tool],
        output_key="kb_notes",
    )


def build_agents(model: BaseLlm | str) -> dict[str, Agent]:
    scene = Agent(
        name="scene_designer",
        model=model,
        description="Designs the structure and fear curve of a horror scene.",
        instruction=f"""
You are a horror scene designer for a psychological horror game in Unity.
Design ONE scene for this request: {{request}}
Build 4-8 beats (ids B1, B2, ...). The scene starts calm (fear_target <= 30),
reaches a peak of at least 70 and then gives the player a release: a later beat
at least 15 points lower than the peak. Prefer ambiguity, isolation and sound
over cheap jump scares. Add 2-4 short inner voice lines for the hero.
Do not describe sound or visual effects: other specialists do that.
Notes from the project knowledge base (may be empty): {{kb_notes?}}
Use them only when they fit the request and do not contradict it.
Feedback from the previous review (empty on the first draft): {{feedback?}}
{LANGUAGE}
""",
        output_schema=SceneDesign,
        output_key="scene",
    )
    audio = Agent(
        name="audio_designer",
        model=model,
        description="Plans sound cues for every beat.",
        instruction=f"""
You are a sound designer. The scene design is given as input.
Write 1 or 2 sound cues for every beat: beat_id must be an existing beat id,
volume from 0.0 to 1.0. Use silence deliberately before the peak.
Do not change the beats and do not plan visual effects.
{LANGUAGE}
""",
        output_schema=AudioPlan,
        output_key="audio_plan",
    )
    visual = Agent(
        name="visual_designer",
        model=model,
        description="Plans lighting and screen effects for the beats.",
        instruction=f"""
You are a visual effects artist. The scene design is given as input.
Plan 1 or 2 effects per beat: beat_id must be an existing beat id,
intensity from 0.0 to 1.0, effect from the allowed list. Tie the intensity
to the beat's fear_target. Do not change the beats and do not plan sound.
{LANGUAGE}
""",
        output_schema=VisualPlan,
        output_key="visual_plan",
    )
    director = Agent(
        name="director",
        model=model,
        description="Accepts the scene or sends it back with comments.",
        instruction=f"""
You are the creative director of the game. Decide whether the scene is ready
for implementation.
Scene: {{scene}}
Audio plan: {{audio_plan}}
Visual plan: {{visual_plan}}
Return APPROVE only if the fear curve builds up convincingly, the sound and
visual plans support every beat, and the scene relies on atmosphere rather than
only on jump scares. Otherwise return REVISE with at most 5 specific comments
for the scene designer.
{LANGUAGE}
""",
        output_schema=Verdict,
        output_key="verdict",
    )
    return {"scene": scene, "audio": audio, "visual": visual, "director": director}
