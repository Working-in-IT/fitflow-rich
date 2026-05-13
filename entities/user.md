# Entity: User

Конечный пользователь FitFlow.

## Lifecycle states

```
registered → trial → paid (monthly | annual) → churned | renewed
```

| State | Условие |
|---|---|
| `registered` | Есть событие `registration`, но нет `subscription_started` |
| `trial` | Есть `subscription_started` с `properties.plan = 'trial'`, прошло <7 дней |
| `paid` | Есть `subscription_started` с `properties.plan` ∈ `monthly`/`annual` |
| `churned` | Есть `subscription_cancelled`, нет последующего `subscription_started` |
| `renewed` | После `paid` — снова `subscription_started` |

## Идентификация

- `user_id` (TEXT) — стабильный ID, никогда не меняется.
- Используется как FK в `events.user_id` и `feedback.user_id`.

## Сегментация

Базовые срезы:

- **По persona** (нет явного поля, выводится через `onboarding_step_1_profile.properties.age_band` + `gender`):
  - «Занятый Профессионал»: возраст 25–45.
  - «Молодая Мама»: возраст 25–35 + female + cтавил «возвращение в форму после родов» как цель.
  - «Студент»: возраст 18–24.
- **По tenure** (через MIN `event_timestamp`):
  - new (≤30 дней)
  - settling (31–90)
  - established (>90)
- **По platform** (`events.platform`):
  - ios / android / web

## Связанные таблицы

- `events.user_id` — все действия пользователя.
- `feedback.user_id` — обратная связь.

## Бизнес-смысл

User — атомарная единица аналитики FitFlow. Все продуктовые метрики (retention, conversion, NSM) считаются на user-level и потом агрегируются.
