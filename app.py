import telebot
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    # ضع رابط مشروعك في Railway هنا
    # يجب أن يبدأ بـ https://
    web_app = WebAppInfo(url='https://your-app-name.up.railway.app') 
    btn = InlineKeyboardButton(text="START AI", web_app=web_app)
    markup.add(btn)
    
    bot.send_message(message.chat.id, "أهلاً بك! اضغط على الزر أدناه لبدء الشات مع الذكاء الاصطناعي:", reply_markup=markup)

bot.infinity_polling()
