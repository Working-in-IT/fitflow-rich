---
name: data-docs
description: "Генерация / обновление data dictionary для SQLite-таблиц: читает PRAGMA, делает sample, дописывает data/README.md. Триггеры: 'опиши таблицу [X]', 'обнови data dictionary', 'data-docs для [X]', '/data-docs'."
version: 0.1.0
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# Data Docs

Генерирует или обновляет описание SQLite-таблицы в `data/README.md`. Используется, когда: (1) добавили новую таблицу, (2) добавили колонку, (3) уточняем семантику значений категориальных колонок (например, что значит `event_name = 'X'`).

## Когда использовать

```
Запрос пользователя?
│
├─ "опиши таблицу [X]"              → полный цикл
├─ "обнови data dictionary"          → diff existing vs actual
├─ "data-docs для [X]"               → полный цикл
└─ "/data-docs [X]"                  → полный цикл
```

## Процесс

### Шаг 1. Сверить существующий data dictionary с реальной схемой

```bash
# Прочитать существующий data/README.md
cat data/README.md

# Получить реальную схему
sqlite3 data/fitflow.db "PRAGMA table_info(<table>)"
```

Сравнить:
- Колонки, описанные в data/README.md, но отсутствующие в БД → пометить как «устарели».
- Колонки в БД, но не в data/README.md → нужно дописать.

### Шаг 2. Уточнить семантику колонок (через AskUserQuestion)

Для каждой новой колонки спросить:

- Что означает (1 строка)?
- Тип значений (число / категория / текст / дата)?
- Если категория — какие значения возможны и что они означают?

### Шаг 3. Получить распределение значений категориальных колонок

```bash
sqlite3 -header -column data/fitflow.db \
    "SELECT <column>, COUNT(*) FROM <table> GROUP BY <column> ORDER BY 2 DESC LIMIT 20"
```

### Шаг 4. Обновить `data/README.md`

Добавить / обновить секцию таблицы по шаблону:

```markdown
## Таблица `<table>`

[1-строчное описание]

| Колонка | Тип | Описание | Пример |
|---|---|---|---|
| ... | ... | ... | ... |

### Значения `<column>` (распределение)

| Value | Кол-во | Семантика |
|---|---|---|
| ... | ... | ... |

### Примеры запросов

\```sql
SELECT ...;
\```
```

### Шаг 5. Verify

```bash
# Проверить, что обновлённый README ссылается на правильные колонки
sqlite3 data/fitflow.db "PRAGMA table_info(<table>)" | awk '{print $2}'
grep -E "^\| .{3,30}\s*\|" data/README.md | awk -F'|' '{print $2}'
```

Колонки должны совпадать.

## Связанные скиллы

- `analyze-sqlite` — для первичной разведки.
- `funnel-analysis`, `product-feedback` — потребители data dictionary.
