import os
import telebot
from flask import Flask, request
import logging
import sys

# Минимальное логирование
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    logger.error("Нет токена!")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    print("🔥🔥🔥 ПОЛУЧЕН POST-ЗАПРОС! 🔥🔥🔥")
    print(f"Headers: {request.headers}")
    print(f"Data: {request.get_data()}")

@app.route('/ping')
def ping():
    return "pong"

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    """Только POST запросы от Telegram"""
    try:
        logger.info("Получен запрос")
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return "Error", 500

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ Бот работает!\nОтправь 4 цифры")

@bot.message_handler(func=lambda m: True)
def handle(message):
    try:
        text = message.text.strip()
        
        # Простая проверка
        if text.isdigit() and len(text) == 4:
            result = str((int(text) ^ 8279) & 8191).zfill(4)
            bot.reply_to(message, f"✅ Результат: {result}")
        else:
            bot.reply_to(message, "❌ Нужно ровно 4 цифры!")
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        bot.reply_to(message, "❌ Ошибка")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Запуск на порту {port}")
    app.run(host='0.0.0.0', port=port)
