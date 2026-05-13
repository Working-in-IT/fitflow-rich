---
name: create-research
description: "Скаффолдинг нового исследования: создаёт `researches/<slug>/` по канонической структуре, интерактивно заполняет frontmatter (research_question, hypotheses, metrics_impact). Триггеры: '/create-research', 'создай исследование', 'новый research', 'оформи исследование'."
allowed-tools: Read, Write, Edit, Glob, Bash, AskUserQuestion, TodoWrite
---

# Create Research

Создаёт новый research-артефакт по канонической структуре.

Канонический артефакт исследования состоит из:
- `researches/<slug>/README.md` — frontmatter + постановка вопроса + решение
- `researches/<slug>/findings.md` — лабораторные заметки (living document, не публикуется)
- `researches/<slug>/REPORT.md` — финальный отчёт (создаётся после завершения)
- `researches/<slug>/sql/` — SQL-запросы (создаётся по мере необходимости)
- `researches/<slug>/figures/` — графики и диаграммы (создаётся по мере необходимости)

## Когда использовать

- Нужно начать новое исследование по продукту
- Уже есть `<slug>.md` старого формата → надо мигрировать в каноническую структуру (использовать вместе с pre-fill из существующего файла)
- Brainstorm → research (после `superpowers:brainstorming` определена тема, надо завести артефакт)

## Входные данные

```
/create-research [slug]
```

- `slug` — kebab-case, **без даты** (дата в slug = период данных, не дата работы). Если не задан — сгенерировать из title.

## Алгоритм

### Шаг 1. Определить целевую папку

Целевая папка: `researches/<slug>/`

Если папка `<slug>` уже существует — **СТОП**. Не перезаписывать. Сообщить пользователю и предложить новый slug.

### Шаг 2. Собрать frontmatter через AskUserQuestion

Минимально необходимый набор (одним батчем `AskUserQuestion`, multiSelect=false):

| Поле | Вопрос | Дефолт если skip |
|------|--------|------------------|
| `title` | Краткое название (1 строка) | required, не skip |
| `research_question` | Вопрос исследования: что именно хотим понять? | required |
| `period_analyzed` | Период данных (YYYY-MM-DD .. YYYY-MM-DD) | `TBD` |
| `data_sources` | Источники данных (SQLite, CSV, API, etc) | `[TBD]` |
| `metrics_impact.lever` | Какой рычаг двигаем? | options: `retention`, `activation`, `engagement`, `monetization` |
| `metrics_impact.metric` | Конкретная метрика | required |
| `metrics_impact.baseline` | Текущее значение метрики (с источником) | `TBD` |

Опциональные (НЕ спрашивать сразу, оставить плейсхолдеры в README.md для редактирования):
- `hypotheses` (если пользователь явно их назовёт в title/question — извлечь, иначе плейсхолдер)
- `expected_outcome`
- `affected_users` — `TBD`
- `related_projects`, `related_researches` — `[]`
- `decision_status`, `decision_date`, `risks_closed` — `null` / `null` / `[]` (заполняются при переходе research в `published`)

**Living research:** если research долгоиграющий (постоянно обновляется новыми данными, без терминальной фазы), сразу спросить через AskUserQuestion: установить `status: living` (вместо `draft`) с `data_validity: <дата>`. У `living` research НЕ должно быть `published_at`.

### Шаг 3. Сгенерировать slug (если не задан)

Из title → kebab-case, английские слова где можно (термины оставить как есть транслитом):
- "Анализ retention после онбординга" → `retention-after-onboarding`
- "Workout completion rate deep dive" → `workout-completion-rate-deep-dive`

**Проверка:** длина ≤ 60 символов, никаких дат, только `[a-z0-9-]`.

### Шаг 4. Создать структуру артефакта

Создать директорию `researches/<slug>/` и три файла:

1. `README.md` — с frontmatter и структурой (заполнить на шагах 5–6)
2. `findings.md` — лабораторные заметки (пустой скелет)
3. `REPORT.md` — финальный отчёт (пустой скелет, заполняется после завершения)

Папки `sql/`, `figures/` НЕ создавать сейчас — они появятся когда понадобятся.

**Структура README.md frontmatter:**

```yaml
---
type: research
artifact_id: "fitflow:research:<slug>"
slug: <slug>
title: "<Title>"
status: draft
owners: [<login>]
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
research_question: "<вопрос>"
period_analyzed: "TBD"
data_sources: [TBD]
hypotheses: []
metrics_impact:
  lever: TBD
  metric: TBD
  baseline: TBD
  target: TBD
  affected_users: TBD
related_projects: []
related_researches: []
decision_status: null
decision_date: null
risks_closed: []
---
```

### Шаг 5. Заполнить frontmatter README.md

Заменить плейсхолдеры на собранные значения:
- `fitflow:research:<slug>` → реальные значения
- `<slug>` → значение
- `<Title>` → title пользователя
- `created_at` / `updated_at` → сегодня (YYYY-MM-DD)
- `owners` → текущий пользователь (`git config user.email` → login до `@`)
- `research_question`, `period_analyzed`, `data_sources`, `metrics_impact.*` → из ответов пользователя
- Поля, на которые пользователь не ответил → плейсхолдер `TBD` (не удалять поле полностью)

### Шаг 6. Заполнить тело README.md

Раздел `# <Title>` → реальный title.

Секцию `## Вопрос исследования` → развёрнутая формулировка из `research_question`.

Остальные секции оставить плейсхолдерами. Пользователь дополнит вручную:

```markdown
## Почему сейчас

_TBD_

## Гипотезы

| ID | Гипотеза | Статус |
|----|----------|--------|
| H1 | _TBD_ | draft |

## Метод

_TBD_

## Ожидаемый исход

_TBD_

## Решение

_Заполняется при переходе в `status: published`._

### Что решили

_TBD_

### Почему сейчас — какие риски сняты

_TBD_

### Обоснование выбора варианта

_TBD_

## Ссылки

- _TBD_
```

**Секция `## Решение`** — оставить плейсхолдеры. Будет заполнена когда research переходит в `status: published`.

### Шаг 7. Создать findings.md и REPORT.md

`findings.md`:
```markdown
# <Title> — Findings (Lab)

_Лабораторные заметки. Не публикуется. Здесь — сырые данные, промежуточные расчёты, тупики._
```

`REPORT.md`:
```markdown
---
type: report
artifact_id: "fitflow:research:<slug>"
slug: <slug>
title: "<Title> — REPORT"
status: draft
owners: [<login>]
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
---

# <Title> — REPORT

_Финальный отчёт. Заполняется после завершения анализа._
```

### Шаг 8. Записать в KNOWLEDGE_LOG.md

Append в `KNOWLEDGE_LOG.md` в корне репозитория:

```
## [YYYY-MM-DD] create-research | <Title>
- **Path:** researches/<slug>/
- **Question:** <research_question>
- **Lever:** <metrics_impact.lever> → <metric>
- **Status:** draft
```

### Шаг 9. Подсказка пользователю

Вывести:

```
✅ Research создан: researches/<slug>/

Следующие шаги:
1. Заполнить плейсхолдеры в README.md:
   - Гипотезы (таблица H1/H2/...)
   - Метод
   - Ожидаемый исход
2. Начать findings.md по мере анализа
3. После завершения — заполнить REPORT.md финальными выводами
4. После публикации — `/ingest-research researches/<slug>/README.md` для распространения по BLUEPRINT
```

## Edge cases

- **Slug коллизия:** если `researches/<slug>/` уже существует — СТОП, предложить новый slug.
- **Trailing whitespace в title:** strip.
- **Несуществующая папка `researches/`:** создать автоматически.

## Структура артефакта (inline reference)

```
researches/<slug>/
  README.md      — frontmatter + постановка + решение (публикуемый)
  findings.md    — лабораторные заметки (внутренний)
  REPORT.md      — финальный отчёт (публикуемый)
  sql/           — SQL-запросы (создаётся по мере необходимости)
  figures/       — графики и диаграммы (создаётся по мере необходимости)
```
