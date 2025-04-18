import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from google_sheet_helper import save_results_to_google_sheet
from analyze_candidate import analyze_candidate
import os
from dotenv import load_dotenv

load_dotenv()

iq_test_questions = [
    {
        "question": "1. Какое число должно быть следующим в ряду: 2, 4, 8, 16, ?",
        "options": ["20", "24", "32", "30"],
        "correct": 2
    },
    {
        "question": "2. Если ДЕНЬ относится к НОЧИ, то ЛЕТО относится к ...?",
        "options": ["ЗИМА", "СОЛНЦЕ", "ОСЕНЬ", "ТЕПЛО"],
        "correct": 0
    },
    {
        "question": "3. Найдите лишнее слово: кот, собака, воробей, попугай.",
        "options": ["кот", "собака", "воробей", "попугай"],
        "correct": 2  # воробей — дикая птица, остальные — домашние
    },
    {
        "question": "4. Решите уравнение: 5x - 3 = 2x + 6",
        "options": ["x = 1", "x = 2", "x = 3", "x = 4"],
        "correct": 2
    },
    {
        "question": "5. Увеличим стороны квадрата в 2 раза. Что произойдёт?",
        "options": [
            "Площадь ×2",
            "Без изменений",
            "Площадь ×4",
            "Периметр уменьшится"
        ],
        "correct": 2
    },
    {
        "question": "6. Какое слово можно составить из букв: П, А, Н, О, Р, А, М, А?",
        "options": ["ПАРМА", "ПАНОРАМА", "НОРА", "МАНГО"],
        "correct": 1
    },
    {
        "question": "7. Утка стоит на одной ноге и весит 3 кг. Сколько будет весить утка, если она встанет на две ноги?",
        "options": ["1.5 кг", "3 кг", "6 кг", "2 кг"],
        "correct": 1
    },
    {
        "question": "8. В семье 2 отца и 2 сына. Сколько всего человек?",
        "options": ["4", "5", "3", "6"],
        "correct": 2
    },
    {
        "question": "9. Какое из этих чисел делится на 9: 627, 724, 123, 358?",
        "options": ["627", "724", "123", "358"],
        "correct": 0
    },
    {
        "question": "10. Найдите слово, которое является анаграммой слова ‘ПАРК’",
        "options": ["ПАКР", "ПАРК", "КРАП", "ПАРА"],
        "correct": 2
    }
]


def get_iq_keyboard(options):
    return ReplyKeyboardMarkup([options], one_time_keyboard=True, resize_keyboard=True)

async def ask_iq_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get("iq_index", 0) == 0:
        context.user_data["iq_test_questions"] = [q["question"] for q in iq_test_questions]
    index = context.user_data.get("iq_index", 0)
    if index < len(iq_test_questions):
        question = iq_test_questions[index]
        await update.message.reply_text(question["question"], reply_markup=get_iq_keyboard(question["options"]))
        return 8  # IQ
    else:
        return await analyze_iq(update, context)

async def process_iq_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    index = context.user_data.get("iq_index", 0)
    question = iq_test_questions[index]
    user_answer = update.message.text.strip()
    try:
        selected = question["options"].index(user_answer)
    except ValueError:
        await update.message.reply_text("Пожалуйста, выберите из предложенных вариантов.")
        return 8
    is_correct = 1 if selected == question["correct"] else 0
    context.user_data.setdefault("iq_scores", []).append(is_correct)
    context.user_data["iq_index"] += 1
    return await ask_iq_question(update, context)

# 💬 Эти переменные ты указываешь один раз где-нибудь в bot_main.py
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # id группы с форумами
THREAD_ID_HIRING = int(os.getenv("THREAD_ID_HIRING", "1234567890"))  # id темы "Найм"

async def analyze_iq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    correct = sum(context.user_data.get("iq_scores", []))
    level = "Очень высокий уровень IQ" if correct >= 8 else "Средний уровень IQ" if correct >= 5 else "Ниже среднего IQ"
    context.user_data["iq_result"] = f"Вы ответили правильно на {correct} из 10 вопросов.\n{level}"
    
    await update.message.reply_text(context.user_data["iq_result"], reply_markup=ReplyKeyboardRemove())

    # Генерируем AI-анализ
    try:
        # await update.message.reply_text("📊 Генерируется итоговая аналитика кандидата...")
        summary = analyze_candidate(context.user_data)

        # Отправка анализа в тему форума "Найм"
        await context.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            message_thread_id=THREAD_ID_HIRING,
            text=f"📥 Новый кандидат:\n\n{summary}"
        )

        logging.info("Анализ кандидата успешно отправлен в тему 'Найм'.")

    except Exception as e:
        logging.error(f"Ошибка при генерации или отправке анализа кандидата: {e}")
        await update.message.reply_text("⚠️ Ошибка при создании финального анализа.")

    
    await update.message.reply_text("🎉 Тестирование завершено! Благодарим за участие.",
        reply_markup=ReplyKeyboardMarkup([["🧠 Новый тест"]], one_time_keyboard=True, resize_keyboard=True)
    )

    # Сохраняем в Google Таблицу
    try:
        save_results_to_google_sheet(context.user_data)
        logging.info("Все результаты сохранены в Google Таблицу.")
    except Exception as e:
        logging.error(f"Ошибка сохранения: {e}")    

    return ConversationHandler.END