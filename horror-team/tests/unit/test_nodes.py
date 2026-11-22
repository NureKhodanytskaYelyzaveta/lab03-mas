"""Модульні тести детермінованих функцій."""
from app.nodes import fear_curve, gate, link_issues, render_report, scene_issues
from tests.fixtures import APPROVE, AUDIO, GOOD, REVISE, VISUAL, beat


class FakeState(dict):
    def to_dict(self):
        return dict(self)


class FakeCtx:
    def __init__(self, **state):
        self.state = FakeState(state)


def test_good_scene_has_no_issues():
    assert scene_issues(GOOD) == []


def test_scene_without_peak_or_release():
    flat = {**GOOD, "beats": [beat(i, 20 + i) for i in range(1, 6)]}
    assert any("кульмінації" in i for i in scene_issues(flat))
    no_release = {**GOOD, "beats": [beat(1, 10), beat(2, 40), beat(3, 70), beat(4, 90)]}
    assert any("розрядки" in i for i in scene_issues(no_release))


def test_scene_duplicate_ids_and_range():
    dup = {**GOOD, "beats": [beat(1, 10), beat(1, 50), beat(3, 120), beat(4, 20)]}
    text = " ".join(scene_issues(dup))
    assert "унікальними" in text and "від 0 до 100" in text


def test_link_issues_detects_unknown_and_uncovered():
    audio = {"cues": [{"beat_id": "B9", "volume": 2}]}
    issues = link_issues(GOOD, audio, {"effects": []})
    assert any("неіснуючий біт B9" in i for i in issues)
    assert any("поза межами" in i for i in issues)
    assert any("B1 не має" in i for i in issues)
    assert link_issues(GOOD, AUDIO, VISUAL) == []


def test_gate_routes_and_limit():
    assert gate(FakeCtx(drafts=1), APPROVE).actions.route == "publish"
    ctx = FakeCtx(drafts=1)
    assert gate(ctx, REVISE).actions.route == "revise"
    ctx = FakeCtx(drafts=3)
    assert gate(ctx, REVISE).actions.route == "publish"
    assert ctx.state["stop_reason"] == "max_drafts"


def test_fear_curve_and_report():
    assert fear_curve(GOOD) == [0.15, 0.4, 0.65, 0.85, 0.45]
    report = render_report({"scene": GOOD, "audio_plan": AUDIO, "visual_plan": VISUAL,
                            "verdict": APPROVE, "drafts": 1, "stop_reason": "approved"})
    assert "## Звук" in report and "[0.15, 0.4, 0.65, 0.85, 0.45]" in report
