import telebot
import os
from google import genai
from flask import Flask, send_from_directory, request, jsonify
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')
URL = 'https://telegramaibot-production-522e.up.railway.app'

client = genai.Client(api_key=GEMINI_KEY)
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
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=full_prompt
        )
        return jsonify({'reply': response.text})
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

# ✅ Webhook بدل polling
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200

@app.route('/set_webhook')
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f'{URL}/{TOKEN}')
    return 'Webhook set!', 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    web_app = WebAppInfo(url=URL)
    btn = InlineKeyboardButton(text="START AI", web_app=web_app)
    markup.add(btn)
    bot.send_message(message.chat.id, "أهلاً بك! اضغط على الزر أدناه:", reply_markup=markup)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
