# Мой клауд — Telegram-бот с Claude

## Как запустить на Railway

1. **Ключ Claude.** Зайдите на console.anthropic.com, пополните баланс и создайте API-ключ (Settings → API Keys). Это отдельная оплата, не подписка Claude.
2. **GitHub.** Создайте новый репозиторий и загрузите туда все файлы из этой папки (кнопка «Add file → Upload files»).
3. **Railway.** На railway.com: New Project → Deploy from GitHub repo → выберите репозиторий.
4. **Переменные.** В проекте откройте Variables и добавьте:
   - `TELEGRAM_BOT_TOKEN` — токен от @BotFather
   - `ANTHROPIC_API_KEY` — ключ из шага 1
5. **Ваш ID.** Напишите боту `/start`, и он пришлёт ваш Telegram ID. Добавьте переменную `ALLOWED_USER_IDS` с этим числом. Railway перезапустит бота, после этого он будет отвечать только вам.

Команды бота: `/start` — приветствие, `/new` — начать разговор заново.

Ключи и токены храните только в Variables на Railway, никогда не кладите их в код на GitHub.
