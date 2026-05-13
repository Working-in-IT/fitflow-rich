# Output Templates

Шаблоны для research-артефакта, который создаёт `funnel-analysis`.

## Структура

```
researches/funnel-<funnel_slug>-<YYYY-QN>/
├── README.md           # навигация + frontmatter
├── findings.md         # сырые наблюдения по шагам 1-5
├── REPORT.md           # итог: funnel table + drop-off insights в E/H/R
└── sql/
    ├── funnel_counts.sql       # шаги 1-2
    ├── funnel_segments.sql     # шаг 4
    └── event_volume.sql        # шаг 5
```

SQL хранится в `researches/<slug>/sql/`.

## README.md (шаблон)

```markdown
---
title: "Funnel Analysis: <Product> / <Funnel Name> (<YYYY-QN>)"
type: research
product: <product-slug>
status: completed   # draft | in_progress | completed
research_question: >
  Где именно в воронке <funnel_name> для <Product> теряются пользователи,
  какие шаги и сегменты больше всего влияют на конверсию, и какие гипотезы
  объясняют наблюдаемые drop-off?
funnel_design:
  steps:
    - step_1: <event_name_1>
    - step_2: <event_name_2>
    - step_3: <event_name_3>
    - step_4: <event_name_4>
  time_window: <"7d" | "open-ended" | "24h">
  segments:
    - persona
    - <platform | source если есть>
hypotheses:
  - "h1: biggest drop-off на шаге <N> объясняется <гипотеза>"
  - "h2: разрыв между persona A и persona B на шаге <N> связан с <гипотеза>"
metrics_impact:
  lever: conversion   # обычно через увеличение step_conversion
  primary_metric: overall_conversion
  baseline: <value>
  potential_effect: <range, e.g. "+X% trial→paid conversion">
period: "YYYY-MM-DD — YYYY-MM-DD"
author: <login or "auto-generated">
date_created: YYYY-MM-DD
sources:
  - data/fitflow.db (events table)
links:
  blueprint: BLUEPRINT.md
  product_context: PRODUCT_CONTEXT.md
---

# Funnel Analysis: <Product> / <Funnel Name> (<YYYY-QN>)

## Навигация

- [REPORT.md](REPORT.md) — итоговая funnel-таблица и drop-off insights в E/H/R
- [findings.md](findings.md) — сырые наблюдения по шагам анализа
- [sql/](sql/) — воспроизводимые запросы

## Контекст

Период: <YYYY-MM-DD> — <YYYY-MM-DD>. Time window: <7d>. Сегментация: `persona` + <platform/source/...>.

## Главные находки (TL;DR)

1. Overall conversion воронки = <X%>. Biggest drop-off — шаг <N> (<step_name>): −<dropoff_n> пользователей (−<pct>%), impact score <value>.
2. <Сегментная разница: лучший vs худший сегмент>
3. <Event volume status: стабилен / есть аномалия на шаге N>

Полные формулировки и обоснования — в REPORT.md.
```

## REPORT.md (шаблон)

```markdown
# Funnel Report: <Product> / <Funnel Name> (<YYYY-QN>)

Период анализа: <даты>. Time window: <7d>. Источники: `data/fitflow.db` (таблица `events`). Аудитория отчёта: <PM/команда продукта/leadership>.

## Executive Summary

Воронка <funnel_name> в FitFlow за <период>: overall conversion <X%>. Biggest drop-off — шаг <N> (<step_name>): теряем <dropoff_n> пользователей (−<pct>% от прошлого шага). По impact score шаг <N> — кандидат №1 на оптимизацию. Ожидаемый эффект на business outcome при реализации топ-1 рекомендации — <оценка влияния на trial→paid conversion>.

Все цифры воспроизводимы через SQL в [sql/](sql/).

## Funnel Design

- **Шаги:** <step_1> → <step_2> → <step_3> → <step_4>
- **Time window:** <7d / open-ended / etc>
- **Шаг 1 (denominator):** все пользователи, сделавшие <step_1_event> хотя бы раз за период.
- **Дедупликация:** на уровне DISTINCT user_id (один пользователь = одно прохождение шага).

Валидация дизайна (см. funnel_design_guide.md):
- Sequential ✅
- Mutually exclusive ✅
- Exhaustive ✅ / `[⚠️ возможен скрытый шаг между N и N+1]` если есть подозрение.
- Anchored to denominator ✅

## Funnel Table

| # | Step | Users | Step conv | Overall conv | Drop-off |
|---|------|------:|----------:|-------------:|---------:|
| 1 | <step_1> | <n> | — | 100.0% | — |
| 2 | <step_2> | <n> | <%> | <%> | −<n> (−<%>) |
| 3 | <step_3> | <n> | <%> | <%> | −<n> (−<%>) |
| 4 | <step_4> | <n> | <%> | <%> | −<n> (−<%>) |

**Overall funnel conversion:** <X%>.

## Highest Impact Drop-off

**Шаг:** <step_name> (с шага N-1 на шаг N).
**Потеряно:** <dropoff_n> пользователей (<dropoff_pct>% относительно шага N-1).
**Impact score:** <value> (см. формулу в funnel_design_guide.md).
**Recovery value:** ~<X> FTE/мес при полном устранении drop-off (верхняя оценка).

Этот шаг — место, где стоит сосредоточить усилия команды.

## Time-to-convert

| Переход | median | P75 | P95 |
|---------|-------:|----:|----:|
| step_1 → step_2 | <s> | <s> | <s> |
| step_2 → step_3 | <s> | <s> | <s> |
| step_3 → step_4 | <s> | <s> | <s> |

<Если P95 на каком-то шаге сильно выше остальных — добавь заметку: «P95 на шаге N показывает хвост в <X> часов, что может означать пользователей с прерванной сессией. Стоит копнуть.»>

## Segment Breakdown

### По persona

| Segment | Step1 users | Step4 users | Overall conv | vs avg |
|---------|------------:|------------:|-------------:|-------:|
| weight_loss | <n> | <n> | <%> | <±pp> |
| muscle_gain | <n> | <n> | <%> | <±pp> |
| general_fitness | <n> | <n> | <%> | <±pp> |
| <unknown> | <n> | <n> | <%> | <±pp> |

**Notable finding:** <сегмент с самым большим разрывом и предварительная гипотеза>.

### По <platform / source> (если есть)

| Segment | Step1 users | Step4 users | Overall conv |
|---------|------------:|------------:|-------------:|
| <value> | <n> | <n> | <%> |

## Event Volume Check

Weekly event count за последние 8 недель по каждому шагу:

| Step | wk-8 | wk-7 | ... | wk-1 (current) | Δ vs prev | Note |
|------|-----:|-----:|----:|---------------:|----------:|------|
| <step_1> | <n> | <n> | ... | <n> | <±%> | <stable / alert> |
| <step_2> | <n> | <n> | ... | <n> | <±%> | |

**Заключение:** event volume стабилен / есть аномалия `[⚠️ возможно инструментирование на шаге N]`.

## Drop-off Insights

### Insight 1: <шаг — короткое название>

**Evidence:**
- Drop-off шаг <N>: <dropoff_n> пользователей (<dropoff_pct>%) [sql/funnel_counts.sql].
- Impact score: <value>.
- Сегментная картина: persona <X> делает этот переход в <pct>% случаев, persona <Y> — только в <pct>% [sql/funnel_segments.sql].
- Time-to-convert: median <s>, P95 <s> — <норм / хвост заметный>.
- Event volume стабилен для шагов 1 и <N>.

**Hypothesis:**
- H1: <«Если <причина>, то <наблюдение>»>. <Связка с продуктовым контекстом — JTBD, persona, release notes>.
- H2 (альтернативная): <другая интерпретация>. `[❓ требует валидации]` если уверенность низкая.

**Recommendation:**
- Действие: <конкретное>.
- Рычаг: `conversion ↑` (увеличить step_conversion с <X%> до <Y%>) | `time_to_convert ↓` (сократить P75 с <s> до <s>).
- Эффект на business outcome: <оценка влияния на trial→paid conversion или retention>.
- Сценарий проверки: <A/B-тест / интервью с пользователями / замер до-после>.
- Приоритет: <L/M/H по impact_score>.

### Insight 2: ...

(Аналогично, 2-5 штук в итоговом отчёте)

## Что не вошло (известные слепые зоны)

- <Сегмент / dimension, по которым данных не хватило>.
- <Что хорошо бы досмотреть в следующей итерации>.
- <Известные ограничения данных>.

## Воспроизводимость

Все цифры воспроизводимы через SQL в [sql/](sql/):
- `funnel_counts.sql` — funnel-таблица + time-to-convert (шаги 2-3).
- `funnel_segments.sql` — сегментная разбивка (шаг 4).
- `event_volume.sql` — weekly trend (шаг 5).

## Связь с базой знаний

После прочтения REPORT — запусти `/ingest-research <этот файл>` для распространения выводов по `BLUEPRINT.md`, `PRODUCT_CONTEXT.md`, `researches/INDEX.md`, `KNOWLEDGE_LOG.md`.
```

## findings.md (шаблон)

```markdown
# Findings: Funnel Analysis <Product> / <Funnel Name> (<YYYY-QN>)

Сырые наблюдения по фазам. Финальная версия — в REPORT.md.

## Фаза 0. Уточнение event-модели

- Шаги funnel: <list>
- Event table: <table>
- Time window: <value>
- Dimensions: <list>
- Обоснование выбора: <если был не очевиден>

## Шаг 1. Валидация design

- Sequential check: <pass / detected violations>
- Mutually exclusive check: <pass / detected>
- Exhaustive check: <list of considered missing steps>
- Anchored denominator: <step_1 definition + sanity check>

## Шаг 2. Funnel counts + time-to-convert

<Сюда — основная таблица + time-to-convert из funnel_analyzer.py>

## Шаг 3. Biggest drop-off

<Какой шаг, impact score, recovery value, почему этот, а не другой>

## Шаг 4. Segment breakdown

<Все сегментные таблицы по persona + optional dimensions>

## Шаг 5. Event volume check

<Weekly counts таблица + интерпретация>

## Открытые вопросы

- <Что хочется доуточнить>.
- <Что не получилось проверить из-за пробелов в данных>.
```

## SQL header (шаблон)

```sql
-- Funnel Analysis: FitFlow / <Funnel Name> (<YYYY-QN>)
-- Step: 2 / funnel counts
-- Period: <YYYY-MM-DD> — <YYYY-MM-DD>
-- Event table: events (data/fitflow.db)
-- Steps: <step_1> → <step_2> → <step_3> → <step_4>
-- Time window: <7d>
-- Run via: sqlite3 data/fitflow.db < funnel_counts.sql
-- Author: <login>
-- Date: <YYYY-MM-DD>

WITH user_first_step AS (
  ...
)
SELECT ...
```
