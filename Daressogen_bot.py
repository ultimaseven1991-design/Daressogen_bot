import os
import telebot
from flask import Flask, request
import requests
import time
import logging

# Настройка логирования (чтобы видеть ошибки)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.environ.get('BOT_TOKEN')
RENDER_URL = os.environ.get('RENDER_URL')

if not TOKEN or not RENDER_URL:
    exit("❌ Нет токена или URL!")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ========== ВОССТАНОВЛЕНИЕ ВЕБХУКА ==========
def ensure_webhook():
    webhook_url = f"{RENDER_URL}/webhook/{TOKEN}"
    try:
        info = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo").json()
        if info['result']['url'] != webhook_url:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", 
                         json={"url": webhook_url})
            logger.info("✅ Вебхук восстановлен")
    except Exception as e:
        logger.error(f"Ошибка вебхука: {e}")

# ========== МАРШРУТЫ ==========
@app.route('/')
def index():
    return "Bot OK"

@app.route('/ping')
def ping():
    ensure_webhook()
    return "pong"

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    """Основной обработчик сообщений"""
    try:
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
        return "Error", 500

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@bot.message_handler(commands=['start'])
def start(message):
    try:
        bot.reply_to(message, "✅ Бот работает!\nОтправь 4 цифры")
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")

@bot.message_handler(func=lambda m: True)
def handle(message):
    try:
        text = message.text.strip()
        
        # === ЗАЩИТА ОТ ЛЮБЫХ СИМВОЛОВ ===
        # 1. Проверка на пустое сообщение
        if not text:
            bot.reply_to(message, "❌ Пустое сообщение")
            return
        
        # 2. Оставляем только цифры из текста
        cleaned = ''.join(c for c in text if c.isdigit())
        
        # 3. Проверяем, что:
        #    - есть ровно 4 цифры
        #    - не было других символов (clean == text)
        if len(cleaned) == 4 and cleaned == text:
            result = str((int(cleaned) ^ 8279) & 8191).zfill(4)
            bot.reply_to(message, f"✅ Результат: `{result}`", parse_mode="Markdown")
        else:
            if cleaned != text:
                # Были посторонние символы
                bot.reply_to(message, "❌ Используйте ТОЛЬКО цифры, без пробелов и символов!")
            else:
                # Не 4 цифры
                bot.reply_to(message, "❌ Нужно ввести ровно 4 цифры!")
                
    except Exception as e:
        logger.error(f"Ошибка в обработке: {e}")
        try:
            bot.reply_to(message, "😕 Произошла ошибка. Отправьте /start")
        except:
            pass

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    ensure_webhook()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
