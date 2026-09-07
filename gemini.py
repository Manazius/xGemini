import asyncio
import logging
import re
import sys
from slixmpp import ClientXMPP
from google import genai
from google.genai import types

import config

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("xgemini")

# Настройки из config.py с дефолтными значениями на случай отсутствия
JID = config.JID
PASSWORD = config.PASSWORD
ALLOWED_JIDS = set(getattr(config, "ALLOWED_JIDS", []))
GEMINI_API_KEY = config.GEMINI_API_KEY
GEMINI_MODEL = getattr(config, "GEMINI_MODEL", "gemini-2.5-flash-lite")
TEMPERATURE = getattr(config, "TEMPERATURE", 0.8)
SYSTEM_PROMPT = getattr(
    config,
    "SYSTEM_PROMPT",
    "Ты остроумный и прямой собеседник в Jabber/XMPP. "
    "Общайся неформально, на равных, без корпоративных клише. "
    "Форматирование: чистый plain text без Markdown."
)


def clean_markdown(text: str) -> str:
    """Удаляет базовые маркеры Markdown для чистого отображения в Jabber."""
    if not text:
        return ""
    # Удаляем жирный и курсив (* или _)
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
    # Удаляем инлайн-код `code`
    text = re.sub(r"`(.*?)`", r"\1", text)
    # Удаляем блоки кода ```code```
    text = re.sub(r"```.*?\n(.*?)```", r"\1", text, flags=re.DOTALL)
    # Удаляем заголовки #
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    return text.strip()


class GeminiBot(ClientXMPP):
    def __init__(self, jid: str, password: str):
        super().__init__(jid, password)

        # Регистрация плагинов XMPP
        self.register_plugin("xep_0030")  # Service Discovery
        self.register_plugin("xep_0199")  # XMPP Ping (keep-alive)
        self.register_plugin("xep_0085")  # Chat State Notifications (composing...)

        # Обработчики событий
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

        # Клиент Google GenAI
        self.ai_client = genai.Client(api_key=GEMINI_API_KEY)
        self.generation_config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=TEMPERATURE,
        )

        # Сессии чатов для каждого JID: {bare_jid: chat_instance}
        self.chats = {}

    async def start(self, event):
        self.send_presence()
        await self.get_roster()
        logger.info("Бот успешно подключился к XMPP-серверу под JID: %s", self.boundjid.bare)

        # Включаем периодический keepalive пинг каждые 60 секунд
        self["xep_0199"].enable_keepalive(interval=60, timeout=20)

    def get_or_create_chat(self, bare_jid: str):
        if bare_jid not in self.chats:
            logger.info("Создание новой сессии диалога для: %s", bare_jid)
            self.chats[bare_jid] = self.ai_client.aio.chats.create(
                model=GEMINI_MODEL,
                config=self.generation_config
            )
        return self.chats[bare_jid]

    def reset_chat(self, bare_jid: str):
        if bare_jid in self.chats:
            del self.chats[bare_jid]
            logger.info("Контекст диалога сброшен для: %s", bare_jid)

    async def message(self, msg):
        # Реагируем только на личные сообщения (chat) и обычные без явного типа
        if msg["type"] not in ("chat", "normal"):
            return

        body = (msg["body"] or "").strip()
        if not body:
            return

        sender_bare = msg["from"].bare

        # Проверка белого списка (если он задан)
        if ALLOWED_JIDS and sender_bare not in ALLOWED_JIDS:
            logger.warning("Отклонено сообщение от неавторизованного JID: %s", sender_bare)
            return

        # Команды сброса контекста
        if body.lower() in ("!clear", "/clear", "сброс", "забудь"):
            self.reset_chat(sender_bare)
            msg.reply("Контекст диалога очищен. О чем поговорим?").send()
            return

        # Отправляем статус "Печатает..." отдельным пакетом перед запросом к API
        typing_msg = self.make_message(mto=msg["from"], mtype=msg["type"])
        typing_msg["chat_state"] = "composing"
        typing_msg.send()

        try:
            chat = self.get_or_create_chat(sender_bare)
            response = await chat.send_message(body)

            clean_text = clean_markdown(response.text)

            # Прикрепляем статус "Активен" прямо к итоговому ответу
            reply = msg.reply(clean_text)
            reply["chat_state"] = "active"
            reply.send()

        except Exception as e:
            logger.error("Ошибка при генерации ответа: %s", e, exc_info=True)
            err_reply = msg.reply(f"Произошла ошибка при обращении к API: {e}")
            err_reply["chat_state"] = "active"
            err_reply.send()


def main():
    xmpp_host = getattr(config, "XMPP_HOST", None)
    xmpp_port = getattr(config, "XMPP_PORT", 5222)

    bot = GeminiBot(JID, PASSWORD)

    if xmpp_host:
        bot.connect((xmpp_host, xmpp_port))
    else:
        bot.connect()

    bot.loop.run_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Остановка бота вручную...")
        sys.exit(0)
