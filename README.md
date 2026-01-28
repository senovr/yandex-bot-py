# Yandex Messenger Bot Async Client

Асинхронный Python-клиент для Yandex Messenger Bot API.

## Особенности

- ✅ Асинхронный дизайн на основе `asyncio`
- ✅ Полная типизация с `mypy`
- ✅ Мощная система фильтров для обработчиков сообщений
- ✅ Очередь с ограничением размера (bounded queue)
- ✅ Контроль параллельности обработчиков
- ✅ Лимитирование частоты запросов (rate limiting)
- ✅ Автоматический ретрай с экспоненциальным бэкоффом
- ✅ Экологичный выход (graceful shutdown)
- ✅ Структурированное логирование

## Установка

```bash
pip install ymbot-async
```

## Быстрый старт

```python
import asyncio
from ymbot_async import Bot, BotConfig

async def main():
    # Создаем конфигурацию бота
    config = BotConfig(token="your_bot_token")
    
    # Инициализируем бота
    async with Bot(config) as bot:
        # Регистрируем обработчик команды /start
        @bot.message_handler(commands=["start"])
        async def start_handler(update):
            await bot.api_client.send_message(
                chat_id=update.message.chat.id,
                text="Привет! Я бот.",
            )
        
        # Запускаем поллинг
        await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

## Конфигурация

```python
from ymbot_async import BotConfig

config = BotConfig(
    token="your_bot_token",
    
    # HTTP настройки
    timeout_connect=10.0,    # Таймаут подключения (сек)
    timeout_read=30.0,       # Таймаут чтения (сек)
    
    # Rate limiting
    requests_per_second=30,   # Макс. запросов в секунду
    max_concurrent_requests=10,  # Макс. параллельных запросов
    
    # Поллинг
    polling_timeout=1.0,     # Таймаут ожидания обновлений
    polling_limit=100,       # Макс. обновлений за запрос
    polling_backoff=2.0,     # Коэффициент бэкоффа
    polling_max_backoff=30.0, # Макс. бэкофф (сек)
    
    # Диспетчер
    queue_maxsize=1000,      # Размер очереди (0 = без ограничений)
    concurrency=5,           # Параллельность обработчиков
    
    # Логирование
    log_level="INFO",        # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format="json",       # json или console
)
```

## Обработчики сообщений

### Базовый обработчик

```python
@bot.message_handler()
async def echo_handler(update):
    await bot.api_client.send_message(
        chat_id=update.message.chat.id,
        text=update.message.text,
    )
```

### Команды

```python
@bot.message_handler(commands=["start", "help"])
async def start_handler(update):
    await bot.api_client.send_message(
        chat_id=update.message.chat.id,
        text="Справочная информация",
    )
```

### Текст

```python
@bot.message_handler(text="привет")
async def hello_handler(update):
    await bot.api_client.send_message(
        chat_id=update.message.chat.id,
        text="Привет!",
    )
```

### Регулярные выражения

```python
import re

@bot.message_handler(text=re.compile(r"^\d+$"))
async def number_handler(update):
    await bot.api_client.send_message(
        chat_id=update.message.chat.id,
        text=f"Вы ввели число: {update.message.text}",
    )
```

### Комбинация фильтров

```python
from ymbot_async import CommandFilter, ChatTypeFilter, TextFilter

@bot.message_handler(
    filters=CommandFilter("start") & ChatTypeFilter("private")
)
async def private_start_handler(update):
    await bot.api_client.send_message(
        chat_id=update.message.chat.id,
        text="Привет из личного чата!",
    )
```

## Отправка сообщений

### Простое сообщение

```python
await bot.api_client.send_message(
    chat_id=chat_id,
    text="Привет!",
)
```

### С разметкой

```python
await bot.api_client.send_message(
    chat_id=chat_id,
    text="**Жирный** текст",
    parse_mode="Markdown",
)
```

### С инлайн-кнопками

```python
from ymbot_async import InlineButton, InlineKeyboardMarkup

keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineButton(text="Кнопка 1", callback_data="btn1"),
            InlineButton(text="Кнопка 2", callback_data="btn2"),
        ],
        [
            InlineButton(text="Ссылка", url="https://example.com"),
        ],
    ]
)

await bot.api_client.send_message(
    chat_id=chat_id,
    text="Выберите действие:",
    reply_markup=keyboard,
)
```

## Обработка callback-запросов

```python
from ymbot_async import CallbackQueryHandler, CallbackDataFilter

# Регистрируем обработчик callback
async def callback_handler(update):
    callback_data = update.message.text
    
    if callback_data == "btn1":
        await bot.api_client.answer_callback_query(
            callback_query_id=update.message.id,
            text="Нажата кнопка 1",
        )
    
    elif callback_data == "btn2":
        await bot.api_client.edit_message_text(
            chat_id=update.message.chat.id,
            message_id=update.message.id,
            text="Текст обновлен!",
        )

handler = CallbackQueryHandler(
    callback=callback_handler,
    filters=CallbackDataFilter("btn1|btn2"),  # regex pattern
)

bot.dispatcher.register_handler(handler)
```

## Лимитирование частоты запросов

Бот автоматически лимитирует количество запросов к API:

```python
config = BotConfig(
    token="your_bot_token",
    requests_per_second=30,      # 30 запросов/сек
    max_concurrent_requests=10,   # 10 параллельных запросов
)
```

## Контроль параллельности

Настройте количество параллельно обрабатываемых обновлений:

```python
config = BotConfig(
    token="your_bot_token",
    concurrency=5,  # 5 обновлений обрабатываются одновременно
)
```

## Очередь с ограничением

Настройте максимальный размер очереди обновлений:

```python
config = BotConfig(
    token="your_bot_token",
    queue_maxsize=1000,  # Если очередь заполнена, обновления отбрасываются
)
```

## Грэйсфул-шатдаун

```python
import signal
import asyncio

from ymbot_async import Bot, BotConfig

async def main():
    config = BotConfig(token="your_bot_token")
    
    async with Bot(config) as bot:
        @bot.message_handler(commands=["start"])
        async def start_handler(update):
            await bot.api_client.send_message(
                chat_id=update.message.chat.id,
                text="Привет!",
            )
        
        # Запускаем поллинг в задаче
        polling_task = asyncio.create_task(bot.run_polling())
        
        # Ожидаем сигнала
        shutdown_event = asyncio.Event()
        
        # Обработка SIGINT (Ctrl+C)
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(
            signal.SIGINT,
            shutdown_event.set,
        )
        
        # Ожидаем сигнала завершения
        await shutdown_event.wait()
        
        # Грэйсфул-шатдаун
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Структура проекта

```
src/ymbot_async/
├── __init__.py          # Главный модуль
├── bot.py               # Класс Bot
├── config.py            # BotConfig
├── errors.py            # Исключения
├── logging.py           # Настройка логов
├── api/                 # API клиент
│   ├── __init__.py
│   ├── schemas.py       # Pydantic модели
│   └── client.py        # ApiClient
├── dispatcher/          # Диспетчер
│   ├── __init__.py
│   ├── dispatcher.py    # Dispatcher
│   ├── handlers.py      # Обработчики
│   └── filters.py       # Фильтры
├── runtime/             # Runtime
│   ├── __init__.py
│   ├── polling.py       # Long polling
│   └── offset_manager.py # Управление offset
└── transport/           # Транспортный уровень
    ├── __init__.py
    └── httpx_transport.py
```

## Логирование

Настройте формат логов:

```python
# JSON формат (для структурированного логирования)
config = BotConfig(
    token="your_bot_token",
    log_level="INFO",
    log_format="json",
)

# Консольный формат (для разработки)
config = BotConfig(
    token="your_bot_token",
    log_level="DEBUG",
    log_format="console",
)
```

## Разработка

### Установка зависимостей для разработки

```bash
# Установка всех зависимостей с uv
uv sync --dev
```

### Запуск тестов

Проект использует многоуровневую стратегию тестирования:

- **Unit тесты** - быстрые, изолированные тесты для отдельных компонентов
- **Smoke тесты** - быстрые проверки критического функционала
- **Integration тесты** - тесты взаимодействия компонентов
- **E2E тесты** - тесты с реальным API (требуют REAL_BOT_TOKEN)

#### Запуск всех тестов (кроме E2E)

```bash
# Все тесты кроме E2E
uv run pytest tests/ -v -m "not e2e"
```

#### Запуск конкретных типов тестов

```bash
# Unit тесты
uv run pytest tests/unit/ -v

# Smoke тесты
uv run pytest tests/smoke/ -v

# Integration тесты
uv run pytest tests/integration/ -v

# E2E тесты (требует REAL_BOT_TOKEN)
# Смотрите раздел ниже "Запуск E2E тестов"

# Без покрытия кода (быстрее)
uv run pytest tests/ -v --no-cov -m "not e2e"
```

#### Запуск E2E тестов

E2E тесты требуют реальный токен бота для взаимодействия с Yandex Messenger API.

```bash
# Windows (CMD)
set REAL_BOT_TOKEN=ваш_токен_здесь
uv run pytest tests/e2e/ -v -m e2e

# Windows (PowerShell)
$env:REAL_BOT_TOKEN="ваш_токен_здесь"
uv run pytest tests/e2e/ -v -m e2e

# Linux/Mac (Bash)
export REAL_BOT_TOKEN="ваш_токен_здесь"
uv run pytest tests/e2e/ -v -m e2e
```

Если `REAL_BOT_TOKEN` не установлен, E2E тесты будут автоматически пропущены (skipped).

#### Отчеты по покрытию кода (Coverage Reports)

После запуска тестов автоматически генерируются два типа отчетов:

**1. Консольный отчет**
- Отображается в терминале после завершения тестов
- Показывает процент покрытия для каждого модуля
- Выделяет непокрытые строки (цветом)
- Пример вывода:
  ```
  ---------- coverage: platform win32, python 3.11 -----------
  Name                                      Stmts   Miss  Cover   Missing
  -------------------------------------------------------------------------
  src/ymbot_async/__init__.py                  2      0   100%
  src/ymbot_async/api/client.py               45      5    89%   23-27, 45
  src/ymbot_async/bot.py                      30      2    93%   12, 15
  -------------------------------------------------------------------------
  TOTAL                                       77      7    91%
  ```

**2. HTML отчет**
- Генерируется в директории `htmlcov/`
- Интерактивный отчет с подсветкой кода
- Покрывает все модули проекта
- Показывает какие строки не покрыты тестами

**Как открыть HTML отчет:**

```bash
# Windows
start htmlcov/index.html

# Mac
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

Или откройте файл `htmlcov/index.html` в браузере вручную.

**Отключение генерации отчетов:**
```bash
# Без покрытия (быстрее)
uv run pytest tests/ -v --no-cov -m "not e2e"
```

#### Запуск линтеров

```bash
# Ruff (линтер и форматтер)
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Mypy (проверка типов)
uv run mypy src/
```

### Форматирование кода

```bash
# Автоматическое форматирование
uv run ruff format src/ tests/

# Проверка форматирования без изменений
uv run ruff format --check src/ tests/
```

## Лицензия

MIT

## Поддержка

Для вопросов и предложений создайте issue на GitHub.