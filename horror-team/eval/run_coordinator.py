"""Координатор: 3 запити x 3 повтори -> eval/coordinator_results.csv"""
import asyncio
import csv
from pathlib import Path

from google.adk.models import Gemini
from google.genai import types

from app.agent import MODEL
from app.coordinator import build_coordinator
from run_cli import run_once

QUERIES = [
    "Який звук і ефекти потрібні для сцени в ліфті?",
    "Як побудувати криву страху для сцени в покинутій лікарні?",
    "Спроєктуй сцену в ліфті: структура, звук і візуальні ефекти.",
]


async def main() -> None:
    model = Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=6))
    rows = []
    for q_id, query in enumerate(QUERIES, 1):
        for rep in range(1, 4):
            result = await run_once(build_coordinator(model), query)
            experts = sorted({s["author"] for s in result["trace"]
                              if s["author"].endswith("_expert")})
            rows.append({"query": f"Q{q_id}", "repeat": rep, "experts": "+".join(experts),
                         "llm_calls": sum(result["llm_calls"].values()),
                         "tokens": sum(result["tokens"].values()),
                         "seconds": result["seconds"]})
            print(rows[-1], flush=True)
            await asyncio.sleep(2)
    out = Path(__file__).parent / "coordinator_results.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print("saved:", out)


if __name__ == "__main__":
    asyncio.run(main())
