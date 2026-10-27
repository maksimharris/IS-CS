# -*- coding: utf-8 -*-
"""Task 4.1. Creating a notification to Roskomnadzor under Art. 21 p. 3.1 of 152-FZ."""
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "data", "documents", "breach_notification.txt")
INITIAL_DEADLINE_HOURS = 24
FOLLOWUP_DEADLINE_HOURS = 72


def determine_kind(detection_date, now):
    """Within 24 hours of detection - initial notification; later - follow-up (investigation results, within 72 h)."""
    elapsed = (now - detection_date).total_seconds() / 3600
    kind = "первичное" if elapsed <= INITIAL_DEADLINE_HOURS else "дополнительное"
    return kind, elapsed


def create_notification(details, file_path, now=None, responsible="Лисицына Анна Валерьевна"):
    """Creates the notification file. Returns the notification kind and a list of deadline remarks."""
    now = now or datetime.now()
    detected = details["дата и время обнаружения"]
    kind, elapsed = determine_kind(detected, now)
    remarks = []
    if kind == "первичное" and details.get("расследование завершено"):
        remarks.append("Расследование уже завершено — можно сразу подготовить и дополнительное уведомление.")
    if kind == "дополнительное":
        if elapsed > FOLLOWUP_DEADLINE_HOURS:
            remarks.append(f"Срок 72 часа пропущен (прошло {elapsed:.0f} ч) — возможен штраф по ст. 13.11 ч. 11 КоАП РФ.")
        remarks.append("Если первичное уведомление не направлялось в срок 24 часа, срок нарушен.")
    if kind == "дополнительное" and not details.get("расследование завершено"):
        remarks.append("Расследование не завершено — в уведомлении указано, что результаты будут направлены дополнительно.")
    c = open(TEMPLATE, encoding="utf-8").read()
    text = c.format(
        notification_type=f"{kind} (прошло {elapsed:.1f} ч с обнаружения)",
        detection_date=detected.strftime("%d.%m.%Y %H:%M"),
        people_count=f"{details['число пострадавших людей']:,}".replace(",", " "),
        data_kinds=", ".join(details["виды данных"]),
        cause=details["причина утечки"],
        measures=details["принятые меры"],
        investigation="завершено" if details.get("расследование завершено") else "проводится",
        responsible=responsible)
    if remarks:
        text += "\nСлужебные замечания (не для отправки): " + " ".join(remarks) + "\n"
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    return {"вид": kind, "прошло часов": elapsed, "замечания": remarks, "путь": file_path}


if __name__ == "__main__":
    print(create_notification(
        {"дата и время обнаружения": datetime(2026, 10, 25, 9, 0), "число пострадавших людей": 5000,
         "виды данных": ["иные"], "причина утечки": "ошибка конфигурации", "принятые меры": "доступ закрыт",
         "расследование завершено": False}, os.path.join(ROOT, "reports", "sample_notification.txt")))
