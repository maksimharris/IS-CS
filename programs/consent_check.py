# -*- coding: utf-8 -*-
"""Task 2.2. Checking consent texts for personal data processing."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCUMENTS_DIR = os.path.join(ROOT, "data", "documents")
REPORT_FILE = os.path.join(ROOT, "reports", "consent_report.txt")

# Signs that the consent is embedded in another document (Art. 9 p. 1 of 152-FZ: consent is a separate document)
EMBEDDED_CONSENT_PHRASES = [
    r"договор", r"оферт", r"пользовательск\w+ соглашени", r"условия использования",
    r"настоящим договором", r"в рамках соглашения", r"принимая условия",
]

# Mandatory semantic parts: name -> search patterns
REQUIRED_PARTS = {
    "конкретные цели обработки": [r"цел[ьи]\w*\s+обработк", r"\bцел[ьи]\b"],
    "конкретный перечень данных": [r"перечень\s+данных", r"перечень\s+персональных"],
    "срок действия согласия": [r"срок\s+действия", r"согласие\s+действует"],
    "порядок отзыва": [r"отзыв", r"отозвать"],
}
VAGUE_PHRASES = [r"в\s+любых\s+целях", r"любые\s+цели", r"иные\s+цели", r"любые\s+данные", r"бессрочно"]

EMBEDDED_FINE = 300_000
MISSING_PART_FINE = 100_000
MAX_FINE = 700_000


def check_consent(text, document_kind):
    """Returns a dict: whether the document is correct, what is missing, the fine, an explanation.

    вид_документа — «работник» или «клиент».
    """
    if document_kind not in ("работник", "клиент"):
        raise ValueError("вид документа должен быть «работник» или «клиент»")
    lowered = text.lower()
    missing_parts = []
    fine = 0

    embedded = [f for f in EMBEDDED_CONSENT_PHRASES if re.search(f, lowered)]
    if embedded:
        fine += EMBEDDED_FINE
        missing_parts.append("отдельность документа (согласие отсылает к договору/оферте)")

    for part, patterns_list in REQUIRED_PARTS.items():
        if not any(re.search(o, lowered) for o in patterns_list):
            missing_parts.append(part)
            fine += MISSING_PART_FINE
    if any(re.search(res, lowered) for res in VAGUE_PHRASES):
        missing_parts.append("конкретность формулировок (найдены размытые обороты)")
        fine += MISSING_PART_FINE

    # Kind-specific rule: a laboratory client consent must explicitly mention biometric data
    if document_kind == "клиент" and not re.search(r"биометрическ|геном|днк", lowered):
        missing_parts.append("указание на биометрические (геномные) данные")
        fine += MISSING_PART_FINE
    if document_kind == "работник" and not re.search(r"подпис", lowered):
        missing_parts.append("подпись субъекта")
        fine += MISSING_PART_FINE

    fine = min(fine, MAX_FINE)
    correct = not missing_parts
    if correct:
        state, explanation = "в порядке", "Документ отдельный, содержит цели, перечень данных, срок и порядок отзыва."
    else:
        state = "грубая ошибка" if embedded or len(missing_parts) >= 3 else "замечание"
        explanation = ("Нарушены требования ст. 9 ч. 4 152-ФЗ (возможный штраф по ст. 13.11 ч. 1–2 КоАП РФ). "
                     "Не хватает: " + "; ".join(missing_parts) + ".")
    return {
        "документ правильный": correct,
        "состояние": state,
        "не хватает частей": missing_parts,
        "размер возможного штрафа в рублях": fine,
        "пояснение": explanation,
    }


def kind_from_filename(name):
    return "работник" if "employee" in name else "клиент"


def check_all_consents(folder=DOCUMENTS_DIR):
    """Processes all consent files in the folder (the name contains consent)."""
    summary = {}
    for name in sorted(os.listdir(folder)):
        if name.endswith(".txt") and "consent" in name:
            with open(os.path.join(folder, name), encoding="utf-8") as f:
                summary[name] = check_consent(f.read(), kind_from_filename(name))
    return summary


def main():
    results = check_all_consents()
    lines = ["ОТЧЁТ ПО СОГЛАСИЯМ", "=" * 40]
    for name, res in results.items():
        lines += [f"Файл: {name}",
                   f"  Правильный: {'да' if res['документ правильный'] else 'нет'} ({res['состояние']})",
                   f"  Не хватает: {', '.join(res['не хватает частей']) or '—'}",
                   f"  Возможный штраф: {res['размер возможного штрафа в рублях']:,} руб.".replace(",", " "),
                   f"  Пояснение: {res['пояснение']}", ""]
    text = "\n".join(lines)
    print(text)
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
