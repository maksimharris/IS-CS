# -*- coding: utf-8 -*-
"""Task 3.3. Checking cross-border transfer requests."""
import os
import sys
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "data"))
sys.path.insert(0, os.path.join(ROOT, "programs"))
from country_check import check_country
from transfer_requests import requests

REPORT_FILE = os.path.join(ROOT, "reports", "transfer_report.txt")
SPECIAL_KINDS = ("специальные", "биометрические")


def workdays_between(start, end):
    """Number of working days (Mon-Fri) after the start date up to and including the end date. Holidays are not taken into account."""
    days, doc = 0, start
    while doc < end:
        doc += timedelta(days=1)
        if doc.weekday() < 5:
            days += 1
    return days


def check_request(request):
    """Returns a dict with the verdict and the full list of reasons."""
    reasons = []
    c = check_country(request["страна-получатель"])
    verdict = c["приговор"]
    if verdict == "запрещено":
        reasons.append(f"Страна {c['название']}: передача запрещена. " + "; ".join(c["условия"]))
    else:
        reasons.append(f"Страна {c['название']}: {verdict}.")

    # Roskomnadzor notification and 10 working days
    if not request["был ли уведомлён Роскомнадзор"]:
        reasons.append("Роскомнадзор не уведомлён (ст. 12 ч. 4 152-ФЗ) — передача невозможна.")
        verdict = "запрещено"
    else:
        elapsed = workdays_between(request["дата уведомления"], request["текущая дата"])
        if elapsed < c["число дней ожидания"]:
            reasons.append(f"Прошло {elapsed} раб. дн. из {c['число дней ожидания']} — ждать ещё "
                           f"{c['число дней ожидания'] - elapsed}.")
            if verdict == "разрешено":
                verdict = "разрешено при условиях"
        else:
            reasons.append(f"Срок ожидания выдержан ({elapsed} раб. дн.).")

    # Special consents
    special = [kind_item for kind_item in request["виды передаваемых данных"] if kind_item in SPECIAL_KINDS]
    if special and not request["есть ли согласие людей"]:
        reasons.append("Для видов данных " + ", ".join(special) +
                       " нужно отдельное письменное согласие (ст. 10 ч. 1, ст. 11 ч. 1 152-ФЗ) — его нет.")
        verdict = "запрещено"
    elif special:
        reasons.append("Особое согласие на " + ", ".join(special) + " имеется; проверьте письменную форму.")
    if not request["есть ли согласие людей"] and c["число дней ожидания"] > 0 and verdict != "запрещено":
        reasons.append("Для страны без адекватной защиты нужно письменное согласие на трансграничную передачу "
                       "(ст. 12 ч. 5 152-ФЗ) — его нет.")
        verdict = "запрещено"
    return {"номер": request["номер"], "страна": c["название"], "приговор": verdict,
            "причины": reasons, "условия": c["условия"]}


def main():
    lines = ["ОТЧЁТ ПО ПЕРЕДАЧЕ ДАННЫХ ЗА ГРАНИЦУ", "=" * 40]
    for entry in requests:
        res = check_request(entry)
        lines += [f"Заявка №{res['номер']} → {res['страна']}: {res['приговор'].upper()}"] +\
                  [f"  - {p}" for p in res["причины"]] + [""]
    text = "\n".join(lines)
    print(text)
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
