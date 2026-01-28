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

## Примеры

### 1. Эхо-бот

Простой бот, который повторяет сообщения пользователя:

```python
import asyncio
from ymbot_async import Bot, BotConfig

async def main():
    config = BotConfig(token="your_bot_token")
    
    async with Bot(config) as bot:
        @bot.message_handler()
        async def echo_handler(update):
            # Повторяем сообщение пользователя
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text=update.message.text or "Вы отправили сообщение без текста",
            )
        
        await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Бот справка с командами

Бот с базовыми командами для предоставления информации:

```python
import asyncio
from ymbot_async import Bot, BotConfig, CommandFilter

async def main():
    config = BotConfig(token="your_bot_token")
    
    async with Bot(config) as bot:
        # Команда /start - приветствие
        @bot.message_handler(commands=["start"])
        async def start_handler(update):
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text=(
                    "👋 Привет! Я справочный бот.\n\n"
                    "Доступные команды:\n"
                    "/start - Начать работу\n"
                    "/help - Справка\n"
                    "/about - О проекте"
                ),
            )
        
        # Команда /help - справка
        @bot.message_handler(commands=["help"])
        async def help_handler(update):
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text=(
                    "📚 Справка по использованию:\n\n"
                    "• Отправьте любое сообщение - получите ответ\n"
                    "• Используйте команды для навигации\n"
                    "• Поддержка работает 24/7"
                ),
            )
        
        # Команда /about - о проекте
        @bot.message_handler(commands=["about"])
        async def about_handler(update):
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text="🚀 Бот на Yandex Messenger Bot Async Client v1.0",
            )
        
        await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Бот-опросник

Интерактивный бот, который проводит опрос через инлайн-кнопки:

```python
import asyncio
from ymbot_async import (
    Bot, BotConfig, CommandFilter, 
    InlineButton, InlineKeyboardMarkup, CallbackDataFilter
)

async def main():
    config = BotConfig(token="your_bot_token")
    
    async with Bot(config) as bot:
        # Команда /survey - начало опроса
        @bot.message_handler(commands=["survey"])
        async def survey_handler(update):
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineButton(text="🔵 Хорошо", callback_data="good"),
                        InlineButton(text="⚪ Удовлетворительно", callback_data="ok"),
                        InlineButton(text="🔴 Плохо", callback_data="bad"),
                    ],
                    [
                        InlineButton(text="❌ Отмена", callback_data="cancel"),
                    ],
                ]
            )
            
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text="Как вы оцениваете качество сервиса?",
                reply_markup=keyboard,
            )
        
        # Обработка выбора пользователя
        @bot.message_handler(filters=CallbackDataFilter("good|ok|bad|cancel"))
        async def survey_callback_handler(update):
            callback_data = update.message.text
            
            if callback_data == "cancel":
                await bot.api_client.send_message(
                    login=update.message.from_user.login,
                    text="Опрос отменен. Спасибо за внимание!",
                )
            else:
                rating = {
                    "good": "👍 Отлично!",
                    "ok": "👌 Хорошо",
                    "bad": "👎 Спасибо за обратную связь",
                }.get(callback_data, "Спасибо!")
                
                await bot.api_client.send_message(
                    login=update.message.from_user.login,
                    text=f"{rating} Ваше мнение важно для нас.",
                )
        
        await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Бот-модератор для групп

Бот, который работает только в групповых чатах и управляет порядком:

```python
import asyncio
import re
from ymbot_async import (
    Bot, BotConfig, CommandFilter, 
    ChatTypeFilter, TextFilter
)

async def main():
    config = BotConfig(token="your_bot_token")
    
    async with Bot(config) as bot:
        # Команда /rules - показать правила (только в группах)
        @bot.message_handler(
            filters=CommandFilter("rules") & ChatTypeFilter("group")
        )
        async def rules_handler(update):
            await bot.api_client.send_message(
                chat_id=update.message.chat.id,
                text=(
                    "📋 Правила группы:\n\n"
                    "1. Уважайте других участников\n"
                    "2. Без спама и рекламы\n"
                    "3. Оставайтесь на теме чата\n"
                    "4. Соблюдайте этику общения"
                ),
            )
        
        # Обработка спам-сообщений (только в группах)
        @bot.message_handler(
            filters=ChatTypeFilter("group") & 
            TextFilter(re.compile(r"(https?://\S+){3,}", re.IGNORECASE))
        )
        async def spam_handler(update):
            # Удаляем сообщение с несколькими ссылками
            await bot.api_client.delete_message(
                chat_id=update.message.chat.id,
                message_id=update.message.message_id,
            )
            
            # Отправляем предупреждение
            await bot.api_client.send_message(
                chat_id=update.message.chat.id,
                text=f"⚠️ Сообщение от @{update.message.from_user.login} удалено как спам",
            )
        
        # Команда /warn - предупредить пользователя
        @bot.message_handler(
            filters=CommandFilter("warn") & ChatTypeFilter("group")
        )
        async def warn_handler(update):
            # Ответ на сообщение предупреждением
            if update.message.reply_message_id:
                await bot.api_client.send_message(
                    chat_id=update.message.chat.id,
                    text="⚠️ Это предупреждение. Соблюдайте правила чата!",
                    reply_message_id=update.message.reply_message_id,
                )
        
        await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. Бот-калькулятор

Бот, который вычисляет математические выражения:

```python
import asyncio
import re
from ymbot_async import Bot, BotConfig, TextFilter

async def main():
    config = BotConfig(token="your_bot_token")
    
    async with Bot(config) as bot:
        # Обработка математических выражений
        @bot.message_handler(filters=TextFilter(re.compile(r"^\d+[\+\-\*\/\^]\d+$")))
        async def calc_handler(update):
            expression = update.message.text
            
            try:
                # Замена ^ на ** для степени
                expr = expression.replace("^", "**")
                result = eval(expr)
                
                await bot.api_client.send_message(
                    login=update.message.from_user.login,
                    text=f"📊 {expression} = {result}",
                )
            except Exception:
                await bot.api_client.send_message(
                    login=update.message.from_user.login,
                    text="❌ Ошибка вычисления. Проверьте выражение.",
                )
        
        # Команда /calc - помощь
        @bot.message_handler(commands=["calc"])
        async def calc_help_handler(update):
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text=(
                    "🧮 Калькулятор\n\n"
                    "Примеры:\n"
                    "2+2\n"
                    "10*5\n"
                    "100/4\n"
                    "3^2 (степень)"
                ),
            )
        
        await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

### 6. Бот с меню выбора

Бот с интерактивным меню для навигации по разделам:

```python
import asyncio
from ymbot_async import (
    Bot, BotConfig, CommandFilter, 
    InlineButton, InlineKeyboardMarkup, CallbackDataFilter
)

# Создание главного меню
def get_main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineButton(text="📰 Новости", callback_data="news"),
                InlineButton(text="📚 Каталог", callback_data="catalog"),
            ],
            [
                InlineButton(text="🛒 Корзина", callback_data="cart"),
                InlineButton(text="👤 Профиль", callback_data="profile"),
            ],
            [
                InlineButton(text="❓ Помощь", callback_data="help"),
            ],
        ]
    )

async def main():
    config = BotConfig(token="your_bot_token")
    
    async with Bot(config) as bot:
        # Команда /menu - главное меню
        @bot.message_handler(commands=["menu"])
        async def menu_handler(update):
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text="🏠 Главное меню",
                reply_markup=get_main_menu(),
            )
        
        # Обработка кнопок меню
        @bot.message_handler(filters=CallbackDataFilter("news|catalog|cart|profile|help"))
        async def menu_callback_handler(update):
            callback_data = update.message.text
            
            responses = {
                "news": "📰 Последние новости:\n\n• Новая версия бота v2.0\n• Скидки до 50%",
                "catalog": "📚 Каталог товаров:\n\n1. Товар А\n2. Товар Б\n3. Товар В",
                "cart": "🛒 Ваша корзина пуста",
                "profile": "👤 Профиль пользователя:\n\nИмя: Пользователь\nСтатус: Активен",
                "help": "❓ Справка:\n\nИспользуйте кнопки для навигации по разделам.",
            }
            
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text=responses.get(callback_data, "Раздел не найден"),
                reply_markup=get_main_menu(),
            )
        
        await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

### 7. Бот обратной связи

Бот, который пересылает сообщения администратору:

```python
import asyncio
import os
from ymbot_async import Bot, BotConfig, CommandFilter

ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "admin")

async def main():
    config = BotConfig(token="your_bot_token")
    
    async with Bot(config) as bot:
        # Команда /feedback - отправка обратной связи
        @bot.message_handler(commands=["feedback"])
        async def feedback_handler(update):
            # Получаем текст сообщения после команды
            text = update.message.text
            feedback_text = text.replace("/feedback", "").strip()
            
            if not feedback_text:
                await bot.api_client.send_message(
                    login=update.message.from_user.login,
                    text="❌ Пожалуйста, введите сообщение после команды /feedback",
                )
                return
            
            # Отправляем администратору
            await bot.api_client.send_message(
                login=ADMIN_LOGIN,
                text=(
                    f"📩 Новое сообщение обратной связи\n\n"
                    f"От: @{update.message.from_user.login}\n"
                    f"Текст: {feedback_text}"
                ),
                important=True,  # Важное сообщение
            )
            
            # Подтверждение пользователю
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text="✅ Ваше сообщение отправлено администратору",
            )
        
        # Команда /contact - контактная информация
        @bot.message_handler(commands=["contact"])
        async def contact_handler(update):
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text=(
                    "📞 Связаться с нами:\n\n"
                    f"Email: support@example.com\n"
                    f"Telegram: @{ADMIN_LOGIN}\n"
                    "Время работы: Пн-Пт, 9:00-18:00"
                ),
            )
        
        await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

### 8. Бот для личных уведомлений

Бот, который отправляет важные сообщения без уведомлений:

```python
import asyncio
from ymbot_async import Bot, BotConfig, CommandFilter

async def main():
    config = BotConfig(token="your_bot_token")
    
    async with Bot(config) as bot:
        # Команда /notify - тихое уведомление
        @bot.message_handler(commands=["notify"])
        async def notify_handler(update):
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text="🔕 Это тихое уведомление (без звука)",
                disable_notification=True,
            )
        
        # Команда /urgent - срочное сообщение
        @bot.message_handler(commands=["urgent"])
        async def urgent_handler(update):
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text="🔔 СРОЧНО! Это важное уведомление!",
                important=True,
            )
        
        # Команда /remind - напоминание
        @bot.message_handler(commands=["remind"])
        async def remind_handler(update):
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text=(
                    "⏰ Напоминание:\n\n"
                    "• Проверьте почту\n"
                    "• Подтвердите встречу\n"
                    "• Закройте задачи за сегодня"
                ),
                disable_web_page_preview=True,  # Без превью ссылок
            )
        
        await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

### 9. Бот-помощник с контекстом

Бот, который запоминает контекст и ведет диалог:

```python
import asyncio
from ymbot_async import Bot, BotConfig, TextFilter

# Хранилище контекста диалогов
context_storage: dict[str, dict] = {}

async def main():
    config = BotConfig(token="your_bot_token")
    
    async with Bot(config) as bot:
        # Команда /reset - сброс контекста
        @bot.message_handler(commands=["reset"])
        async def reset_handler(update):
            user_login = update.message.from_user.login
            if user_login in context_storage:
                del context_storage[user_login]
            
            await bot.api_client.send_message(
                login=user_login,
                text="🔄 Контекст сброшен. Напомните, о чем мы говорили?",
            )
        
        # Обработка вопросов и ответов с контекстом
        @bot.message_handler(filters=TextFilter("да|нет|конечно|хорошо"))
        async def context_handler(update):
            user_login = update.message.from_user.login
            response = update.message.text.lower()
            
            # Получаем предыдущий контекст
            context = context_storage.get(user_login, {})
            last_topic = context.get("last_topic")
            
            if last_topic:
                if last_topic == "greeting":
                    if response in ["да", "конечно"]:
                        await bot.api_client.send_message(
                            login=user_login,
                            text="Отлично! Я здесь, чтобы помочь. Чем могу быть полезен?",
                        )
                    elif response == "нет":
                        await bot.api_client.send_message(
                            login=user_login,
                            text="Понял! Обращайтесь, если что-то понадобится.",
                        )
                
                # Обновляем контекст
                context_storage[user_login] = {
                    "last_topic": "dialog",
                    "last_response": response,
                }
        
        # Приветствие и начало диалога
        @bot.message_handler(filters=TextFilter("привет|здравствуйте|хай"))
        async def greeting_handler(update):
            user_login = update.message.from_user.login
            
            context_storage[user_login] = {
                "last_topic": "greeting",
                "last_response": None,
            }
            
            await bot.api_client.send_message(
                login=user_login,
                text=(
                    "👋 Здравствуйте! Рад вас видеть.\n\n"
                    "Хотите узнать о моих возможностях?"
                ),
            )
        
        # Общие вопросы
        @bot.message_handler()
        async def general_handler(update):
            user_login = update.message.from_user.login
            text = update.message.text.lower()
            
            if "как дела" in text:
                await bot.api_client.send_message(
                    login=user_login,
                    text="✅ Все отлично! Готов помочь вам с любыми вопросами.",
                )
            elif "что умеешь" in text:
                await bot.api_client.send_message(
                    login=user_login,
                    text=(
                        "🤖 Я умею:\n\n"
                        "• Отвечать на вопросы\n"
                        "• Запоминать контекст диалога\n"
                        "• Помогать с задачами\n"
                        "• Отправлять уведомления"
                    ),
                )
            else:
                await bot.api_client.send_message(
                    login=user_login,
                    text="🤔 Интересный вопрос! Расскажите подробнее?",
                )
        
        await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

### 10. Бот с валидацией данных

Бот, который проверяет форматы данных (email, телефон и т.д.):

```python
import asyncio
import re
from ymbot_async import (
    Bot, BotConfig, CommandFilter, 
    TextFilter, InlineButton, InlineKeyboardMarkup
)

def validate_email(text: str) -> bool:
    """Валидация email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, text))

def validate_phone(text: str) -> bool:
    """Валидация телефона (формат: +7XXXXXXXXXX)"""
    pattern = r'^\+7\d{10}$'
    return bool(re.match(pattern, text))

def validate_inn(text: str) -> bool:
    """Валидация ИНН"""
    pattern = r'^\d{10}$|^\d{12}$'
    return bool(re.match(pattern, text))

async def main():
    config = BotConfig(token="your_bot_token")
    
    async with Bot(config) as bot:
        # Команда /validate - меню валидации
        @bot.message_handler(commands=["validate"])
        async def validate_menu_handler(update):
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineButton(text="📧 Email", callback_data="validate_email"),
                        InlineButton(text="📱 Телефон", callback_data="validate_phone"),
                    ],
                    [
                        InlineButton(text="🏢 ИНН", callback_data="validate_inn"),
                        InlineButton(text="❌ Отмена", callback_data="cancel"),
                    ],
                ]
            )
            
            await bot.api_client.send_message(
                login=update.message.from_user.login,
                text="Выберите тип данных для валидации:",
                reply_markup=keyboard,
            )
        
        # Обработка выбора типа валидации
        @bot.message_handler(
            filters=TextFilter("validate_email|validate_phone|validate_inn|cancel")
        )
        async def validate_callback_handler(update):
            user_login = update.message.from_user.login
            callback_data = update.message.text
            
            if callback_data == "cancel":
                await bot.api_client.send_message(
                    login=user_login,
                    text="Валидация отменена",
                )
                return
            
            # Устанавливаем режим валидации
            context = {
                "mode": callback_data.replace("validate_", ""),
            }
            
            instructions = {
                "email": "📧 Введите email для проверки (пример: user@example.com)",
                "phone": "📱 Введите номер телефона (формат: +7XXXXXXXXXX)",
                "inn": "🏢 Введите ИНН (10 или 12 цифр)",
            }
            
            await bot.api_client.send_message(
                login=user_login,
                text=instructions.get(context["mode"], "Неизвестный тип"),
            )
        
        # Валидация email
        @bot.message_handler(filters=TextFilter(re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')))
        async def email_validation_handler(update):
            user_login = update.message.from_user.login
            email = update.message.text
            
            if validate_email(email):
                await bot.api_client.send_message(
                    login=user_login,
                    text=f"✅ Email {email} - валидный",
                )
            else:
                await bot.api_client.send_message(
                    login=user_login,
                    text=f"❌ Email {email} - невалидный",
                )
        
        # Валидация телефона
        @bot.message_handler(filters=TextFilter(re.compile(r'^\+7\d{10}$')))
        async def phone_validation_handler(update):
            user_login = update.message.from_user.login
            phone = update.message.text
            
            if validate_phone(phone):
                await bot.api_client.send_message(
                    login=user_login,
                    text=f"✅ Телефон {phone} - валидный",
                )
            else:
                await bot.api_client.send_message(
                    login=user_login,
                    text=f"❌ Телефон {phone} - невалидный. Формат: +7XXXXXXXXXX",
                )
        
        # Валидация ИНН
        @bot.message_handler(filters=TextFilter(re.compile(r'^\d{10}$|^\d{12}$')))
        async def inn_validation_handler(update):
            user_login = update.message.from_user.login
            inn = update.message.text
            
            if validate_inn(inn):
                await bot.api_client.send_message(
                    login=user_login,
                    text=f"✅ ИНН {inn} - валидный",
                )
            else:
                await bot.api_client.send_message(
                    login=user_login,
                    text=f"❌ ИНН {inn} - невалидный (10 или 12 цифр)",
                )
        
        await bot.run_polling()

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