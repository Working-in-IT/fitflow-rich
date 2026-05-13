# Funnel Design Guide

Расширение SKILL.md — методология дизайна воронки + SQL-паттерны + mapping dimensions для FitFlow. Адаптация принципов от [nimrodfisher/data-analytics-skills](https://github.com/nimrodfisher/data-analytics-skills) под контекст SQLite-данных FitFlow.

## 4 принципа корректного дизайна

Воронка корректна, если её шаги удовлетворяют 4 условиям:

### 1. Sequential (последовательность)

Пользователь не может попасть на шаг N, не пройдя N-1. Если может — это не воронка, это набор событий с произвольным порядком.

**Проверка:** для случайной выборки из 10 пользователей, дошедших до шага N, проверь, есть ли у них шаг N-1 раньше по времени. Если у >5% нет — воронка не последовательна.

**Anti-pattern:** «открыл дашборд» и «просмотрел метрику» — не имеют чёткой последовательности (открыть метрику можно из любого места).

### 2. Mutually exclusive (уникальность)

Каждый пользователь считается ОДИН раз на шаге за период. Без дедупликации цифры будут завышены, conversion упадёт ниже реального.

**Проверка:** счёт через `COUNT(DISTINCT user_id)`, не `COUNT(*)`.

**Anti-pattern:** «5 раз открыл редактор → засчитываем 5 раз шаг 1». На самом деле это один пользователь.

### 3. Exhaustive within scope (полнота)

Нет пропущенных шагов между двумя соседними, которые могли бы объяснить drop-off.

**Пример:** funnel «execute_query → save_query» пропускает шаг «query_returned_results». Если 20% запросов падают с ошибкой, drop-off спутается с шагом execute. Правильная воронка: `execute_query → query_returned_results → save_query`.

**Проверка:** перед фиксированием шагов спроси у пользователя «какие важные события могут происходить между шагами N и N+1, которые могли бы повлиять на drop-off?»

### 4. Anchored to denominator (заякорённость)

Шаг 1 определяет универсум — кого считаем «зашедшим в воронку». Все conversion рассчитываются относительно него.

**Проверка:** определение шага 1 должно отвечать на вопрос «кто потенциально интересуется этим сценарием?» Если шаг 1 — `view_homepage`, то воронка включает всех, кто зашёл на главную (включая случайных). Если шаг 1 — `click_create_query` — это уже более узкий интент.

**Anti-pattern:** взять шаг 1 «слишком широким» (зашёл на сайт) и потом удивляться, что conversion 0.5%.

## 3 типа conversion rate

### Step-over-step (для поиска места проблемы)

```
step_conversion[N] = users_at_step[N] / users_at_step[N-1]
```

**Когда использовать:** искать, где в воронке самый большой относительный drop-off. Отвечает на вопрос «из дошедших до шага N-1, какая доля перешла на N?».

### Overall (для коммуникации со стейкхолдерами)

```
overall_conversion[N] = users_at_step[N] / users_at_step[1]
```

**Когда использовать:** доносить общее состояние воронки. Отвечает на вопрос «из всех зашедших, какая доля дошла до шага N?».

### Drop-off (абсолютные потери)

```
dropoff_n[N] = users_at_step[N-1] − users_at_step[N]
dropoff_rate[N] = 1 − step_conversion[N]
```

**Когда использовать:** приоритизация. 40% drop-off на шаге с 100 пользователями ≠ 40% drop-off на шаге с 10000 — нужны абсолютные цифры.

## Impact score (приоритизация)

```
impact_score[N] = dropoff_n[N] × value_per_user_at_step[N]
```

Где `value_per_user_at_step` — оценка ценности доведения пользователя до конца воронки. Для FitFlow:

```
value_per_user = conversion_remaining_steps × value_per_paid_user
```

Или прокси: если каждый дошедший до конца с вероятностью P становится платным пользователем — `value = P`.

**Recovery value:**
```
recovery_value[N] = dropoff_n[N] × conversion_remaining_steps × value_per_completion
```

Это «верхняя оценка» того, сколько можно вернуть, если бы drop-off полностью убрали. На практике никогда не получается 100%, но это полезный orientation для прикидки «стоит ли вообще копать».

## Time windows

### Open-ended

Пользователь может дойти до последнего шага когда угодно. Подходит для воронок, длящихся неделями (освоение новой фичи, возвращение к тренировкам).

**Когда:** долгие пути, без явного «срока годности» интента.

### Time-bounded

Фиксированное окно (24h / 7d / 30d). Дошёл позже — считается отвалившимся.

**Когда:** onboarding, daily-сценарии, где «вернусь через 2 месяца» — это уже не та же сессия задачи.

### Cohort-based

Группировка пользователей по дате старта + наблюдение фиксированный период.

**Когда:** период-к-периоду сравнение. Без cohort'ов сравнение этого квартала с прошлым нечестное (другие пользователи, другой состав).

## Mapping dimensions для FitFlow

Стандартное место для dimensions сегментации — JSON-поле `properties` в таблице `events` (SQLite).

| Dimension | Как получить | Примечания |
|-----------|-------------|------------|
| platform | `json_extract(properties, '$.platform')` | `ios` / `android` — мобильная платформа |
| source | `json_extract(properties, '$.source')` | Источник установки / вход |
| persona | из `onboarding_step_1_profile` events — `json_extract(properties, '$.persona')` | Цель пользователя: weight_loss, muscle_gain, etc. |

**Если нужного dimension нет в `properties`:**
1. Посмотри схему таблицы в `data/README.md`.
2. Если поля нет — пометь как `[⚠️ dimension недоступен]` и предложи добавить инструментирование.

## SQL templates

### Funnel counts (шаг 2)

Базовый паттерн — для каждого пользователя отметить, какие шаги он прошёл, потом агрегировать.

```sql
-- SQLite (data/fitflow.db): funnel counts
-- Run: sqlite3 data/fitflow.db < sql/funnel_counts.sql
WITH user_first_step AS (
  -- Шаг 1: кто зашёл в воронку и когда (берём первый раз за период)
  SELECT
    user_id,
    MIN(event_ts) AS step1_ts
  FROM events
  WHERE event_name = '<step_1_event>'
    AND date(event_ts) >= date('now', '-<period> days')
  GROUP BY user_id
),
user_step_completion AS (
  -- Для каждого пользователя — first_ts каждого шага в пределах time window
  SELECT
    ufs.user_id,
    ufs.step1_ts,
    MIN(CASE WHEN e.event_name = '<step_2_event>' THEN e.event_ts END) AS step2_ts,
    MIN(CASE WHEN e.event_name = '<step_3_event>' THEN e.event_ts END) AS step3_ts,
    MIN(CASE WHEN e.event_name = '<step_4_event>' THEN e.event_ts END) AS step4_ts
  FROM user_first_step ufs
  LEFT JOIN events e
    ON e.user_id = ufs.user_id
    AND e.event_ts >= ufs.step1_ts
    AND e.event_ts <= datetime(ufs.step1_ts, '+<time_window> days')
  GROUP BY ufs.user_id, ufs.step1_ts
)
SELECT
  COUNT(*)                                                              AS step1_users,
  SUM(CASE WHEN step2_ts IS NOT NULL THEN 1 ELSE 0 END)                AS step2_users,
  SUM(CASE WHEN step2_ts IS NOT NULL AND step3_ts IS NOT NULL THEN 1 ELSE 0 END) AS step3_users,
  SUM(CASE WHEN step2_ts IS NOT NULL AND step3_ts IS NOT NULL AND step4_ts IS NOT NULL THEN 1 ELSE 0 END) AS step4_users
FROM user_step_completion;
```

**Примечание:** SQLite не поддерживает `COUNT(*) FILTER (WHERE ...)` — используй `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`. Для INTERVAL используй `datetime(ts, '+N days')`.

**Важно:** condition `step3_users` включает `step2_ts IS NOT NULL` — это enforce sequential принцип на уровне SQL (без него можно дойти до step3, миновав step2, что нарушает воронку).

### Funnel by segment (шаг 4)

К `user_step_completion` добавь LEFT JOIN с таблицей персон и/или `json_extract`:

```sql
-- SQLite: funnel by persona segment
... user_step_completion as before ...,
user_persona AS (
  SELECT
    user_id,
    json_extract(properties, '$.persona') AS persona
  FROM events
  WHERE event_name = 'onboarding_step_1_profile'
  GROUP BY user_id
),
user_segments AS (
  SELECT
    usc.*,
    COALESCE(up.persona, '<unknown>') AS persona,
    json_extract(e.properties, '$.platform') AS platform
  FROM user_step_completion usc
  LEFT JOIN user_persona up ON up.user_id = usc.user_id
  LEFT JOIN events e ON e.user_id = usc.user_id AND e.event_ts = usc.step1_ts
)
SELECT
  persona,
  platform,
  COUNT(*) AS step1_users,
  SUM(CASE WHEN step4_ts IS NOT NULL THEN 1 ELSE 0 END) AS step4_users,
  ROUND(1.0 * SUM(CASE WHEN step4_ts IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 3) AS overall_conversion
FROM user_segments
GROUP BY persona, platform
HAVING COUNT(*) >= 20  -- отсекать сегменты слишком маленькие для выводов
ORDER BY step1_users DESC;
```

### Event volume check (шаг 5)

```sql
-- SQLite: event volume check
-- Run: sqlite3 data/fitflow.db < sql/event_volume.sql
SELECT
  strftime('%Y-%W', event_ts) AS week,
  event_name,
  COUNT(*) AS event_count,
  COUNT(DISTINCT user_id) AS unique_users
FROM events
WHERE date(event_ts) >= date('now', '-56 days')  -- 8 weeks
  AND event_name IN ('<step_1>', '<step_2>', '<step_3>', '<step_4>')
GROUP BY strftime('%Y-%W', event_ts), event_name
ORDER BY week DESC, event_name;
```

Сравни последние 1-2 недели с предыдущими 6. Изменение >±30% week-over-week — повод проверить инструментирование.

### Time-to-convert (опционально к шагу 2)

```sql
-- SQLite: time-to-convert (approximate percentiles via subquery)
-- Note: SQLite has no built-in APPROX_PERCENTILE; use Python or manual rank approach
SELECT
  '<step_2>' AS to_step,
  AVG(CAST((julianday(step2_ts) - julianday(step1_ts)) * 86400 AS INTEGER)) AS avg_seconds,
  MIN(CAST((julianday(step2_ts) - julianday(step1_ts)) * 86400 AS INTEGER)) AS min_seconds,
  MAX(CAST((julianday(step2_ts) - julianday(step1_ts)) * 86400 AS INTEGER)) AS max_seconds
FROM user_step_completion
WHERE step2_ts IS NOT NULL;
-- For median/P75/P95 — pipe results to Python: sorted(vals); vals[int(len(vals)*0.5)]
```

## Funnel quality checklist

Перед интерпретацией результатов прогони:

- [ ] **Шаг 1 чётко определён** и отвечает на вопрос «кто потенциально интересуется этим сценарием».
- [ ] **Time window выбран осознанно** — не open-ended «по умолчанию», а в соответствии с природой сценария.
- [ ] **Sequential проверен** — на выборке из 10 пользователей у >95% есть шаг N-1 до шага N.
- [ ] **Дедупликация** — все count'ы через `COUNT(DISTINCT user_id)`.
- [ ] **Между соседними шагами нет «спрятанных»** событий, которые могли бы быть причиной drop-off.
- [ ] **Хотя бы 1 гипотеза для biggest drop-off** есть до того, как пишешь recommendation.
- [ ] **Сегментация хотя бы по одному dimension** проведена.
- [ ] **Event volume проверен** — нет «вдруг упавших» цифр из-за ETL.

## Anti-patterns (чего не делать)

- **Считать на сессиях, а не на пользователях.** Сессия — это сколько раз пользователь зашёл; пользователь — это уникальный человек. Сравнения должны быть на user-level (DISTINCT user_id).
- **Брать первое событие пользователя как шаг 1.** Если пользователь делал что-то 3 раза за период, и каждый раз первый шаг был «open_query_editor» — это всё ещё один user. Не считать каждый «первый event» как отдельного пользователя.
- **Сравнивать total counts разных периодов без cohort'ов.** Прошлый квартал и этот — разные пользователи, разные сезонные эффекты. Используй cohort-based funnel или фиксируй фильтры (new users only / vested users only).
- **Игнорировать конечный шаг.** Если 50% дошли до шага 4, но только 5% — до шага 5, это критично. Не считай overall_conversion только до шага 4.
- **Рекомендация «улучшить UX шага N»** без указания, какая метрика двигается и насколько. Рычаг + baseline + target обязательны.
