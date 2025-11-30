"""
Скрипт для подготовки и обучения модели Hugging Face Transformers
для классификации абзацев договора по типам:
NDA, RESPONSIBILITY, TERM, APPENDIX, OTHER
"""

from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments

# Настройки
MODEL_NAME = "DeepPavlov/rubert-base-cased"   # предобученная русская модель
TRAIN_CSV = "train.csv"                       # CSV с размеченными абзацами - для обучения
TEST_CSV = "test.csv"                         # CSV с размеченными абзацами - для проверки
OUTPUT_DIR = "./trained_model"
NUM_EPOCHS = 3
BATCH_SIZE = 8
LEARNING_RATE = 2e-5

dataset = load_dataset("csv", data_files={"train": TRAIN_CSV, "test": TEST_CSV})

# Токенизация
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize(batch):
    return tokenizer(batch["paragraph"], padding=True, truncation=True, max_length=512)

tokenized_dataset = dataset.map(tokenize, batched=True)

# Создаем модель
num_labels = len(dataset["train"].features["label"].names)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=num_labels
)

# Настройка Trainer
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    evaluation_strategy="epoch",
    learning_rate=LEARNING_RATE,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    num_train_epochs=NUM_EPOCHS,
    save_total_limit=2,
    logging_dir="./logs",
    logging_steps=50
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["test"]
)

# Обучение модели
trainer.train()

# Сохранение модели и токенизатора
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"Модель успешно обучена и сохранена в {OUTPUT_DIR}")
