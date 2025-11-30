from extractor import extract_text

file_path = "C:\\Users\\boss-\\PycharmProjects\\AgreementCheck\\docsExamples\\dogovor_postavki.docx"   # путь к тестовому файлу
text = extract_text(file_path)

print("=== Извлечённый текст ===")
print(text)