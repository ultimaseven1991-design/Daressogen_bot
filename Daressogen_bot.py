import os
import telebot

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Приветствие
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 Привет! Я бот для преобразования чисел.\n\n"
        "📝 Отправь мне **4 цифры** (например, 1234), "
        "и я применю к ним специальную формулу.\n\n"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# Обработка всех сообщений
@bot.message_handler(func=lambda message: True)
def calculate_number(message):
    try:
        # Получаем текст и убираем лишние пробелы
        user_input = message.text.strip()
        
        # Проверка 1: Пустое сообщение
        if not user_input:
            bot.reply_to(message, "❌ Вы отправили пустое сообщение. Нужно ввести 4 цифры!")
            return
        
        # Проверка 2: Только цифры?
        if not user_input.isdigit():
            # Если есть пробелы, покажем пример
            if ' ' in user_input:
                bot.reply_to(message, "❌ Не используйте пробелы! Нужно ввести 4 цифры подряд.\n"
                                      "✅ Правильно: `1234`", parse_mode="Markdown")
            else:
                bot.reply_to(message, f"❌ Нужно ввести ТОЛЬКО цифры. Вы ввели: '{user_input}'")
            return
        
        # Проверка 3: Ровно 4 цифры?
        if len(user_input) != 4:
            bot.reply_to(message, f"❌ Нужно ввести РОВНО 4 цифры. Вы ввели {len(user_input)} цифр(ы).\n"
                                  f"✅ Пример: `1234`", parse_mode="Markdown")
            return
        
        # Если все проверки пройдены - вычисляем
        chislo = int(user_input)
        result = (chislo ^ 8279) & 8191
        result_str = str(result).zfill(4)
        
        # Отправляем красивый ответ
        response = (
            f"✅ **Введено:** `{user_input}`\n"
            f"🔢 **Результат:** `{result_str}`\n"
            f"✨ Формула: ({user_input} XOR 8279) AND 8191 = {result_str}"
        )
        bot.reply_to(message, response, parse_mode="Markdown")
        
    except Exception as e:
        # Ловим любые неожиданные ошибки
        error_message = (
            "😕 Произошла неизвестная ошибка.\n"
            f"Текст ошибки: `{str(e)}`\n\n"
            "Попробуйте еще раз или отправьте /start"
        )
        bot.reply_to(message, error_message, parse_mode="Markdown")
        # Выводим ошибку в логи Render для отладки
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    print("✅ Бот запущен и готов к работе!")
    bot.polling(none_stop=True)
