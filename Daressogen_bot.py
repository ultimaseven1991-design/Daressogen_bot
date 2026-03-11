import telebot
from telebot import types

# Токен вашего бота (получите у @BotFather)
TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Привет! Отправь мне 4 цифры, и я применю к ним формулу: (число XOR 8279) AND 8191")

@bot.message_handler(func=lambda message: True)
def calculate_number(message):
    try:
        # Проверяем, что введено ровно 4 цифры
        text = message.text.strip()
        
        # Удаляем возможные пробелы и проверяем, что это число из 4 цифр
        if not text.isdigit() or len(text) != 4:
            bot.reply_to(message, "❌ Пожалуйста, введите ровно 4 цифры (например, 1234)")
            return
        
        # Преобразуем в число
        mynum = int(text)
        
        # Применяем формулу из вашего кода
        result = (mynum ^ 8279) & 8191
        
        # Форматируем результат как 4 цифры (добавляем ведущие нули если нужно)
        result_str = str(result).zfill(4)
        
        # Отправляем результат
        response = f"✅ Введено: {text}\n🔢 Результат: {result_str}"
        bot.reply_to(message, response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# Запускаем бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)
