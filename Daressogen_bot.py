import os
import telebot
from flask import Flask, request
import logging
import requests
import time
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Токен из переменных окружения
TOKEN = os.environ.get('BOT_TOKEN')
RENDER_URL = os.environ.get('RENDER_URL')

if not TOKEN:
    logger.error("❌ BOT_TOKEN не установлен!")
    sys.exit(1)

if not RENDER_URL:
    logger.error("❌ RENDER_URL не установлен!")
    sys.exit(1)

logger.info(f"✅ Токен загружен: {TOKEN[:10]}...")
logger.info(f"✅ URL сервера: {RENDER_URL}")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ========== НАСТРОЙКА ВЕБХУКА ПРИ ЗАПУСКЕ ==========
def setup_webhook():
    """Принудительная установка вебхука"""
    webhook_url = f"{RENDER_URL}/webhook/{TOKEN}"
    
    logger.info(f"🔄 Устанавливаю вебхук на: {webhook_url}")
    
    # Шаг 1: Удаляем старый вебхук
    delete_url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
    delete_response = requests.post(delete_url, json={"drop_pending_updates": True})
    logger.info(f"📤 Удаление вебхука: {delete_response.json()}")
    
    time.sleep(1)
    
    # Шаг 2: Устанавливаем новый вебхук
    set_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    set_response = requests.post(set_url, json={
        "url": webhook_url,
        "drop_pending_updates": True,
        "max_connections": 40
    })
    
    logger.info(f"📥 Установка вебхука: {set_response.json()}")
    
    if set_response.json().get('ok'):
        logger.info("✅ Вебхук успешно установлен!")
        
        # Шаг 3: Проверяем статус
        time.sleep(1)
        check_url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        check_response = requests.get(check_url)
        webhook_info = check_response.json()
        logger.info(f"🔍 Статус вебхука: {webhook_info}")
        
        return True
    else:
        logger.error("❌ Не удалось установить вебхук!")
        return False

# Вызываем установку ДО запуска сервера
logger.info("🚀 Начинаю настройку вебхука...")
if not setup_webhook():
    logger.error("❌ Критическая ошибка: вебхук не установлен!")
    # Не выходим, пробуем продолжить

# ========== МАРШРУТЫ FLASK ==========
@app.route('/')
def index():
    logger.debug("GET /")
    return "Bot is running! 🚀"

@app.route('/ping')
def ping():
    logger.debug("GET /ping")
    return "pong"

@app.route('/debug')
def debug():
    """Проверка статуса вебхука"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(url)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    """Обработчик сообщений от Telegram"""
    logger.info("📩 ПОЛУЧЕНО СООБЩЕНИЕ ОТ TELEGRAM!")
    
    try:
        json_string = request.get_data().decode('utf-8')
        logger.info(f"📄 Данные: {json_string[:200]}")
        
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        
        logger.info("✅ Сообщение обработано")
        return "OK", 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки: {e}")
        return "Error", 500

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"👤 Команда /start от {message.from_user.id}")
    bot.reply_to(message, "✅ Бот работает! Отправь мне 4 цифры.")

@bot.message_handler(commands=['debug'])
def debug_command(message):
    """Проверка статуса бота"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(url)
        data = response.json()
        
        status = f"📊 **Статус:**\n"
        status += f"• URL: {data['result'].get('url', 'не установлен')}\n"
        status += f"• Ожидает: {data['result'].get('pending_update_count', 0)}\n"
        
        bot.reply_to(message, status, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(func=lambda message: True)
def echo(message):
    logger.info(f"👤 Сообщение от {message.from_user.id}: {message.text}")
    
    try:
        user_input = message.text.strip()
        
        if not user_input.isdigit() or len(user_input) != 4:
            bot.reply_to(message, "❌ Нужно ввести ровно 4 цифры!")
            return
        
        chislo = int(user_input)
        result = (chislo ^ 8279) & 8191
        result_str = str(result).zfill(4)
        
        bot.reply_to(message, f"✅ Результат: `{result_str}`", parse_mode="Markdown")
        logger.info(f"✅ Отправлен результат {result_str}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск Flask сервера на порту {port}")
    app.run(host='0.0.0.0', port=port)
