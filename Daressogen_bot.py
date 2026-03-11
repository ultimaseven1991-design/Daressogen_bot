import os
import telebot
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ========== HTTP-ЗАГЛУШКА (для Render) ==========
# Этот сервер просто отвечает "OK" на любые запросы
# Render думает, что это веб-сайт, и не ругается на порты

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'Telegram bot is running!')
    
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    
    # Отключаем логи (чтобы не засоряли консоль)
    def log_message(self, format, *args):
        pass

def run_http_server():
    try:
        # Render сам говорит, какой порт использовать через переменную PORT
        port = int(os.environ.get('PORT', 10000))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f"🌐 HTTP-заглушка запущена на порту {port}")
        print(f"✅ Render больше не будет ругаться на порты!")
        server.serve_forever()
    except Exception as e:
        print(f"⚠️ Ошибка HTTP-сервера: {e}")

# Запускаем HTTP-сервер в отдельном потоке
http_thread = Thread(target=run_http_server, daemon=True)
http_thread.start()

# ========== ОСНОВНОЙ КОД БОТА ==========

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 Привет! Я бот для преобразования чисел.\n\n"
        "📝 Отправь мне **4 цифры** (например, 1234), "
        "и я применю к ним специальную формулу.\n\n"
        "🔢 Формула: (число XOR 8279) AND 8191"
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
            f"✨ Формула: ({user_input} XOR 8279) AND 8191 = {result_str}"
        )
        bot.reply_to(message, response, parse_mode="Markdown")
        
    except Exception as e:
        error_message = (
            "😕 Произошла неизвестная ошибка.\n"
            f"Текст ошибки: `{str(e)}`\n\n"
            "Попробуйте еще раз или отправьте /start"
        )
        bot.reply_to(message, error_message, parse_mode="Markdown")
        print(f"Ошибка в боте: {e}")

if __name__ == '__main__':
    print("✅ Бот запущен и готов к работе!")
    print("🚀 HTTP-заглушка работает в фоне")
    bot.polling(none_stop=True)
