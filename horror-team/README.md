# horror-team — мультиагентна система на Google ADK 2.x

Команда агентів проєктує сцену для психологічного горору на Unity: біти й криву страху,
звук, візуальні ефекти, репліки внутрішнього голосу (Yarn Spinner). Крива страху
виводиться у форматі 0..1 для `FearLevelController`.

```bash
uv sync                                   # або: pip install google-adk pytest
cp .env.example .env                      # вписати GEMINI_API_KEY
uv run pytest -q                          # 14 тестів без API
agents-cli playground                     # ADK Playground
uv run python run_cli.py "Герой заходить у покинуту дитячу лікарню..."
uv run python run_cli.py "..." --mode solo|coordinator
uv run python -m eval.run_experiment      # експеримент + сліпа оцінка
```
Граф: `docs/graph.md`. Звіт: `docs/report.md`. Паспорт: `MAS-CARD.md`.
