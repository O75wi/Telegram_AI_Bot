import telebot
import os
from flask import Flask, send_from_directory
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import threading

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    web_app = WebAppInfo(url='https://telegramaibot-production-522e.up.railway.app') 
    btn = InlineKeyboardButton(text="START AI", web_app=web_app)
    markup.add(btn)
    bot.send_message(message.chat.id, "أهلاً بك! اضغط على الزر أدناه:", reply_markup=markup)

def run_bot():
    bot.infinity_polling()

if name == 'main':
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=8080)
