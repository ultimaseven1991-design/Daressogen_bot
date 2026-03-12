import os
import telebot
import time
import threading
from flask import Flask, request, jsonify
import logging
import requests
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== ОСНОВНОЙ КОД БОТА ==========

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    logger.error("BOT_TOKEN не установлен!")
    sys.exit(1)

# Инициализируем бота без polling
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()  # Сразу удаляем вебхук при старте

# Создаем Flask приложение
app = Flask(__name__)

# Функция для полного сброса всех подключений
def force_reset_webhook():
    """Принудительно сбрасывает все подключения бота"""
    try:
        # Используем прямой запрос к API Telegram
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.post(url, json={
            "drop_pending_updates": True
        })
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Webhook удален: {result}")
            return True
        else:
            logger.error(f"Ошибка удаления webhook: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при сбросе webhook: {e}")
        return False

# Функция установки webhook
def setup_webhook():
    """Устанавливает webhook для бота"""
    render_url = os.environ.get('RENDER_URL')
    if not render_url:
        logger.error("RENDER_URL не установлен!")
        return False
    
    webhook_url = f"{render_url.rstrip('/')}/{TOKEN}"
    
    try:
        # Используем прямой запрос к API для установки webhook
        url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
        response = requests.post(url, json={
            "url": webhook_url,
            "drop_pending_updates": True,
            "max_connections": 40,
            "allowed_updates": ["message", "callback_query"]
        })
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info(f"Webhook успешно установлен на {webhook_url}")
                
                # Проверяем статус webhook
                time.sleep(1)
                check_url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
                check_response = requests.get(check_url)
                if check_response.status_code == 200:
                    webhook_info = check_response.json()
                    logger.info(f"Статус webhook: {webhook_info}")
                return True
            else:
                logger.error(f"Ошибка установки webhook: {result}")
                return False
        else:
            logger.error(f"HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при установке webhook: {e}")
        return False

# Маршруты Flask
@app.route('/')
def index():
    return jsonify({
        "status": "running",
        "mode": "webhook",
        "timestamp": time.time()
    })

@app.route('/ping')
def ping():
    return "pong"

@app.route('/health')
def health():
    """Проверка здоровья"""
    return jsonify({
        "status": "healthy",
        "webhook_configured": True,
        "timestamp": time.time()
    })

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Основной обработчик webhook от Telegram"""
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            
            # Обрабатываем обновление
            bot.process_new_updates([update])
            
            return "OK", 200
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Wrong content type"}), 403

@app.route('/debug/webhook', methods=['GET'])
def debug_webhook():
    """Отладочный маршрут для проверки статуса webhook"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(url)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to get webhook info"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Функция для поддержания активности
def keep_alive():
    """Периодически проверяет статус и поддерживает активность"""
    while True:
        try:
            # Проверяем статус webhook
            url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    webhook_info = data['result']
                    if webhook_info.get('url'):
                        logger.debug(f"Webhook активен, ожидающих: {webhook_info.get('pending_update_count', 0)}")
                    else:
                        logger.warning("Webhook не настроен! Пробуем перенастроить...")
                        setup_webhook()
            
            # Пингуем свой сервер
            render_url = os.environ.get('RENDER_URL')
            if render_url:
                try:
                    requests.get(f"{render_url}/ping", timeout=5)
                except:
                    pass
            
            time.sleep(300)  # Каждые 5 минут
            
        except Exception as e:
            logger.error(f"Ошибка в keep_alive: {e}")
            time.sleep(60)

# ========== ОБРАБОТЧИКИ КОМАНД БОТА ==========

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 Привет! Я бот для преобразования чисел.\n\n"
        "📝 Отправь мне **4 цифры** (например, 1234), "
        "и я применю к ним специальную формулу.\n\n"
        "ℹ️ Бот работает в режиме webhook и всегда онлайн!\n"
        "📊 Отправьте /status для проверки статуса"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def status_command(message):
    """Проверка статуса бота"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                info = data['result']
                status_text = (
                    f"📊 **Статус бота:**\n"
                    f"• Режим: Webhook\n"
                    f"• URL: {info.get('url', 'не установлен')[:50]}...\n"
                    f"• Ожидающих обновлений: {info.get('pending_update_count', 0)}\n"
                    f"• Макс. соединений: {info.get('max_connections', 40)}\n"
                )
                
                if info.get('last_error_date'):
                    status_text += f"• Последняя ошибка: {info.get('last_error_message', 'неизвестно')}\n"
            else:
                status_text = "❌ Не удалось получить статус webhook"
        else:
            status_text = "❌ Ошибка подключения к Telegram API"
        
        bot.reply_to(message, status_text, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

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
        logger.error(f"Ошибка в обработчике: {e}")

# ========== ЗАПУСК ==========

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("ЗАПУСК БОТА В РЕЖИМЕ WEBHOOK")
    logger.info("=" * 50)
    
    # 1. Принудительно сбрасываем все старые подключения
    logger.info("Шаг 1: Сброс всех старых подключений...")
    if force_reset_webhook():
        logger.info("✓ Все старые подключения сброшены")
    else:
        logger.warning("⚠ Проблема при сбросе подключений")
    
    time.sleep(2)
    
    # 2. Устанавливаем новый webhook
    logger.info("Шаг 2: Установка нового webhook...")
    if setup_webhook():
        logger.info("✓ Webhook успешно установлен")
    else:
        logger.error("✗ Критическая ошибка: не удалось установить webhook")
        sys.exit(1)
    
    time.sleep(1)
    
    # 3. Запускаем поток поддержания активности
    logger.info("Шаг 3: Запуск потока поддержания активности...")
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    logger.info("✓ Поток поддержания активности запущен")
    
    # 4. Запускаем Flask сервер
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Шаг 4: Запуск Flask сервера на порту {port}")
    logger.info("=" * 50)
    logger.info("БОТ УСПЕШНО ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
    logger.info("=" * 50)
    
    app.run(host='0.0.0.0', port=port)
