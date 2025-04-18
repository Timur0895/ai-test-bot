import logging
import threading
import http.server
import socketserver
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import os
from dotenv import load_dotenv

load_dotenv()

# Состояния
PROFILE, FULL_NAME, AGE, GENDER, PERSONALITY, NEXT_TEST, MASLOW, NEXT_TEST_2, IQ = range(9)

# Импорты логики тестов
from personality_test import ask_personality_question, process_personality_response
from maslow_test import ask_maslow_question, process_maslow_response
from iq_test import ask_iq_question, process_iq_response

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [["🧠 Сформировать мой профиль"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("👋 Привет! Я - HR-ассистент и я помогу тебе пройти небольшое тестирование", reply_markup=reply_markup)
    return PROFILE

async def profile_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != "🧠 Сформировать мой профиль":
        await update.message.reply_text("Пожалуйста, нажмите кнопку '🧠 Сформировать мой профиль'.")
        return PROFILE
    await update.message.reply_text("✍️ Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())
    return FULL_NAME

async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    full_name = update.message.text.strip()
    context.user_data["full_name"] = full_name
    await update.message.reply_text(" 👤 Спасибо! Теперь укажите ваш возраст:")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    age = update.message.text.strip()
    context.user_data["age"] = age
    gender_keyboard = [["👨 Мужской", "👩 Женский"]]
    reply_markup = ReplyKeyboardMarkup(gender_keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("🚻 Укажите ваш пол:", reply_markup=reply_markup)
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    gender = update.message.text.strip()
    if gender not in ["👨 Мужской", "👩 Женский"]:
        await update.message.reply_text("Пожалуйста, выберите один из предложенных вариантов.")
        return GENDER

    context.user_data["gender"] = gender.replace("👨 ", "").replace("👩 ", "")
    context.user_data["personality_index"] = 0
    context.user_data["personality_answers"] = []

    # 🔥 Мягкий переход перед началом теста на тип личности
    await update.message.reply_text(
        "🧠 Отлично! Сейчас начнётся небольшой тест, который поможет нам понять ваш тип личности.\n\n"
    )

    return await ask_personality_question(update, context)


async def start_maslow_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text("🌱 Запускаем тест по Пирамиде Маслоу...", reply_markup=ReplyKeyboardRemove())
    context.user_data["maslow_index"] = 0
    context.user_data["maslow_answers"] = []
    return await ask_maslow_question(update, context)

async def start_iq_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text("🧩 Запускаем IQ тест...", reply_markup=ReplyKeyboardRemove())
    context.user_data["iq_index"] = 0
    context.user_data["iq_scores"] = []
    return await ask_iq_question(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Тестирование прервано.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

    # Запускаем фейковый сервер для Render (чтобы не ругался на отсутствие порта)
    def fake_web_server():
        PORT = 10000
        Handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            httpd.serve_forever()

    threading.Thread(target=fake_web_server, daemon=True).start()


    TOKEN = os.getenv("TELEGRAM_TOKEN")  # Замените на свой
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🧠 Новый тест$") & ~filters.COMMAND, start)
        ],            
        states={
            PROFILE: [
                MessageHandler(
                    filters.Regex("^🧠 (Сформировать мой профиль|Новый тест)$") & ~filters.COMMAND,
                    profile_start
                )
            ],
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_full_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            PERSONALITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_personality_response)],
            NEXT_TEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_maslow_test)],
            MASLOW: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_maslow_response)],
            NEXT_TEST_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_iq_test)],
            IQ: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_iq_response)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
