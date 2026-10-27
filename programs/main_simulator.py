# -*- coding: utf-8 -*-
"""Section 5. Main simulator for checking compliance with the personal data law.

Run: python programs/main_simulator.py
Text query parsing uses only built-in Python tools (strings, dicts, the re module).
"""
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _dir in ("data", "programs"):
    sys.path.insert(0, os.path.join(ROOT, _dir))

FINAL_REPORT_FILE = os.path.join(ROOT, "reports", "final_report.txt")
NOTIFICATION_FILE = os.path.join(ROOT, "reports", "last_notification.txt")
EXIT_WORDS = ("выход", "exit", "quit", "q")

# Penalty points (weights chosen by us): the heavier the sanction, the more points
VIOLATION_WEIGHT = {"нарушение по биометрии": 25, "отсутствие уведомления": 15, "нарушение по согласию": 10}
DOCUMENT_WEIGHT = {"грубая ошибка": 10, "замечание": 4, "в порядке": 0}
LEAK_WEIGHT = {"утечка малого размера": 5, "утечка среднего размера": 10, "утечка крупного размера": 15}


# ---------- Step 1. Loading artifacts ----------
def fail_and_exit(message):
    print("ОШИБКА ЗАГРУЗКИ: " + message)
    sys.exit(1)


def load_artifacts():
    try:
        from organization import organization
        from data_map import data_map
        from violations import violations
        from countries import countries
        from transfer_requests import requests
    except Exception as e:  # incomplete or broken data file
        fail_and_exit(f"не удалось подключить данные: {e!r}")
    required = ["название", "отрасль", "год основания", "годовая выручка в рублях", "количество сотрудников",
                    "количество человек, чьи данные хранятся в базе", "список присутствующих видов данных",
                    "признак наличия происшествий за 2024-2025 годы", "список отделений",
                    "список стран для расширения деятельности", "ответственный за обработку данных"]
    for p in required:
        if p not in organization:
            fail_and_exit(f"в паспорте организации нет поля «{p}»")
    if sum(o["число людей"] for o in organization["список отделений"]) !=\
            organization["количество человек, чьи данные хранятся в базе"]:
        fail_and_exit("сумма людей по отделениям не совпадает с общим числом людей в паспорте")
    if len(data_map.get("записи", [])) < 15:
        fail_and_exit("в карте данных меньше 15 записей")
    allowed = {"общедоступные", "специальные", "биометрические", "иные"}
    for entry in data_map["записи"]:
        if entry.get("вид данных") not in allowed:
            fail_and_exit(f"запись {entry.get('номер')} карты данных: недопустимый вид данных")
    if len(violations.get("список", [])) != 3:
        fail_and_exit("в файле нарушений должно быть ровно 3 записи")
    if len(countries) < 20:
        fail_and_exit("в справочнике меньше 20 стран")
    if len(requests) != 3:
        fail_and_exit("в файле заявок должно быть 3 заявки")
    return organization, data_map, violations, requests


# ---------- Step 2. Document check ----------
def check_documents():
    from consent_check import check_consent, kind_from_filename, DOCUMENTS_DIR
    summary = []
    for name in sorted(os.listdir(DOCUMENTS_DIR)):
        if not name.endswith(".txt"):
            continue
        text = open(os.path.join(DOCUMENTS_DIR, name), encoding="utf-8").read()
        if "consent" in name:
            res = check_consent(text, kind_from_filename(name))
            summary.append({"файл": name, "состояние": res["состояние"], "причина": res["пояснение"],
                         "штраф": res["размер возможного штрафа в рублях"]})
        elif "policy" in name:
            word_count = len(text.split())
            missing = [res for res in ("цел", "правовые основания", "срок", "прав", "контакт") if res not in text.lower()]
            ok = word_count >= 1500 and not missing
            summary.append({"файл": name, "состояние": "в порядке" if ok else "замечание",
                         "причина": f"{word_count} слов; " + ("все разделы на месте" if not missing else "нет разделов: " + ", ".join(missing)),
                         "штраф": 0 if ok else 100_000})
        else:  # sample notification
            ok = all(p in text for p in ("{notification_type}", "{people_count}", "{detection_date}"))
            summary.append({"файл": name, "состояние": "в порядке" if ok else "замечание",
                         "причина": "шаблон содержит поля для подстановки" if ok else "в шаблоне нет обязательных полей",
                         "штраф": 0 if ok else 100_000})
    return summary


# ---------- Step 3. Violation recalculation ----------
def recalc_violations(violations, organization):
    from fine_calculator import calculate_fine
    summary = []
    for v in violations["список"]:
        res = calculate_fine(v["вид для расчёта штрафа"], organization["количество человек, чьи данные хранятся в базе"],
                             False, organization["годовая выручка в рублях"])
        summary.append({"нарушение": v, "расчёт": res})
    return summary


# ---------- Step 4. Parsing the user phrase ----------
COUNTRY_ALIASES = {"US": r"сша|америк|штатах|штатов", "GB": r"англи|великобритани", "BY": r"белорус|беларус",
                "KR": r"коре", "AE": r"оаэ|эмират", "CN": r"кита|китае"}


def _stem(title):
    return re.sub(r"[аяйьыиеуюо]+$", "", title.lower())


def find_country(text):
    from countries import countries
    lowered = text.lower()
    for code, data in countries.items():
        pattern = COUNTRY_ALIASES.get(code)
        patterns = [r"(?<![а-я])" + (pattern if pattern else re.escape(_stem(data["название страны"].split()[-1])))]
        if any(re.search(pat, lowered) for pat in patterns):
            return code
    return None


def find_number(text):
    m = re.search(r"(\d{1,3}(?:[  ]\d{3})+|\d+)(\s*(?:тыс\w*|k|к\b))?", text.lower())
    if not m:
        return None
    count = int(re.sub(r"\s", "", m.group(1)))
    return count * 1000 if m.group(2) and "тыс" in m.group(2) or (m.group(2) or "").strip() in ("k", "к") else count


def parse_query(text):
    lowered = text.lower()
    kinds = []
    if re.search(r"биометр|днк|геном|лиц[ао]|отпечат", lowered):
        kinds.append("биометрические")
    if re.search(r"специальн|здоров|медицин|диагноз|заболеван|религи|национальн", lowered):
        kinds.append("специальные")
    if re.search(r"общедоступн", lowered):
        kinds.append("общедоступные")
    action = None
    if re.search(r"утечк|происшеств|взлом|слит|похищен|инцидент", lowered):
        action = "происшествие"
    elif re.search(r"передат|передач|отправ|перевест|вывез", lowered):
        action = "передача"
    return {"исходный текст": text, "страна": find_country(text), "число людей": find_number(text),
            "виды данных": kinds or ["иные"], "виды указаны": bool(kinds), "действие": action,
            "повторно": bool(re.search(r"повторн|снова|опять|ещё раз|еще раз|вновь|уже была", lowered))}


def process_query(parsed, organization):
    """Returns a dict with the results for the user query."""
    from country_check import check_country
    from fine_calculator import calculate_fine
    res = {"разбор": parsed, "приговор": None, "условия": [], "ссылки": [], "баллы": 0, "риск": 0, "пояснения": []}
    revenue = organization["годовая выручка в рублях"]
    if parsed["действие"] == "передача":
        if not parsed["страна"]:
            res["пояснения"].append("Страна не распознана — укажите страну получателя.")
            return res
        c = check_country(parsed["страна"])
        res.update({"приговор": c["приговор"], "условия": list(c["условия"]), "ссылки": c["ссылки на закон"],
                  "страна": c["название"], "дней": c["число дней ожидания"]})
        if "биометрические" in parsed["виды данных"] or "специальные" in parsed["виды данных"]:
            res["условия"].append("Нужно отдельное письменное согласие на данные особых видов (ст. 10, 11 152-ФЗ)")
        if c["приговор"] == "запрещено":
            res["баллы"] = 8
        elif c["приговор"] == "разрешено при условиях":
            res["баллы"] = 3
            res["риск"] = calculate_fine("нарушение по согласию", parsed["число людей"] or 0, False, revenue)["наибольший размер штрафа"]
    elif parsed["действие"] == "происшествие":
        count = parsed["число людей"] or 0
        kind = "утечка малого размера" if count <= 10_000 else "утечка среднего размера" if count <= 100_000 else "утечка крупного размера"
        calcs = [calculate_fine(kind, count, parsed["повторно"], revenue)]
        points = LEAK_WEIGHT[kind]
        if "биометрические" in parsed["виды данных"]:
            calcs.append(calculate_fine("нарушение по биометрии", count, parsed["повторно"], revenue))
            points += 10
        if "специальные" in parsed["виды данных"]:
            points += 5
        if parsed["повторно"]:
            points += 10
        best = max(calcs, key=lambda item: item["наибольший размер штрафа"])
        res.update({"приговор": "утечка: " + kind, "ссылки": ["ст. 21 ч. 3.1 152-ФЗ", "ст. 13.11 КоАП РФ"],
                  "баллы": points, "риск": best["наибольший размер штрафа"], "расчёт штрафа": best,
                  "страна": parsed["страна"] and None})
        res["условия"] = ["Уведомить РКН в течение 24 часов", "Направить результаты расследования в течение 72 часов"]
        from notification_builder import create_notification
        notice = create_notification({"дата и время обнаружения": datetime.now(), "число пострадавших людей": count,
                                  "виды данных": parsed["виды данных"], "причина утечки": "уточняется",
                                  "принятые меры": "доступ ограничен, начато расследование",
                                  "расследование завершено": False}, NOTIFICATION_FILE,
                                 responsible=organization["ответственный за обработку данных"])
        res["пояснения"].append(f"Сформировано {notice['вид']} уведомление: {NOTIFICATION_FILE}")
    else:
        res["пояснения"].append("Не удалось определить действие (передача или происшествие).")
    return res


# ---------- Step 5. Final report ----------
def rubles(item_x):
    return f"{int(item_x):,}".replace(",", " ") + " руб."


def build_report(organization, documents, violations_calc, queries):
    report_lines = ["ИТОГОВЫЙ ОТЧЁТ О СООТВЕТСТВИИ ТРЕБОВАНИЯМ 152-ФЗ", "=" * 60, "", "1. ОБЩИЕ СВЕДЕНИЯ ОБ ОРГАНИЗАЦИИ"]
    report_lines += [f"  Название: {organization['название']}", f"  Отрасль: {organization['отрасль']}",
          f"  Год основания: {organization['год основания']}",
          f"  Годовая выручка: {rubles(organization['годовая выручка в рублях'])}",
          f"  Сотрудников: {organization['количество сотрудников']}",
          f"  Людей в базе: {organization['количество человек, чьи данные хранятся в базе']:,}".replace(",", " "),
          f"  Ответственный: {organization['ответственный за обработку данных']}", "", "2. ИТОГИ ПРОВЕРКИ ДОКУМЕНТОВ"]
    for doc in documents:
        report_lines.append(f"  {doc['файл']}: {doc['состояние']} — {doc['причина']} Штраф: {rubles(doc['штраф'])}")
    report_lines += ["", "3. НАЙДЕННЫЕ НАРУШЕНИЯ"]
    for item in violations_calc:
        v, res = item["нарушение"], item["расчёт"]
        report_lines += [f"  №{v['номер']} ({v['вид']}), запись карты данных {v['запись карты данных']}: {v['описание']}",
              f"     Норма: {v['норма права']}",
              f"     Заложенный штраф: {rubles(v['размер штрафа в рублях'])}; расчёт: "
              f"{rubles(res['наименьший размер штрафа'])} – {rubles(res['наибольший размер штрафа'])}",
              f"     Исправление: {v['что нужно сделать']}"]
    report_lines += ["", "4. РАЗБОР ЗАПРОСОВ ПОЛЬЗОВАТЕЛЯ"]
    if not queries:
        report_lines.append("  Запросов пока не было.")
    for number, entry in enumerate(queries, 1):
        res, query_result = entry["разбор"], entry
        report_lines += [f"  Запрос {number}: «{res['исходный текст']}»",
              f"     Действие: {res['действие'] or 'не определено'}; страна: {query_result.get('страна') or res['страна'] or '—'}; "
              f"людей: {res['число людей'] or '—'}; виды данных: {', '.join(res['виды данных'])}"
              + ("; повторно" if res["повторно"] else ""),
              f"     Приговор: {query_result['приговор'] or '—'}",
              f"     Условия: {'; '.join(query_result['условия']) or '—'}",
              f"     Ссылки на закон: {'; '.join(query_result['ссылки']) or '—'}"]
        if "расчёт штрафа" in query_result:
            fine_result = query_result["расчёт штрафа"]
            report_lines.append(f"     Штраф: {rubles(fine_result['наименьший размер штрафа'])} – {rubles(fine_result['наибольший размер штрафа'])}; "
                     f"оборотный: {'да' if fine_result['оборотный штраф применим'] else 'нет'}")
        report_lines += [f"     {p}" for p in query_result["пояснения"]]

    # Score
    total_points = sum(VIOLATION_WEIGHT.get(item["нарушение"]["вид для расчёта штрафа"], 10) for item in violations_calc)
    total_points += sum(DOCUMENT_WEIGHT[doc["состояние"]] for doc in documents) + sum(entry["баллы"] for entry in queries)
    score = max(0, 100 - total_points)
    risk = sum(item["расчёт"]["наибольший размер штрафа"] for item in violations_calc)
    risk += sum(doc["штраф"] for doc in documents) + sum(entry["риск"] for entry in queries)
    actions = [f"Нарушение №{item['нарушение']['номер']}: {item['нарушение']['что нужно сделать']}"
                for item in sorted(violations_calc, key=lambda item: -item["расчёт"]["наибольший размер штрафа"])]
    for doc in documents:
        if doc["состояние"] != "в порядке":
            actions.append(f"Исправить документ {doc['файл']}: {doc['причина']}")
    for entry in queries:
        if entry["приговор"] and entry["приговор"].startswith("утечка"):
            actions.append("Уложиться в 24/72 часа по утечке и направить уведомления в РКН")
    report_lines += ["", "5. ИТОГОВАЯ ОЦЕНКА", f"  Оценка соответствия: {score} из 100 (штрафных баллов: {total_points})",
          f"  Общий риск штрафов: {rubles(risk)}", "  Первоочередные действия:"]
    report_lines += [f"   {number}. {doc}" for number, doc in enumerate(actions[:5], 1)]
    return "\n".join(report_lines) + "\n"


def save_report(text):
    os.makedirs(os.path.dirname(FINAL_REPORT_FILE), exist_ok=True)
    with open(FINAL_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(text)


# ---------- Step 6. Conversation loop ----------
def main():
    organization, _map, violations, _requests = load_artifacts()
    documents = check_documents()
    calcs = recalc_violations(violations, organization)
    queries = []
    save_report(build_report(organization, documents, calcs, queries))
    print(f"Здравствуйте! Симулятор проверки соответствия 152-ФЗ — {organization['название']}.")
    print("Опишите ситуацию, например: «Хотим передать данные 20 000 клиентов в Китай для аналитики»")
    print("или «Обнаружена утечка 5 000 записей из базы в США». Для завершения введите «выход».")
    while True:
        try:
            phrase = input("> ").strip()
        except EOFError:
            break
        if phrase.lower() in EXIT_WORDS:
            print("До свидания! Итоговый отчёт: " + FINAL_REPORT_FILE)
            break
        if not phrase:
            continue
        summary = process_query(parsed_query := parse_query(phrase), organization)
        queries.append(summary)
        report = build_report(organization, documents, calcs, queries)
        save_report(report)
        print(f"Страна: {summary.get('страна') or parsed_query['страна'] or '—'}; приговор: {summary['приговор'] or '—'}")
        for u in summary["условия"] + summary["пояснения"]:
            print("  - " + u)
        print("Отчёт обновлён.")


if __name__ == "__main__":
    main()
