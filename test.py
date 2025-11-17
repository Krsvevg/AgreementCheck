from extractor import extract_text

file_path = "C:\\Users\\boss-\\Downloads\\Telegram Desktop\\2.pdf"   # путь к тестовому файлу
text = extract_text(file_path)

print("=== Извлечённый текст ===")
print(text)