import asyncio
import logging
from google import genai
from google.genai import types
import config
import slixmpp

# Настройка системного логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)


class GeminiXmppBot(slixmpp.ClientXMPP):

  def __init__(self, jid, password):
    super().__init__(jid, password)
    self.add_event_handler("session_start", self.start)
    self.add_event_handler("message", self.message)
    self.chats = {}

  async def start(self, event):
    self.send_presence()
    await self.get_roster()
    logging.info(f"Бот успешно подключен как {self.boundjid.bare}")

  async def message(self, msg):
    if msg["type"] in ("chat", "normal") and msg["body"]:
      user_message = msg["body"]
      sender_jid = msg["from"].bare

      # 1. Белый список: игнорируем всех, кого нет в ALLOWED_JIDS
      if getattr(config, "ALLOWED_JIDS", None) and sender_jid not in config.ALLOWED_JIDS:
        logging.warning(f"Отклонено сообщение от неизвестного JID: {sender_jid}")
        return

      # 2. Команда очистки контекста
      if user_message.strip().lower() in ("/clear", "!clear", "сброс", "!reset"):
        self.chats.pop(sender_jid, None)
        self.send_message(mto=msg["from"], mbody="Контекст очищен. Начнем с чистого листа!", mtype=msg["type"])
        logging.info(f"Контекст очищен для пользователя {sender_jid}")
        return

      # Инициализация сессии для нового пользователя
      if sender_jid not in self.chats:
        model_name = getattr(config, "GEMINI_MODEL")

        self.chats[sender_jid] = gemini_client.aio.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Ты — ассистент в простом текстовом XMPP-мессенджере. "
                    "1. Категорически запрещено использовать любую Markdown-разметку "
                    "для форматирования текста (никаких звездочек ** для жирного, "
                    "никаких решеток для заголовков и т.д.). Пиши только чистый текст. "
                    "2. Не генерируй и не пытайся создавать изображения, видео "
                    "или иные медиафайлы, отвечай исключительно текстом."
                )
            ),
        )

      chat_session = self.chats[sender_jid]

      # 3. Отправляем статус "Печатает..." (composing)
      typing_msg = self.make_message(mto=msg["from"], mtype=msg["type"])
      typing_msg["chat_state"] = "composing"
      typing_msg.send()

      # Запрашиваем ответ у Google
      try:
        response = await chat_session.send_message(user_message)
        reply_text = response.text if response.text else "Пустой ответ."
      except ValueError as e:
        # 4. Перехват ошибки цензуры Google (Safety Settings)
        reply_text = "⚠️ Ответ заблокирован внутренними фильтрами безопасности Google."
        logging.warning(f"Блокировка контента для {sender_jid}: {e}")
      except Exception as e:
        # Логируем любые другие ошибки с полным трейсбеком
        reply_text = f"Ошибка при вызове API: {e}"
        logging.error(f"Ошибка API при обработке сообщения от {sender_jid}:", exc_info=True)

      # Убираем статус "Печатает..." и отправляем сам текст
      reply_msg = self.make_message(mto=msg["from"], mtype=msg["type"])
      reply_msg["chat_state"] = "active"
      reply_msg["body"] = reply_text
      reply_msg.send()


if __name__ == "__main__":
  xmpp = GeminiXmppBot(config.JID, config.PASSWORD)

  # Регистрируем нужные XEP-расширения
  xmpp.register_plugin("xep_0199")  # XMPP Ping (поддержание соединения)
  xmpp.register_plugin("xep_0085")  # Уведомления о состоянии чата (печатает...)

  if xmpp.connect():
    loop = asyncio.get_event_loop()
    try:
      loop.run_forever()
    except KeyboardInterrupt:
      logging.info("Остановка бота по команде (Ctrl+C)...")
      xmpp.disconnect()
  else:
    logging.error("Не удалось подключиться к XMPP серверу.")
