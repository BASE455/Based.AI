import re
import os
import requests
import pytesseract
from PIL import Image

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# =======================
# 🔐 НАСТРОЙКИ
# =======================

import os
TOKEN = os.getenv("BOT_TOKEN")
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

# =======================
# 🌍 ОПРЕДЕЛЕНИЕ ЯЗЫКА
# =======================

def detect_language(text: str) -> str:
    text = text.lower()

    if re.search(r"[әөүұқғң]", text):
        return "kz"
    if re.search(r"[а-яё]", text):
        return "ru"
    if re.search(r"[a-z]", text):
        return "en"

    return "en"

# =======================
# 🚫 ЗАЩИТА ОТ ГОТОВЫХ ОТВЕТОВ
# =======================

def is_homework_request(text: str) -> bool:
    keywords = [
        "реши", "решение", "ответ",
        "готовый ответ", "дай ответ",
        "solve", "answer", "do my homework",
        "шығарып бер", "дай жауап"
    ]
    text = text.lower()
    return any(k in text for k in keywords)

# =======================
# 🧠 ПРОМПТ ДЛЯ ИИ
# =======================

def build_prompt(text: str, lang: str) -> str:
    if lang == "kz":
        return (
            "Сен мектеп оқушыларына арналған оқу көмекшісі ИИ-сің.\n"
            "Сен ЕШҚАШАН дайын жауап немесе нақты шешім бермейсің.\n"
            "Тек ұғымдарды, терминдерді және тақырыптарды қарапайым тілмен түсіндіресің.\n"
            "Егер сұрақ есепке қатысты болса — шешпей, қалай ойлау керегін түсіндір.\n\n"
            f"Сұрақ: {text}"
        )

    if lang == "ru":
        return (
            "Ты учебный ИИ-помощник для школьников.\n"
            "Ты НИКОГДА не даёшь готовые ответы или решения.\n"
            "Ты объясняешь термины, понятия и темы простым языком.\n"
            "Если вопрос — задача, объясни подход, но не решай.\n\n"
            f"Вопрос: {text}"
        )

    return (
        "You are an educational AI assistant for students.\n"
        "You never give direct answers or solve tasks.\n"
        "You explain concepts, terms, and approaches step by step.\n\n"
        f"Question: {text}"
    )

# =======================
# 🤖 ЗАПРОС К OLLAMA
# =======================

def ask_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    return response.json()["response"]

# =======================
# 📸 OCR
# =======================

def extract_text_from_image(path: str) -> str:
    img = Image.open(path)
    return pytesseract.image_to_string(img, lang="rus+kaz+eng").strip()

# =======================
# 📩 HANDLERS
# =======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет!\n"
        "Я школьный ИИ-помощник.\n"
        "📚 Объясняю темы и термины\n"
        "📸 Понимаю фото\n"
        "❌ Не решаю задания за ученика"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if is_homework_request(text):
        await update.message.reply_text(
            "⚠️ Я не даю готовые ответы.\n"
            "Но могу объяснить тему или подход к решению 🙂"
        )
        return

    lang = detect_language(text)
    prompt = build_prompt(text, lang)
    answer = ask_ollama(prompt)

    await update.message.reply_text(answer)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()

    path = "temp.jpg"
    await file.download_to_drive(path)

    await update.message.reply_text("📷 Распознаю текст с изображения...")

    text = extract_text_from_image(path)
    os.remove(path)

    if not text:
        await update.message.reply_text("❌ Не удалось распознать текст.")
        return

    lang = detect_language(text)
    prompt = build_prompt(text, lang)
    answer = ask_ollama(prompt)

    await update.message.reply_text(answer)

# =======================
# 🚀 ЗАПУСК
# =======================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущен и работает...")
    app.run_polling()

if __name__ == "__main__":
    main()
