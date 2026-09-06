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
   git clone [https://github.com/manazius/xgemini.git](https://github.com/manazius/xgemini.git)
   cd xgemini
   
2. Установите зависимости:
    pip install -r requirements.txt

3. Создайте конфиг на основе примера:
    cp example.config.py config.py
    Укажите в config.py свой JID, пароль и API-ключ Gemini.

4. Запуск:
    python gemini.py
