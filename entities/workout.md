# Entity: Workout

Тренировка — основная единица контента в FitFlow.

## Типы

| Тип | Семантика | Длительность |
|---|---|---|
| `yoga` | Йога: hatha, vinyasa, yin | 15–60 мин |
| `hiit` | High-Intensity Interval Training | 10–30 мин |
| `strength` | Силовые тренировки с весом тела или гантелями | 20–45 мин |
| `cardio` | Кардио-тренировки (без оборудования) | 15–45 мин |
| `meditation` | Медитации, дыхательные практики | 5–20 мин |

## Intensity levels

- `low` — beginner / recovery
- `med` — стандартный уровень
- `high` — продвинутый

## Запись в events

При начале тренировки создаётся событие `workout_started` с `properties`:

```json
{
    "workout_type": "yoga",
    "duration_minutes": 25,
    "intensity": "med"
}
```

## Бизнес-смысл

Workout — главная value-unit. Метрика «workouts per active user per week ≥3» — это NSM. Один workout = пользователь сделал шаг к привычке (JTBD).
