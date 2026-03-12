import os
import telebot
import time
import threading
from flask import Flask, request
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ОСНОВНОЙ КОД БОТА ==========

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Создаем Flask приложение для вебхуков
app = Flask(__name__)

# Обработчик для пинг-запросов (чтобы бот не засыпал)
@app.route('/')
def index():
    return "Bot is running!", 200

@app.route('/ping')
def ping():
    return "pong", 200

# Обработчик вебхука от Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Wrong content type", 403

# Функция для отправки периодических пингов
def keep_alive():
    """Функция для поддержания активности бота"""
    while True:
        try:
            # Отправляем себе сообщение (опционально)
            # bot.send_message(ADMIN_CHAT_ID, "Пинг от бота")
            
            # Логируем время
            logger.info(f"Бот активен: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Ждем 10 минут перед следующим пингом
            time.sleep(600)
        except Exception as e:
            logger.error(f"Ошибка в keep_alive: {e}")
            time.sleep(60)

# ========== ОБРАБОТЧИКИ КОМАНД ==========

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 Привет! Я бот для преобразования чисел.\n\n"
        "📝 Отправь мне **4 цифры** (например, 1234), "
        "и я применю к ним специальную формулу.\n\n"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def calculate_number(message):
    try:
        user_input = message.text.strip()
        
        if not user_input:
            bot.reply_to(message, "❌ Вы отправили пустое сообщение. Нужно ввести 4 цифры!")
            return
        
        if not user_input.isdigit():
            if ' ' in user_input:
                bot.reply_to(message, "❌ Не используйте пробелы! Нужно ввести 4 цифры подряд.\n"
                                      "✅ Правильно: `1234`", parse_mode="Markdown")
            else:
                bot.reply_to(message, f"❌ Нужно ввести ТОЛЬКО цифры. Вы ввели: '{user_input}'")
            return
        
        if len(user_input) != 4:
            bot.reply_to(message, f"❌ Нужно ввести РОВНО 4 цифры. Вы ввели {len(user_input)} цифр(ы).\n"
                                  f"✅ Пример: `1234`", parse_mode="Markdown")
            return
        
        chislo = int(user_input)
        result = (chislo ^ 8279) & 8191
        result_str = str(result).zfill(4)
        
        response = (
            f"✅ **Введено:** `{user_input}`\n"
            f"🔢 **Результат:** `{result_str}`\n"
        )
        bot.reply_to(message, response, parse_mode="Markdown")
        
    except Exception as e:
        error_message = (
            "😕 Произошла неизвестная ошибка.\n"
            f"Текст ошибки: `{str(e)}`\n\n"
            "Попробуйте еще раз или отправьте /start"
        )
        bot.reply_to(message, error_message, parse_mode="Markdown")
        logger.error(f"Ошибка в боте: {e}")

# ========== ЗАПУСК БОТА ==========

if __name__ == '__main__':
    # Определяем режим работы
    USE_WEBHOOK = os.environ.get('USE_WEBHOOK', 'False').lower() == 'true'
    
    if USE_WEBHOOK:
        # Режим вебхуков (рекомендуется для Render.com)
        RENDER_URL = os.environ.get('RENDER_URL')  # URL вашего приложения на Render
        if not RENDER_URL:
            logger.warning("RENDER_URL не установлен! Использую локальный хост для теста.")
            RENDER_URL = "http://localhost:5000"
        
        # Удаляем старый вебхук и устанавливаем новый
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=f"{RENDER_URL}/webhook")
        logger.info(f"Вебхук установлен на {RENDER_URL}/webhook")
        
        # Запускаем Flask приложение
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        # Режим поллинга (обычный режим)
        logger.info("Запуск бота в режиме поллинга...")
        
        # Запускаем поток для поддержания активности
        keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
        keep_alive_thread.start()
        
        # Запускаем бота
        bot.infinity_polling()
