# example.config.py
# Скопируйте этот файл как config.py и укажите реальные данные

# Учетные данные для подключения бота к XMPP-серверу
JID = "bot_username@your-server.org"
PASSWORD = "your_secret"

# API-ключ Gemini (получить в Google AI Studio)
GEMINI_API_KEY = "AIzaSy..."

# Список разрешенных пользователей (белый список JID).
# Оставьте список пустым или укажите свои аккаунты, чтобы ботом не могли пользоваться посторонние.
ALLOWED_JIDS = [
    "user@your-server.org",
]

# Модель Gemini для генерации ответов
# Например: "gemini-3.5-flash-lite", "gemini-3.6-flash"
GEMINI_MODEL = "gemini-3.5-flash-lite"
