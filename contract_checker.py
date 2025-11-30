import re
from extractor import extract_text
from transformers import pipeline

# Нормализация текста
def normalize_text(text):
    text = text.replace('\xa0', ' ')
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# Разбиение на абзацы
def split_into_paragraphs(text):
    paragraphs = re.split(r'(?<=[.!?]) +', text)
    return [p.strip() for p in paragraphs if p.strip()]

# Проверка правил
def check_contract_rules(text, available_files=None):
    results = {}

    # Примеры правил (можно расширять)
    amounts = re.findall(r'([\d\s]+) ?₽', text)
    amounts = [int(a.replace(' ', '')) for a in amounts]
    results['sum_10m'] = all(a <= 10_000_000 for a in amounts) if amounts else None

    results['subcontract_sum'] = all(int(m.group(1).replace(' ','') ) < 2_000_000
                                     for m in re.finditer(r'([\d\s]+) ?₽.*(субподрядчик)', text, re.I)) \
                                if re.search(r'субподрядчик', text, re.I) else None

    forbidden_words = ['предоплата', 'аванс', 'до начала работ']
    results['forbidden_words'] = [w for w in forbidden_words if w.lower() in text.lower()]

    results['nds'] = 'НДС' in text or 'удержан' in text
    results['company_ok'] = 'ООО «Ромашка»' in text
    results['inn_ok'] = '6678122494' in text
    results['not_individual'] = 'ИП' not in text.lower() and 'физлицо' not in text.lower()
    results['director_signature'] = bool(re.search(r'Иванов И\. И\.|заместител', text, re.I))
    results['customer_signature'] = 'подпись' in text.lower()
    results['stamp'] = 'ООО «Ромашка»' in text and 'печать' in text.lower()
    results['sign_date'] = '25.01.2025' in text
    results['work_term'] = 'срок' in text.lower()
    results['nda'] = 'NDA' in text or 'неразглаш' in text.lower()
    results['responsibility'] = 'ответственность' in text.lower()
    results['no_fines'] = 'штраф' not in text.lower()
    bad_phrases = ['по договорённости сторон', 'в разумный срок']
    results['bad_phrases'] = [p for p in bad_phrases if p in text.lower()]

    duration_match = re.search(r'срок действия.*?(\d+).*?мес', text, re.I)
    results['duration_ok'] = int(duration_match.group(1)) <= 12 if duration_match else None

    date_matches = re.findall(r'(\d{2}\.\d{2}\.\d{4})', text)
    results['end_after_start'] = False
    if len(date_matches) >= 2:
        from datetime import datetime
        start = datetime.strptime(date_matches[0], "%d.%m.%Y")
        end = datetime.strptime(date_matches[1], "%d.%m.%Y")
        results['end_after_start'] = end > start

    results['not_perpetual'] = 'бессрочн' not in text.lower()

    required_apps = ['Спецификация', 'График работ']
    results['applications'] = {}
    available_files = available_files or []
    for app in required_apps:
        in_text = app in text
        in_files = any(app in f for f in available_files)
        results['applications'][app] = in_text or in_files

    return results

# Подключение обученной модели Hugging Face
def load_contract_model(model_path="./trained_model"):
    nlp = pipeline("text-classification", model=model_path, tokenizer=model_path)
    return nlp

def classify_paragraphs(text, nlp_model):
    paragraphs = split_into_paragraphs(text)
    results = []
    for p in paragraphs:
        label = nlp_model(p)
        results.append({"paragraph": p, "label": label[0]['label'], "score": label[0]['score']})
    return results

# Печать отчёта
def print_report(rules_results, ml_results):
    print("\n===== Проверка правил =====")
    for k, v in rules_results.items():
        if isinstance(v, list):
            print(f"{k}: {'Найдены: ' + ', '.join(v) if v else 'Пройдена'}")
        elif isinstance(v, dict):
            for app, ok in v.items():
                print(f"Приложение {app}: {'Присутствует' if ok else 'Отсутствует'}")
        elif isinstance(v, bool):
            print(f"{k}: {'Пройдена' if v else 'Не пройдена'}")
        else:
            print(f"{k}: {'Пройдена' if v else 'Не пройдена'}")

    print("\n===== Классификация абзацев =====")
    for item in ml_results:
        print(f"[{item['label']}] ({item['score']:.2f}) {item['paragraph']}")

# Главная функция
def check_contract(file_path, available_files=None, model_path="./trained_model"):
    text = extract_text(file_path)
    text = normalize_text(text)
    rules_results = check_contract_rules(text, available_files)

    nlp_model = load_contract_model(model_path)
    ml_results = classify_paragraphs(text, nlp_model)

    print_report(rules_results, ml_results)
    return rules_results, ml_results

if __name__ == "__main__":
    file_path = "docsExamples\\dogovor_uslug.docx"  #файл
    #available_files = ["Спецификация.pdf", "График работ.pdf"]  # если есть приложения
    check_contract(file_path)
