"""Telegram-бот, который отвечает через Claude.

Настройки берутся из переменных окружения (в Railway: вкладка Variables):
  TELEGRAM_BOT_TOKEN  — токен от @BotFather
  ANTHROPIC_API_KEY   — ключ с console.anthropic.com
  ALLOWED_USER_IDS    — ваш Telegram ID (несколько — через запятую).
                        Пока пусто, бот отвечает только вашим ID, чтобы вы его узнали.
  CLAUDE_MODEL        — необязательно, по умолчанию claude-sonnet-5-5
  SYSTEM_PROMPT       — необязательно, инструкция для Claude
"""

import logging
import os
from collections import defaultdict, deque

from anthropic import AsyncAnthropic
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
)
log = logging.getLogger("bot")

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
SYSTEM_PROMPT = os.environ.get(
    "SYSTEM_PROMPT",
    "Ты дружелюбный помощник в Telegram. Отвечай на языке пользователя, "
    "коротко и по делу. Помогаешь вести Telegram-канал: пишешь посты, "
    "придумываешь идеи и контент-планы.",
)
ALLOWED_USER_IDS = {
    int(x) for x in os.environ.get("ALLOWED_USER_IDS", "").replace(" ", "").split(",") if x
}

MAX_HISTORY = 20          # сколько последних сообщений помнить
TELEGRAM_LIMIT = 4000     # максимальная длина одного сообщения в Telegram

client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
history: dict[int, deque] = defaultdict(lambda: deque(maxlen=MAX_HISTORY))


def is_allowed(update: Update) -> bool:
    return update.effective_user is not None and update.effective_user.id in ALLOWED_USER_IDS


async def deny(update: Update) -> None:
    uid = update.effective_user.id if update.effective_user else "?"
    await update.message.reply_text(
        f"Доступ закрыт.\nВаш Telegram ID: {uid}\n"
        "Добавьте его в переменную ALLOWED_USER_IDS в Railway."
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny(update)
        return
    await update.message.reply_text(
        "Привет! Я Claude. Пиши что угодно.\n/new — начать разговор заново."
    )


async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny(update)
        return
    history[update.effective_chat.id].clear()
    await update.message.reply_text("Начали заново 🙂")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny(update)
        return

    chat_id = update.effective_chat.id
    msgs = history[chat_id]
    msgs.append({"role": "user", "content": update.message.text})

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)

    # История должна начинаться с сообщения пользователя
    conv = list(msgs)
    while conv and conv[0]["role"] != "user":
        conv.pop(0)

    try:
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=conv,
        )
        answer = "".join(b.text for b in resp.content if b.type == "text").strip()
    except Exception:
        log.exception("Claude API error")
        msgs.pop()  # не запоминаем вопрос без ответа
        await update.message.reply_text("Ошибка при обращении к Claude, попробуйте ещё раз.")
        return

    if not answer:
        answer = "…"
    msgs.append({"role": "assistant", "content": answer})

    for i in range(0, len(answer), TELEGRAM_LIMIT):
        await update.message.reply_text(answer[i : i + TELEGRAM_LIMIT])


def main() -> None:
    if not ALLOWED_USER_IDS:
        log.warning("ALLOWED_USER_IDS пуст — бот только сообщает людям их ID.")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_chat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    log.info("Bot started, model=%s", MODEL)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
