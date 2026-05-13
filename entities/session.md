# Entity: Session

Сессия использования приложения — последовательность событий одного пользователя без долгих перерывов.

## Определение

Сессия — последовательность событий одного `user_id`, где разрыв между соседними событиями ≤30 минут. После 30+ минут паузы — новая сессия.

## Как считать в SQL

```sql
WITH event_gaps AS (
    SELECT user_id, event_timestamp,
           julianday(event_timestamp) -
             LAG(julianday(event_timestamp)) OVER (PARTITION BY user_id ORDER BY event_timestamp)
             AS gap_days
    FROM events
)
SELECT user_id,
       COUNT(*) FILTER (WHERE gap_days IS NULL OR gap_days * 24 * 60 > 30) AS sessions
FROM event_gaps
GROUP BY user_id;
```

## Зачем

Sessions — promxy для engagement. Метрики сессий:

- Длительность сессии.
- События в сессии (например, сколько `workout_started` за одну сессию).
- Возвратность сессий (сколько сессий в неделю на пользователя).

Не путать с `workout` — workout это событие внутри сессии, сессия может содержать 0 или больше тренировок.
