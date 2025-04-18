import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from maslow_test import ask_maslow_question  # для перехода к следующему тесту

# Константа следующего состояния
NEXT_TEST = 5

personality_questions = [
    # Адаптивность (1–3)
    {"question": "1. Я легко адаптируюсь к новым условиям и быстро включаюсь в незнакомый рабочий процесс.", "characteristic": "Адаптивность"},
    {"question": "2. В стрессовых ситуациях я сохраняю спокойствие и способность рационально принимать решения.", "characteristic": "Адаптивность"},
    {"question": "3. Я положительно воспринимаю изменения и открыт к новым методам и экспериментам.", "characteristic": "Адаптивность"},

    # Инициативность (4–6)
    {"question": "4. Мне комфортно самостоятельно принимать решения, даже если я не обладаю всей информацией.", "characteristic": "Инициативность"},
    {"question": "5. Я стремлюсь находить решения в нестандартных ситуациях и не боюсь пробовать новое.", "characteristic": "Инициативность"},
    {"question": "6. Я часто беру на себя дополнительные задачи, не дожидаясь прямого указания.", "characteristic": "Инициативность"},

    # Эмоциональный интеллект (7–9)
    {"question": "7. В конфликтных ситуациях я стараюсь находить компромисс и сохранить продуктивные отношения.", "characteristic": "Эмоциональный интеллект"},
    {"question": "8. Я спокойно воспринимаю конструктивную критику и использую её для развития.", "characteristic": "Эмоциональный интеллект"},
    {"question": "9. Я умею замечать эмоциональное состояние других и адаптировать своё поведение в общении.", "characteristic": "Эмоциональный интеллект"},

    # Самоорганизация (10–12)
    {"question": "10. Я умею планировать своё время и редко откладываю дела на последний момент.", "characteristic": "Самоорганизация"},
    {"question": "11. Для меня важно видеть результат своей работы — это поддерживает мою мотивацию.", "characteristic": "Самоорганизация"},
    {"question": "12. Даже в трудностях я стараюсь довести начатое до конца.", "characteristic": "Самоорганизация"},

    # Коммуникативные навыки (13–15)
    {"question": "13. Мне комфортно работать в команде, я активно взаимодействую с коллегами.", "characteristic": "Коммуникативные навыки"},
    {"question": "14. Я легко нахожу контакт с новыми людьми и поддерживаю эффективную коммуникацию.", "characteristic": "Коммуникативные навыки"},
    {"question": "15. Я умею ясно и убедительно излагать свои мысли в устной и письменной форме.", "characteristic": "Коммуникативные навыки"}
]


def get_scale_keyboard():
    keyboard = [
        [str(i) for i in range(1, 6)],
        [str(i) for i in range(6, 11)]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

async def ask_personality_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get("personality_index", 0) == 0:
        context.user_data["personality_test_questions"] = [q["question"] for q in personality_questions]
    index = context.user_data.get("personality_index", 0)
    if index < len(personality_questions):
        question = personality_questions[index]
        await update.message.reply_text(
            f"{question['question']}\n",
            reply_markup=get_scale_keyboard()
        )
        return 4  # PERSONALITY
    else:
        return await analyze_personality(update, context)

async def process_personality_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    index = context.user_data.get("personality_index", 0)
    try:
        answer = int(update.message.text)
        if not 1 <= answer <= 10:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число от 1 до 10.")
        return 4
    context.user_data.setdefault("personality_answers", []).append(answer)
    context.user_data["personality_index"] = index + 1
    return await ask_personality_question(update, context)

def interpret_score(score: int) -> str:
    if score >= 27:
        return "очень высокий уровень"
    elif score >= 22:
        return "высокий уровень"
    elif score >= 16:
        return "средний уровень"
    else:
        return "низкий уровень"

async def analyze_personality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answers = context.user_data.get("personality_answers", [])
    groups = {
        "Адаптивность": sum(answers[0:3]),
        "Инициативность": sum(answers[3:6]),
        "Эмоциональный интеллект": sum(answers[6:9]),
        "Самоорганизация": sum(answers[9:12]),
        "Коммуникативные навыки": sum(answers[12:15]),
    }
    analysis = ["Результаты теста на тип личности:"]
    for name, score in groups.items():
        analysis.append(f"- {name}: {score}/30 ({interpret_score(score)})")
    context.user_data["personality_result"] = "\n".join(analysis)
    await update.message.reply_text(context.user_data["personality_result"], reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text(
        "Чтобы продолжить, нажмите кнопку для прохождения теста по Пирамиде Маслоу.",
        reply_markup=ReplyKeyboardMarkup([["🔺 Тест Маслоу"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return NEXT_TEST
