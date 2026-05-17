# FitFlow Data Dictionary

## Обзор

SQLite-база `fitflow.db` содержит две таблицы для аналитики FitFlow:
- `events` (107 185 строк) — логи пользовательских событий за период.
- `feedback` (1 224 строки) — обратная связь из всех каналов (NPS, app store reviews, support, in-app).

Подключение из Python:

```python
import sqlite3
conn = sqlite3.connect("data/fitflow.db")
```

## Таблица `events`

Логи пользовательских действий. Один пользователь = много строк.

| Колонка | Тип | Описание | Пример |
|---|---|---|---|
| `event_id` | TEXT (PK) | Уникальный ID события | `evt_a3f9b2c1` |
| `user_id` | TEXT | ID пользователя | `usr_b7e4a8d2` |
| `event_name` | TEXT | Тип события — см. полный список ниже | `workout_started` |
| `event_timestamp` | TIMESTAMP | UTC-время события | `2026-03-15 08:14:23` |
| `platform` | TEXT | `ios` / `android` / `web` | `ios` |
| `properties` | JSON | Доп. свойства события — см. секцию ниже | `{"workout_type": "yoga"}` |

### Значения `event_name` (распределение)

| Event | Кол-во | Семантика |
|---|---|---|
| `workout_started` | 92 948 | Пользователь начал тренировку (нажал Play) |
| `registration` | 3 000 | Пользователь создал аккаунт |
| `subscription_started` | 3 000 | Пользователь начал trial (или подписку) |
| `onboarding_step_1_profile` | 3 000 | Заполнил профиль (возраст, пол, уровень) |
| `onboarding_step_2_goals` | 2 120 | Выбрал фитнес-цели |
| `onboarding_complete` | 1 785 | Завершил онбординг, попал на главную |
| `subscription_cancelled` | 1 332 | Отменил подписку |

### Onboarding funnel

Последовательность для воронки регистрации:

```
registration (3000)
   ↓
onboarding_step_1_profile (3000, 100% conversion)
   ↓
onboarding_step_2_goals (2120, 70.7% conversion)
   ↓
onboarding_complete (1785, 84.2% step / 59.5% overall)
```

Drop-off:
- step 1 → step 2: 880 пользователей (29.3%) теряются. **Самый большой drop-off**.
- step 2 → complete: 335 пользователей (15.8%) теряются.

### Структура `properties` (JSON)

Зависит от типа события. Распространённые ключи:

- Для `onboarding_step_1_profile`: `persona` (`busy_professional` / `young_mom` / `student`), `fitness_level` (`beginner` / `intermediate` / `advanced`), `age_range` (`18-24` / `25-34` / `35-44` / `45+`), `gender` (`male` / `female`).
- Для `workout_started`: `workout_type` (yoga/hiit/strength/cardio/meditation), `duration_minutes`, `intensity` (low/med/high).
- Для `subscription_started`: `plan` (trial/monthly/annual), `price_usd`.
- Для `onboarding_step_2_goals`: `goals` (array of: weight_loss, tone, flexibility, endurance).
- Для `subscription_cancelled`: `reason` (price, motivation_lost, found_alternative, technical_issues, other).

### Persona-приближение

Persona каждого пользователя выводится из `onboarding_step_1_profile.properties.persona`. Distribution (PRODUCT_CONTEXT.md):

| persona | Объём | Возраст | Triggers и боли |
|---|---|---|---|
| `busy_professional` | ~48% (~1455 users) | 25-44 | Утренние / вечерние слоты 20-40 мин, ценит гибкость и прогресс-трекинг |
| `young_mom` | ~26% (~787 users) | 25-34, female | Дневной сон ребёнка 20-30 мин, постродовое состояние, нуждается в beginner-режиме |
| `student` | ~25% (~758 users) | 18-24 | Между лекциями 15-25 мин, ограниченный бюджет, ценит trial |

`fitness_level` (`beginner` / `intermediate` / `advanced`) — самооценка уровня, влияет на onboarding completion и retention.

## Таблица `feedback`

Обратная связь из 5 каналов. Один пользователь может оставить несколько отзывов.

| Колонка | Тип | Описание |
|---|---|---|
| `feedback_id` | TEXT (PK) | Уникальный ID отзыва |
| `user_id` | TEXT | ID пользователя (может быть NULL для анонимных) |
| `feedback_date` | DATE | Дата отзыва |
| `channel` | TEXT | Канал — см. список |
| `rating` | INTEGER | 1–5 (для рейтинговых каналов) или NULL |
| `text` | TEXT | Текст отзыва (на русском) |
| `platform` | TEXT | `ios` / `android` / `web` |

### Распределение по каналам

| channel | Кол-во | Семантика |
|---|---|---|
| `nps_survey` | 351 | Ответы на NPS-опросник в приложении |
| `google_play_review` | 249 | Отзывы из Google Play |
| `in_app_feedback` | 221 | Произвольная обратная связь через кнопку |
| `app_store_review` | 209 | Отзывы из App Store |
| `support_ticket` | 194 | Тикеты в поддержку |

### NPS-семантика (5-балльная шкала)

Для `channel = 'nps_survey'` используется адаптированная 5-балльная шкала:
- `rating` ∈ {1, 2} — детракторы
- `rating` ∈ {3, 4} — нейтралы (passives)
- `rating` = 5 — промоутеры
- `text` — комментарий к оценке (на русском)

NPS-like score (формула): `100 × (count_promoters − count_detractors) / total`.

## Примеры запросов

### Топ событий за период

```sql
SELECT event_name, COUNT(*) AS cnt
FROM events
GROUP BY event_name
ORDER BY 2 DESC;
```

### Onboarding funnel

```sql
WITH steps AS (
    SELECT user_id, MIN(CASE WHEN event_name = 'registration' THEN event_timestamp END) AS t0,
                    MIN(CASE WHEN event_name = 'onboarding_step_1_profile' THEN event_timestamp END) AS t1,
                    MIN(CASE WHEN event_name = 'onboarding_step_2_goals' THEN event_timestamp END) AS t2,
                    MIN(CASE WHEN event_name = 'onboarding_complete' THEN event_timestamp END) AS t3
    FROM events
    WHERE event_name IN ('registration', 'onboarding_step_1_profile',
                          'onboarding_step_2_goals', 'onboarding_complete')
    GROUP BY user_id
)
SELECT
    COUNT(t0) AS registered,
    COUNT(t1) AS step1,
    COUNT(t2) AS step2,
    COUNT(t3) AS complete
FROM steps;
```

### NPS по неделям

```sql
SELECT
    strftime('%Y-W%W', feedback_date) AS week,
    AVG(rating) AS nps_avg,
    COUNT(*) AS responses
FROM feedback
WHERE channel = 'nps_survey'
GROUP BY week
ORDER BY week;
```

## Кредиты

Данные — синтетические, оригинал из [Working-in-IT/agentic-analytics-workshop](https://github.com/Working-in-IT/agentic-analytics-workshop).
