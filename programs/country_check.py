# -*- coding: utf-8 -*-
"""Task 3.2. Destination country check. The data comes from data/countries.py."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "data"))
from countries import countries  # the reference is imported, not stored inside the function

WAIT_DAYS_NO_PROTECTION = 10  # working days, Art. 12 p. 12 of 152-FZ


def check_country(code):
    """Returns a dict: code, title, verdict, conditions, law references, number of waiting days."""
    code = code.upper().strip()
    if code not in countries:
        return {"код": code, "название": "неизвестная страна", "приговор": "запрещено",
                "условия": ["Страна отсутствует в справочнике — передача недопустима до проверки"],
                "ссылки на закон": ["ст. 12 152-ФЗ"], "число дней ожидания": 0}
    c = countries[code]
    refs = ["ст. 12 152-ФЗ", c["ссылка на источник"]]
    conditions = ["Направить в Роскомнадзор уведомление о намерении передавать данные (ст. 12 ч. 4 152-ФЗ)"]

    if c["особый режим"] == "запрещено":
        return {"код": code, "название": c["название страны"], "приговор": "запрещено",
                "условия": [c["правила передачи"]], "ссылки на закон": refs, "число дней ожидания": 0}

    if c["достаточная защита по версии Роскомнадзора"] or c["входит в Конвенцию 108"]:
        verdict, days = "разрешено", 0
        conditions.append("Передачу можно начать сразу после направления уведомления")
    else:
        verdict, days = "разрешено при условиях", WAIT_DAYS_NO_PROTECTION
        conditions += ["Оценка вреда субъектам и мер защиты у получателя (ст. 12 ч. 5 152-ФЗ)",
                    f"Выдержать {WAIT_DAYS_NO_PROTECTION} рабочих дней с даты уведомления РКН",
                    "Получить от получателя обязательство по обеспечению конфиденциальности"]
    if c["особый режим"] == "особый":
        verdict = "разрешено при условиях"
        days = max(days, WAIT_DAYS_NO_PROTECTION)
        conditions.append("Особый режим: " + c["правила передачи"])
    return {"код": code, "название": c["название страны"], "приговор": verdict,
            "условия": conditions, "ссылки на закон": refs, "число дней ожидания": days}


if __name__ == "__main__":
    for k in ("IL", "CN", "UA", "ZZ"):
        print(check_country(k))
