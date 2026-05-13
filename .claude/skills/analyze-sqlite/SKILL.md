---
name: analyze-sqlite
description: "Разведка SQLite-базы FitFlow: list tables, describe schema, sample queries. Используй когда нужно посмотреть структуру данных, проверить что в таблице, или подобрать колонки для агрегата. Триггеры: 'что в базе', 'опиши таблицу', 'покажи данные', 'analyze sqlite', '/analyze-sqlite'."
version: 0.1.0
allowed-tools: Read, Bash, Write, AskUserQuestion
---

# Analyze SQLite

Скилл проводит разведку SQLite-базы `data/fitflow.db`: перечисляет таблицы, описывает схемы, делает sample-выборки и базовые агрегаты. Используется как первый шаг перед более глубоким анализом (`funnel-analysis`, `product-feedback`).

## Когда использовать

```
Запрос пользователя?
│
├─ "что в базе"                       → list tables + sample
├─ "опиши таблицу [X]"               → describe schema + sample
├─ "покажи распределение [X]"        → GROUP BY + COUNT
├─ "/analyze-sqlite [таблица?]"     → весь цикл разведки
└─ "сколько [event/feedback] [X]"    → agg query
```

## Аргументы

- **db_path** (по умолчанию `data/fitflow.db`).
- **table** (опционально) — если указано, фокус на этой таблице.

## Процесс

### Шаг 1. List tables

```bash
sqlite3 data/fitflow.db ".tables"
```

### Шаг 2. Describe schema каждой таблицы

```bash
sqlite3 data/fitflow.db "PRAGMA table_info(events)"
sqlite3 data/fitflow.db "PRAGMA table_info(feedback)"
```

### Шаг 3. Sample queries

Для events:

```bash
sqlite3 -header -column data/fitflow.db "SELECT * FROM events LIMIT 5"
sqlite3 -header -column data/fitflow.db "SELECT event_name, COUNT(*) FROM events GROUP BY event_name ORDER BY 2 DESC LIMIT 10"
```

Для feedback:

```bash
sqlite3 -header -column data/fitflow.db "SELECT * FROM feedback LIMIT 5"
sqlite3 -header -column data/fitflow.db "SELECT channel, COUNT(*) FROM feedback GROUP BY channel ORDER BY 2 DESC"
```

### Шаг 4. Сверка с data dictionary

Прочитать `data/README.md` — сравнить полученные колонки и значения с заявленными в data dictionary. Если есть расхождения — отметить.

### Шаг 5. Резюме

Выдать пользователю:

- Список таблиц + строк.
- Топ-5 значений ключевых категориальных колонок (event_name, channel).
- Период данных (MIN/MAX event_timestamp).
- Расхождения с data dictionary, если есть.

## Безопасность

- Read-only. Все запросы — `SELECT`, `PRAGMA`, `WITH`. Никаких `UPDATE`/`INSERT`/`DELETE`.
- Если sample-запрос возвращает >100 строк — обрезать в выводе, показать первые 20 + count total.

## Связанные скиллы

- `data-docs` — после разведки, если data dictionary не отражает реальное состояние.
- `funnel-analysis` — глубокий анализ воронок поверх events.
- `product-feedback` — анализ feedback-таблицы.
