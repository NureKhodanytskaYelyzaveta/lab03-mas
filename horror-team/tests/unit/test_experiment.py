"""Експеримент і сліпа оцінка на підмінній моделі."""
import asyncio
import csv

from app.agent import build_workflow
from app.baseline import build_solo_agent
from eval.run_experiment import experiment, unblind, write_blind
from tests.fixtures import APPROVE, AUDIO, AUDIO_M, DIRECTOR, GOOD, SCENE, VISUAL, VISUAL_M
from tests.scripted import ScriptedLlm

SOLO = {"scene": GOOD, "audio_plan": AUDIO, "visual_plan": VISUAL}


def test_experiment_blind_pipeline(tmp_path):
    team_m = ScriptedLlm(model="s", script={SCENE: [GOOD], AUDIO_M: [AUDIO],
                                            VISUAL_M: [VISUAL], DIRECTOR: [APPROVE]})
    solo_m = ScriptedLlm(model="s", script={"whole game-design team": [SOLO]})
    reqs = [{"id": "R1", "request": "Герой іде темним коридором лікарні."}]
    rows = asyncio.run(experiment(build_workflow(team_m), build_solo_agent(solo_m), reqs, 0))
    assert {r["system"] for r in rows} == {"team", "solo"}
    team = next(r for r in rows if r["system"] == "team")
    solo = next(r for r in rows if r["system"] == "solo")
    assert team["llm_calls"] == 4 and solo["llm_calls"] == 1
    write_blind(rows, tmp_path / "blind")
    reports = list((tmp_path / "blind").glob("report_*.md"))
    assert len(reports) == 2 and all("## Рішення" not in p.read_text("utf-8") for p in reports)
    with open(tmp_path / "blind" / "scores.csv", "w", encoding="utf-8") as f:
        f.write("blind_id,score_0_2\n01,2\n02,1\n")
    with open(tmp_path / "results.csv", "w", newline="", encoding="utf-8") as f:
        pub = [{k: v for k, v in r.items() if k != "_report"} for r in rows]
        w = csv.DictWriter(f, fieldnames=pub[0].keys())
        w.writeheader()
        w.writerows(pub)
    summary = unblind(tmp_path / "results.csv", tmp_path / "blind", tmp_path / "s.csv")
    assert {s["system"] for s in summary} == {"team", "solo"}
