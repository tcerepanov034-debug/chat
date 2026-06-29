from flask import Flask, render_template_string, request, jsonify, session
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime, timedelta
import base64
import requests
import json
import os
import time

app = Flask(__name__)
app.secret_key = 'ultra_secret_key_2026'
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)

# ============================================
# КОНФИГ
# ============================================
DB_FILE = 'messages.db'
MAX_MESSAGES = 1000
BACKUP_CHAT_ID = 'YOUR_CHAT_ID'      # ЗАМЕНИТЬ
BOT_TOKEN = 'YOUR_BOT_TOKEN'         # ЗАМЕНИТЬ

active_users = {}
last_activity = {}  # для энергосбережения

# ============================================
# БАЗА ДАННЫХ
# ============================================
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
            voice_data TEXT,
            ip TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            name TEXT PRIMARY KEY,
            last_seen TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ============================================
# HTML (МОБИЛЬНАЯ ОПТИМИЗАЦИЯ)
# ============================================
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="theme-color" content="#0b0d15">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>🚀 Ультра-Чат (Mobile)</title>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <style>
        /* ===== БАЗА ===== */
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
            -webkit-tap-highlight-color: transparent;
            -webkit-touch-callout: none;
        }
        body {
            font-family: -apple-system, 'Segoe UI', Roboto, sans-serif;
            background: #0b0d15;
            min-height: 100vh;
            min-height: 100dvh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px;
            overflow: hidden;
            touch-action: pan-y;
        }
        
        /* ===== ПАРАЛЛАКС (упрощён для мобил) ===== */
        #parallax-bg {
            position: fixed;
            top: -30px;
            left: -30px;
            width: calc(100% + 60px);
            height: calc(100% + 60px);
            background: 
                radial-gradient(circle at 20% 30%, rgba(99,102,241,0.12) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(236,72,153,0.08) 0%, transparent 50%),
                #0b0d15;
            z-index: 0;
            transition: transform 0.15s ease-out;
            pointer-events: none;
            will-change: transform;
        }
        
        .chat {
            position: relative;
            z-index: 1;
            width: 100%;
            max-width: 550px;
            height: 95vh;
            height: 95dvh;
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 28px;
            padding: 16px 16px 20px;
            border: 1px solid rgba(255,255,255,0.06);
            box-shadow: 0 20px 60px rgba(0,0,0,0.7);
            display: flex;
            flex-direction: column;
            animation: fadeIn 0.5s ease;
        }
        @keyframes fadeIn {
            0% { opacity: 0; transform: scale(0.97); }
            100% { opacity: 1; transform: scale(1); }
        }

        /* ===== ШАПКА ===== */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            flex-shrink: 0;
        }
        .header h1 {
            color: #e8edf5;
            font-size: clamp(18px, 4.5vw, 22px);
            font-weight: 700;
            letter-spacing: 1px;
            text-shadow: 0 0 30px rgba(99,102,241,0.2);
        }
        .header .badge {
            display: flex;
            align-items: center;
            gap: 6px;
            color: rgba(255,255,255,0.3);
            font-size: clamp(11px, 2.5vw, 13px);
        }
        .online-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.85); }
            100% { opacity: 1; transform: scale(1); }
        }

        /* ===== ИМЯ ===== */
        .name-row {
            display: flex;
            gap: 8px;
            margin-bottom: 8px;
            flex-shrink: 0;
        }
        .name-row input {
            flex: 1;
            padding: 10px 14px;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.06);
            background: rgba(255,255,255,0.04);
            color: #e8edf5;
            font-size: clamp(14px, 3.2vw, 16px);
            outline: none;
            min-height: 44px;
            -webkit-appearance: none;
        }
        .name-row input:focus { border-color: rgba(99,102,241,0.3); }
        .name-row input::placeholder { color: rgba(255,255,255,0.15); }

        /* ===== СООБЩЕНИЯ ===== */
        .msgs {
            flex: 1;
            overflow-y: auto;
            padding: 6px 0 4px;
            display: flex;
            flex-direction: column;
            gap: 5px;
            -webkit-overflow-scrolling: touch;
            scroll-behavior: smooth;
            min-height: 0;
        }
        .msgs::-webkit-scrollbar { width: 3px; }
        .msgs::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 4px; }

        .msg {
            max-width: 85%;
            padding: 9px 14px;
            border-radius: 18px;
            font-size: clamp(14px, 3vw, 16px);
            word-break: break-word;
            animation: slideUp 0.25s ease;
            touch-action: manipulation;
        }
        @keyframes slideUp {
            0% { opacity: 0; transform: translateY(10px) scale(0.96); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        .msg.own { 
            align-self: flex-end; 
            background: #6366f1; 
            color: #fff;
            border-bottom-right-radius: 4px;
        }
        .msg.other { 
            align-self: flex-start; 
            background: rgba(255,255,255,0.06); 
            color: #e8edf5;
            border-bottom-left-radius: 4px;
        }
        .msg .name { 
            font-size: clamp(10px, 2vw, 12px); 
            opacity: 0.5; 
            margin-bottom: 1px;
            font-weight: 500;
        }
        .msg .time { 
            font-size: clamp(9px, 1.8vw, 11px); 
            opacity: 0.25; 
            margin-top: 3px; 
            text-align: right;
        }
        .msg .voice-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,255,255,0.08);
            border-radius: 30px;
            padding: 6px 14px;
            cursor: pointer;
            font-size: clamp(13px, 2.8vw, 15px);
            border: 1px solid rgba(255,255,255,0.05);
            touch-action: manipulation;
            min-height: 38px;
        }
        .msg .voice-btn:active { transform: scale(0.95); }

        /* ===== ПЕЧАТАЕТ ===== */
        .typing-indicator {
            color: rgba(255,255,255,0.15);
            font-size: clamp(11px, 2.2vw, 13px);
            padding: 2px 6px;
            min-height: 24px;
            font-style: italic;
            flex-shrink: 0;
        }

        /* ===== ВВОД ===== */
        .input-area {
            margin-top: 6px;
            padding-top: 8px;
            border-top: 1px solid rgba(255,255,255,0.04);
            flex-shrink: 0;
        }
        .input-row {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .input-row input[type="text"] {
            flex: 1;
            padding: 12px 16px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.06);
            background: rgba(255,255,255,0.04);
            color: #e8edf5;
            font-size: clamp(15px, 3.2vw, 17px);
            outline: none;
            min-height: 48px;
            -webkit-appearance: none;
        }
        .input-row input:focus { border-color: rgba(99,102,241,0.25); }
        .input-row input::placeholder { color: rgba(255,255,255,0.12); }

        .input-row button {
            padding: 12px 18px;
            border: none;
            border-radius: 16px;
            background: linear-gradient(135deg, #6366f1, #818cf8);
            color: #fff;
            font-weight: 600;
            cursor: pointer;
            transition: 0.15s;
            min-height: 48px;
            min-width: 48px;
            font-size: clamp(16px, 3.5vw, 20px);
            touch-action: manipulation;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .input-row button:active { transform: scale(0.92); }
        .input-row button.voice-btn {
            background: rgba(255,255,255,0.05);
            color: #e8edf5;
            font-size: clamp(18px, 4vw, 22px);
            padding: 12px 14px;
        }
        .input-row button.voice-btn.recording {
            background: #ef4444;
            animation: flash 0.6s infinite;
        }
        @keyframes flash {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        /* ===== АДАПТИВ ===== */
        @media (max-width: 480px) {
            .chat { 
                padding: 12px 12px 16px; 
                border-radius: 20px;
                height: 98vh;
                height: 98dvh;
            }
            .msg { max-width: 90%; }
            .input-row input[type="text"] { padding: 10px 14px; min-height: 44px; }
            .input-row button { min-height: 44px; min-width: 44px; padding: 10px 14px; }
        }

        @media (max-width: 380px) {
            .chat { padding: 8px 8px 12px; border-radius: 16px; }
            .msg { font-size: 13px; padding: 7px 12px; }
        }

        @media (orientation: landscape) and (max-height: 500px) {
            .chat { height: 98vh; height: 98dvh; }
            .msgs { max-height: 40vh; }
            .header h1 { font-size: 16px; }
        }

        /* ===== ПОДДЕРЖКА ТЕМНЫХ РЕЖИМОВ ===== */
        @media (prefers-color-scheme: light) {
            body { background: #f0f2f5; }
            .chat { background: rgba(255,255,255,0.85); border-color: rgba(0,0,0,0.06); }
            .header h1 { color: #1a1a2e; }
            .msg.other { background: rgba(0,0,0,0.05); color: #1a1a2e; }
            .name-row input, .input-row input[type="text"] {
                background: rgba(0,0,0,0.03);
                color: #1a1a2e;
            }
            .typing-indicator { color: rgba(0,0,0,0.2); }
            .input-row button.voice-btn { background: rgba(0,0,0,0.04); color: #1a1a2e; }
        }
    </style>
</head>
<body>
    <div id="parallax-bg"></div>

    <div class="chat">
        <!-- ШАПКА -->
        <div class="header">
            <h1>⚡ Чат</h1>
            <span class="badge">
                <span class="online-dot"></span>
                <span id="onlineCount">0</span>
            </span>
        </div>

        <!-- ИМЯ -->
        <div class="name-row">
            <input type="text" id="nameInput" placeholder="Ваше имя" inputmode="text" autocomplete="username" />
        </div>

        <!-- СООБЩЕНИЯ -->
        <div class="msgs" id="msgs"></div>
        <div class="typing-indicator" id="typingIndicator">✎</div>

        <!-- ВВОД -->
        <div class="input-area">
            <div class="input-row">
                <input type="text" id="input" placeholder="Сообщение..." inputmode="text" autocomplete="off" />
                <button onclick="sendMessage()" aria-label="Отправить">➤</button>
                <button class="voice-btn" id="voiceBtn" onclick="toggleVoice()" aria-label="Голосовое">🎤</button>
            </div>
        </div>
    </div>

    <script>
        // ============================================
        // ПОЛНАЯ МОБИЛЬНАЯ ВЕРСИЯ
        // ============================================

        // ---- ПАРАЛЛАКС (мобильный с гироскопом) ----
        let isMobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
        
        if (window.DeviceOrientationEvent && isMobile) {
            window.addEventListener('deviceorientation', function(e) {
                const x = (e.gamma || 0) / 45;
                const y = (e.beta || 0) / 45 - 0.5;
                document.getElementById('parallax-bg').style.transform = `translate(${x * 15}px, ${y * 15}px)`;
            });
        } else {
            document.addEventListener('mousemove', (e) => {
                const x = e.clientX / window.innerWidth - 0.5;
                const y = e.clientY / window.innerHeight - 0.5;
                document.getElementById('parallax-bg').style.transform = `translate(${x * 20}px, ${y * 20}px)`;
            });
        }

        // ---- СКРОЛЛ ПРИ ОТКРЫТИИ КЛАВИАТУРЫ (мобилы) ----
        if (isMobile) {
            window.addEventListener('focusin', (e) => {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                    setTimeout(() => {
                        document.querySelector('.msgs').scrollTop = document.querySelector('.msgs').scrollHeight;
                    }, 300);
                }
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
        let lastMessageTime = 0;

        if (name) document.getElementById('nameInput').value = name;

        // ---- ИМЯ ----
        document.getElementById('nameInput').addEventListener('change', function() {
            name = this.value.trim() || 'Аноним';
            localStorage.setItem('chatName', name);
            socket.emit('set_name', name);
        });

        // ---- ПЕЧАТАЕТ (с таймаутом) ----
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
                });
        }

        // ---- ВОСПРОИЗВЕДЕНИЕ ГОЛОСОВОГО ----
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
            }).then(() => {
                input.value = '';
                socket.emit('typing', { name: sender, isTyping: false });
                // Вибрация на мобилках
                if (isMobile && navigator.vibrate) navigator.vibrate(10);
                loadMessages();
            });
        }

        document.getElementById('input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });

        // ---- ГОЛОСОВЫЕ (мобильная оптимизация) ----
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
                        }).then(() => {
                            loadMessages();
                            if (isMobile && navigator.vibrate) navigator.vibrate(10);
                        });
                    };
                    reader.readAsDataURL(blob);
                    stream.getTracks().forEach(t => t.stop());
                };
                mediaRecorder.start();
                isRecording = true;
                document.getElementById('voiceBtn').textContent = '⏹';
                document.getElementById('voiceBtn').classList.add('recording');
                
                // Вибрация при старте записи
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

        // ---- БЛОКИРОВКА ДВОЙНОГО ЗУМА (iOS) ----
        document.addEventListener('gesturestart', function(e) { e.preventDefault(); });
    </script>
</body>
</html>
'''

# ============================================
# МАРШРУТЫ (БЕЗ ИЗМЕНЕНИЙ)
# ============================================
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/messages')
def get_messages():
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

@app.route('/send', methods=['POST'])
def send_message():
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
    check_and_cleanup()
    socketio.emit('new_message')
    return 'ok'

@app.route('/send_voice', methods=['POST'])
def send_voice():
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
    check_and_cleanup()
    socketio.emit('new_message')
    return 'ok'

# ============================================
# АВТО-ОЧИСТКА + РЕЗЕРВ
# ============================================
def backup_to_telegram(messages):
    if not BOT_TOKEN or 'YOUR_BOT_TOKEN' in BOT_TOKEN:
        return
    text = "📦 Резервная копия чата:\n\n"
    for m in messages[:50]:
        text += f"[{m[2]}] {m[0]}: {m[1][:100]}\n"
    if len(text) > 4000:
        text = text[:4000] + "\n...обрезано"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': BACKUP_CHAT_ID, 'text': text})
    except:
        pass

def check_and_cleanup():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM messages')
    count = c.fetchone()[0]
    if count > MAX_MESSAGES:
        c.execute('SELECT sender, text, timestamp FROM messages ORDER BY id ASC LIMIT ?', (MAX_MESSAGES // 2,))
        old = c.fetchall()
        if old:
            backup_to_telegram(old)
        c.execute('DELETE FROM messages WHERE id IN (SELECT id FROM messages ORDER BY id ASC LIMIT ?)', (MAX_MESSAGES // 2,))
        conn.commit()
    conn.close()

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
        active_users[request.sid]['last_active'] = datetime.now()

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
    print("🚀 Ультра-Чат (Mobile Ready) запущен на http://0.0.0.0:5000")
    print("📱 Поддержка телефонов: Android, iOS (Safari/Chrome)")
    print("🎤 Голосовые: работают на мобильных браузерах")
    print("⚡ Параллакс: гироскоп на телефонах, мышь на ПК")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)