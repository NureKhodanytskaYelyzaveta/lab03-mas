# horror-team: мультиагентна система на Google ADK 2.x

Команда агентів проєктує сцену для психологічного горору на Unity: біти й криву страху,
звук, візуальні ефекти, репліки внутрішнього голосу (Yarn Spinner). Крива страху
виводиться у форматі 0..1 для `FearLevelController`.

```bash
uv sync --extra kb                        # залежності (kb потрібен для кроку 13 і тестів)
cp .env.example .env                      # вписати GEMINI_API_KEY
uv run pytest -q                          # 25 тестів без API
uv run adk web --port 8080 .              # ADK Playground (або agents-cli playground)
uv run python run_cli.py "Герой заходить у покинуту дитячу лікарню..."
uv run python run_cli.py "..." --mode solo|coordinator
uv run python -m eval.run_experiment      # експеримент + сліпа оцінка
uv run python -m eval.run_coordinator     # координатор: 3 запити x 3 повтори
```

## Просунуті кроки
- **Крок 13, база знань із ЛР 2.** Задайте `OBSIDIAN_VAULT` у `.env`, проіндексуйте сховище
  (`uv run python -m kb.indexer`): у графі з'явиться агент-дослідник із `search_knowledge`.
- **Крок 14, людина в циклі.** Сцена зі звуком >= 0.9 або страхом >= 95 перед публікацією
  чекає підтвердження людини (в терміналі `y/n`, у Playground через інтерфейс).

Граф: `docs/graph.md`. Звіт: `docs/report.md`. Паспорт: `MAS-CARD.md`.
