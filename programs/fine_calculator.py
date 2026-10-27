# -*- coding: utf-8 -*-
"""Task 4.2. Administrative fine calculation (simplified model of Art. 13.11 of the Administrative Code, edition effective 30.05.2025)."""

# violation kind -> (minimum, maximum, minimum if repeated, maximum if repeated, basis)
FINE_TABLE = {
    "утечка малого размера":   (3_000_000, 5_000_000, None, None, "ст. 13.11 ч. 12 КоАП РФ (1–10 тыс. субъектов)"),
    "утечка среднего размера":  (5_000_000, 10_000_000, None, None, "ст. 13.11 ч. 13 КоАП РФ (10–100 тыс. субъектов)"),
    "утечка крупного размера":  (10_000_000, 15_000_000, None, None, "ст. 13.11 ч. 14 КоАП РФ (свыше 100 тыс. субъектов)"),
    "отсутствие уведомления":   (1_000_000, 3_000_000, 3_000_000, 5_000_000, "ст. 13.11 ч. 11 КоАП РФ"),
    "нарушение по биометрии":   (10_000_000, 20_000_000, 20_000_000, 20_000_000, "ст. 13.11 ч. 4 КоАП РФ"),
    "нарушение по согласию":    (300_000, 700_000, 700_000, 1_500_000, "ст. 13.11 ч. 1–2 КоАП РФ"),
}
# Turnover fine for a repeated leak (since 30.05.2025): 1-3 % of revenue, not less than 20 mln and not more than 500 mln rubles.
TURNOVER_KINDS = ("утечка малого размера", "утечка среднего размера", "утечка крупного размера", "нарушение по биометрии")
SHARE_MIN, SHARE_MAX = 0.01, 0.03
TURNOVER_LOWER_LIMIT, TURNOVER_UPPER_LIMIT = 20_000_000, 500_000_000


def calculate_fine(kind, people_count, repeat, annual_revenue):
    """Returns: smallest and largest fine, whether the turnover fine applies, legal justification."""
    if kind not in FINE_TABLE:
        raise ValueError(f"Неизвестный вид нарушения: {kind}")
    min_fine, max_fine, min_fine_repeat, max_fine_repeat, basis = FINE_TABLE[kind]
    justification = [f"Базовая санкция: {basis}."]
    smallest, largest = min_fine, max_fine
    # number of people: adjust the leak category if the actual number differs from the declared kind
    if kind.startswith("утечка") and people_count < 1_000:
        justification.append("Число субъектов менее 1000 — состав ч. 12–14 может не наступать, берётся нижняя категория.")
    turnover = False
    if repeat:
        if min_fine_repeat is not None:
            smallest, largest = min_fine_repeat, max_fine_repeat
            justification.append("Повторность: применяется повышенная санкция.")
        if kind in TURNOVER_KINDS:
            turnover = True
            turnover_min = min(max(annual_revenue * SHARE_MIN, TURNOVER_LOWER_LIMIT), TURNOVER_UPPER_LIMIT)
            turnover_max = min(max(annual_revenue * SHARE_MAX, TURNOVER_LOWER_LIMIT), TURNOVER_UPPER_LIMIT)
            smallest, largest = max(smallest, turnover_min), max(largest, turnover_max)
            justification.append("Оборотный штраф с 30.05.2025: 1–3 % выручки за год (не менее "
                               "20 млн и не более 500 млн руб.), ст. 13.11 КоАП РФ.")
    return {"наименьший размер штрафа": int(smallest), "наибольший размер штрафа": int(largest),
            "оборотный штраф применим": turnover, "правовое обоснование": " ".join(justification)}


if __name__ == "__main__":
    print(calculate_fine("утечка крупного размера", 300_000, True, 840_000_000))
