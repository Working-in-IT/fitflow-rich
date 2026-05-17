# fitflow-rich

**Богатый контекст** для FitFlow — вымышленного мобильного фитнес-приложения. Это репо используется как **A/B-контраст** к [Working-in-IT/fitflow-bare](https://github.com/Working-in-IT/fitflow-bare) в вебинаре [Podlodka ProductCrew](https://podlodka.io/productcrew) «Агентная аналитика для продактов».

## 🚀 Идёшь на воркшоп?

Чтобы работать руками во время эфира — пройди [**SETUP.md**](SETUP.md) **за день до воркшопа**. Там пошаговая инструкция: Python, git, VS Code, Claude Code, доступ к Claude и smoke test. Время на подготовку — 30–45 минут с нуля.

> **📢 Обновление 2026-05-17:** датасет расширен и обогащён (добавлены persona-properties и больше NPS-отзывов). **Если ты уже клонировал репо — выполни `git pull`**. Если есть локальные изменения — сначала `git stash`. Smoke test прежний — пройдёт после обновления.

## Что внутри

```
.
├── CLAUDE.md                  # роль агента, правила, references
├── PRODUCT_CONTEXT.md         # JTBD, 3 персоны, business model, NSM, метрики
├── BLUEPRINT.md               # current state, roadmap, recent decisions
├── KNOWLEDGE_LOG.md           # история продуктовых решений
├── data/
│   ├── fitflow.db             # SQLite: 107K событий + 1.2K отзывов (~350 nps_survey)
│   ├── schema.sql             # CREATE TABLE statements
│   └── README.md              # data dictionary
├── entities/                  # описания доменных сущностей
└── .claude/skills/            # 7 скиллов для аналитической работы
```

## Зачем

Это репо демонстрирует, как **контекст продукта и контекст данных превращают AI-агента в аналитического партнёра**. Тот же агент, тот же вопрос, но с `PRODUCT_CONTEXT.md`, `data/README.md` и skill-pack — даёт product-grounded analysis вместо generic-вывода.

Сравнение — в [fitflow-bare](https://github.com/Working-in-IT/fitflow-bare).

## Как использовать

1. Форкни этот репо.
2. Открой в [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) (или другом агентном IDE, поддерживающем .claude/skills).
3. Задай агенту вопрос — например: «Найди drop-off в onboarding funnel пользователей. Top-2 гипотезы причин, проверь одну хи-квадратом.»
4. Сравни ответ с тем, что даёт [fitflow-bare](https://github.com/Working-in-IT/fitflow-bare) на тот же вопрос.

## Лицензия

MIT — см. [LICENSE](LICENSE).

## Кредиты

- Оригинальные данные: [Working-in-IT/agentic-analytics-workshop](https://github.com/Working-in-IT/agentic-analytics-workshop)
- Вдохновение для skill-pack: [nimrodfisher/data-analytics-skills](https://github.com/nimrodfisher/data-analytics-skills) (no LICENSE, используется с атрибуцией)
- Автор: [Данила Шевцов](https://t.me/workinginit) / Telegram-канал «Работая в айтишечке»
