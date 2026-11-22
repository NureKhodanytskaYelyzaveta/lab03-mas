"""Тести оркестрації графа на підмінній моделі (без API)."""
import asyncio

from app.agent import build_workflow
from app.nodes import MAX_DRAFTS
from run_cli import run_once
from tests.fixtures import (APPROVE, AUDIO, AUDIO_M, DIRECTOR, GOOD, REQUEST, REVISE, SCENE,
                            VISUAL, VISUAL_M)
from tests.scripted import ScriptedLlm


def run(script):
    model = ScriptedLlm(model="scripted", script=script)
    return asyncio.run(run_once(build_workflow(model), REQUEST)), model


def test_approved_on_first_round():
    result, model = run({SCENE: [GOOD], AUDIO_M: [AUDIO], VISUAL_M: [VISUAL],
                         DIRECTOR: [APPROVE]})
    state = result["state"]
    assert state["stop_reason"] == "approved" and state["drafts"] == 1
    assert "## Біти і крива страху" in state["report"]
    assert sorted(model.calls) == sorted([SCENE, AUDIO_M, VISUAL_M, DIRECTOR])


def test_revise_loop_then_approve():
    result, model = run({SCENE: [GOOD, GOOD], AUDIO_M: [AUDIO], VISUAL_M: [VISUAL],
                         DIRECTOR: [REVISE, APPROVE]})
    assert result["state"]["drafts"] == 2
    assert model.calls.count(SCENE) == 2 and model.calls.count(DIRECTOR) == 2


def test_loop_is_bounded():
    result, model = run({SCENE: [GOOD], AUDIO_M: [AUDIO], VISUAL_M: [VISUAL],
                         DIRECTOR: [REVISE]})
    assert result["state"]["stop_reason"] == "max_drafts"
    assert model.calls.count(DIRECTOR) == MAX_DRAFTS


def test_bad_scene_goes_back_without_other_agents():
    bad = {**GOOD, "beats": GOOD["beats"][:2]}  # лише 2 біти
    result, model = run({SCENE: [bad, GOOD], AUDIO_M: [AUDIO], VISUAL_M: [VISUAL],
                         DIRECTOR: [APPROVE]})
    assert model.calls[:2] == [SCENE, SCENE]
    assert result["state"]["stop_reason"] == "approved"


def test_broken_links_go_back_before_director():
    broken = {"cues": [{"beat_id": "B9", "kind": "ambient", "description": "x",
                        "volume": 0.4}]}
    result, model = run({SCENE: [GOOD, GOOD], AUDIO_M: [broken, AUDIO], VISUAL_M: [VISUAL],
                         DIRECTOR: [APPROVE]})
    assert model.calls.count(SCENE) == 2
    assert model.calls.count(DIRECTOR) == 1  # директор не витрачений на зламані плани


def test_short_request_is_rejected_without_llm():
    model = ScriptedLlm(model="scripted", script={})
    result = asyncio.run(run_once(build_workflow(model), "жах"))
    assert model.calls == []
    assert any("Запит відхилено" in r["text"] for r in result["trace"])
