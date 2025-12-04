# UspMusicFinder Bot - План разработки

**Общая длительность:** 28 дней (4 недели)
**Методология:** Agile / Итеративная разработка
**Цель:** Production-ready музыкальный Telegram бот

---

## 📅 Общий обзор

| Неделя | Фаза | Основные задачи | Результат |
|--------|------|----------------|-----------|
| **1** | MVP | Базовый бот, поиск, скачивание | Работающий поиск и отправка музыки |
| **2** | UI/UX | Кнопки, TOP, улучшения | Полноценный интерфейс |
| **3** | Расширение | Inline режим, альт. источники | Дополнительный функционал |
| **4** | Production | Оптимизация, деплой, мониторинг | Production на VPS |

---

## 🗓️ НЕДЕЛЯ 1: MVP - Базовый функционал

**Цель:** Создать работающий бот, который ищет и скачивает музыку

---

### День 1-2: Настройка проекта и базовый бот

#### ✅ Задачи:

**1. Настройка окружения**
- [x] Создать проект через `create-python-project.ps1`
- [ ] Обновить `requirements.txt`
- [ ] Создать `.env` файл с токеном
- [ ] Установить зависимости: `pip install -r requirements.txt`

**2. Структура проекта**
- [ ] Создать директории:
  - `src/handlers/` - обработчики команд
  - `src/searchers/` - поисковые модули
  - `src/downloaders/` - загрузчики
  - `src/utils/` - утилиты
  - `data/temp/` - временные файлы
  - `data/cache/` - кэш
  - `logs/` - логи

**3. Базовые файлы**

`src/config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str
    BOT_USERNAME: str = "UspMusicFinder_bot"

    TEMP_DIR: str = "./data/temp"
    CACHE_DIR: str = "./data/cache"
    LOGS_DIR: str = "./logs"

    MAX_FILE_SIZE: int = 52428800  # 50MB
    MAX_DURATION: int = 600  # 10 min

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
```

`src/utils/logger.py`:
```python
import logging
from pathlib import Path
from src.config import settings

def setup_logger():
    Path(settings.LOGS_DIR).mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(f"{settings.LOGS_DIR}/bot.log"),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)

logger = setup_logger()
```

`src/bot.py`:
```python
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from src.config import settings

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()
```

**4. Handlers - /start и /help**

`src/handlers/start.py`:
```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Чтобы я смог распознать музыку, отправь мне что-то из этого:\n\n"
        "• Название песни или исполнителя\n"
        "• Слова из песни\n"
        "• Голосовое сообщение\n"
        "• Видео\n"
        "• Аудио\n"
        "• Видеосообщение\n\n"
        "(Бот работает напрямую и в чатах тоже.)"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🎵 <b>Как пользоваться:</b>\n\n"
        "1️⃣ Отправь мне название песни или исполнителя\n"
        "2️⃣ Выбери трек из списка (нажми кнопку 1-10)\n"
        "3️⃣ Получи аудио файл!\n\n"
        "📊 <b>Команды:</b>\n"
        "/start - Начать работу\n"
        "/help - Эта справка\n"
        "/top - Популярные песни\n\n"
        "💡 <b>Inline режим:</b>\n"
        "В любом чате введи: @UspMusicFinder_bot название песни"
    )
```

`src/main.py`:
```python
import asyncio
from src.bot import bot, dp
from src.handlers import start
from src.utils.logger import logger

async def main():
    # Подключить роутеры
    dp.include_router(start.router)

    # Удалить вебхук (для polling)
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Bot started successfully")
    logger.info(f"Bot @{(await bot.me()).username} is running...")

    # Запустить polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

**5. Тестирование**
- [ ] Запустить бот: `python src/main.py`
- [ ] Проверить `/start` команду
- [ ] Проверить `/help` команду
- [ ] Проверить логирование в `logs/bot.log`

#### 📦 Deliverables:

- ✅ Работающий базовый бот
- ✅ Логирование настроено
- ✅ Конфигурация из .env
- ✅ /start и /help команды работают

---

### День 3-4: YouTube Music поиск

#### ✅ Задачи:

**1. Установка yt-dlp**

```bash
pip install yt-dlp
```

**2. Создать модель данных**

`src/models.py`:
```python
from dataclasses import dataclass

@dataclass
class Track:
    id: str  # YouTube video ID
    title: str
    artist: str = "Unknown"
    duration: int = 0  # seconds
    url: str = ""

    @property
    def formatted_duration(self) -> str:
        """Форматировать длительность как MM:SS"""
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"
```

**3. Поисковик YouTube Music**

`src/searchers/youtube.py`:
```python
from typing import List
from yt_dlp import YoutubeDL
from src.models import Track
from src.utils.logger import logger

class YouTubeSearcher:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch10',
        }

    async def search(self, query: str) -> List[Track]:
        """Поиск треков на YouTube Music"""
        try:
            with YoutubeDL(self.ydl_opts) as ydl:
                logger.info(f"Searching YouTube for: {query}")
                result = ydl.extract_info(f"ytsearch10:{query}", download=False)

                if not result or 'entries' not in result:
                    logger.warning(f"No results for: {query}")
                    return []

                tracks = []
                for entry in result['entries']:
                    if not entry:
                        continue

                    # Парсинг названия (обычно "Artist - Title")
                    title = entry.get('title', 'Unknown')
                    artist = "Unknown"

                    if ' - ' in title:
                        parts = title.split(' - ', 1)
                        artist = parts[0].strip()
                        title = parts[1].strip()

                    track = Track(
                        id=entry['id'],
                        title=title,
                        artist=artist,
                        duration=entry.get('duration', 0),
                        url=f"https://youtube.com/watch?v={entry['id']}"
                    )
                    tracks.append(track)

                logger.info(f"Found {len(tracks)} tracks")
                return tracks[:10]

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

# Singleton instance
youtube_searcher = YouTubeSearcher()
```

**4. Тестирование поиска**

`tests/test_youtube_search.py`:
```python
import pytest
from src.searchers.youtube import youtube_searcher

@pytest.mark.asyncio
async def test_search():
    tracks = await youtube_searcher.search("Время назад")

    assert len(tracks) > 0
    assert tracks[0].id is not None
    assert tracks[0].title is not None
    print(f"\n✅ Found {len(tracks)} tracks:")
    for i, track in enumerate(tracks, 1):
        print(f"{i}. {track.artist} - {track.title} ({track.formatted_duration})")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_search())
```

Запуск теста:
```bash
python tests/test_youtube_search.py
```

**5. Интеграция в бот**

`src/handlers/search.py`:
```python
from aiogram import Router, F
from aiogram.types import Message
from src.searchers.youtube import youtube_searcher
from src.utils.logger import logger

router = Router()

@router.message(F.text)
async def text_search_handler(message: Message):
    """Обработчик текстовых запросов"""
    query = message.text

    # Игнорировать команды
    if query.startswith('/'):
        return

    logger.info(f"User {message.from_user.id} searched: {query}")

    # Показать "печатает..."
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Поиск
    tracks = await youtube_searcher.search(query)

    if not tracks:
        await message.answer("❌ Ничего не найдено. Попробуй другой запрос.")
        return

    # Формировать список результатов
    text = f"<b>{query}</b>\n\n"
    for i, track in enumerate(tracks, 1):
        text += f"{i}. {track.title} {track.formatted_duration}\n"

    await message.answer(text)
```

Обновить `src/main.py`:
```python
from src.handlers import start, search

async def main():
    dp.include_router(start.router)
    dp.include_router(search.router)  # Добавить
    # ...
```

#### 📦 Deliverables:

- ✅ YouTube Music поиск работает
- ✅ Возвращает до 10 результатов
- ✅ Парсинг названия и исполнителя
- ✅ Бот показывает список треков

---

### День 5-7: Скачивание и отправка аудио

#### ✅ Задачи:

**1. Downloader модуль**

`src/downloaders/youtube_dl.py`:
```python
import os
from pathlib import Path
from yt_dlp import YoutubeDL
from src.config import settings
from src.utils.logger import logger

class YouTubeDownloader:
    def __init__(self):
        Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)

        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{settings.TEMP_DIR}/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    async def download(self, video_id: str) -> str:
        """Скачать трек и вернуть путь к MP3 файлу"""
        try:
            url = f"https://youtube.com/watch?v={video_id}"
            logger.info(f"Downloading: {video_id}")

            with YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                # Путь к файлу
                filename = ydl.prepare_filename(info)
                mp3_file = filename.rsplit('.', 1)[0] + '.mp3'

                # Проверить размер
                if os.path.exists(mp3_file):
                    file_size = os.path.getsize(mp3_file)
                    if file_size > settings.MAX_FILE_SIZE:
                        os.remove(mp3_file)
                        raise Exception(f"File too large: {file_size} bytes")

                    logger.info(f"Downloaded: {mp3_file} ({file_size} bytes)")
                    return mp3_file
                else:
                    raise Exception("MP3 file not created")

        except Exception as e:
            logger.error(f"Download error for {video_id}: {e}")
            raise

youtube_downloader = YouTubeDownloader()
```

**2. Кэш для результатов поиска**

`src/utils/cache.py`:
```python
from typing import Optional, List
from datetime import datetime, timedelta
from src.models import Track

class SimpleCache:
    """Простой in-memory кэш"""
    def __init__(self):
        self._cache = {}

    def set(self, key: str, value: List[Track], ttl: int = 600):
        """Сохранить в кэш (ttl в секундах)"""
        expire_at = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = {
            'data': value,
            'expire_at': expire_at
        }

    def get(self, key: str) -> Optional[List[Track]]:
        """Получить из кэша"""
        if key not in self._cache:
            return None

        item = self._cache[key]

        # Проверить истечение
        if datetime.now() > item['expire_at']:
            del self._cache[key]
            return None

        return item['data']

    def clear(self):
        """Очистить кэш"""
        self._cache.clear()

cache = SimpleCache()
```

**3. Inline keyboard с кнопками**

`src/keyboards.py`:
```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from src.models import Track

def create_track_keyboard(tracks: List[Track]) -> InlineKeyboardMarkup:
    """Создать клавиатуру с кнопками 1-10"""
    buttons = []

    # Первая строка: 1-5
    row1 = [
        InlineKeyboardButton(text=str(i), callback_data=f"track:{i}")
        for i in range(1, min(6, len(tracks) + 1))
    ]

    # Вторая строка: 6-10
    row2 = [
        InlineKeyboardButton(text=str(i), callback_data=f"track:{i}")
        for i in range(6, min(11, len(tracks) + 1))
    ]

    if row1:
        buttons.append(row1)
    if row2:
        buttons.append(row2)

    return InlineKeyboardMarkup(inline_keyboard=buttons)
```

**4. Обновить search handler**

`src/handlers/search.py`:
```python
from aiogram import Router, F
from aiogram.types import Message
from src.searchers.youtube import youtube_searcher
from src.keyboards import create_track_keyboard
from src.utils.cache import cache
from src.utils.logger import logger

router = Router()

@router.message(F.text)
async def text_search_handler(message: Message):
    query = message.text

    if query.startswith('/'):
        return

    logger.info(f"User {message.from_user.id} searched: {query}")

    await message.bot.send_chat_action(message.chat.id, "typing")

    tracks = await youtube_searcher.search(query)

    if not tracks:
        await message.answer("❌ Ничего не найдено. Попробуй другой запрос.")
        return

    # Сохранить в кэш (10 минут)
    cache_key = f"search:{message.from_user.id}"
    cache.set(cache_key, tracks, ttl=600)

    # Формировать список
    text = f"<b>{query}</b>\n\n"
    for i, track in enumerate(tracks, 1):
        text += f"{i}. {track.title} {track.formatted_duration}\n"

    # Клавиатура
    keyboard = create_track_keyboard(tracks)

    await message.answer(text, reply_markup=keyboard)
```

**5. Callback handler для кнопок**

`src/handlers/callbacks.py`:
```python
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.types import FSInputFile
import os
from src.downloaders.youtube_dl import youtube_downloader
from src.utils.cache import cache
from src.utils.logger import logger

router = Router()

@router.callback_query(F.data.startswith("track:"))
async def track_callback_handler(callback: CallbackQuery):
    """Обработчик кнопок 1-10"""
    try:
        # Получить номер трека
        track_num = int(callback.data.split(":")[1])

        # Получить из кэша
        cache_key = f"search:{callback.from_user.id}"
        tracks = cache.get(cache_key)

        if not tracks:
            await callback.answer("❌ Результаты устарели. Поищи заново.", show_alert=True)
            return

        if track_num < 1 or track_num > len(tracks):
            await callback.answer("❌ Неверный номер трека.", show_alert=True)
            return

        track = tracks[track_num - 1]

        # Показать "Загрузка..."
        await callback.message.edit_text("⏳ Загрузка...")

        logger.info(f"User {callback.from_user.id} downloading: {track.id}")

        # Скачать
        file_path = await youtube_downloader.download(track.id)

        # Отправить аудио
        audio_file = FSInputFile(file_path)

        await callback.message.answer_audio(
            audio=audio_file,
            performer=track.artist,
            title=track.title,
            duration=track.duration
        )

        # Удалить сообщение "Загрузка..."
        await callback.message.delete()

        # Удалить файл
        if os.path.exists(file_path):
            os.remove(file_path)

        await callback.answer("✅ Готово!")

    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback.message.edit_text("❌ Ошибка при скачивании. Попробуй другой трек.")
        await callback.answer()
```

Обновить `src/main.py`:
```python
from src.handlers import start, search, callbacks

async def main():
    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(callbacks.router)  # Добавить
    # ...
```

**6. Тестирование**
- [ ] Поиск трека
- [ ] Нажать кнопку 1-10
- [ ] Получить MP3 файл
- [ ] Проверить метаданные (исполнитель, название)
- [ ] Проверить удаление временного файла

#### 📦 Deliverables:

- ✅ Скачивание MP3 через yt-dlp
- ✅ Inline keyboard с кнопками
- ✅ Callback обработчик
- ✅ Отправка аудио в Telegram
- ✅ Кэширование результатов поиска

---

### ✅ Итог Week 1:

**MVP готов!** Бот умеет:
- ✅ Искать музыку по названию
- ✅ Показывать список до 10 треков
- ✅ Скачивать MP3
- ✅ Отправлять аудио файлы

---

## 🗓️ НЕДЕЛЯ 2: UI/UX и улучшения

**Цель:** Улучшить пользовательский интерфейс и добавить TOP популярных

---

### День 8-10: Улучшение UI

#### ✅ Задачи:

**1. Красивые сообщения**

Обновить `src/handlers/search.py`:
```python
# Формировать красивый список
text = f"🎵 <b>{query}</b>\n\n"
for i, track in enumerate(tracks, 1):
    # Иконки для первых 3 треков
    icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "▫️"
    text += f"{icon} <b>{i}.</b> {track.title} <code>{track.formatted_duration}</code>\n"

text += "\n👇 Выбери номер трека"
```

**2. Progress индикаторы**

```python
# При скачивании показывать прогресс
await callback.message.edit_text(
    f"⏳ <b>Загрузка...</b>\n\n"
    f"🎵 {track.title}\n"
    f"👤 {track.artist}\n"
    f"⏱ {track.formatted_duration}"
)
```

**3. Обработка ошибок - красиво**

```python
# Если ничего не найдено
await message.answer(
    "❌ <b>Ничего не найдено</b>\n\n"
    "💡 Попробуй:\n"
    "• Проверить правильность названия\n"
    "• Использовать английский язык\n"
    "• Написать только название песни или исполнителя"
)

# Если файл слишком большой
await callback.message.edit_text(
    "❌ <b>Файл слишком большой</b>\n\n"
    f"Размер: {file_size_mb} MB\n"
    f"Лимит Telegram: 50 MB\n\n"
    "Попробуй другой трек."
)
```

**4. Rate limiting**

`src/utils/rate_limiter.py`:
```python
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests: int = 5, period: int = 60):
        self.max_requests = max_requests
        self.period = period  # seconds
        self.requests = defaultdict(list)

    def is_allowed(self, user_id: int) -> bool:
        """Проверить, разрешен ли запрос"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.period)

        # Удалить старые запросы
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > cutoff
        ]

        # Проверить лимит
        if len(self.requests[user_id]) >= self.max_requests:
            return False

        # Добавить текущий запрос
        self.requests[user_id].append(now)
        return True

    def time_until_allowed(self, user_id: int) -> int:
        """Сколько секунд до следующего разрешенного запроса"""
        if not self.requests[user_id]:
            return 0

        oldest = min(self.requests[user_id])
        wait_until = oldest + timedelta(seconds=self.period)
        wait_seconds = (wait_until - datetime.now()).total_seconds()

        return max(0, int(wait_seconds))

rate_limiter = RateLimiter(max_requests=5, period=60)
```

Использование в handlers:
```python
from src.utils.rate_limiter import rate_limiter

@router.message(F.text)
async def text_search_handler(message: Message):
    # Проверить rate limit
    if not rate_limiter.is_allowed(message.from_user.id):
        wait_time = rate_limiter.time_until_allowed(message.from_user.id)
        await message.answer(
            f"⏳ <b>Слишком много запросов</b>\n\n"
            f"Подожди {wait_time} секунд."
        )
        return

    # ... остальной код
```

**5. Статистика использования**

`src/utils/stats.py`:
```python
from collections import defaultdict
from datetime import datetime

class Stats:
    def __init__(self):
        self.searches = defaultdict(int)  # {query: count}
        self.downloads = defaultdict(int)  # {track_id: count}
        self.users = set()

    def log_search(self, user_id: int, query: str):
        self.searches[query] += 1
        self.users.add(user_id)

    def log_download(self, user_id: int, track_id: str):
        self.downloads[track_id] += 1
        self.users.add(user_id)

    def get_popular_queries(self, limit: int = 10):
        """Топ популярных запросов"""
        sorted_queries = sorted(
            self.searches.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_queries[:limit]

    def get_total_users(self) -> int:
        return len(self.users)

stats = Stats()
```

#### 📦 Deliverables:

- ✅ Красивые форматированные сообщения
- ✅ Progress индикаторы
- ✅ Улучшенная обработка ошибок
- ✅ Rate limiting (5 запросов/минуту)
- ✅ Статистика использования

---

### День 11-12: TOP популярных песен

#### ✅ Задачи:

**1. Хардкод TOP треков (временно)**

`src/data/top_tracks.py`:
```python
TOP_TRACKS = {
    "ru": [  # Россия
        {"query": "Время назад Сплин", "artist": "Сплин", "title": "Время, назад!"},
        {"query": "Группа крови Кино", "artist": "Кино", "title": "Группа крови"},
        {"query": "Мама я в Дубае Филипп Киркоров", "artist": "Киркоров", "title": "Мама я в Дубае"},
        # ... еще 7 треков
    ],
    "en": [  # Англия/США
        {"query": "Blinding Lights The Weeknd", "artist": "The Weeknd", "title": "Blinding Lights"},
        {"query": "Shape of You Ed Sheeran", "artist": "Ed Sheeran", "title": "Shape of You"},
        # ... еще 8 треков
    ],
    "uz": [  # Узбекистан
        {"query": "Жиганская Jakone Kiliana", "artist": "Jakone & Kiliana", "title": "Жиганская"},
        # ... еще 9 треков
    ],
    # ... другие страны
}
```

**2. TOP handler**

`src/handlers/top.py`:
```python
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from src.searchers.youtube import youtube_searcher
from src.data.top_tracks import TOP_TRACKS
from src.keyboards import create_track_keyboard
from src.utils.cache import cache

router = Router()

@router.message(Command("top"))
async def cmd_top(message: Message):
    """Показать выбор стран"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿", callback_data="top:uz"),
            InlineKeyboardButton(text="🇷🇺", callback_data="top:ru"),
            InlineKeyboardButton(text="🇬🇧", callback_data="top:en"),
            InlineKeyboardButton(text="🇰🇿", callback_data="top:kz"),
            InlineKeyboardButton(text="🇹🇷", callback_data="top:tr"),
            InlineKeyboardButton(text="🇦🇿", callback_data="top:az"),
        ]
    ])

    await message.answer(
        "🎵 <b>TOP Popular Songs</b>\n\n"
        "Choose a language:",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("top:"))
async def top_country_callback(callback: CallbackQuery):
    """Показать топ для страны"""
    country = callback.data.split(":")[1]

    if country not in TOP_TRACKS:
        await callback.answer("❌ Топ для этой страны пока не доступен", show_alert=True)
        return

    await callback.message.edit_text("⏳ Загрузка топа...")

    # Получить топ треки для страны
    top_list = TOP_TRACKS[country]

    # Поискать первый трек чтобы получить реальные данные
    tracks = []
    for item in top_list:
        results = await youtube_searcher.search(item["query"])
        if results:
            tracks.append(results[0])  # Первый результат

    if not tracks:
        await callback.message.edit_text("❌ Ошибка загрузки топа")
        return

    # Сохранить в кэш
    cache_key = f"search:{callback.from_user.id}"
    cache.set(cache_key, tracks, ttl=3600)  # 1 час

    # Формировать список
    text = "🎵 <b>TOP Popular Songs</b>\n\n"
    for i, track in enumerate(tracks, 1):
        text += f"{i}. {track.artist} — {track.title}\n"

    text += "\n👇 Выбери номер трека"

    keyboard = create_track_keyboard(tracks)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
```

Добавить в `src/main.py`:
```python
from src.handlers import start, search, callbacks, top

async def main():
    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(callbacks.router)
    dp.include_router(top.router)  # Добавить
```

**3. Кэш для TOP**

TOP треки кэшируются на 1 час, чтобы не делать поиск каждый раз.

#### 📦 Deliverables:

- ✅ `/top` команда работает
- ✅ Выбор страны (флаги)
- ✅ Показ топ 10 треков
- ✅ Кэширование на 1 час

---

### День 13-14: Полировка и тесты

#### ✅ Задачи:

**1. Обновить /help**
```python
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🎵 <b>UspMusicFinder Bot</b>\n\n"

        "<b>Как пользоваться:</b>\n"
        "1️⃣ Отправь название песни или исполнителя\n"
        "2️⃣ Выбери трек из списка (1-10)\n"
        "3️⃣ Получи MP3 файл!\n\n"

        "📊 <b>Команды:</b>\n"
        "/start - Начать работу\n"
        "/help - Эта справка\n"
        "/top - Популярные песни\n"
        "/stats - Статистика бота (опционально)\n\n"

        "💡 <b>Inline режим:</b>\n"
        "В любом чате: <code>@UspMusicFinder_bot название</code>\n\n"

        "⚡️ <b>Лимиты:</b>\n"
        "• Максимум 5 запросов в минуту\n"
        "• Максимальный размер файла: 50 MB\n"
        "• Максимальная длительность: 10 минут"
    )
```

**2. Unit тесты**

`tests/test_searcher.py`:
```python
import pytest
from src.searchers.youtube import youtube_searcher

@pytest.mark.asyncio
async def test_youtube_search():
    tracks = await youtube_searcher.search("Test Song")
    assert isinstance(tracks, list)
    assert len(tracks) <= 10
```

`tests/test_downloader.py`:
```python
import pytest
import os
from src.downloaders.youtube_dl import youtube_downloader

@pytest.mark.asyncio
async def test_download():
    # Используй короткий тестовый трек
    file_path = await youtube_downloader.download("dQw4w9WgXcQ")

    assert os.path.exists(file_path)
    assert file_path.endswith('.mp3')

    # Очистка
    os.remove(file_path)
```

**3. Логирование улучшить**

Добавить в логи больше информации:
```python
logger.info(f"User {user_id} | Search: {query} | Results: {len(tracks)}")
logger.info(f"User {user_id} | Download: {track.id} | Title: {track.title}")
logger.error(f"Download failed | Track: {track_id} | Error: {str(e)}")
```

#### 📦 Deliverables:

- ✅ Обновленная /help команда
- ✅ Unit тесты
- ✅ Улучшенное логирование
- ✅ Код отрефакторен

---

### ✅ Итог Week 2:

**UI/UX готов!** Бот имеет:
- ✅ Красивые сообщения
- ✅ Progress индикаторы
- ✅ Rate limiting
- ✅ TOP популярных песен
- ✅ Улучшенная обработка ошибок
- ✅ Статистика

---

## 🗓️ НЕДЕЛЯ 3: Inline режим и расширения

**Цель:** Добавить inline режим и дополнительные источники

---

### День 15-17: Inline режим

#### ✅ Задачи:

**1. Включить inline в BotFather**

В @BotFather:
```
/setinline
@UspMusicFinder_bot
Введи название песни...
```

**2. Inline handler**

`src/handlers/inline.py`:
```python
from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultAudio
from src.searchers.youtube import youtube_searcher
from src.utils.logger import logger

router = Router()

@router.inline_query()
async def inline_search_handler(inline_query: InlineQuery):
    """Обработчик inline запросов"""
    query = inline_query.query

    if not query or len(query) < 3:
        # Минимум 3 символа
        await inline_query.answer([], cache_time=60)
        return

    logger.info(f"Inline query from {inline_query.from_user.id}: {query}")

    # Поиск
    tracks = await youtube_searcher.search(query)

    if not tracks:
        await inline_query.answer([], cache_time=60)
        return

    # Создать результаты
    results = []
    for i, track in enumerate(tracks[:10]):
        # Note: InlineQueryResultAudio требует прямую ссылку на MP3
        # Для YouTube это не подходит, используем InlineQueryResultArticle

        result = InlineQueryResultArticle(
            id=str(i),
            title=track.title,
            description=f"{track.artist} • {track.formatted_duration}",
            input_message_content=InputTextMessageContent(
                message_text=f"🎵 {track.artist} - {track.title}\n\n"
                             f"Используй @UspMusicFinder_bot чтобы скачать"
            ),
            thumbnail_url=f"https://img.youtube.com/vi/{track.id}/default.jpg"
        )
        results.append(result)

    await inline_query.answer(results, cache_time=300)
```

**Примечание:** Для полноценного inline с отправкой аудио нужны прямые ссылки на MP3, которых у YouTube нет. Альтернатива - использовать webhook и отправлять аудио после выбора.

**3. Webhook подход для inline (опционально)**

Более сложный вариант - настроить webhook и обрабатывать `chosen_inline_result`:

```python
@router.chosen_inline_result()
async def chosen_inline_handler(chosen: ChosenInlineResult):
    """Когда пользователь выбрал результат"""
    track_index = int(chosen.result_id)

    # Получить трек из кэша или переискать
    # Скачать и отправить через bot.send_audio()
```

#### 📦 Deliverables:

- ✅ Inline режим работает
- ✅ Показывает результаты поиска
- ✅ (Опционально) Отправка аудио через chosen_inline_result

---

### День 18-19: Альтернативные источники (опционально)

#### ✅ Задачи:

**1. iTunes API поиск**

`src/searchers/itunes.py`:
```python
import aiohttp
from typing import List
from src.models import Track

class iTunesSearcher:
    API_URL = "https://itunes.apple.com/search"

    async def search(self, query: str) -> List[Track]:
        """Поиск в iTunes"""
        params = {
            'term': query,
            'media': 'music',
            'limit': 10
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.API_URL, params=params) as resp:
                data = await resp.json()

                tracks = []
                for item in data.get('results', []):
                    track = Track(
                        id=str(item['trackId']),
                        title=item.get('trackName', 'Unknown'),
                        artist=item.get('artistName', 'Unknown'),
                        duration=int(item.get('trackTimeMillis', 0) / 1000),
                        url=item.get('previewUrl', '')  # 30 sec preview
                    )
                    tracks.append(track)

                return tracks

itunes_searcher = iTunesSearcher()
```

**2. Fallback механизм**

```python
async def search_with_fallback(query: str) -> List[Track]:
    """Поиск с fallback на альтернативные источники"""
    # Сначала YouTube
    tracks = await youtube_searcher.search(query)

    if tracks:
        return tracks

    # Если не нашли - попробовать iTunes
    tracks = await itunes_searcher.search(query)

    return tracks
```

#### 📦 Deliverables:

- ✅ (Опционально) iTunes API интегрирован
- ✅ Fallback механизм
- ✅ Несколько источников поиска

---

### День 20-21: Расширенные функции

#### ✅ Задачи:

**1. Распознавание голосовых сообщений (опционально)**

Требует API вроде AudD.io или Shazam. Платный функционал.

**2. История поиска пользователя**

`src/utils/history.py`:
```python
from collections import defaultdict, deque
from typing import List

class SearchHistory:
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.history = defaultdict(lambda: deque(maxlen=max_size))

    def add(self, user_id: int, query: str):
        if query not in self.history[user_id]:
            self.history[user_id].append(query)

    def get(self, user_id: int) -> List[str]:
        return list(self.history[user_id])

history = SearchHistory()
```

`/history` команда:
```python
@router.message(Command("history"))
async def cmd_history(message: Message):
    user_history = history.get(message.from_user.id)

    if not user_history:
        await message.answer("📭 История поиска пуста")
        return

    text = "📜 <b>История поиска:</b>\n\n"
    for i, query in enumerate(reversed(user_history), 1):
        text += f"{i}. {query}\n"

    await message.answer(text)
```

**3. /stats команда (для админа)**

```python
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    # Только для админа
    ADMIN_ID = 123456789  # Твой user_id

    if message.from_user.id != ADMIN_ID:
        return

    from src.utils.stats import stats

    popular = stats.get_popular_queries(limit=10)

    text = "📊 <b>Статистика бота</b>\n\n"
    text += f"👥 Всего пользователей: {stats.get_total_users()}\n\n"
    text += "<b>Популярные запросы:</b>\n"
    for query, count in popular:
        text += f"• {query}: {count}\n"

    await message.answer(text)
```

#### 📦 Deliverables:

- ✅ История поиска
- ✅ /stats команда
- ✅ (Опционально) Распознавание аудио

---

### ✅ Итог Week 3:

**Расширенный функционал!** Бот имеет:
- ✅ Inline режим
- ✅ (Опционально) Альтернативные источники
- ✅ История поиска
- ✅ Статистика

---

## 🗓️ НЕДЕЛЯ 4: Production Ready

**Цель:** Подготовить бот к деплою на VPS

---

### День 22-24: Оптимизация

#### ✅ Задачи:

**1. Cleanup старых файлов**

`src/utils/cleanup.py`:
```python
import os
import time
from pathlib import Path
from src.config import settings
from src.utils.logger import logger

def cleanup_old_files(max_age_seconds: int = 3600):
    """Удалить файлы старше 1 часа"""
    temp_dir = Path(settings.TEMP_DIR)

    if not temp_dir.exists():
        return

    now = time.time()
    deleted = 0

    for file_path in temp_dir.glob("*.mp3"):
        age = now - file_path.stat().st_mtime

        if age > max_age_seconds:
            file_path.unlink()
            deleted += 1

    if deleted > 0:
        logger.info(f"Cleaned up {deleted} old files")

# Запускать периодически
async def cleanup_task():
    """Фоновая задача очистки"""
    while True:
        cleanup_old_files()
        await asyncio.sleep(3600)  # Каждый час
```

Добавить в `src/main.py`:
```python
import asyncio
from src.utils.cleanup import cleanup_task

async def main():
    # ... настройка роутеров

    # Запустить фоновую очистку
    asyncio.create_task(cleanup_task())

    await dp.start_polling(bot)
```

**2. Redis кэш (опционально)**

Если планируется много пользователей, использовать Redis вместо in-memory кэша:

```python
import redis.asyncio as redis

class RedisCache:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)

    async def set(self, key: str, value: str, ttl: int):
        await self.redis.setex(key, ttl, value)

    async def get(self, key: str) -> str:
        return await self.redis.get(key)
```

**3. SQLite для статистики**

`src/database.py`:
```python
import aiosqlite
from pathlib import Path

DB_PATH = "data/database.db"

async def init_db():
    """Инициализация базы данных"""
    Path("data").mkdir(exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS search_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                results_count INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS download_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                track_id TEXT NOT NULL,
                track_title TEXT,
                artist TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()

async def log_search(user_id: int, query: str, results_count: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO search_stats (user_id, query, results_count) VALUES (?, ?, ?)",
            (user_id, query, results_count)
        )
        await db.commit()

async def log_download(user_id: int, track_id: str, track_title: str, artist: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO download_stats (user_id, track_id, track_title, artist) VALUES (?, ?, ?, ?)",
            (user_id, track_id, track_title, artist)
        )
        await db.commit()
```

#### 📦 Deliverables:

- ✅ Автоматическая очистка старых файлов
- ✅ (Опционально) Redis кэш
- ✅ SQLite для статистики

---

### День 25-26: Docker и деплой

#### ✅ Задачи:

**1. Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установить ffmpeg (нужен для yt-dlp)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Копировать requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копировать код
COPY . .

# Создать директории
RUN mkdir -p data/temp data/cache logs

CMD ["python", "src/main.py"]
```

**2. docker-compose.yml**

```yaml
version: '3.8'

services:
  bot:
    build: .
    restart: always
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    networks:
      - bot-network

  redis:
    image: redis:7-alpine
    restart: always
    networks:
      - bot-network
    volumes:
      - redis-data:/data

networks:
  bot-network:
    driver: bridge

volumes:
  redis-data:
```

**3. Деплой на VPS**

```bash
# На VPS
cd /opt
git clone <your-repo> usp-music-finder
cd usp-music-finder

# Создать .env
nano .env
# Вставить BOT_TOKEN и другие настройки

# Запустить
docker-compose up -d

# Проверить логи
docker-compose logs -f bot
```

**4. Systemd service (альтернатива Docker)**

`/etc/systemd/system/usp-music-bot.service`:
```ini
[Unit]
Description=UspMusicFinder Telegram Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/usp-music-finder
ExecStart=/opt/usp-music-finder/.venv/bin/python src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск:
```bash
sudo systemctl enable usp-music-bot
sudo systemctl start usp-music-bot
sudo systemctl status usp-music-bot
```

#### 📦 Deliverables:

- ✅ Dockerfile
- ✅ docker-compose.yml
- ✅ Деплой на VPS
- ✅ Systemd service

---

### День 27-28: Мониторинг и финальная полировка

#### ✅ Задачи:

**1. Healthcheck endpoint (для Docker)**

```python
from aiohttp import web

async def healthcheck(request):
    return web.Response(text="OK")

async def start_healthcheck_server():
    app = web.Application()
    app.router.add_get('/health', healthcheck)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

# В main.py
async def main():
    # Запустить healthcheck сервер
    asyncio.create_task(start_healthcheck_server())

    # ... остальное
```

Обновить Dockerfile:
```dockerfile
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1
```

**2. Логи - ротация**

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    f"{settings.LOGS_DIR}/bot.log",
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)
```

**3. Уведомления админу**

```python
ADMIN_ID = 123456789  # Твой user_id

async def notify_admin(text: str):
    """Отправить уведомление админу"""
    try:
        await bot.send_message(ADMIN_ID, f"⚠️ {text}")
    except Exception:
        pass

# Использование при критических ошибках
try:
    # ... код
except Exception as e:
    logger.critical(f"Critical error: {e}")
    await notify_admin(f"Critical error: {e}")
```

**4. Backup базы данных**

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/usp-music-finder"

mkdir -p $BACKUP_DIR

# Бэкап базы данных
cp /opt/usp-music-finder/data/database.db $BACKUP_DIR/database_$DATE.db

# Удалить старые бэкапы (старше 30 дней)
find $BACKUP_DIR -name "database_*.db" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Добавить в crontab:
```bash
0 3 * * * /opt/usp-music-finder/backup.sh
```

**5. Финальные тесты**

- [ ] Поиск музыки работает
- [ ] Скачивание работает
- [ ] TOP популярных работает
- [ ] Inline режим работает
- [ ] Rate limiting работает
- [ ] Логи пишутся
- [ ] Cleanup файлов работает
- [ ] Бот переживает перезапуск

#### 📦 Deliverables:

- ✅ Healthcheck endpoint
- ✅ Ротация логов
- ✅ Уведомления админу
- ✅ Backup скрипт
- ✅ Финальное тестирование

---

### ✅ Итог Week 4:

**Production Ready!** Бот готов к работе:
- ✅ Docker контейнер
- ✅ Деплой на VPS
- ✅ Мониторинг
- ✅ Логи и backup
- ✅ Все фичи работают

---

## 📊 Финальный Checklist

### MVP функционал
- [ ] Поиск музыки по тексту (YouTube)
- [ ] Inline keyboard (кнопки 1-10)
- [ ] Скачивание MP3
- [ ] Отправка аудио в Telegram
- [ ] /start, /help команды

### UI/UX
- [ ] Красивые сообщения
- [ ] Progress индикаторы
- [ ] Обработка ошибок
- [ ] Rate limiting
- [ ] TOP популярных песен

### Расширенный функционал
- [ ] Inline режим
- [ ] История поиска
- [ ] Статистика использования
- [ ] (Опционально) Альтернативные источники

### Production
- [ ] Docker контейнер
- [ ] Деплой на VPS
- [ ] Логирование
- [ ] Мониторинг (healthcheck)
- [ ] Backup базы данных
- [ ] Автоматическая очистка файлов

---

## 🎯 Критерии успеха

1. **Функциональность:** Бот находит и скачивает 90%+ популярных треков
2. **Производительность:** Скачивание занимает < 30 секунд
3. **Надежность:** Uptime > 99%
4. **UX:** Пользователи получают результат за < 3 клика

---

## 📚 Полезные ресурсы

- **aiogram docs:** https://docs.aiogram.dev/
- **yt-dlp docs:** https://github.com/yt-dlp/yt-dlp
- **Telegram Bot API:** https://core.telegram.org/bots/api

---

**Готов к разработке!** 🚀

Следующий шаг: [ACTIONS.md](ACTIONS.md) - Пошаговые инструкции для старта.
