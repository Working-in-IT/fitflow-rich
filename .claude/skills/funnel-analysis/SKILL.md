---
name: funnel-analysis
description: "Анализ конверсионной воронки с поиском drop-off в продукте FitFlow на основе event-логов в SQLite-таблице events. Используй этот скилл ВСЕГДА когда пользователь просит 'воронка', 'funnel', 'найди drop-off', 'почему падает conversion', 'где люди отваливаются', 'разбери воронку', 'funnel analysis', '/funnel-analysis', 'где ломается воронка', а также когда нужно понять на каком шаге пользователи отсеиваются, сравнить conversion между сегментами (platform / source / persona), или проверить не упал ли event volume после релиза. Скилл валидирует дизайн воронки (sequential / mutually exclusive / exhaustive), считает step-over-step и overall conversion, находит biggest drop-off по impact score, разбивает по сегментам, проверяет аномалии в event volume, выдаёт drop-off insights в формате Evidence / Hypothesis / Recommendation с привязкой к business outcome (например, trial→paid conversion)."
version: 0.1.0
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion, Glob, Grep
---

# Funnel Analysis

Скилл строит конверсионную воронку из event-логов SQLite-базы FitFlow (data/fitflow.db) и отвечает на вопрос «**где именно ломается путь пользователя**». На выходе — research-артефакт с funnel-таблицей, biggest drop-off insights в формате Evidence / Hypothesis / Recommendation, разбивкой по сегментам и проверкой аномалий event volume.

## Когда использовать

```
Запрос пользователя?
│
├─ "воронка [funnel]"                        → Полный цикл
├─ "найди drop-off в [funnel]"               → Полный цикл
├─ "почему падает conversion"                → Полный цикл
├─ "разбери воронку [feature/flow]"          → Полный цикл
├─ "funnel для [сценарий]"                   → Полный цикл
├─ "/funnel-analysis [funnel]"               → Полный цикл
├─ "сравни conversion по platform/persona"   → Шаги 1-4 + сегментация
└─ "не упал ли event volume после релиза"    → Шаг 5 + контекст
```

## Аргументы

- **funnel_name** (рекомендуемый): что за воронка («onboarding», «trial_to_paid», «workout_completion»). Если не указано — спроси.
- **period_days** (опционально, по умолчанию `30`).
- **time_window** (опционально, по умолчанию `7d`): за какое время пользователь должен пройти всю воронку.

## Источник

Адаптировано из [nimrodfisher/data-analytics-skills](https://github.com/nimrodfisher/data-analytics-skills/tree/main/03-data-analysis-investigation/funnel-analysis) (использовано с атрибуцией, no LICENSE).

## Глоссарий

Для коллег без бэкграунда в продуктовой аналитике.

**Про воронку:**
- **Воронка (funnel)** — упорядоченная последовательность шагов, через которую пользователь проходит к целевому действию. Пример: «регистрация → онбординг → первая тренировка → подписка».
- **Шаг воронки (step)** — конкретное событие из event-лога, обязательное для прохождения.
- **Step-over-step conversion** — `users_at_step_N / users_at_step_N-1`. Отвечает на вопрос: «Сколько процентов из дошедших до шага N-1 перешли на шаг N?»
- **Overall conversion** — `users_at_step_N / users_at_step_1`. Отвечает на вопрос: «Из всех зашедших в воронку, сколько дошли до шага N?»
- **Drop-off** — пользователи, которые дошли до шага N-1, но не дошли до шага N.
- **Impact score** — `dropoff_n × value_per_user`. Позволяет приоритизировать drop-off: 40% drop-off на шаге 2 при 10k пользователях больнее, чем 40% drop-off на шаге 5 при 100 пользователях.
- **Time-to-convert** — медиана, P75, P95 времени между двумя шагами для тех, кто их прошёл. Долгая пауза может означать трение, даже если drop-off небольшой.

**Про время:**
- **Time window** — за какой период от первого шага пользователь обязан пройти все остальные. Если `7d` и пользователь дошёл до шага 4 на 8-й день — он считается «отвалившимся».
- **Open-ended funnel** — без time window (пользователь может дойти когда угодно). Подходит для воронок, которые могут длиться неделями (освоение новой фичи, возвращение к тренировкам).
- **Time-bounded funnel** — фиксированное окно. Подходит для onboarding или daily-сценариев.
- **Cohort-based funnel** — группировка пользователей по дате старта + наблюдение за фиксированный период. Нужно для честного сравнения «период-к-периоду».

**Про сегментацию:**
- **persona** — тип пользователя, выводится из `onboarding_step_1_profile` (поле `properties` в событии). Базовый dimension для FitFlow.
- **properties** — JSON-поле в событиях SQLite-таблицы `events`, где лежат `platform`, `source`, `persona` и другие атрибуты. Путь: `json_extract(properties, '$.platform')`.

## Связь с базой знаний

Перед стартом прочитай:
1. `BLUEPRINT.md` — что это за продукт, какие ключевые сценарии (часто из BLUEPRINT понятно, какие воронки имеют смысл).
2. `PRODUCT_CONTEXT.md` (если есть) — определения метрик, baseline conversion.
3. `data/README.md` — схема таблицы `events` (особенно где лежит `properties` и какие там поля).

## Процесс

### Фаза 0. Уточнение event-модели funnel

Перед анализом определи 4 вещи через `AskUserQuestion` (или из контекста, если очевидно):

1. **Шаги funnel** — упорядоченный список событий. Пример для FitFlow «onboarding funnel»:
   - `registration` → `onboarding_step_1_profile` → `onboarding_step_2_goals` → `onboarding_complete`
2. **Event table** — SQLite-таблица `events` в `data/fitflow.db`.
3. **Time window** — за сколько пользователь должен пройти воронку (`24h`, `7d`, `30d`, `open-ended`).
4. **Dimensions для сегментации** — `persona` (из `onboarding_step_1_profile`) опционально; из `properties`: `platform`, `source`. Путь — например `json_extract(properties, '$.platform')`.

Если у тебя есть продуктовый дефолт для этой воронки (из BLUEPRINT или прошлых исследований) — предлагай как Recommended, но дай переопределить.

### Шаг 1. Определи шаги и валидируй design

Прежде чем считать цифры — проверь, что шаги воронки удовлетворяют 4 принципам (детально в `references/funnel_design_guide.md`):

1. **Sequential** — пользователь не может попасть на шаг N, не пройдя N-1. Если может — это не воронка, это набор событий.
2. **Mutually exclusive** — каждый пользователь считается один раз на шаге за период. Без дедупликации цифры будут завышены.
3. **Exhaustive within scope** — нет пропущенных шагов между двумя соседними, которые могли бы объяснить drop-off.
4. **Anchored to denominator** — шаг 1 определяет знаменатель для всех conversion. Чётко зафиксируй, кого считаем «зашедшим в воронку».

Если хотя бы один принцип нарушен — **остановись и сообщи**: «текущий дизайн funnel приведёт к неверным цифрам». Лучше переопределить шаги, чем выдать запутывающий отчёт.

### Шаг 2. Conversion + time-to-convert

Построй user-level dataset:
- Для каждого пользователя, дошедшего до шага 1 — отметь, какие следующие шаги он прошёл и когда (в пределах time window).
- Для каждого шага посчитай:
  - `users_at_step_N`
  - `step_conversion = users_at_step_N / users_at_step_N-1`
  - `overall_conversion = users_at_step_N / users_at_step_1`
  - `dropoff_n = users_at_step_N-1 − users_at_step_N`
  - `dropoff_rate = 1 − step_conversion`

Дополнительно для time-to-convert между шагами:
- `median_time_to_step_N` — медианное время от предыдущего шага до текущего
- `p75_time_to_step_N`, `p95_time_to_step_N` — для понимания хвостов

**Используй `scripts/funnel_analyzer.py`** для расчёта таблицы. Скрипт принимает steps + counts (+ опционально сегменты) и выдаёт готовую таблицу с conversion / drop-off / impact score. Это избавляет от ручного расчёта и одинаковых ошибок.

SQL-каркас для извлечения counts — в `references/funnel_design_guide.md` раздел «SQL templates».

Для выполнения SQL-запросов к SQLite используй:
```bash
sqlite3 data/fitflow.db "SELECT ..."
```

### Шаг 3. Найди biggest drop-off

Используй **impact score**, не только процент:

```
impact_score = dropoff_n × value_per_user_at_step
```

Где `value_per_user_at_step` — оценка того, насколько ценно довести этого пользователя до конца. Для FitFlow это связано с business outcome (например, trial→paid conversion):
- **Conversion value** — если каждый дошедший до конца становится платным пользователем или возвращается к тренировкам регулярно.
- **Conversion remaining steps** — если уцелевшие пользователи имеют conversion 60% до конца воронки, recovery_value = dropoff_n × 0.6 × value_per_completion.

Шаг с максимальным `impact_score` (не максимальным процентом drop-off!) — это место, куда стоит вкладывать усилия команды.

### Шаг 4. Сегментация drop-off

Прогони воронку отдельно по сегментам и найди, где разрыв «лучший vs худший» сегмент особенно большой. Это самые ёмкие источники гипотез.

**Основная сегментация:** по `persona` (выводится из `onboarding_step_1_profile`).
**Опциональная** (если есть в данных): `platform`, `source`.

**Где лежат dimensions:**
- В таблице `events` — в JSON-поле `properties`: `json_extract(properties, '$.platform')`.
- Для persona — искать среди событий `onboarding_step_1_profile` и джойнить по `user_id`.
- Если нужного dimension нет — спроси у пользователя путь или вынеси в «не вошло».

Для каждого сегмента посчитай overall_conversion + step_conversion. Ранжируй и найди:
1. Сегмент с самой низкой overall conversion (где найти opportunity)
2. Сегмент с самой высокой (что переносить на остальных).
3. **Шаг, на котором разрыв максимален** — это и есть «локация» проблемы.

### Шаг 5. Event volume check

Прежде чем интерпретировать drop-off — проверь, не сломан ли event log сам по себе. Типичные источники путаницы:

1. **Резкое падение event volume** — релиз сломал инструментирование. Drop-off в воронке может быть артефактом, а не реальной проблемой.
2. **Резкий всплеск** — наоборот, новое событие или дубликаты (один шаг считается дважды).
3. **Сдвиг в долях между шагами** — могло переименоваться событие или появиться новое выше по воронке.

Что проверить:
- Weekly trend по каждому шагу за последние 8 недель.
- Сравнение текущего периода с предыдущим (same length).
- Алерт если изменение >±30% week-over-week — пометь как `[⚠️ возможно инструментирование]` и обсуди с командой.

Если volume стабилен — drop-off можно интерпретировать как реальное продуктовое явление. Если нет — сначала разобраться с инструментированием.

### Шаг 6. Синтез — Drop-off insights в E/H/R

Из материалов шагов 2-5 сформируй 2-5 **Drop-off Insights** (не более — каждый должен быть substantial). Каждый — в формате Evidence / Hypothesis / Recommendation.

## Формат Drop-off Insight (E / H / R)

```markdown
### Drop-off Insight N: <шаг — короткое название>

**Evidence (что мы видим в данных):**
- Шаг, на котором произошёл drop-off, и абсолютные цифры с источником.
- Impact score: dropoff_n × value.
- Сегментная картина: где разрыв максимален.
- Time-to-convert: если медиана/P95 высокая — отметь.
- Event volume: подтверди, что drop-off не артефакт инструментирования.

**Hypothesis (почему):**
- H1: «Если <причина>, то <наблюдение>». Связка с продуктовым контекстом (JTBD, persona, релизы).
- H2 (альтернативная если есть).
- `[❓ требует валидации]` если уверенность низкая.

**Recommendation:**
- Действие — конкретное, измеримое.
- **Рычаг:** `conversion ↑` (увеличить долю прошедших шаг) или `time_to_convert ↓` (ускорить переход).
- **Эффект на business outcome** — оценка влияния на trial→paid conversion или retention.
- **Сценарий проверки** — A/B-тест, замер до/после, интервью с пользователями.
- **Приоритет** — L / M / H, по impact_score.
```

## Структура research-артефакта

Скилл создаёт research-артефакт:

```
researches/funnel-<funnel_slug>-<YYYY-QN>/
├── README.md          # frontmatter, навигация, TL;DR
├── findings.md        # сырые наблюдения по шагам 1-5
├── REPORT.md          # итог: funnel table + drop-off insights в E/H/R
└── sql/
    ├── funnel_counts.sql
    ├── funnel_segments.sql
    └── event_volume.sql
```

**В REPORT.md обязательны:**
- Funnel table (steps, users, step_conversion, overall_conversion, dropoff_n, dropoff_pct).
- Highest impact drop-off block.
- Segment breakdown (минимум по persona).
- Event volume check.
- 2-5 drop-off insights в E/H/R.
- Что НЕ вошло (известные слепые зоны).

Шаблоны и подробности — в `references/output_template.md`.

## Привязка к метрикам

Каждый drop-off insight указывает:
1. **Рычаг**: `conversion` (доля прошедших шаг) или `time_to_convert` (время до завершения).
2. **Текущее значение** (baseline) — step_conversion или median_time_to_step.
3. **Целевое значение** — реалистично, не «удвоить».
4. **Эффект на business outcome** — оценка влияния на trial→paid conversion или retention (ключевые метрики FitFlow).

Если рычаг определить невозможно — пометь `[❓ требует обсуждения]`, не выдумывай связь.

## Anti-patterns

- **Считать только конечный overall conversion** — теряется информация о том, где именно ломается. Всегда давай step-over-step таблицу.
- **Брать топ-drop-off по проценту, а не по impact score** — большой процент на маленьком сегменте даёт меньше пользы, чем средний процент на большом.
- **Не дедуплицировать пользователей** — один пользователь с 5 повторами шага 1 не должен считаться как 5 пользователей. Сравнения нужно делать на уровне `DISTINCT user_id`.
- **Сегментировать только по самому крупному dimension** — низкая conversion в крупном сегменте может быть mix-эффектом.
- **Не проверять event volume перед интерпретацией drop-off** — половина «вдруг упавших conversion» оказывается артефактами инструментирования.
- **Сравнивать периоды без cohort'ов** — если в прошлом периоде была другая sample, сравнение нечестное. Используй cohort-based funnel.

## Чеклист перед сдачей REPORT

- [ ] Шаги funnel прошли валидацию (sequential / mutually exclusive / exhaustive / anchored).
- [ ] Funnel table содержит step_conversion + overall_conversion + dropoff_n + dropoff_pct.
- [ ] Biggest drop-off определён по impact_score (не по проценту).
- [ ] Time-to-convert посчитан хотя бы медиана.
- [ ] Сегментация по `persona` + хотя бы одному dimension из `properties` (если есть).
- [ ] Event volume check выполнен — нет аномалий или они помечены.
- [ ] Каждый drop-off insight в формате E/H/R с привязкой к рычагу.
- [ ] SQL-файлы сохранены в `researches/<slug>/sql/`.
- [ ] frontmatter в README.md заполнен (research_question, hypotheses, metrics_impact).
- [ ] KNOWLEDGE_LOG.md обновлён записью.

## Связанные скиллы

- **`analyze-sqlite`** — базовая работа с SQLite. Использовать для ad-hoc SQL внутри шагов.
- **`ingest-research`** — после готового REPORT.md, чтобы распространить выводы.

## Подробнее

- `references/funnel_design_guide.md` — принципы дизайна, SQL templates, mapping dimensions, edge cases.
- `references/output_template.md` — шаблоны README.md / REPORT.md / findings.md / SQL header.
- `scripts/funnel_analyzer.py` — Python: принимает steps + counts (+ опционально сегменты) → funnel-таблица + impact score + biggest drop-off. Запускать как `python3 funnel_analyzer.py --demo` для примера.
