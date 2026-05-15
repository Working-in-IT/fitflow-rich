# Подготовка к воркшопу «Агентная аналитика для продактов»

Чтобы во время воркшопа работать руками, а не воевать с установкой, пройди этот чек-лист **за день до эфира**. Если что-то сломается — будет время написать в чат и починить.

**Время на подготовку:** 30–45 минут, если ставишь с нуля. 5 минут, если у тебя уже есть Python, git и Claude Code.

**Что в итоге получишь:**
- Установленный Claude Code в твоей IDE
- Два склонированных репо (`fitflow-bare` и `fitflow-rich`) с готовой SQLite-базой
- Работающая подписка

Если на любом шаге застрял — пиши в чате конференции, поможем разобраться.

## TL;DR — короткий список

1. **Python 3.11+** — для запуска скиллов rich-репо (хи-квадрат, кластеризация фидбэка)
2. **Git** — чтобы склонировать репозитории
3. **IDE** — VS Code, Cursor или JetBrains (любая из трёх)
4. **Claude Code** — расширение для IDE от Anthropic
5. **Активная подписка на Claude** (Pro / Max / Team / Enterprise) или API-доступ
6. **Два репо склонированы** — `fitflow-bare` и `fitflow-rich`
7. **Smoke test пройден** — Claude отвечает на тестовый запрос, SQLite-база читается

Дальше — подробные инструкции по каждому шагу для macOS, Linux и Windows.

## Шаг 1. Python 3.11+

Python нужен для запуска SQL-запросов к локальной базе (модуль `sqlite3` идёт в стандартной поставке) и для скиллов rich-репо, которые используют `scikit-learn` и `scipy`.

**Проверь, что уже стоит:**

```bash
python3 --version
```

Если выводит `Python 3.11.x` или новее — переходи к шагу 2. Если `Python 3.10.x` или младше — ставь свежий.

### macOS

Через [Homebrew](https://brew.sh) (рекомендуемый способ):

```bash
# Установка Homebrew, если его нет
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установка Python
brew install python@3.12

# Проверка
python3 --version
# Ожидаем: Python 3.12.x
```

### Linux (Ubuntu / Debian)

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Проверка
python3 --version
```

Для Ubuntu 22.04 и старше Python 3.11+ может не быть в стандартных репозиториях — используй [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa):

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv
```

### Windows

**Рекомендуемый путь — WSL2** (подсистема Linux в Windows). После установки следуй инструкциям для Linux выше.

Установка WSL2:

```powershell
# Запустить PowerShell от администратора
wsl --install -d Ubuntu
```

После перезагрузки откроется терминал Ubuntu — в нём ставишь Python по Linux-инструкции выше.

**Если нативно (без WSL):**

```powershell
winget install Python.Python.3.12
```

Или скачай установщик с [python.org/downloads](https://www.python.org/downloads/) — обязательно поставь галочку **Add Python to PATH** при установке.

## Шаг 2. Git

Git нужен, чтобы склонировать репозитории воркшопа.

**Проверка:**

```bash
git --version
```

Если выводит версию (любую, от 2.20+) — переходи к шагу 3.

### macOS

```bash
brew install git
```

Или установи [Xcode Command Line Tools](https://developer.apple.com/xcode/resources/), где git идёт в комплекте:

```bash
xcode-select --install
```

### Linux

```bash
sudo apt install -y git
```

### Windows

В WSL — `sudo apt install -y git`. Нативно:

```powershell
winget install Git.Git
```

Или скачай с [git-scm.com/download/win](https://git-scm.com/download/win).

## Шаг 3. IDE и Claude Code

Claude Code — это расширение для IDE от Anthropic, через которое мы общаемся с агентом. Рекомендую **[VS Code](https://code.visualstudio.com/)** — бесплатный, кросс-платформенный, и большинство примеров в документации Claude Code построены вокруг него.

Альтернативы, если уже работаешь в них: [JetBrains IDEs](https://www.jetbrains.com/) (PyCharm, IntelliJ) или [Cursor](https://cursor.com/) — Claude Code поддерживается везде одинаково.

### Установка VS Code

**macOS:**

```bash
brew install --cask visual-studio-code
```

Или скачай .dmg с [code.visualstudio.com/download](https://code.visualstudio.com/download).

**Linux:**

```bash
sudo snap install code --classic
```

Или скачай .deb / .rpm с [code.visualstudio.com/download](https://code.visualstudio.com/download).

**Windows:**

```powershell
winget install Microsoft.VisualStudioCode
```

Или скачай установщик с [code.visualstudio.com/download](https://code.visualstudio.com/download).

### Установка расширения Claude Code

1. Открой VS Code
2. Перейди в Extensions (Cmd+Shift+X на macOS, Ctrl+Shift+X на Linux/Windows)
3. Найди «Claude Code» от Anthropic
4. Нажми Install
5. Перезапусти VS Code

Альтернатива — через терминал:

```bash
code --install-extension anthropic.claude-code
```

Подробная документация: [docs.anthropic.com/en/docs/claude-code](https://docs.anthropic.com/en/docs/claude-code).

### Установка в JetBrains

В Settings → Plugins → Marketplace найди «Claude Code» и установи. После перезапуска IDE появится панель агента.

## Шаг 4. Доступ к Claude

Чтобы Claude Code работал, нужна **активная подписка на Claude** — личная или корпоративная.

Подходит любая из:

- **Claude Pro** ($20/мес) — индивидуальная подписка, для воркшопа хватит с запасом
- **Claude Max** ($100/мес) — если уже пользуешься Claude активно
- **Claude Team / Enterprise** — если в компании подключено
- **API-ключ от Anthropic Console** — для тех, кто предпочитает оплату по факту использования

Оформить подписку: [claude.ai/upgrade](https://claude.ai/upgrade). API-ключ выпускается на [console.anthropic.com](https://console.anthropic.com).

### Подключение в Claude Code

После установки расширения открой панель Claude Code в IDE (значок в боковой панели). При первом запуске он попросит авторизоваться:

- Если у тебя подписка Claude Pro / Max / Team — войди через **Sign in with Claude**
- Если API-ключ — выбери **Use API key** и вставь его

**Если работаешь в компании** — сначала спроси, есть ли корпоративный доступ к Claude или Anthropic API. Многие компании уже подключены и тебе не надо платить из своего кармана.

## Шаг 5. Клонирование репозиториев воркшопа

Два публичных репо на GitHub. Можно сразу клонировать обе:

```bash
# Выбери папку, где будут лежать проекты
cd ~/Projects   # или любая другая

# Клонируем bare-репо (минимальный контекст)
git clone https://github.com/Working-in-IT/fitflow-bare.git

# Клонируем rich-репо (богатый контекст со скиллами)
git clone https://github.com/Working-in-IT/fitflow-rich.git
```

**Хочешь свой форк, чтобы экспериментировать?** Зайди на каждый репо на GitHub, нажми Fork, и клонируй уже свою копию:

```bash
git clone https://github.com/<твой-логин>/fitflow-bare.git
git clone https://github.com/<твой-логин>/fitflow-rich.git
```

## Шаг 6. Зависимости Python для rich-репо

В bare-репо ничего ставить не надо — Claude использует только стандартную библиотеку Python. В rich-репо стоит установить `scikit-learn` и `scipy` для скиллов кластеризации фидбэка и стат-проверок.

### Вариант А — через `uv` (быстрее, рекомендуем)

[`uv`](https://docs.astral.sh/uv/) — современный менеджер пакетов от Astral, в 10–100 раз быстрее `pip`.

Установка `uv`:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Установка зависимостей:

```bash
cd ~/Projects/fitflow-rich
uv venv                           # создаёт виртуальное окружение
source .venv/bin/activate         # на macOS/Linux
# .venv\Scripts\activate          # на Windows
uv pip install scikit-learn scipy numpy
```

### Вариант Б — через `pip` (стандартный путь)

```bash
cd ~/Projects/fitflow-rich
python3 -m venv .venv
source .venv/bin/activate         # macOS/Linux
# .venv\Scripts\activate          # Windows
pip install scikit-learn scipy numpy
```

## Шаг 7. Smoke test — проверка, что всё работает

Это финальная проверка. Если все три пункта проходят — ты готов к воркшопу.

### 7.1. Базы данных читаются

```bash
python3 -c "import sqlite3; print(sqlite3.connect('$HOME/Projects/fitflow-bare/data/fitflow.db').execute('SELECT COUNT(*) FROM events').fetchone())"
# Ожидаем: (107185,)

python3 -c "import sqlite3; print(sqlite3.connect('$HOME/Projects/fitflow-rich/data/fitflow.db').execute('SELECT COUNT(*) FROM events').fetchone())"
# Ожидаем: (107185,)
```

Если выводит `(107185,)` — база на месте, Python с sqlite3 работают.

### 7.2. Скилл product-feedback работает (только для rich-репо)

```bash
cd ~/Projects/fitflow-rich
python3 .claude/skills/product-feedback/product_feedback_analysis.py --db data/fitflow.db --days 90 | head -10
```

Ожидаем вывод со статистикой NPS без ошибок. Если падает с `ModuleNotFoundError: No module named 'sklearn'` — вернись к шагу 6 и поставь зависимости.

### 7.3. Claude Code отвечает

Открой `fitflow-bare` в IDE, открой панель Claude Code и отправь:

```
Прочитай README.md и опиши в одном предложении, что это за репо.
```

Если Claude вернул осмысленный ответ за 10–30 секунд — отлично, ты готов. Если запросил API-ключ или вернул ошибку про баланс — вернись к шагу 4.

## За 15 минут до воркшопа

Финальный быстрый чек:

- [ ] Ноутбук подключён к зарядке
- [ ] Wi-Fi стабильный, по возможности — кабель
- [ ] Telegram, Slack, почта — режим «не беспокоить»
- [ ] IDE открыта, оба репо открыты в отдельных окнах (или вкладках)
- [ ] Claude Code panel виден в обоих окнах
- [ ] Чат с агентом пустой (если запускал тесты — очисти контекст)
- [ ] Ссылка на трансляцию открыта на втором экране или в наушниках на телефоне

## Если что-то не работает

| Симптом | Что делать |
|---|---|
| `python3: command not found` | Шаг 1 не прошёл. Перезапусти терминал после установки. На macOS попробуй `python3.12` вместо `python3`. |
| `git: command not found` | Шаг 2 не прошёл. На macOS запусти `xcode-select --install`. |
| Claude Code не появляется в IDE | Перезапусти IDE. Проверь, что расширение включено (Extensions → Claude Code → Enable). |
| `Authentication error` от Claude | Шаг 4 — проверь, что подписка активна или API-ключ скопирован целиком (формат `sk-ant-api03-...`). Перелогинься в Claude Code. |
| `Rate limit exceeded` | Если на подписке — подожди час или апгрейдни тариф. Если на API — пополни баланс на console.anthropic.com. |
| `ModuleNotFoundError: sklearn` | Шаг 6 — активируй виртуальное окружение (`source .venv/bin/activate`) перед запуском скиллов. |
| SQLite-база не найдена | Проверь, что репо клонирован полностью: `ls fitflow-bare/data/` должен показать `fitflow.db`. |
| Claude Code не видит файлы репо | В Claude Code panel убедись, что выбрана правильная папка как workspace (через File → Open Folder). |

## Полезные ссылки

- 📦 **Репозитории:** [fitflow-bare](https://github.com/Working-in-IT/fitflow-bare) и [fitflow-rich](https://github.com/Working-in-IT/fitflow-rich)
- 📚 **Документация Claude Code:** [docs.anthropic.com/claude-code](https://docs.anthropic.com/en/docs/claude-code)
- 💎 **Подписка на Claude:** [claude.ai/upgrade](https://claude.ai/upgrade)
- 💳 **Anthropic Console (API-ключи):** [console.anthropic.com](https://console.anthropic.com)
- 🐍 **Python:** [python.org/downloads](https://www.python.org/downloads/)
- ⚡ **uv (менеджер пакетов):** [docs.astral.sh/uv](https://docs.astral.sh/uv/)
- 📱 **Канал «Работая в айтишечке»:** [t.me/working_in_it](https://t.me/working_in_it)
- 💬 **Вопросы по подготовке:** в Telegram-канал или Podlodka ProductCrew Discord
