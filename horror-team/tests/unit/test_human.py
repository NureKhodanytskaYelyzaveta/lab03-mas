"""Крок 14: людина в циклі для ризикових сцен (тести без API)."""
import asyncio

from app.agent import build_workflow
from app.nodes import MAX_DRAFTS, risk_reasons
from run_cli import run_once
from tests.fixtures import (APPROVE, AUDIO, AUDIO_M, DIRECTOR, GOOD, LOUD_AUDIO, REQUEST, SCENE,
                            VISUAL, VISUAL_M)
from tests.scripted import ScriptedLlm


class Human:
    """Підмінна людина: відповідає за списком і запам'ятовує запити."""
    def __init__(self, *answers):
        self.answers, self.asked = list(answers), []

    def __call__(self, message, payload):
        self.asked.append((message, payload))
        return self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]


def run(audio, human, scene=None):
    model = ScriptedLlm(model="scripted", script={SCENE: scene or [GOOD], AUDIO_M: audio,
                                                  VISUAL_M: [VISUAL], DIRECTOR: [APPROVE]})
    return asyncio.run(run_once(build_workflow(model), REQUEST, human=human)), model


def test_safe_scene_does_not_ask_human():
    human = Human({"approved": True})
    result, _ = run([AUDIO], human)
    assert human.asked == [] and result["human_requests"] == 0
    assert result["state"]["stop_reason"] == "approved"
    assert "Ризики" not in result["state"]["report"]


def test_risky_scene_approved_by_human():
    human = Human({"approved": True, "comment": ""})
    result, _ = run([LOUD_AUDIO], human)
    assert len(human.asked) == 1 and "гучний звук у біті B4" in human.asked[0][0]
    assert result["state"]["human"] == "approved"
    assert "Рішення людини: approved" in result["state"]["report"]


def test_risky_scene_rejected_goes_back_to_designer():
    human = Human({"approved": False, "comment": "приглушити стінгер"})
    result, model = run([LOUD_AUDIO, AUDIO], human, scene=[GOOD, GOOD])
    assert len(human.asked) == 1                      # друга чернетка безпечна
    assert model.calls.count(SCENE) == 2
    assert result["state"]["drafts"] == 2 and "Ризики" not in result["state"]["report"]


def test_human_rejection_loop_is_bounded():
    human = Human({"approved": False, "comment": "ще тихіше"})
    result, model = run([LOUD_AUDIO], human, scene=[GOOD])
    assert result["state"]["stop_reason"] == "human_rejected"
    assert len(human.asked) == MAX_DRAFTS == model.calls.count(SCENE)


def test_graph_waits_when_nobody_answers():
    result, _ = run([LOUD_AUDIO], None)
    assert result["waiting_for_human"] and "report" not in result["state"]


def test_risk_reasons_rules():
    assert risk_reasons(GOOD, AUDIO) == []
    assert len(risk_reasons(GOOD, LOUD_AUDIO)) == 1
    silent = {"cues": [{"beat_id": "B1", "kind": "silence", "volume": 1.0}]}
    assert risk_reasons(GOOD, silent) == []           # тиша не ризик
    extreme = {**GOOD, "beats": [{**GOOD["beats"][3], "fear_target": 98}]}
    assert any("екстремальна" in r for r in risk_reasons(extreme, AUDIO))
