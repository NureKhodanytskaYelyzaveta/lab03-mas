"""Експеримент: команда агентів проти одного агента на тих самих запитах.

uv run python -m eval.run_experiment          -> eval/results.csv + eval/blind/
Потім: заповніть eval/blind/scores.csv (оцінка 0-2 за ключем blind_id) і
uv run python -m eval.run_experiment --unblind -> eval/summary.csv
"""
import argparse
import asyncio
import csv
import json
import random
from pathlib import Path

from app.nodes import link_issues, render_report, scene_issues
from run_cli import run_once

HERE = Path(__file__).parent


def metrics(state: dict, result: dict) -> dict:
    """Детерміновані ознаки якості результату + вартість."""
    scene = state.get("scene") or {}
    audio = state.get("audio_plan") or {}
    visual = state.get("visual_plan") or {}
    beats = scene.get("beats", [])
    return {
        "beats": len(beats),
        "scene_issues": len(scene_issues(scene)) if scene else None,
        "link_issues": len(link_issues(scene, audio, visual)) if scene else None,
        "audio_cues": len(audio.get("cues", [])),
        "visual_effects": len(visual.get("effects", [])),
        "peak_fear": max((b.get("fear_target", 0) for b in beats), default=None),
        "drafts": state.get("drafts", 1),
        "stop_reason": state.get("stop_reason", "single call"),
        "llm_calls": sum(result["llm_calls"].values()),
        "tokens": sum(result["tokens"].values()),
        "seconds": result["seconds"],
    }


async def experiment(team, solo, requests: list[dict], pause: float = 2.0) -> list[dict]:
    rows = []
    for item in requests:
        for system, agent in (("team", team), ("solo", solo)):
            result = await run_once(agent, item["request"])
            state = result["state"]
            if system == "solo":
                state = state.get("solo") or {}
            rows.append({"id": item["id"], "system": system, **metrics(state, result),
                         "_report": render_report(state)})
            await asyncio.sleep(pause)  # пауза між запусками: ліміти безкоштовного рівня
    return rows


def write_blind(rows: list[dict], out: Path, seed: int = 7) -> None:
    """Сліпа оцінка: перемішані звіти без назви системи і без рядка «Рішення»."""
    out.mkdir(exist_ok=True)
    order = list(range(len(rows)))
    random.Random(seed).shuffle(order)
    key = []
    for n, i in enumerate(order, 1):
        text = rows[i]["_report"].split("## Рішення")[0].rstrip()
        (out / f"report_{n:02d}.md").write_text(text, encoding="utf-8")
        key.append({"blind_id": f"{n:02d}", "id": rows[i]["id"], "system": rows[i]["system"]})
    with open(out / "key.csv", "w", newline="", encoding="utf-8") as f:  # не відкривати до оцінки
        w = csv.DictWriter(f, fieldnames=["blind_id", "id", "system"])
        w.writeheader()
        w.writerows(key)
    with open(out / "scores.csv", "w", newline="", encoding="utf-8") as f:
        f.write("blind_id,score_0_2\n" + "".join(f"{k['blind_id']},\n" for k in key))


def unblind(results: Path, blind: Path, out: Path) -> list[dict]:
    key = {r["blind_id"]: r for r in csv.DictReader(open(blind / "key.csv", encoding="utf-8"))}
    scores = {r["blind_id"]: float(r["score_0_2"])
              for r in csv.DictReader(open(blind / "scores.csv", encoding="utf-8"))
              if r["score_0_2"].strip()}
    rows = list(csv.DictReader(open(results, encoding="utf-8")))
    summary = []
    for system in ("team", "solo"):
        sel = [r for r in rows if r["system"] == system]
        q = [scores[b] for b, k in key.items() if k["system"] == system and b in scores]
        def avg(col):
            vals = [float(r[col]) for r in sel if r[col] not in ("", "None")]
            return round(sum(vals) / len(vals), 2) if vals else None
        summary.append({"system": system, "quality_0_2": round(sum(q) / len(q), 2) if q else None,
                        "llm_calls": avg("llm_calls"), "tokens": avg("tokens"),
                        "seconds": avg("seconds"), "scene_issues": avg("scene_issues"),
                        "link_issues": avg("link_issues"), "audio_cues": avg("audio_cues"),
                        "visual_effects": avg("visual_effects")})
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=summary[0].keys())
        w.writeheader()
        w.writerows(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unblind", action="store_true")
    args = parser.parse_args()
    if args.unblind:
        for row in unblind(HERE / "results.csv", HERE / "blind", HERE / "summary.csv"):
            print(row)
        return
    from google.adk.models import Gemini
    from google.genai import types

    from app.agent import MODEL, build_workflow
    from app.baseline import build_solo_agent
    model = Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=6))
    requests = json.loads((HERE / "requests.json").read_text(encoding="utf-8"))
    rows = asyncio.run(experiment(build_workflow(model), build_solo_agent(model), requests))
    write_blind(rows, HERE / "blind")
    public = [{k: v for k, v in r.items() if k != "_report"} for r in rows]
    with open(HERE / "results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=public[0].keys())
        writer.writeheader()
        writer.writerows(public)
    for row in public:
        print(row)


if __name__ == "__main__":
    main()
