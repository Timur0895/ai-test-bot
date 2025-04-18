import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes

# Константа перехода к следующему тесту
NEXT_TEST_2 = 7

maslow_test_questions = [
    # Потребность в безопасности
    {"question": "1. Я предпочитаю стабильность и понятные условия работы, а не постоянные изменения.", "category": "Потребность в безопасности"},
    {"question": "2. Наличие гарантий и защитных механизмов важно для меня при выборе места работы.", "category": "Потребность в безопасности"},
    {"question": "3. В неоднозначных ситуациях я испытываю дискомфорт и предпочитаю чёткие инструкции.", "category": "Потребность в безопасности"},
    {"question": "4. Мне важна уверенность в завтрашнем дне и защищённость от неожиданных рисков.", "category": "Потребность в безопасности"},

    # Социальная потребность
    {"question": "5. Мне важно работать в коллективе и чувствовать себя частью команды.", "category": "Социальная потребность"},
    {"question": "6. Я поддерживаю неформальное общение с коллегами и ценю дружескую атмосферу.", "category": "Социальная потребность"},
    {"question": "7. Мне важно одобрение от других людей и признание моей роли в команде.", "category": "Социальная потребность"},
    {"question": "8. Я люблю получать обратную связь от коллег и руководства.", "category": "Социальная потребность"},

    # Потребность в самоутверждении
    {"question": "9. Я стремлюсь к высоким результатам и хочу быть замеченным за свои достижения.", "category": "Потребность в самоутверждении"},
    {"question": "10. Мне важно продвигаться по карьерной лестнице и видеть перспективу роста.", "category": "Потребность в самоутверждении"},
    {"question": "11. Признание моих достижений важно для меня и напрямую влияет на мою мотивацию.", "category": "Потребность в самоутверждении"},

    # Потребность в самоактуализации
    {"question": "12. Я хочу постоянно развиваться и выходить за рамки привычных задач.", "category": "Потребность в самоактуализации"},
    {"question": "13. Возможность самореализации в работе для меня ключевая.", "category": "Потребность в самоактуализации"},
    {"question": "14. Я ставлю долгосрочные цели и стремлюсь к их реализации.", "category": "Потребность в самоактуализации"},
    {"question": "15. Я готов обучаться новым навыкам и применять их в практике.", "category": "Потребность в самоактуализации"}
]


def get_maslow_keyboard():
    return ReplyKeyboardMarkup([
        ["Совершенно верно", "Скорее верно"],
        ["Затрудняюсь ответить", "Скорее неверно"],
        ["Совершенно неверно"]
    ], one_time_keyboard=True, resize_keyboard=True)

async def ask_maslow_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get("maslow_index", 0) == 0:
        context.user_data["maslow_test_questions"] = [q["question"] for q in maslow_test_questions]
    index = context.user_data.get("maslow_index", 0)
    if index < len(maslow_test_questions):
        question = maslow_test_questions[index]
        await update.message.reply_text(question["question"], reply_markup=get_maslow_keyboard())
        return 6  # MASLOW
    else:
        return await analyze_maslow(update, context)

async def process_maslow_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    map_answer = {
        "Совершенно верно": 5,
        "Скорее верно": 4,
        "Затрудняюсь ответить": 3,
        "Скорее неверно": 2,
        "Совершенно неверно": 1
    }
    user_text = update.message.text.strip()
    if user_text not in map_answer:
        await update.message.reply_text("Пожалуйста, выберите вариант ответа.")
        return 6
    context.user_data.setdefault("maslow_answers", []).append(map_answer[user_text])
    context.user_data["maslow_index"] = context.user_data.get("maslow_index", 0) + 1
    return await ask_maslow_question(update, context)

async def analyze_maslow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answers = context.user_data.get("maslow_answers", [])
    categories = {}
    for i, question in enumerate(maslow_test_questions[:len(answers)]):
        cat = question["category"]
        categories.setdefault(cat, 0)
        categories[cat] += answers[i]
    result = "\n".join([f"- {k}: {v} баллов" for k, v in categories.items()])
    context.user_data["maslow_result"] = f"Результаты теста по Пирамиде Маслоу:\n{result}"
    await update.message.reply_text(context.user_data["maslow_result"], reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text(
        "Чтобы продолжить, нажмите кнопку для прохождения IQ теста",
        reply_markup=ReplyKeyboardMarkup([["🧩 IQ тест"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return NEXT_TEST_2
