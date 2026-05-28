import telebot
import os
import google.generativeai as genai
from flask import Flask, send_from_directory, request, jsonify
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import threading

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        history = data.get('history', [])
        
        system = "أنت CodeCraft AI متخصص في توليد أكواد HTML احترافية وتصميم شعارات SVG. رد دائماً بالعربي."
        
        full_prompt = system + "\n\n"
        for h in history:
            role = "المستخدم" if h['role'] == 'user' else "المساعد"
            full_prompt += f"{role}: {h['content']}\n"
        full_prompt += f"المستخدم: {message}"
        
        response = model.generate_content(full_prompt)
        return jsonify({'reply': response.text})
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    web_app = WebAppInfo(url='https://telegramaibot-production-522e.up.railway.app')
    btn = InlineKeyboardButton(text="START AI", web_app=web_app)
    markup.add(btn)
    bot.send_message(message.chat.id, "أهلاً بك! اضغط على الزر أدناه:", reply_markup=markup)

# ✅ هذا يشتغل دائماً على Railway
threading.Thread(target=bot.infinity_polling, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
