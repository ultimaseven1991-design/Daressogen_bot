import threading
import os
import telebot
from flask import Flask, request, jsonify
import logging
import requests
import time
import sys
import json

# Настройка логирования с максимальной детализацией
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# ========== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ==========
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

# ========== ИНИЦИАЛИЗАЦИЯ БОТА ==========
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ========== ФУНКЦИЯ УСТАНОВКИ ВЕБХУКА ==========
def setup_webhook():
    """Принудительная установка вебхука"""
    webhook_url = f"{RENDER_URL}/webhook/{TOKEN}"
    
    logger.info(f"🔄 Устанавливаю вебхук на: {webhook_url}")
    
    try:
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
            "max_connections": 40,
            "allowed_updates": ["message", "callback_query"]
        })
        
        logger.info(f"📥 Установка вебхука: {set_response.json()}")
        
        if set_response.json().get('ok'):
            logger.info("✅ Вебхук успешно установлен!")
            
            # Шаг 3: Проверяем статус
            time.sleep(1)
            check_url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
            check_response = requests.get(check_url)
            webhook_info = check_response.json()
            logger.info(f"🔍 Статус вебхука: {json.dumps(webhook_info, indent=2, ensure_ascii=False)}")
            
            return True
        else:
            logger.error(f"❌ Ошибка установки вебхука: {set_response.json()}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка в setup_webhook: {e}")
        return False

# ========== МАРШРУТЫ FLASK ==========
@app.route('/')
def index():
    logger.debug("GET /")
    return "Bot is running! 🚀"

@app.route('/ping')
def ping():
    logger.debug("GET /ping")
    return "pong"

@app.route('/health')
def health():
    """Проверка здоровья"""
    return jsonify({
        "status": "healthy",
        "token_set": bool(TOKEN),
        "timestamp": time.time()
    })

@app.route('/debug')
def debug():
    """Отладка - информация о вебхуке"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(url)
        return jsonify({
            "webhook_info": response.json(),
            "server_time": time.time(),
            "render_url": RENDER_URL
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    """ОСНОВНОЙ ОБРАБОТЧИК - ВСЕ СООБЩЕНИЯ ПРИХОДЯТ СЮДА"""
    logger.info("=" * 60)
    logger.info("📩 ПОЛУЧЕНО СООБЩЕНИЕ ОТ TELEGRAM!")
    
    try:
        # Получаем ВСЕ данные запроса
        json_string = request.get_data().decode('utf-8')
        logger.info(f"📄 ПОЛНЫЕ ДАННЫЕ (первые 500 символов): {json_string[:500]}")
        
        # Парсим JSON для проверки структуры
        data = json.loads(json_string)
        logger.info(f"📊 СТРУКТУРА: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        
        # Создаем update объект
        update = telebot.types.Update.de_json(json_string)
        
        # Детальный разбор сообщения
        if update.message:
            logger.info(f"👤 ИНФОРМАЦИЯ О СООБЩЕНИИ:")
            logger.info(f"  • ID сообщения: {update.message.message_id}")
            logger.info(f"  • От пользователя: {update.message.from_user.id} (@{update.message.from_user.username})")
            logger.info(f"  • Chat ID: {update.message.chat.id}")
            logger.info(f"  • Текст: '{update.message.text}'")
            logger.info(f"  • Тип: {update.message.content_type}")
        elif update.callback_query:
            logger.info(f"🔄 Callback query: {update.callback_query.data}")
        else:
            logger.info(f"❓ Неизвестный тип обновления: {update}")
        
        # Обрабатываем обновление через бота
        logger.info("🔄 Передаю обновление боту...")
        bot.process_new_updates([update])
        logger.info("✅ Обновление передано боту")
        
        return "OK", 200
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка парсинга JSON: {e}")
        logger.error(f"❌ Сырые данные: {request.get_data()}")
        return "Invalid JSON", 400
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в webhook: {e}")
        logger.exception("Полный стек ошибки:")
        return "Error", 500

# ========== ОБРАБОТЧИКИ КОМАНД БОТА ==========
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Обработчик команды /start"""
    logger.info("=" * 60)
    logger.info(f"🎯 ВЫЗВАН ОБРАБОТЧИК /start")
    logger.info(f"👤 Пользователь: {message.from_user.id} (@{message.from_user.username})")
    logger.info(f"💬 Текст: {message.text}")
    
    try:
        # Пробуем отправить ответ
        sent_message = bot.reply_to(
            message, 
            "✅ **Бот работает!**\n\nОтправь мне 4 цифры, например: `1234`",
            parse_mode="Markdown"
        )
        logger.info(f"✅ Ответ отправлен! ID сообщения: {sent_message.message_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки ответа на /start: {e}")
        # Пробуем альтернативный метод
        try:
            sent_message = bot.send_message(
                message.chat.id,
                "✅ Бот работает! Отправь мне 4 цифры."
            )
            logger.info(f"✅ Альтернативный ответ отправлен! ID: {sent_message.message_id}")
        except Exception as e2:
            logger.error(f"❌ И альтернативный метод не сработал: {e2}")

@bot.message_handler(commands=['debug'])
def handle_debug(message):
    """Обработчик команды /debug"""
    logger.info(f"🎯 ВЫЗВАН ОБРАБОТЧИК /debug от {message.from_user.id}")
    
    try:
        # Получаем информацию о вебхуке
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(url)
        data = response.json()
        
        # Формируем ответ
        webhook_url = data['result'].get('url', 'не установлен')
        pending = data['result'].get('pending_update_count', 0)
        
        debug_text = f"🔧 **Отладка:**\n"
        debug_text += f"• Webhook: {webhook_url[:50]}...\n"
        debug_text += f"• Ожидает: {pending}\n"
        debug_text += f"• Ваш ID: {message.from_user.id}\n"
        debug_text += f"• Chat ID: {message.chat.id}"
        
        bot.reply_to(message, debug_text, parse_mode="Markdown")
        logger.info("✅ Отладочная информация отправлена")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в /debug: {e}")
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Обработчик ВСЕХ остальных сообщений"""
    logger.info("=" * 60)
    logger.info(f"🎯 ВЫЗВАН ОСНОВНОЙ ОБРАБОТЧИК")
    logger.info(f"👤 Пользователь: {message.from_user.id} (@{message.from_user.username})")
    logger.info(f"💬 Текст сообщения: '{message.text}'")
    logger.info(f"📊 Длина текста: {len(message.text) if message.text else 0}")
    
    try:
        user_input = message.text.strip()
        
        # Проверка на 4 цифры
        if user_input.isdigit() and len(user_input) == 4:
            chislo = int(user_input)
            result = (chislo ^ 8279) & 8191
            result_str = str(result).zfill(4)
            
            response_text = f"✅ **Результат:** `{result_str}`"
            logger.info(f"🧮 Вычисление: {user_input} -> {result_str}")
        else:
            response_text = "❌ Нужно ввести ровно 4 цифры!"
            logger.info(f"❌ Неверный формат: {user_input}")
        
        # Отправляем ответ
        sent_message = bot.reply_to(message, response_text, parse_mode="Markdown")
        logger.info(f"✅ Ответ отправлен! ID: {sent_message.message_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в основном обработчике: {e}")
        logger.exception("Полный стек ошибки:")
        
        # Пробуем отправить сообщение об ошибке
        try:
            bot.reply_to(message, f"😕 Ошибка: {str(e)[:100]}")
        except:
            pass

# ========== ФУНКЦИЯ ПОДДЕРЖАНИЯ АКТИВНОСТИ ==========
def keep_alive():
    """Периодическая проверка статуса"""
    while True:
        try:
            time.sleep(60)  # Каждую минуту
            logger.debug("💓 Keep-alive ping")
            
            # Проверяем вебхук
            url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    pending = data['result'].get('pending_update_count', 0)
                    if pending > 0:
                        logger.warning(f"⚠️ Есть ожидающие обновления: {pending}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в keep_alive: {e}")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК БОТА")
    logger.info("=" * 60)
    
    # Устанавливаем вебхук
    if setup_webhook():
        logger.info("✅ Вебхук настроен, запускаю сервер...")
    else:
        logger.warning("⚠️ Проблема с вебхуком, но пробую запустить сервер")
    
    # Запускаем поток поддержания активности
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    logger.info("✅ Поток keep-alive запущен")
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск Flask на порту {port}")
    logger.info("=" * 60)
    
    # ВАЖНО: отключаем debug режим Flask
    app.run(host='0.0.0.0', port=port, debug=False)
