import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

SYSTEM_PROMPT = """Ты Консилиум, теплый и мудрый ИИ-собеседник, созданный Надеждой с 30-летним опытом в медицине. Помогай человеку разобраться в себе, используя пять подходов: КПТ Бека, экзистенциальный Ялома, инструменты Стутца, отношения Перель, глубинный Юнга. Никогда не ставь диагнозов. Не заменяй врача. Отвечай тепло на русском языке. Задавай один вопрос за раз. Если человек в кризисе - направь к специалисту."""

user_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("Привет. Я Консилиум.\n\nЧто сейчас происходит в твоей жизни?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import anthropic
    user_id = update.effective_user.id
    user_message = update.message.text
    if user_id not in user_histories:
        user_histories[user_id] = []
    user_histories[user_id].append({"role": "user", "content": user_message})
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]
    await update.message.chat.send_action("typing")
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=user_histories[user_id]
        )
        assistant_message = response.content[0].text
        user_histories[user_id].append({"role": "assistant", "content": assistant_message})
        await update.message.reply_text(assistant_message)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Что-то пошло не так. Попробуй ещё раз.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("Начинаем заново.\n\nЧто сейчас происходит в твоей жизни?")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Консилиум запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
