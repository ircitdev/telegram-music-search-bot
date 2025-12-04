# 🎵 UspMusicFinder Bot

Telegram бот для поиска и скачивания музыки с YouTube Music. Легкий, быстрый и удобный способ найти любимую песню!

**Bot:** [@UspMusicFinder_bot](https://t.me/UspMusicFinder_bot)

---

## ✨ Возможности

- 🔍 **Поиск музыки** - по названию песни или исполнителю
- ⬇️ **Скачивание MP3** - высокое качество (192 kbps)
- 📊 **TOP популярных** - топ треков по странам
- 🎯 **Удобный UI** - кнопки выбора, красивое форматирование
- 📝 **Метаданные** - правильные теги (исполнитель, название)
- ⚡ **Быстро** - асинхронный поиск и скачивание

---

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/yourusername/UspMusicFinder.git
cd UspMusicFinder
```

### 2. Установка зависимостей

```bash
# Создать виртуальное окружение
python -m venv .venv

# Активировать (Windows)
.\.venv\Scripts\activate

# Активировать (Linux/Mac)
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

### 3. Конфигурация

Создайте файл `.env` в корневой директории:

```env
# Telegram Bot
BOT_TOKEN=your_bot_token_here
BOT_USERNAME=UspMusicFinder_bot

# Пути
TEMP_DIR=./data/temp
CACHE_DIR=./data/cache
LOGS_DIR=./logs
DATABASE_PATH=./data/database.db

# Лимиты
MAX_FILE_SIZE=52428800  # 50MB
MAX_DURATION=600  # 10 минут
RATE_LIMIT_REQUESTS=5  # запросов в минуту
RATE_LIMIT_PERIOD=60  # секунд

# Логирование
LOG_LEVEL=INFO

# Функции
ENABLE_CACHE=true
ENABLE_STATS=true
ENABLE_INLINE=true
```

**Где получить BOT_TOKEN:**

1. Напиши боту [@BotFather](https://t.me/botfather) в Telegram
2. Команда `/newbot`
3. Следуй инструкциям
4. Скопируй полученный токен в `.env`

### 4. Запуск

```bash
python -m src.main
```

**Ожидаемый вывод:**

```log
2025-12-04 13:XX:XX | INFO | usp_music_finder | Bot started: @UspMusicFinder_bot
2025-12-04 13:XX:XX | INFO | usp_music_finder | Polling mode activated
```

---

## 📖 Использование

### Поиск музыки

1. Отправь боту название песни или исполнителя
2. Выбери трек из списка (кнопки 1-10)
3. Получи MP3 файл!

**Примеры:**

- `Bohemian Rhapsody`
- `Queen`
- `The Beatles - Let It Be`

### Команды

```bash
/start - Начать работу с ботом
/help - Показать справку
/top - Популярные песни по странам
```

---

## 🏗️ Архитектура

```
┌─────────────────┐
│  Telegram Bot   │
│   (aiogram)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dispatcher    │ ← Обработка команд
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌─────────────────┐
│  Search Handler │  │  Inline Handler │
└────────┬────────┘  └────────┬────────┘
         │                    │
         └──────────┬─────────┘
                    ▼
         ┌─────────────────┐
         │  Music Searcher │ ← YouTube Music / iTunes
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │   Downloader    │ ← yt-dlp
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Telegram Send  │ ← Отправка MP3
         └─────────────────┘
```

---

## 🛠️ Технологии

### Backend

- **Python 3.11+**
- **aiogram 3.15** - Telegram Bot framework
- **yt-dlp** - универсальный загрузчик медиа
- **mutagen** - работа с метаданными аудио
- **aiohttp** - асинхронные HTTP запросы

### Источники музыки

- **YouTube Music** - основной источник (через yt-dlp)
- **iTunes API** - альтернативный источник
- **Last.fm API** - топ треков по странам

### База данных

- **SQLite** - статистика использования (опционально)
- **Redis** - кэш результатов (опционально)

---

## 📁 Структура проекта

```
UspMusicFinder/
├── src/
│   ├── bot.py              # Инициализация бота
│   ├── config.py           # Настройки из .env
│   ├── main.py             # Точка входа
│   ├── models.py           # Модель Track
│   │
│   ├── handlers/
│   │   ├── start.py        # /start, /help
│   │   ├── search.py       # Поиск по тексту
│   │   ├── top.py          # TOP популярных
│   │   ├── inline.py       # Inline режим
│   │   └── callbacks.py    # Обработка кнопок
│   │
│   ├── searchers/
│   │   ├── youtube.py      # YouTube Music
│   │   └── itunes.py       # iTunes API
│   │
│   ├── downloaders/
│   │   └── youtube_dl.py   # Скачивание через yt-dlp
│   │
│   └── utils/
│       ├── logger.py       # Логирование
│       ├── cache.py        # Кэширование
│       └── rate_limiter.py # Rate limiting
│
├── data/
│   ├── temp/               # Временные файлы
│   ├── cache/              # Кэш результатов
│   └── database.db         # SQLite (опционально)
│
├── logs/                   # Логи
├── .env                    # Конфигурация
└── requirements.txt        # Зависимости
```

---

## 📋 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начать работу с ботом |
| `/help` | Показать справку |
| `/top` | Популярные песни по странам |
| `/history` | История поиска (опционально) |

---

## ⚙️ Конфигурация

### Переменные окружения (.env)

```env
# Telegram Bot
BOT_TOKEN=your_token_here
BOT_USERNAME=UspMusicFinder_bot

# Пути
TEMP_DIR=./data/temp
CACHE_DIR=./data/cache
LOGS_DIR=./logs

# Лимиты
MAX_FILE_SIZE=52428800  # 50MB (лимит Telegram)
MAX_DURATION=600        # 10 минут
RATE_LIMIT_REQUESTS=5   # Запросов в минуту
RATE_LIMIT_PERIOD=60    # Период в секундах

# Логирование
LOG_LEVEL=INFO

# Функции
ENABLE_CACHE=true
ENABLE_STATS=true
ENABLE_INLINE=true
```

---

## 🧪 Разработка

### Установка dev зависимостей

```powershell
pip install -r requirements-dev.txt
```

### Запуск тестов

```powershell
pytest
pytest -v  # verbose
pytest --cov=src  # с покрытием
```

### Форматирование и линтинг

```powershell
# Форматирование
black src tests

# Линтинг
flake8 src tests

# Проверка типов
mypy src
```

### Запуск в режиме разработки

```powershell
# С автоперезагрузкой при изменениях
python src/main.py
```

---

## 🐳 Docker

### Build

```bash
docker build -t usp-music-finder .
```

### Run

```bash
docker run -d \
  --name music-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  usp-music-finder
```

### Docker Compose

```bash
docker-compose up -d
```

---

## 📊 Статистика

Бот собирает анонимную статистику использования:

- Количество поисков
- Популярные запросы
- Количество скачиваний
- Активные пользователи

Статистика хранится в SQLite базе данных.

---

## 🔒 Безопасность

- ✅ API токен в `.env` (не в коде)
- ✅ Rate limiting (5 запросов/минуту)
- ✅ Валидация входных данных
- ✅ Ограничение размера файлов
- ✅ Автоматическая очистка временных файлов
- ✅ Логирование всех действий

---

## 🗺️ Roadmap

### ✅ Phase 1: MVP (Week 1)

- [x] Базовый бот (/start, /help)
- [x] Поиск по YouTube Music
- [x] Скачивание MP3
- [x] Отправка в Telegram

### ✅ Phase 2: UI/UX (Week 2)

- [x] Inline keyboard (кнопки 1-10)
- [x] TOP популярных песен
- [x] Rate limiting
- [x] Красивые сообщения

### 🔄 Phase 3: Extensions (Week 3)

- [ ] Inline режим
- [ ] История поиска
- [ ] Альтернативные источники (iTunes, Deezer)
- [ ] Распознавание аудио (Shazam-like)

### 📅 Phase 4: Production (Week 4)

- [ ] Docker контейнер
- [ ] Деплой на VPS
- [ ] Мониторинг и логи
- [ ] Backup базы данных

---

## 📚 Документация

- [ACTIONS.md](ACTIONS.md) - **НАЧНИ ОТСЮДА** - Пошаговые инструкции
- [PROJECT_SPEC.md](PROJECT_SPEC.md) - Техническая спецификация (73KB)
- [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) - План разработки (4 недели)

---

## 🤝 Contributing

1. Fork проекта
2. Создай feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Открой Pull Request

---

## 📄 License

Этот проект создан для личного использования.

**Примечание:** Убедись что соблюдаешь авторские права на музыку при использовании бота.

---

## 👤 Автор

Создано с помощью DevTools Environment и Claude Code.

**Bot:** [@UspMusicFinder_bot](https://t.me/UspMusicFinder_bot)

---

## 🙏 Благодарности

- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - универсальный загрузчик
- [mutagen](https://github.com/quodlibet/mutagen) - метаданные аудио

---

**Готов к использованию!** 🎵 Начни с [ACTIONS.md](ACTIONS.md)
