# xgemini

Легковесный асинхронный XMPP-бот на Python с интеграцией Gemini API.

## Возможности
- Официальный SDK `google-genai` (поддержка моделей линейки Flash/Flash-Lite).
- Ответы чистым текстом без Markdown (совместимо с любыми классическими XMPP-клиентами).
- Поддержка XEP-0085 (статус набора текста «Печатает...»).
- Поддержка XEP-0199 (XMPP Ping для удержания соединения).
- Белый список JID (`ALLOWED_JIDS`).
- Сброс контекста диалога (`!clear`, `сброс`).
- Поддержка работы через локальный SOCKS5-прокси (например, Cloudflare WARP).

## Установка и запуск

1. Склонируйте репозиторий и перейдите в папку:
   ```bash
   git clone [https://github.com/manazius/xgemini.git](https://github.com/manazius/xgemini.git)
   cd xgemini
   ```
   
3. Установите зависимости:
   ```bash
    pip install -r requirements.txt
   ```
   
5. Создайте конфиг на основе примера:
   ```bash
    cp example.config.py config.py
   nano config.py
   ```bash
    Укажите в config.py свой JID, пароль и API-ключ Gemini.

7. Запуск:
   ```bash
    python gemini.py
   ```
