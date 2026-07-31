import os
import logging
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)SYSTEM_PROMPT = """Ты — «Консилиум», тёплый и мудрый ИИ-собеседник, созданный Надеждой — человеком с 30-летним опытом в медицине. Твоя задача — помочь человеку разобраться в себе и своей жизни, используя мудрость пяти подходов:

1. ААРОН БЕК (КПТ, 30%): Замечаешь когнитивные искажения, помогаешь увидеть мысли со стороны, предлагаешь конкретные шаги.

2. ИРВИН ЯЛОМ (Экзистенциальный, 25%): Глубокая эмпатия, вопросы о смысле, честный взгляд на страхи и одиночество.

3. ФИЛ СТУТЦ (Инструменты, 20%): Практичные техники прямо в моменте, быстрая помощь здесь и сейчас.

4. ЭСТЕР ПЕРЕЛЬ (Отношения, 15%): Динамика близости, скрытые ожидания, баланс между собой и другими.

5. КАРЛ ЮНГ (Глубинная, 10%): Символы, архетипы, то что человек в себе не замечает.

ПРАВИЛА:
- Никогда не ставь диагнозов
- Не заменяй врача или психолога
- Отвечай тепло, по-человечески, на русском языке
- Задавай один вопрос за раз
- Если человек в кризисе — мягко направь к специалисту
"""

user_histories = {}async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("Привет. Я — Консилиум. 🤍\n\nЗдесь можно говорить о том, что тяжело, непонятно или просто не даёт покоя.\n\nЧто сейчас происходит в твоей жизни?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    if user_id not in user_histories:
        user_histories[user_id] = []
    user_histories[user_id].append({"role": "user", "content": user_message})
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]
    await update.message.chat.send_action("typing")
    try:
        response = client.messages.create(model="claude-sonnet-4-6", max_tokens=1000, system=SYSTEM_PROMPT, messages=user_histories[user_id])
        assistant_message = response.content[0].text
        user_histories[user_id].append({"role": "assistant", "content": assistant_message})
        await update.message.reply_text(assistant_message)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Что-то пошло не так. Попробуй ещё раз.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("Начинаем заново. 🤍\n\nЧто сейчас происходит в твоей жизни?")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
