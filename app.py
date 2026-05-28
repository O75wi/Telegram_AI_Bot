import telebot
import os

# سحب التوكن من المتغيرات في Railway
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! البوت يعمل الآن بشكل ممتاز.")

# السطر الأهم: يجعل البوت يسمع الرسائل باستمرار
bot.infinity_polling()
