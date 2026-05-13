---
name: ingest-research
description: "Обработка research-файла: распространение выводов по базе знаний (BLUEPRINT, entities/INDEX, KNOWLEDGE_LOG). Триггеры: '/ingest-research', 'ingest исследование', 'обработай research', 'распространи выводы'."
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, AskUserQuestion, TodoWrite
---

# Ingest Research

Обрабатывает research-файл и распространяет его выводы по базе знаний.

## Когда использовать

- После создания нового исследования
- Когда research-файл существует, но его выводы не отражены в BLUEPRINT
- По рекомендации `/lint-knowledge-base` (suggested actions)

## Входные данные

Путь к файлу исследования. Примеры:
- `/ingest-research researches/retention-after-onboarding/README.md`
- `/ingest-research` (без аргумента — спросить у пользователя какой файл)

## Алгоритм

### Шаг 1. Определить контекст

1. Определить расположение research-файла: `researches/<slug>/README.md`
2. Прочитать текущее состояние целевых файлов (BLUEPRINT.md, KNOWLEDGE_LOG.md) — чтобы знать что обновлять

### Шаг 2. Извлечь из исследования

Прочитать research-файл. Извлечь:

| Что | Где искать | Пример |
|-----|-----------|--------|
| Ключевые метрики | Таблицы, числа в тексте | `Retention D7: 38%` |
| Baseline значения | Таблицы с текущими значениями | `DAU: 1200` |
| Гипотезы | Секции «Гипотезы», «Hypotheses» | `H1: Онбординг слишком длинный` |
| Выводы | Секции «Выводы», «Conclusions», «Key findings» | `Workout completion rate — 62%` |
| Следующие шаги | Секции «Next steps», «Следующие шаги» | `Интервью с пользователями` |
| Период данных | Заголовок, метаданные | `Q1 2026` |
| Источник данных | Метаданные | `SQLite data/fitflow.db` |

### Шаг 3. Обновить файлы

Для каждого файла: проверить существует ли файл. Если да — обновить. Если нет — пометить в отчёте.

**Bidirectional sync (split-pair):**
- Если research имеет непустой `spawned_projects: [<project_artifact_id>, ...]` — для каждого проекта проверить `projects/<slug>/README.md` frontmatter:
  - Если `related_researches` НЕ содержит artifact_id текущего research → добавить (Edit project frontmatter, diff-aware: только если реально меняется).
- Если research имеет `decision_status: committed` И непустой `spawned_projects`:
  - Sanity check: research README должен иметь `## Решение` секцию с `### Передача в проект`. Если её нет → пометить в отчёте `⚠️ research committed, но missing ## Решение → ### Передача в проект`.
  - В `projects/<slug>/README.md` body — проверить, есть ли секция/блок «Discovery → research» с link на research artifact_id. Если нет — пометить рекомендацию (не правим автоматически, потому что body структура проектов разная).
- Conflict: если `<project>.related_researches` указывает на ДРУГОЙ research (не текущий) — НЕ перезаписывать, пометить в отчёте: `⛔ bidirectional conflict: <research>.spawned_projects=[<project>], но <project>.related_researches=[<other_research>]`.

**BLUEPRINT.md:**
- Найти секцию метрик → обновить baseline значения
- Пометка: `[← ingest: <filename>, <date>]` рядом с обновлённым значением
- Если есть гипотезы, которые могут стать backlog items → добавить в секцию бэклога с пометкой `[← ingest]`
- НЕ менять приоритеты, НЕ удалять существующие items

**entities/INDEX.md** (если существует):
- Если research упоминает новые сущности (User, Workout, Session, etc.) → проверить есть ли они в INDEX.md
- Если новая сущность не задокументирована → пометить в отчёте: «Рассмотреть добавление entity-страницы»
- НЕ добавлять entity-страницы автоматически — только рекомендовать

**KNOWLEDGE_LOG.md:**
- Append новую запись типа `ingest`:

```
## [YYYY-MM-DD] ingest | <Research Title>
- **Source:** <источник данных из метаданных research>
- **Updated:** <список файлов, которые были обновлены>
- **Key finding:** <главный вывод, 1-2 предложения>
- **Open questions:** <из секции «Следующие шаги» research>
```

### Шаг 4. Сформировать diff-отчёт

```
📥 Ingest: <filename>

Updated files:
  ✏️ BLUEPRINT.md
     - <что изменилось: конкретные метрики и значения>
  ✏️ KNOWLEDGE_LOG.md
     - New entry: [date] ingest | <title>

⚠️ Attention:
  - <файлы которых нет: «BLUEPRINT.md не найден — создать?»>
  - <метрики без соответствия: «Метрика X из research не найдена в BLUEPRINT»>
  - <гипотезы требующие решения: «5 гипотез — review какие идут в бэклог»>
  - <новые сущности: «Упомянута сущность Y — рассмотреть entities/Y.md»>
```

### Шаг 5. Провязка

- Если обнаружены рассинхроны между файлами → предложить `/lint-knowledge-base`

## Правила

- **Цитировать, не переписывать** — выводы из research берутся as-is
- **Добавлять, не удалять** — старые данные не удаляются, обновляются с пометкой источника
- **Не принимать решений о приоритетах** — помечать `[← ingest]`, человек решает
- **Каждая цифра — с источником** — формат: `значение (период, источник: filename)`
- **Не запускается автоматически** — только по явному вызову
- **Один research за раз** — не батчить несколько researches в одном вызове

## Anti-patterns

- Не переформулировать выводы исследования — цитировать
- Не добавлять метрики в BLUEPRINT автоматически — только обновлять существующие
- Не менять структуру документов — только обновлять значения внутри существующей структуры
- Не батчить несколько researches — один research за раз
