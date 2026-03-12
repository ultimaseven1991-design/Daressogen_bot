import os
import telebot
from flask import Flask, request
import logging
import sys

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ========== СОЗДАЕМ ПРИЛОЖЕНИЕ FLASK ==========
app = Flask(__name__)

# ========== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ==========
TOKEN = os.environ.get('BOT_TOKEN')
RENDER_URL = os.environ.get('RENDER_URL')

if not TOKEN:
    logger.error("❌ BOT_TOKEN не установлен!")
    sys.exit(1)

if not RENDER_URL:
    logger.error("❌ RENDER_URL не установлен!")
    sys.exit(1)

# ========== СОЗДАЕМ БОТА ==========
bot = telebot.TeleBot(TOKEN)

# ========== МАРШРУТЫ FLASK ==========
@app.route('/')
def index():
    return "Bot is running! 🚀"

@app.route('/ping')
def ping():
    """Для UptimeRobot - пинг каждые 5 минут"""
    logger.info("🏓 Пинг получен")
    return "pong"

@app.route('/webhook', methods=['POST'])
def webhook():
    """ОСНОВНОЙ ОБРАБОТЧИК - получает сообщения от Telegram"""
    logger.info("📩 Получен запрос от Telegram")
    
    try:
        # Получаем данные от Telegram
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        
        # Передаем боту
        bot.process_new_updates([update])
        
        # Принудительная обработка (на случай если обработчики не сработали)
        if update.message:
            if update.message.text == '/start':
                handle_start(update.message)
            else:
                handle_message(update.message)
        
        logger.info("✅ Сообщение обработано")
        return "OK", 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return "Error", 500

# ========== ОБРАБОТЧИКИ КОМАНД БОТА ==========
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Обработчик команды /start"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "без username"
        logger.info(f"👤 Команда /start от {user_id} (@{username})")
        
        bot.reply_to(
            message, 
            "✅ **Бот работает!**\n\nОтправь мне **4 цифры**, например: `1234`",
            parse_mode="Markdown"
        )
        logger.info("✅ Ответ на /start отправлен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в /start: {e}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Обработчик всех остальных сообщений"""
    try:
        text = message.text.strip()
        user_id = message.from_user.id
        logger.info(f"👤 Сообщение от {user_id}: '{text}'")
        
        # ЗАЩИТА ОТ ПУСТЫХ СООБЩЕНИЙ
        if not text:
            bot.reply_to(message, "❌ Пустое сообщение")
            return
        
        # ЗАЩИТА ОТ СПЕЦИАЛЬНЫХ СИМВОЛОВ
        # Оставляем только цифры
        cleaned = ''.join(c for c in text if c.isdigit())
        
        # Проверяем, что:
        # 1. Получили ровно 4 цифры
        # 2. Не было других символов (cleaned == text)
        if len(cleaned) == 4 and cleaned == text:
            # Вычисляем результат
            chislo = int(cleaned)
            result = (chislo ^ 8279) & 8191
            result_str = str(result).zfill(4)
            
            bot.reply_to(
                message, 
                f"✅ **Результат:** `{result_str}`", 
                parse_mode="Markdown"
            )
            logger.info(f"✅ Результат для {user_id}: {result_str}")
            
        else:
            if cleaned != text:
                # Были посторонние символы
                bot.reply_to(
                    message, 
                    "❌ Используйте **ТОЛЬКО цифры**, без пробелов и символов!",
                    parse_mode="Markdown"
                )
            else:
                # Не 4 цифры
                bot.reply_to(
                    message, 
                    "❌ Нужно ввести **ровно 4 цифры**!",
                    parse_mode="Markdown"
                )
                
    except Exception as e:
        logger.error(f"❌ Ошибка в обработке: {e}")
        try:
            bot.reply_to(message, "😕 Произошла ошибка. Отправьте /start")
        except:
            pass

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК БОТА")
    logger.info(f"📱 Токен: {TOKEN[:10]}...")
    logger.info(f"🌐 URL: {RENDER_URL}")
    logger.info("=" * 50)
    
    # Проверяем установку вебхука (опционально)
    try:
        webhook_url = f"{RENDER_URL}/webhook"
        import requests
        requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", 
                     json={"url": webhook_url})
        logger.info(f"✅ Вебхук установлен на {webhook_url}")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось установить вебхук: {e}")
    
    # Запускаем сервер
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
