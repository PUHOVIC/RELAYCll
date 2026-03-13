from flask import Flask, request, jsonify, render_template_string
import logging
from datetime import datetime
import threading
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Хранилище сообщений
messages = []  # Список всех сообщений
MAX_MESSAGES = 50  # Храним последние 50 сообщений

# HTML шаблон для телефона
PHONE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            background-color: #9bbb58;
            color: black;
            font-family: monospace;
            font-size: 16px;
            margin: 0;
            padding: 8px;
        }
        .message {
            background-color: #333;
            color: #9bbb58;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
        }
        .message small {
            color: #ccc;
            font-size: 12px;
        }
        .reply-form {
            margin-top: 20px;
        }
        input[type=text] {
            width: 100%;
            padding: 8px;
            margin-bottom: 8px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 10px;
            background-color: #333;
            color: #9bbb58;
            border: none;
            font-size: 16px;
            cursor: pointer;
        }
        button:hover {
            background-color: #444;
        }
        .softkeys {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            display: flex;
            justify-content: space-between;
            padding: 8px;
            background-color: #333;
            color: white;
            font-size: 14px;
        }
        .message-list {
            margin-bottom: 60px;
        }
    </style>
</head>
<body>
    <div class="message-list">
        <h3>Последние сообщения:</h3>
        {% for msg in messages %}
        <div class="message">
            <strong>{{ msg.sender }}:</strong> {{ msg.text }}<br>
            <small>{{ msg.time }}</small>
        </div>
        {% endfor %}
    </div>
    
    <div class="reply-form">
        <form action="/send_reply" method="POST">
            <input type="hidden" name="reply_to" value="{{ reply_to }}">
            <input type="text" name="reply_text" placeholder="Введите ответ..." required>
            <button type="submit">📤 Отправить ответ</button>
        </form>
    </div>
    
    <div class="softkeys">
        <span>Выбрать</span>
        <span>Назад</span>
    </div>
</body>
</html>
"""

@app.route('/incoming', methods=['POST'])
def incoming():
    """Принимает сообщения от Telegram бота"""
    data = request.json
    user_id = data.get('user_id')
    text = data.get('text')
    
    if not user_id or not text:
        return jsonify({"error": "Missing data"}), 400
    
    # Сохраняем сообщение
    messages.append({
        'user_id': user_id,
        'text': text,
        'time': datetime.now().strftime("%H:%M:%S"),
        'direction': 'incoming'
    })
    
    # Ограничиваем размер хранилища
    while len(messages) > MAX_MESSAGES:
        messages.pop(0)
    
    logging.info(f"Received from {user_id}: {text}")
    return jsonify({"status": "ok"}), 200

@app.route('/phone', methods=['GET'])
def phone_view():
    """Страница для телефона - показывает последние 3 сообщения"""
    last_messages = messages[-3:] if messages else []
    return render_template_string(
        PHONE_TEMPLATE, 
        messages=last_messages,
        reply_to=last_messages[-1]['user_id'] if last_messages else ''
    )

@app.route('/send_reply', methods=['POST'])
def send_reply():
    """Принимает ответ от телефона и отправляет боту (который перешлет пользователю)"""
    reply_to = request.form.get('reply_to')
    reply_text = request.form.get('reply_text')
    
    if not reply_to or not reply_text:
        return "Missing data", 400
    
    # Сохраняем исходящее сообщение
    messages.append({
        'user_id': reply_to,
        'text': f"📤 Ответ: {reply_text}",
        'time': datetime.now().strftime("%H:%M:%S"),
        'direction': 'outgoing'
    })
    
    logging.info(f"Reply to {reply_to}: {reply_text}")
    
    # Здесь бот должен будет отправить ответ пользователю
    # Пока просто сохраняем, бот будет забирать через отдельный эндпоинт
    
    return "✅ Ответ отправлен", 200

@app.route('/get_outgoing', methods=['GET'])
def get_outgoing():
    """Эндпоинт для бота - забирает исходящие сообщения для отправки в Telegram"""
    outgoing = []
    for msg in messages:
        if msg.get('direction') == 'outgoing' and not msg.get('sent'):
            outgoing.append({
                'user_id': msg['user_id'],
                'text': msg['text'].replace('📤 Ответ: ', '')
            })
            msg['sent'] = True
    return jsonify(outgoing)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
