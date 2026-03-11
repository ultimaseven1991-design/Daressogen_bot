import os
import telebot

# ========== ОСНОВНОЙ КОД БОТА ==========

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

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
        print(f"Ошибка в боте: {e}")
