import os
import telebot
from flask import Flask, request
import logging
import requests
import time
import threading

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.environ.get('BOT_TOKEN')
RENDER_URL = os.environ.get('RENDER_URL')

if not TOKEN or not RENDER_URL:
    logger.error("❌ Отсутствуют переменные окружения!")
    exit(1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ========== ФУНКЦИЯ ПРОВЕРКИ ВЕБХУКА ==========
def check_webhook():
    """Проверяет, работает ли вебхук, и переустанавливает если нужно"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(url).json()
        
        if response.get('ok'):
            webhook_url = response['result'].get('url', '')
            if not webhook_url:
                logger.warning("⚠️ Вебхук не установлен! Устанавливаю...")
                setup_webhook()
                return False
            elif webhook_url != f"{RENDER_URL}/webhook/{TOKEN}":
                logger.warning("⚠️ Неправильный URL вебхука! Исправляю...")
                setup_webhook()
                return False
            else:
                logger.info("✅ Вебхук работает")
                return True
    except Exception as e:
        logger.error(f"❌ Ошибка проверки вебхука: {e}")
        return False

# ========== УСТАНОВКА ВЕБХУКА ==========
def setup_webhook():
    webhook_url = f"{RENDER_URL}/webhook/{TOKEN}"
    
    try:
        # Удаляем старый
        requests.post(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", 
                     json={"drop_pending_updates": True})
        time.sleep(1)
        
        # Устанавливаем новый
        result = requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", 
                              json={"url": webhook_url}).json()
        
        if result.get('ok'):
            logger.info(f"✅ Вебхук установлен: {webhook_url}")
            return True
        else:
            logger.error(f"❌ Ошибка установки: {result}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

# ========== МОНИТОРИНГ ==========
def monitor():
    """Постоянно проверяет работу бота"""
    while True:
        try:
            # Проверка вебхука каждые 5 минут
            check_webhook()
            
            # Пинг самого себя
            requests.get(f"{RENDER_URL}/ping", timeout=5)
            
            # Проверка ответов бота (тестовый запрос к себе)
            # Отправляем команду /status самому себе (замените на ваш ID)
            # bot.send_message(5304614567, "💓 Keep-alive")
            
            time.sleep(300)  # 5 минут
        except Exception as e:
            logger.error(f"Ошибка в мониторинге: {e}")
            time.sleep(60)

# ========== МАРШРУТЫ ==========
@app.route('/')
def index():
    return "Bot OK"

@app.route('/ping')
def ping():
    return "pong"

@app.route('/reset-webhook')
def reset_webhook():
    """Ручной сброс вебхука"""
    result = setup_webhook()
    return f"Webhook reset: {result}"

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        
        if update.message:
            if update.message.text == '/start':
                handle_start(update.message)
            elif update.message.text == '/reset':
                # Команда для ручного сброса
                setup_webhook()
                bot.reply_to(update.message, "✅ Вебхук перезапущен")
            else:
                handle_message(update.message)
                
        return "OK", 200
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
        return "Error", 500

# ========== ОБРАБОТЧИКИ ==========
@bot.message_handler(commands=['start'])
def handle_start(message):
    try:
        bot.reply_to(message, "✅ Бот работает!\nОтправь 4 цифры, например: 1234")
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    try:
        text = message.text.strip()
        
        if not text:
            bot.reply_to(message, "❌ Пустое сообщение")
            return
        
        cleaned = ''.join(c for c in text if c.isdigit())
        
        if len(cleaned) == 4 and cleaned == text:
            result = str((int(cleaned) ^ 8279) & 8191).zfill(4)
            bot.reply_to(message, f"✅ Результат: `{result}`", parse_mode="Markdown")
        else:
            if cleaned != text:
                bot.reply_to(message, "❌ Используйте ТОЛЬКО цифры, без пробелов и символов!")
            else:
                bot.reply_to(message, "❌ Нужно ввести ровно 4 цифры!")
                
    except Exception as e:
        logger.error(f"Ошибка в обработке: {e}")
        try:
            bot.reply_to(message, "😕 Ошибка. Отправьте /start")
        except:
            pass

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    # Сначала устанавливаем вебхук
    setup_webhook()
    
    # Запускаем мониторинг
    threading.Thread(target=monitor, daemon=True).start()
    
    # Запускаем сервер
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск на порту {port}")
    app.run(host='0.0.0.0', port=port)
