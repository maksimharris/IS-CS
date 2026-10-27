# -*- coding: utf-8 -*-
"""Organization passport: the DNA analysis laboratory chain GeneZis Sibir."""

# The number of people is calculated by the formula from the assignment:
# 300 000 + group number + sum of ordinal numbers in the group list.
GROUP_NUMBER = 31
LIST_NUMBERS_SUM = 16
PEOPLE_IN_DATABASE = 300_000 + GROUP_NUMBER + LIST_NUMBERS_SUM

# Distribution of people across branches (the sum must equal PEOPLE_IN_DATABASE)
_novosibirsk = PEOPLE_IN_DATABASE // 2
_krasnoyarsk = PEOPLE_IN_DATABASE // 3
_minsk = PEOPLE_IN_DATABASE - _novosibirsk - _krasnoyarsk

organization = {
    "название": "ООО «ГенеЗис Сибирь»",
    "отрасль": "Сеть лабораторий по анализу ДНК (генеалогия, медицинская генетика, установление родства)",
    "год основания": 2016,
    "годовая выручка в рублях": 840_000_000,
    "количество сотрудников": 212,
    "количество человек, чьи данные хранятся в базе": PEOPLE_IN_DATABASE,
    "список присутствующих видов данных": ["общедоступные", "специальные", "биометрические", "иные"],
    "признак наличия происшествий за 2024-2025 годы": True,
    "список отделений": [
        {"страна": "RU", "город": "Новосибирск", "число людей": _novosibirsk},
        {"страна": "RU", "город": "Красноярск", "число людей": _krasnoyarsk},
        {"страна": "BY", "город": "Минск", "число людей": _minsk},
    ],
    "список стран для расширения деятельности": [
        {"страна": "KZ", "цель": "Открытие пункта забора биоматериала в Астане"},
        {"страна": "CN", "цель": "Передача обезличенных геномных данных партнёру для аналитики"},
        {"страна": "DE", "цель": "Совместное исследование с университетской клиникой"},
    ],
    "ответственный за обработку данных": "Лисицына Анна Валерьевна",
}
