import os
import telebot
from flask import Flask, request
import logging
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен из переменных окружения
TOKEN = os.environ.get('BOT_TOKEN')
RENDER_URL = os.environ.get('RENDER_URL')

if not TOKEN:
    logger.error("BOT_TOKEN не установлен!")
    exit(1)

if not RENDER_URL:
    logger.error("RENDER_URL не установлен!")
    exit(1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Простая проверка работы сервера
@app.route('/')
def index():
    return "Bot is running!"

@app.route('/ping')
def ping():
    return "pong"

# Вебхук для Telegram
@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    logger.info("Получен запрос от Telegram")
    try:
        json_string = request.get_data().decode('utf-8')
        logger.info(f"Данные: {json_string[:200]}")
        
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        
        return "OK", 200
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return "Error", 500

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"Команда /start от {message.from_user.id}")
    bot.reply_to(message, "Бот работает! ✅")

# Любые текстовые сообщения
@bot.message_handler(func=lambda message: True)
def echo(message):
    logger.info(f"Сообщение от {message.from_user.id}: {message.text}")
    bot.reply_to(message, f"Вы написали: {message.text}")

if __name__ == '__main__':
    # Устанавливаем вебхук при запуске
    webhook_url = f"{RENDER_URL}/webhook/{TOKEN}"
    
    # Удаляем старый вебхук
    requests.post(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
    
    # Устанавливаем новый
    result = requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", 
                          json={"url": webhook_url})
    logger.info(f"Установка вебхука: {result.json()}")
    
    # Запускаем сервер
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
