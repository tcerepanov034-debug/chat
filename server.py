from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime
import os
import sys
import base64

app = Flask(__name__)
app.secret_key = 'ultra_secret_key_2026'
socketio = SocketIO(app, cors_allowed_origins="*")

# ============================================
# БАЗА ДАННЫХ
# ============================================
DB_FILE = 'messages.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            text TEXT,
            timestamp TEXT,
            is_voice BOOLEAN DEFAULT 0,
            voice_data TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()
active_users = {}

# ============================================
# HTML — ПРЕМИУМ-ДИЗАЙН
# ============================================
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>💎 Чат</title>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <style>
        /* ===== БАЗА ===== */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
            min-height: 100dvh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 12px;
            margin: 0;
            overflow: hidden;
        }

        /* ===== ПАРАЛЛАКС-ФОН ===== */
        #parallax-bg {
            position: fixed;
            top: -60px;
            left: -60px;
            width: calc(100% + 120px);
            height: calc(100% + 120px);
            background: 
                radial-gradient(ellipse at 20% 30%, rgba(100, 116, 139, 0.08) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 70%, rgba(148, 163, 184, 0.06) 0%, transparent 60%),
                #f5f7fa;
            z-index: 0;
            transition: transform 0.1s ease-out;
            pointer-events: none;
            will-change: transform;
        }

        /* ===== ОСНОВНОЙ БЛОК ===== */
        .chat {
            position: relative;
            z-index: 1;
            width: 100%;
            max-width: 560px;
            height: 94vh;
            height: 94dvh;
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 32px;
            padding: 20px 20px 18px;
            box-shadow: 
                0 20px 60px rgba(0, 0, 0, 0.06),
                0 8px 24px rgba(0, 0, 0, 0.02),
                inset 0 1px 0 rgba(255, 255, 255, 0.6);
            display: flex;
            flex-direction: column;
            animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes fadeUp {
            0% { opacity: 0; transform: translateY(20px) scale(0.97); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }

        /* ===== ШАПКА ===== */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            flex-shrink: 0;
            padding: 0 4px;
        }
        .header h1 {
            font-size: 20px;
            font-weight: 600;
            color: #1e293b;
            letter-spacing: -0.3px;
        }
        .header h1 span {
            color: #64748b;
            font-weight: 400;
        }
        .badge {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: #64748b;
            font-weight: 500;
        }
        .online-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.85); }
        }

        /* ===== ИМЯ ===== */
        .name-row {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
            flex-shrink: 0;
        }
        .name-row input {
            flex: 1;
            padding: 10px 16px;
            border-radius: 16px;
            border: 1.5px solid #e2e8f0;
            background: #f8fafc;
            color: #1e293b;
            font-size: 14px;
            font-weight: 500;
            outline: none;
            min-height: 44px;
            transition: border-color 0.2s;
        }
        .name-row input:focus {
            border-color: #94a3b8;
            background: #ffffff;
        }
        .name-row input::placeholder {
            color: #94a3b8;
            font-weight: 400;
        }

        /* ===== СООБЩЕНИЯ ===== */
        .msgs {
            flex: 1;
            overflow-y: auto;
            padding: 4px 0 8px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            -webkit-overflow-scrolling: touch;
            scroll-behavior: smooth;
            min-height: 0;
        }
        .msgs::-webkit-scrollbar { width: 4px; }
        .msgs::-webkit-scrollbar-track { background: transparent; }
        .msgs::-webkit-scrollbar-thumb { 
            background: #cbd5e1; 
            border-radius: 20px;
        }

        .msg {
            max-width: 82%;
            padding: 10px 16px;
            border-radius: 20px;
            font-size: 15px;
            line-height: 1.5;
            word-break: break-word;
            animation: slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }
        @keyframes slideIn {
            0% { opacity: 0; transform: translateY(8px) scale(0.96); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        .msg.own {
            align-self: flex-end;
            background: #e2e8f0;
            color: #1e293b;
            border-bottom-right-radius: 6px;
        }
        .msg.other {
            align-self: flex-start;
            background: #ffffff;
            color: #1e293b;
            border: 1px solid #f1f5f9;
            border-bottom-left-radius: 6px;
        }
        .msg .name {
            font-size: 12px;
            font-weight: 600;
            color: #64748b;
            margin-bottom: 2px;
            letter-spacing: 0.2px;
        }
        .msg.own .name { color: #475569; }
        .msg .time {
            font-size: 10px;
            color: #94a3b8;
            margin-top: 4px;
            text-align: right;
            font-weight: 400;
        }
        .msg .voice-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #f1f5f9;
            border-radius: 30px;
            padding: 6px 16px 6px 14px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            color: #1e293b;
            border: 1px solid #e2e8f0;
            min-height: 36px;
            transition: background 0.2s;
        }
        .msg .voice-btn:hover { background: #e2e8f0; }
        .msg .voice-btn:active { transform: scale(0.95); }

        /* ===== ПЕЧАТАЕТ ===== */
        .typing-indicator {
            color: #94a3b8;
            font-size: 13px;
            padding: 4px 6px;
            min-height: 28px;
            font-weight: 400;
            flex-shrink: 0;
            letter-spacing: 0.2px;
        }

        /* ===== ВВОД ===== */
        .input-area {
            margin-top: 8px;
            padding-top: 12px;
            border-top: 1px solid #f1f5f9;
            flex-shrink: 0;
        }
        .input-row {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .input-row input[type="text"] {
            flex: 1;
            padding: 12px 18px;
            border-radius: 24px;
            border: 1.5px solid #e2e8f0;
            background: #f8fafc;
            color: #1e293b;
            font-size: 15px;
            outline: none;
            min-height: 50px;
            transition: border-color 0.2s, background 0.2s;
        }
        .input-row input:focus {
            border-color: #94a3b8;
            background: #ffffff;
        }
        .input-row input::placeholder {
            color: #94a3b8;
        }

        .input-row button {
            padding: 0 20px;
            border: none;
            border-radius: 24px;
            background: #1e293b;
            color: #ffffff;
            font-weight: 500;
            font-size: 15px;
            cursor: pointer;
            min-height: 50px;
            min-width: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s;
            box-shadow: 0 2px 8px rgba(30, 41, 59, 0.08);
        }
        .input-row button:active { 
            transform: scale(0.92);
            background: #0f172a;
        }
        .input-row button.voice-btn {
            background: #f1f5f9;
            color: #1e293b;
            font-size: 20px;
            min-width: 50px;
            box-shadow: none;
        }
        .input-row button.voice-btn:active { background: #e2e8f0; }
        .input-row button.voice-btn.recording {
            background: #fee2e2;
            color: #dc2626;
            animation: pulseRed 1s ease-in-out infinite;
        }
        @keyframes pulseRed {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        /* ===== АДАПТИВ ===== */
        @media (max-width: 480px) {
            .chat { 
                padding: 16px 16px 14px; 
                border-radius: 24px;
                height: 98vh;
                height: 98dvh;
            }
            .msg { max-width: 88%; font-size: 14px; }
            .input-row input { font-size: 14px; min-height: 46px; }
            .input-row button { min-height: 46px; min-width: 46px; font-size: 14px; }
        }

        @media (max-width: 380px) {
            .chat { padding: 12px 12px 12px; border-radius: 20px; }
            .msg { font-size: 13px; padding: 8px 12px; }
            .header h1 { font-size: 17px; }
        }

        /* ===== ТЁМНАЯ ТЕМА (по желанию системы) ===== */
        @media (prefers-color-scheme: dark) {
            body { background: #0f172a; }
            #parallax-bg {
                background: 
                    radial-gradient(ellipse at 20% 30%, rgba(100, 116, 139, 0.06) 0%, transparent 60%),
                    radial-gradient(ellipse at 80% 70%, rgba(148, 163, 184, 0.04) 0%, transparent 60%),
                    #0f172a;
            }
            .chat {
                background: rgba(30, 41, 59, 0.85);
                backdrop-filter: blur(20px);
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
            }
            .header h1 { color: #f1f5f9; }
            .header h1 span { color: #94a3b8; }
            .badge { color: #94a3b8; }
            .name-row input {
                background: #1e293b;
                border-color: #334155;
                color: #f1f5f9;
            }
            .name-row input:focus { background: #1e293b; border-color: #64748b; }
            .msg.own { background: #334155; color: #f1f5f9; }
            .msg.other { background: #1e293b; color: #f1f5f9; border-color: #334155; }
            .msg .name { color: #94a3b8; }
            .msg.own .name { color: #94a3b8; }
            .msg .time { color: #64748b; }
            .msg .voice-btn {
                background: #1e293b;
                border-color: #334155;
                color: #f1f5f9;
            }
            .msg .voice-btn:hover { background: #334155; }
            .typing-indicator { color: #64748b; }
            .input-area { border-color: #1e293b; }
            .input-row input {
                background: #1e293b;
                border-color: #334155;
                color: #f1f5f9;
            }
            .input-row input:focus { background: #1e293b; border-color: #64748b; }
            .input-row button { background: #334155; color: #f1f5f9; }
            .input-row button:active { background: #475569; }
            .input-row button.voice-btn {
                background: #1e293b;
                color: #f1f5f9;
            }
            .input-row button.voice-btn:active { background: #334155; }
            .input-row button.voice-btn.recording {
                background: #7f1d1d;
                color: #fca5a5;
            }
        }
    </style>
</head>
<body>
    <div id="parallax-bg"></div>

    <div class="chat">
        <div class="header">
            <h1>💬 Чат <span>•</span></h1>
            <span class="badge">
                <span class="online-dot"></span>
                <span id="onlineCount">0</span>
            </span>
        </div>

        <div class="name-row">
            <input type="text" id="nameInput" placeholder="Ваше имя" inputmode="text" />
        </div>

        <div class="msgs" id="msgs"></div>
        <div class="typing-indicator" id="typingIndicator">✎</div>

        <div class="input-area">
            <div class="input-row">
                <input type="text" id="input" placeholder="Сообщение..." inputmode="text" autocomplete="off" />
                <button onclick="sendMessage()" aria-label="Отправить">→</button>
                <button class="voice-btn" id="voiceBtn" onclick="toggleVoice()" aria-label="Голосовое">🎤</button>
            </div>
        </div>
    </div>

    <script>
        // ============================================
        // ПОЛНАЯ ЛОГИКА
        // ============================================

        // ---- ПАРАЛЛАКС ----
        const isMobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
        const bg = document.getElementById('parallax-bg');

        if (window.DeviceOrientationEvent && isMobile) {
            window.addEventListener('deviceorientation', function(e) {
                const x = (e.gamma || 0) / 45;
                const y = (e.beta || 0) / 45 - 0.5;
                bg.style.transform = `translate(${x * 12}px, ${y * 12}px)`;
            });
        } else {
            document.addEventListener('mousemove', (e) => {
                const x = e.clientX / window.innerWidth - 0.5;
                const y = e.clientY / window.innerHeight - 0.5;
                bg.style.transform = `translate(${x * 18}px, ${y * 18}px)`;
            });
        }

        // ---- SOCKET ----
        const socket = io({
            transports: ['websocket', 'polling'],
            upgrade: true
        });

        let name = localStorage.getItem('chatName') || '';
        let isRecording = false;
        let mediaRecorder = null;
        let audioChunks = [];
        let typingTimeout = null;

        if (name) document.getElementById('nameInput').value = name;

        // ---- ИМЯ ----
        document.getElementById('nameInput').addEventListener('change', function() {
            name = this.value.trim() || 'Аноним';
            localStorage.setItem('chatName', name);
            socket.emit('set_name', name);
        });

        // ---- ПЕЧАТАЕТ ----
        document.getElementById('input').addEventListener('input', function() {
            const isTyping = this.value.length > 0;
            socket.emit('typing', { name: name, isTyping: isTyping });
            clearTimeout(typingTimeout);
            if (isTyping) {
                typingTimeout = setTimeout(() => {
                    socket.emit('typing', { name: name, isTyping: false });
                }, 3000);
            }
        });

        // ---- ОНЛАЙН ----
        socket.on('online_update', (data) => {
            document.getElementById('onlineCount').textContent = data.count || 0;
        });

        socket.on('typing_update', (data) => {
            const el = document.getElementById('typingIndicator');
            if (data.isTyping && data.name && data.name !== name) {
                el.textContent = `✎ ${data.name} печатает...`;
            } else {
                el.textContent = '✎';
            }
        });

        // ---- ЗАГРУЗКА СООБЩЕНИЙ ----
        function loadMessages() {
            fetch('/messages')
                .then(r => r.json())
                .then(data => {
                    const msgs = document.getElementById('msgs');
                    msgs.innerHTML = '';
                    data.forEach(m => {
                        const div = document.createElement('div');
                        div.className = 'msg ' + (m.sender === name ? 'own' : 'other');
                        let content = m.text;
                        if (m.is_voice && m.voice_data) {
                            content = `<span class="voice-btn" onclick="playVoice('${m.voice_data}')">🔊 Голосовое</span>`;
                        }
                        div.innerHTML = `
                            <div class="name">${m.sender}</div>
                            ${content}
                            <div class="time">${m.time}</div>
                        `;
                        msgs.appendChild(div);
                    });
                    const scroller = document.querySelector('.msgs');
                    scroller.scrollTop = scroller.scrollHeight;
                })
                .catch(() => {});
        }

        // ---- ВОСПРОИЗВЕДЕНИЕ ----
        window.playVoice = function(data) {
            try {
                const audio = new Audio('data:audio/webm;base64,' + data);
                audio.play().catch(() => {});
            } catch(e) {}
        };

        // ---- ОТПРАВКА ----
        function sendMessage() {
            const input = document.getElementById('input');
            const text = input.value.trim();
            if (!text) return;
            
            const sender = document.getElementById('nameInput').value.trim() || 'Аноним';
            
            fetch('/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sender, text })
            })
            .then(() => {
                input.value = '';
                socket.emit('typing', { name: sender, isTyping: false });
                if (isMobile && navigator.vibrate) navigator.vibrate(10);
                loadMessages();
            })
            .catch(() => {});
        }

        document.getElementById('input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });

        // ---- ГОЛОСОВЫЕ ----
        function toggleVoice() {
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        }

        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });
                mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                audioChunks = [];
                mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
                mediaRecorder.onstop = () => {
                    const blob = new Blob(audioChunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onload = () => {
                        const base64 = reader.result.split(',')[1];
                        const sender = document.getElementById('nameInput').value.trim() || 'Аноним';
                        fetch('/send_voice', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ sender, voice: base64 })
                        })
                        .then(() => {
                            loadMessages();
                            if (isMobile && navigator.vibrate) navigator.vibrate(10);
                        })
                        .catch(() => {});
                    };
                    reader.readAsDataURL(blob);
                    stream.getTracks().forEach(t => t.stop());
                };
                mediaRecorder.start();
                isRecording = true;
                document.getElementById('voiceBtn').textContent = '⏹';
                document.getElementById('voiceBtn').classList.add('recording');
                if (isMobile && navigator.vibrate) navigator.vibrate(20);
            } catch(e) {
                alert('❌ Нет доступа к микрофону');
            }
        }

        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                document.getElementById('voiceBtn').textContent = '🎤';
                document.getElementById('voiceBtn').classList.remove('recording');
            }
        }

        // ---- СОКЕТЫ ----
        socket.on('connect', () => {
            socket.emit('set_name', name);
            loadMessages();
        });

        socket.on('new_message', () => {
            loadMessages();
        });

        // ---- ПЕРИОДИЧЕСКАЯ ПРОВЕРКА ----
        setInterval(() => {
            socket.emit('ping');
        }, 30000);

        // ---- ИНИЦИАЛИЗАЦИЯ ----
        loadMessages();
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
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT sender, text, timestamp, is_voice, voice_data FROM messages ORDER BY id DESC LIMIT 200')
        rows = c.fetchall()
        conn.close()
        return jsonify([{
            'sender': r[0],
            'text': r[1] if not r[3] else '🎤 Голосовое',
            'time': r[2],
            'is_voice': bool(r[3]),
            'voice_data': r[4] if r[3] else None
        } for r in rows[::-1]])
    except:
        return jsonify([])

@app.route('/send', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        sender = data.get('sender', 'Аноним')
        text = data.get('text', '')
        if not text:
            return 'empty', 400
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT INTO messages (sender, text, timestamp, is_voice) VALUES (?, ?, ?, 0)',
                  (sender, text, datetime.now().strftime('%H:%M:%S')))
        conn.commit()
        conn.close()
        socketio.emit('new_message')
        return 'ok'
    except:
        return 'error', 500

@app.route('/send_voice', methods=['POST'])
def send_voice():
    try:
        data = request.get_json()
        sender = data.get('sender', 'Аноним')
        voice = data.get('voice', '')
        if not voice:
            return 'empty', 400
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT INTO messages (sender, text, timestamp, is_voice, voice_data) VALUES (?, ?, ?, 1, ?)',
                  (sender, '🎤 Голосовое', datetime.now().strftime('%H:%M:%S'), voice))
        conn.commit()
        conn.close()
        socketio.emit('new_message')
        return 'ok'
    except:
        return 'error', 500

# ============================================
# WEBSOCKET
# ============================================
@socketio.on('connect')
def handle_connect():
    active_users[request.sid] = {'name': 'Аноним', 'last_active': datetime.now()}
    emit('online_update', {'count': len(active_users)}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in active_users:
        del active_users[request.sid]
    emit('online_update', {'count': len(active_users)}, broadcast=True)

@socketio.on('set_name')
def handle_set_name(data):
    if request.sid in active_users:
        active_users[request.sid]['name'] = data.get('name', 'Аноним')

@socketio.on('typing')
def handle_typing(data):
    emit('typing_update', data, broadcast=True, include_self=False)

@socketio.on('ping')
def handle_ping():
    if request.sid in active_users:
        active_users[request.sid]['last_active'] = datetime.now()

# ============================================
# ЗАПУСК
# ============================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Запуск на порту {port}")
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False,
        allow_unsafe_werkzeug=True,
        log_output=True
    )