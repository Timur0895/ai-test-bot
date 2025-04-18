import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def format_qa(questions: list, answers: list) -> str:
    lines = []
    for i in range(len(questions)):
        q = questions[i]
        a = answers[i] if i < len(answers) else "-"
        lines.append(f"Вопрос: {q}\nОтвет: {a}\n")
    return "\n".join(lines)

def analyze_candidate(user_data: dict) -> str:
    full_name = user_data.get("full_name", "Кандидат")
    age = user_data.get("age", "—")
    gender = user_data.get("gender", "—")

    # Блоки результатов
    personality_result = user_data.get("personality_result", "")
    maslow_result = user_data.get("maslow_result", "")
    iq_result = user_data.get("iq_result", "")

    # Вопросы и ответы
    personality_qas = format_qa(
        user_data.get("personality_test_questions", []),
        user_data.get("personality_answers", [])
    )

    maslow_qas = format_qa(
        user_data.get("maslow_test_questions", []),
        user_data.get("maslow_answers", [])
    )

    iq_qas = format_qa(
        user_data.get("iq_test_questions", []),
        user_data.get("iq_scores", [])
    )

    prompt = f"""
Ты — опытный HR-аналитик. Твоя задача — проанализировать кандидата по результатам 3 тестов:

1. Тип личности (soft-skills)
2. Мотивация (по пирамиде Маслоу)
3. Интеллект (IQ)

🔹 Учитывай как итоговые результаты, так и конкретные вопросы и ответы кандидата. Важно понять, насколько кандидат:
— готов к самостоятельной работе;
— устойчив к стрессу;
— способен к обучению;
— подходит под командную/лидерскую роль;
— потенциально проблемен.

📌 Данные кандидата:
ФИО: {full_name}
Возраст: {age}
Пол: {gender}

📍 Обрати особое внимание на возраст и пол кандидата. Например:
— 19-летний может иметь слабую самоорганизацию, и это допустимо.
— 35-летний с низким уровнем IQ — потенциальный риск.
— Мужчина и женщина могут по-разному выражать инициативность или коммуникативность.

📎 Результаты теста на тип личности:
{personality_result}

📎 Вопросы и ответы:
{personality_qas}

📎 Результаты теста по Маслоу:
{maslow_result}

📎 Вопросы и ответы:
{maslow_qas}

📎 Результаты IQ теста:
{iq_result}

📎 Вопросы и ответы:
{iq_qas}

Сформируй развернутый отчёт в таком формате:

==============================

🧾 Профиль кандидата:
ФИО, возраст, пол

✅ Сильные стороны:
- ...

⚠️ Слабые стороны:
- ...

🚨 Подозрительные моменты:
- (...если есть)

🧪 Рекомендации для HR:
- (...как проверять профпригодность)

📊 Оценка по 10-балльной шкале:
- X/10 (10 — идеален, 5 — средне, <5 — сомнительно)

💬 Общая оценка:
- (...)

==============================

🖊 Тон отчёта — чёткий, деловой, без воды.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — опытный HR-аналитик. "
                    "Оценивай кандидата по результатам тестов на основе профессиональных критериев. "
                    "⚠️ ВАЖНО: учитывай возраст и пол кандидата как ключевые характеристики. "
                    "Результаты одного и того же теста могут означать разное для кандидатов разного возраста или пола. "
                    "Оцени эмоциональную зрелость, уровень ответственности и мотивацию с учётом этих факторов."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=1000
    )

    base_summary = response.choices[0].message.content.strip()

    # Добавим блоки результатов личности и Маслоу в конец отчета
    detailed_summary = f"{base_summary}\n\n📌 Результаты по шкалам:\n\n🧠 Тип личности:\n{personality_result}\n\n🎯 Маслоу:\n{maslow_result}"

    return detailed_summary
