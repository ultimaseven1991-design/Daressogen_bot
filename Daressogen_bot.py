import os
import telebot
from flask import Flask, request
import logging
import requests
import time
import threading

# Настройка логирования (только важное)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.environ.get('BOT_TOKEN')
RENDER_URL = os.environ.get('RENDER_URL')

if not TOKEN or not RENDER_URL:
    logger.error("❌ Отсутствуют переменные окружения!")
    exit(1)

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ========== УСТАНОВКА ВЕБХУКА ==========
def setup_webhook():
    webhook_url = f"{RENDER_URL}/webhook/{TOKEN}"
    
    # Удаляем старый и устанавливаем новый вебхук
    requests.post(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", 
                  json={"drop_pending_updates": True})
    time.sleep(0.5)
    
    result = requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", 
                          json={"url": webhook_url}).json()
    
    logger.info(f"✅ Webhook: {result.get('description', 'OK')}")
    return result.get('ok', False)

# ========== МАРШРУТЫ FLASK ==========
@app.route('/')
def index():
    return "Bot OK"

@app.route('/ping')
def ping():
    return "pong"

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    """Получаем сообщения от Telegram"""
    try:
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        
        # Принудительная обработка (на всякий случай)
        if update.message:
            if update.message.text == '/start':
                handle_start(update.message)
            else:
                handle_message(update.message)
                
        return "OK", 200
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return "Error", 500

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "✅ Бот работает!\nОтправь 4 цифры, например: 1234")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip()
    
    if text.isdigit() and len(text) == 4:
        result = str((int(text) ^ 8279) & 8191).zfill(4)
        bot.reply_to(message, f"✅ Результат: `{result}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Нужно ввести ровно 4 цифры!")

# ========== ПОДДЕРЖАНИЕ АКТИВНОСТИ ==========
def keep_alive():
    while True:
        time.sleep(300)  # Каждые 5 минут
        try:
            requests.get(f"{RENDER_URL}/ping", timeout=5)
        except:
            pass

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    setup_webhook()
    threading.Thread(target=keep_alive, daemon=True).start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
