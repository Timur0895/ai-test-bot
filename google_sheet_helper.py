import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import WorksheetNotFound
from time import sleep

def save_results_to_google_sheet(user_data: dict) -> None:
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)

    spreadsheet_url = "https://docs.google.com/spreadsheets/d/13GZ4iYS0NwoYgFG11Z7XhBDQheqZSpwHo2YY_mYbyn4/edit?gid=0#gid=0"
    spreadsheet = client.open_by_url(spreadsheet_url)

    candidate_name = user_data.get("full_name", "Unknown")
    try:
        worksheet = spreadsheet.worksheet(candidate_name)
    except WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=candidate_name, rows="300", cols="4")

    row = 1
    # 📌 Основные данные
    metadata = [
        ["Имя и Фамилия", user_data.get("full_name", "")],
        ["Возраст", user_data.get("age", "")],
        ["Пол", user_data.get("gender", "")],
        ["Результат по типу личности", user_data.get("personality_result", "")],
        ["Результат по Маслоу", user_data.get("maslow_result", "")],
        ["Результат по IQ", user_data.get("iq_result", "")]
    ]
    for entry in metadata:
        worksheet.update(f"A{row}:B{row}", [entry])
        row += 1
        sleep(0.5)

    row += 1  # Пробел

    # 🔍 Секция 1 — Вопросы по типу личности
    worksheet.update(f"A{row}:B{row}", [["Тест на тип личности", "Градация от 1 до 10"]])
    row += 1
    worksheet.update(f"A{row}:B{row}", [["Вопрос", "Ответ"]])
    row += 1
    for i, question in enumerate(user_data.get("personality_test_questions", [])):
        answer = user_data.get("personality_answers", [])[i] if i < len(user_data.get("personality_answers", [])) else ""
        worksheet.update(f"A{row}:B{row}", [[question, str(answer)]])
        row += 1
        sleep(0.5)

    row += 2

    # 🔍 Секция 2 — Вопросы по Маслоу
    worksheet.update(f"A{row}:B{row}", [["Тест по Маслоу", "Градация от 1 до 5"]])
    row += 1
    worksheet.update(f"A{row}:B{row}", [["Вопрос", "Ответ"]])
    row += 1
    for i, question in enumerate(user_data.get("maslow_test_questions", [])):
        answer = user_data.get("maslow_answers", [])[i] if i < len(user_data.get("maslow_answers", [])) else ""
        worksheet.update(f"A{row}:B{row}", [[question, str(answer)]])
        row += 1
        sleep(0.5)

    row += 2

    # 🔍 Секция 3 — Вопросы по IQ
    worksheet.update(f"A{row}:B{row}", [["IQ Тест", "Верно или неверно"]])
    row += 1
    worksheet.update(f"A{row}:B{row}", [["Вопрос", "Ответ"]])
    row += 1
    for i, question in enumerate(user_data.get("iq_test_questions", [])):
        answer = user_data.get("iq_scores", [])[i] if i < len(user_data.get("iq_scores", [])) else ""
        answer_text = "Верно" if answer == 1 else "Неверно"
        worksheet.update(f"A{row}:B{row}", [[question, answer_text]])
        row += 1
        sleep(0.5)
