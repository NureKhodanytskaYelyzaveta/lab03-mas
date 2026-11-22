```
START
  │
intake ──reject──► reject
  │ ok
  ▼
scene_designer ◄───────────── fix ──────────────┐
  │                                              │
  ▼                                              │
scene_check ─────────────────────────────────────┤ (fix: невалідна структура)
  │ ok                                           │
  ├───────────────┐  (паралельно, max_concurrency=2)
  ▼               ▼                              │
audio_designer  visual_designer                  │
  │               │                              │
  └──► plans ◄────┘  (JoinNode)                  │
        │                                        │
        ▼                                        │
    link_check ───────── fix ────────────────────┤ (fix: зламані посилання на біти)
        │ ok                                     │
        ▼                                        │
     director                                    │
        │                                        │
        ▼                                        │
      gate ──revise──► scene_designer ───────────┘ (не більше MAX_DRAFTS = 3)
        │ publish
        ▼
     publish ──► звіт користувачу
```
