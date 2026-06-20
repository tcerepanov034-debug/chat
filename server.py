from flask import Flask, render_template_string, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ============================================
# БАЗА ДАННЫХ
# ============================================
def init_db():
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            text TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ============================================
# HTML
# ============================================
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📡 Чат</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0b0d15;
            font-family: 'Segoe UI', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .chat {
            width: 100%;
            max-width: 550px;
            background: rgba(255,255,255,0.04);
            border-radius: 24px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.06);
        }
        h1 {
            color: #e8edf5;
            font-size: 20px;
            text-align: center;
            margin-bottom: 4px;
        }
        .sub {
            color: rgba(255,255,255,0.2);
            font-size: 12px;
            text-align: center;
            margin-bottom: 16px;
        }
        .msgs {
            height: 350px;
            overflow-y: auto;
            padding: 10px 0;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .msgs::-webkit-scrollbar { width: 4px; }
        .msgs::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
        .msg {
            max-width: 80%;
            padding: 10px 16px;
            border-radius: 16px;
            font-size: 14px;
            word-break: break-word;
            animation: fade 0.3s ease;
        }
        .msg.own { align-self: flex-end; background: #6366f1; color: #fff; }
        .msg.other { align-self: flex-start; background: rgba(255,255,255,0.06); color: #e8edf5; }
        .msg .name { font-size: 11px; opacity: 0.6; margin-bottom: 2px; }
        .msg .time { font-size: 10px; opacity: 0.4; margin-top: 4px; text-align: right; }
        @keyframes fade { 0% { opacity: 0; transform: translateY(10px); } 100% { opacity: 1; transform: translateY(0); } }
        .input {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255,255,255,0.06);
        }
        .input input {
            flex: 1;
            padding: 12px 16px;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.06);
            background: rgba(255,255,255,0.04);
            color: #e8edf5;
            font-size: 14px;
            outline: none;
        }
        .input input:focus { border-color: rgba(99,102,241,0.3); }
        .input input::placeholder { color: rgba(255,255,255,0.2); }
        .input button {
            padding: 12px 24px;
            border: none;
            border-radius: 14px;
            background: linear-gradient(135deg, #6366f1, #818cf8);
            color: #fff;
            font-weight: 600;
            cursor: pointer;
        }
        .input button:active { transform: scale(0.95); }
        .status {
            text-align: center;
            font-size: 12px;
            color: rgba(255,255,255,0.15);
            margin-top: 10px;
        }
        .name-input {
            display: flex;
            gap: 10px;
            margin-bottom: 12px;
        }
        .name-input input {
            flex: 1;
            padding: 10px 16px;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.06);
            background: rgba(255,255,255,0.04);
            color: #e8edf5;
            font-size: 14px;
            outline: none;
        }
        .name-input input:focus { border-color: rgba(99,102,241,0.3); }
    </style>
</head>
<body>
    <div class="chat">
        <h1>📡 Чат</h1>
        <div class="sub">💬 Сообщения хранятся на сервере</div>

        <div class="name-input">
            <input type="text" id="nameInput" placeholder="Ваше имя" />
        </div>

        <div class="msgs" id="msgs"></div>

        <div class="input">
            <input type="text" id="input" placeholder="Сообщение..." />
            <button onclick="send()">➤</button>
        </div>

        <div class="status" id="status">● Загрузка...</div>
    </div>

    <script>
        let name = localStorage.getItem('chatName') || '';
        if (name) {
            document.getElementById('nameInput').value = name;
        }

        document.getElementById('nameInput').addEventListener('change', function() {
            name = this.value.trim() || 'Аноним';
            localStorage.setItem('chatName', name);
        });

        function loadMessages() {
            fetch('/messages')
                .then(r => r.json())
                .then(data => {
                    const msgs = document.getElementById('msgs');
                    msgs.innerHTML = '';
                    data.forEach(m => {
                        const div = document.createElement('div');
                        div.className = 'msg ' + (m.sender === name ? 'own' : 'other');
                        div.innerHTML = `
                            <div class="name">${m.sender}</div>
                            ${m.text}
                            <div class="time">${m.time}</div>
                        `;
                        msgs.appendChild(div);
                    });
                    msgs.scrollTop = msgs.scrollHeight;
                    document.getElementById('status').innerHTML = '● Сообщений: ' + data.length;
                });
        }

        function send() {
            const input = document.getElementById('input');
            const text = input.value.trim();
            if (!text) return;

            const sender = document.getElementById('nameInput').value.trim() || 'Аноним';

            fetch('/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sender: sender, text: text })
            }).then(() => {
                input.value = '';
                loadMessages();
            });
        }

        document.getElementById('input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') send();
        });

        loadMessages();
        setInterval(loadMessages, 5000);
    </script>
</body>
</html>
'''

# ============================================
# МАРШРУТЫ
# ============================================
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/messages')
def get_messages():
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('SELECT sender, text, timestamp FROM messages ORDER BY id DESC LIMIT 100')
    rows = c.fetchall()
    conn.close()
    return jsonify([{'sender': r[0], 'text': r[1], 'time': r[2]} for r in rows[::-1]])

@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    sender = data.get('sender', 'Аноним')
    text = data.get('text', '')
    if not text:
        return 'empty', 400

    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute(
        'INSERT INTO messages (sender, text, timestamp) VALUES (?, ?, ?)',
        (sender, text, datetime.now().strftime('%H:%M:%S'))
    )
    conn.commit()
    conn.close()
    return 'ok'

# ============================================
# ЗАПУСК
# ============================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
