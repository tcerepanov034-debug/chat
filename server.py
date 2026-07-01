from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime
import os
import json

app = Flask(__name__)
app.secret_key = 'ultra_secret_key_2026'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
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
            voice_data TEXT,
            is_image BOOLEAN DEFAULT 0,
            image_data TEXT,
            is_sticker BOOLEAN DEFAULT 0,
            sticker_emoji TEXT,
            reactions TEXT DEFAULT '{}',
            edited BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()
active_users = {}

# ============================================
# HTML
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
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, sans-serif;
            background: #f0f2f5;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px;
            overflow: hidden;
        }
        #parallax-bg {
            position: fixed;
            top: -60px;
            left: -60px;
            width: calc(100% + 120px);
            height: calc(100% + 120px);
            background: 
                radial-gradient(ellipse at 20% 30%, rgba(100,116,139,0.06) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 70%, rgba(148,163,184,0.04) 0%, transparent 60%),
                #f0f2f5;
            z-index: 0;
            transition: transform 0.1s ease-out;
            pointer-events: none;
        }
        .chat {
            position: relative;
            z-index: 1;
            width: 100%;
            max-width: 560px;
            height: 94vh;
            background: rgba(255,255,255,0.92);
            backdrop-filter: blur(20px);
            border-radius: 32px;
            padding: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.06);
            display: flex;
            flex-direction: column;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-shrink: 0;
        }
        .header h1 {
            font-size: 20px;
            font-weight: 600;
            color: #1e293b;
        }
        .badge {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: #64748b;
        }
        .online-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity:1; transform:scale(1); }
            50% { opacity:0.5; transform:scale(0.85); }
        }
        .name-row {
            display: flex;
            gap: 8px;
            margin-bottom: 10px;
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
            outline: none;
            min-height: 44px;
        }
        .name-row input:focus { border-color: #94a3b8; }
        .msgs {
            flex: 1;
            overflow-y: auto;
            padding: 6px 0;
            display: flex;
            flex-direction: column;
            gap: 4px;
            min-height: 0;
        }
        .msgs::-webkit-scrollbar { width: 4px; }
        .msgs::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 20px; }
        .msg-wrapper {
            display: flex;
            flex-direction: column;
            animation: slideIn 0.25s ease;
        }
        @keyframes slideIn {
            0% { opacity:0; transform:translateY(8px); }
            100% { opacity:1; transform:translateY(0); }
        }
        .msg {
            max-width: 82%;
            padding: 8px 14px;
            border-radius: 18px;
            font-size: 15px;
            line-height: 1.5;
            word-break: break-word;
            cursor: pointer;
            position: relative;
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
        .msg .sender-name {
            font-size: 12px;
            font-weight: 600;
            color: #64748b;
            margin-bottom: 2px;
        }
        .msg .time {
            font-size: 10px;
            color: #94a3b8;
            margin-top: 3px;
            text-align: right;
        }
        .msg .sticker {
            font-size: 48px;
            display: block;
            text-align: center;
            padding: 4px 0;
        }
        .msg .voice-circle {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: rgba(0,0,0,0.04);
            border-radius: 30px;
            padding: 4px 16px 4px 12px;
            min-height: 36px;
            cursor: pointer;
        }
        .msg .voice-circle .wave {
            display: flex;
            align-items: center;
            gap: 2px;
            height: 20px;
        }
        .msg .voice-circle .wave span {
            display: block;
            width: 3px;
            background: #64748b;
            border-radius: 2px;
            animation: wave 1s infinite;
        }
        .msg .voice-circle .wave span:nth-child(1) { height: 8px; animation-delay: 0s; }
        .msg .voice-circle .wave span:nth-child(2) { height: 14px; animation-delay: 0.2s; }
        .msg .voice-circle .wave span:nth-child(3) { height: 10px; animation-delay: 0.4s; }
        .msg .voice-circle .wave span:nth-child(4) { height: 18px; animation-delay: 0.1s; }
        .msg .voice-circle .wave span:nth-child(5) { height: 12px; animation-delay: 0.3s; }
        @keyframes wave {
            0%, 100% { transform: scaleY(0.4); }
            50% { transform: scaleY(1); }
        }
        .reactions {
            display: flex;
            gap: 4px;
            margin-top: 3px;
            flex-wrap: wrap;
        }
        .reaction-btn {
            font-size: 16px;
            cursor: pointer;
            padding: 2px 6px;
            border-radius: 12px;
            background: rgba(0,0,0,0.04);
            border: none;
        }
        .msg-menu {
            position: fixed;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
            padding: 8px 0;
            min-width: 180px;
            z-index: 1000;
            display: none;
            border: 1px solid #f1f5f9;
        }
        .msg-menu-item {
            padding: 10px 20px;
            font-size: 14px;
            color: #1e293b;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            border: none;
            background: none;
            width: 100%;
            text-align: left;
        }
        .msg-menu-item:hover { background: #f1f5f9; }
        .msg-menu-item.danger { color: #ef4444; }
        .typing-indicator {
            color: #94a3b8;
            font-size: 13px;
            padding: 4px 6px;
            min-height: 28px;
            flex-shrink: 0;
        }
        .input-area {
            margin-top: 6px;
            padding-top: 10px;
            border-top: 1px solid #f1f5f9;
            flex-shrink: 0;
        }
        .input-row {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .input-row input {
            flex: 1;
            padding: 12px 18px;
            border-radius: 24px;
            border: 1.5px solid #e2e8f0;
            background: #f8fafc;
            color: #1e293b;
            font-size: 15px;
            outline: none;
            min-height: 48px;
        }
        .input-row input:focus { border-color: #94a3b8; }
        .input-row .icon-btn {
            background: #f1f5f9;
            border: none;
            border-radius: 24px;
            color: #1e293b;
            font-size: 18px;
            cursor: pointer;
            min-height: 48px;
            min-width: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .input-row .icon-btn:active { transform: scale(0.92); }
        .input-row .send-btn {
            padding: 0 20px;
            border: none;
            border-radius: 24px;
            background: #1e293b;
            color: #fff;
            font-weight: 500;
            font-size: 15px;
            cursor: pointer;
            min-height: 48px;
            min-width: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .input-row .send-btn:active { transform: scale(0.92); }
        .voice-panel {
            display: flex;
            justify-content: center;
            margin-top: 4px;
        }
        .voice-circle-btn {
            display: flex;
            align-items: center;
            gap: 12px;
            background: #f1f5f9;
            border: none;
            border-radius: 40px;
            padding: 8px 20px;
            cursor: pointer;
            min-height: 44px;
            user-select: none;
            transition: all 0.2s;
        }
        .voice-circle-btn .voice-icon { font-size: 18px; }
        .voice-circle-btn .voice-label {
            font-size: 13px;
            color: #64748b;
            font-weight: 500;
        }
        .voice-circle-btn.recording {
            background: #fee2e2;
            animation: pulseRed 1s infinite;
        }
        @keyframes pulseRed {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        #fileInput { display: none; }

        /* ===== КРУЖОК ЗАПИСИ ===== */
        .tg-voice-circle {
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            display: none;
            align-items: center;
            gap: 20px;
            background: rgba(30, 41, 59, 0.9);
            backdrop-filter: blur(20px);
            padding: 16px 24px 16px 20px;
            border-radius: 60px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .tg-circle-pulse {
            position: absolute;
            top: -8px;
            left: -8px;
            right: -8px;
            bottom: -8px;
            border-radius: 60px;
            border: 2px solid rgba(239,68,68,0.3);
            animation: pulseCircle 1.5s infinite;
        }
        @keyframes pulseCircle {
            0% { transform: scale(1); opacity: 1; }
            100% { transform: scale(1.3); opacity: 0; }
        }
        .tg-circle-inner {
            display: flex;
            align-items: center;
            gap: 16px;
            position: relative;
            z-index: 1;
        }
        .tg-wave {
            display: flex;
            align-items: center;
            gap: 3px;
            height: 24px;
        }
        .tg-wave span {
            display: block;
            width: 4px;
            background: #ef4444;
            border-radius: 2px;
            animation: tgWave 0.8s infinite;
        }
        .tg-wave span:nth-child(1) { height: 8px; animation-delay: 0s; }
        .tg-wave span:nth-child(2) { height: 16px; animation-delay: 0.1s; }
        .tg-wave span:nth-child(3) { height: 22px; animation-delay: 0.2s; }
        .tg-wave span:nth-child(4) { height: 16px; animation-delay: 0.3s; }
        .tg-wave span:nth-child(5) { height: 8px; animation-delay: 0.4s; }
        @keyframes tgWave {
            0%, 100% { transform: scaleY(0.3); }
            50% { transform: scaleY(1); }
        }
        .tg-voice-timer {
            color: #fff;
            font-size: 16px;
            font-weight: 600;
            min-width: 40px;
        }
        .tg-cancel-btn {
            background: rgba(255,255,255,0.1);
            border: none;
            border-radius: 50%;
            color: #fff;
            font-size: 16px;
            cursor: pointer;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* ===== СТИКЕР-ПАНЕЛЬ (появляется по кнопке) ===== */
        .sticker-panel {
            display: none;
            gap: 8px;
            padding: 10px;
            flex-wrap: wrap;
            justify-content: center;
            background: #ffffff;
            border-radius: 16px;
            margin-top: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border: 1px solid #f1f5f9;
            animation: slideUp 0.3s ease;
        }
        .sticker-panel.open {
            display: flex;
        }
        @keyframes slideUp {
            0% { opacity:0; transform:translateY(10px); }
            100% { opacity:1; transform:translateY(0); }
        }
        .sticker-btn {
            font-size: 32px;
            padding: 6px 10px;
            border: none;
            background: #f8fafc;
            border-radius: 12px;
            cursor: pointer;
            transition: transform 0.15s, background 0.15s;
        }
        .sticker-btn:hover {
            transform: scale(1.15);
            background: #f1f5f9;
        }
        .sticker-btn:active { transform: scale(0.9); }
        .sticker-toggle-btn {
            background: #f1f5f9;
            border: none;
            border-radius: 24px;
            color: #1e293b;
            font-size: 20px;
            cursor: pointer;
            min-height: 48px;
            min-width: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }
        .sticker-toggle-btn:active { transform: scale(0.92); }
        .sticker-toggle-btn.active {
            background: #e2e8f0;
        }

        @media (max-width: 480px) {
            .chat { padding: 12px; height: 98vh; }
            .msg { max-width: 88%; font-size: 14px; }
            .sticker-btn { font-size: 28px; }
            .tg-voice-circle { bottom: 80px; padding: 12px 16px; }
        }
        @media (prefers-color-scheme: dark) {
            body { background: #0f172a; }
            #parallax-bg {
                background: radial-gradient(ellipse at 20% 30%, rgba(100,116,139,0.06) 0%, transparent 60%),
                            radial-gradient(ellipse at 80% 70%, rgba(148,163,184,0.04) 0%, transparent 60%),
                            #0f172a;
            }
            .chat { background: rgba(30,41,59,0.92); }
            .header h1 { color: #f1f5f9; }
            .badge { color: #94a3b8; }
            .name-row input { background: #1e293b; border-color: #334155; color: #f1f5f9; }
            .msg.own { background: #334155; color: #f1f5f9; }
            .msg.other { background: #1e293b; color: #f1f5f9; border-color: #334155; }
            .msg .sender-name { color: #94a3b8; }
            .msg .time { color: #64748b; }
            .input-row input { background: #1e293b; border-color: #334155; color: #f1f5f9; }
            .input-row .icon-btn { background: #1e293b; color: #f1f5f9; }
            .input-row .send-btn { background: #334155; color: #f1f5f9; }
            .voice-circle-btn { background: #1e293b; }
            .voice-circle-btn .voice-label { color: #94a3b8; }
            .sticker-toggle-btn { background: #1e293b; color: #f1f5f9; }
            .sticker-panel { background: #1e293b; border-color: #334155; }
            .sticker-btn { background: #334155; color: #f1f5f9; }
            .sticker-btn:hover { background: #475569; }
            .msg-menu { background: #1e293b; border-color: #334155; }
            .msg-menu-item { color: #f1f5f9; }
            .msg-menu-item:hover { background: #334155; }
            .tg-voice-circle { background: rgba(15,23,42,0.95); border-color: #334155; }
        }
    </style>
</head>
<body>
    <div id="parallax-bg"></div>
    <div class="chat">
        <div class="header">
            <h1>💬 Чат</h1>
            <span class="badge">
                <span class="online-dot"></span>
                <span id="onlineCount">0</span>
            </span>
        </div>
        <div class="name-row">
            <input type="text" id="nameInput" placeholder="Ваше имя" />
        </div>
        <div class="msgs" id="msgs"></div>
        <div class="typing-indicator" id="typingIndicator">✎</div>
        <div class="input-area">
            <div class="input-row">
                <input type="text" id="input" placeholder="Сообщение..." />
                <button class="sticker-toggle-btn" id="stickerToggle" onclick="toggleStickers()">😊</button>
                <button class="icon-btn" onclick="document.getElementById('fileInput').click()">📷</button>
                <button onclick="sendMessage()" class="send-btn">→</button>
            </div>
            <div class="sticker-panel" id="stickerPanel">
                <button class="sticker-btn" onclick="sendSticker('😊')">😊</button>
                <button class="sticker-btn" onclick="sendSticker('😂')">😂</button>
                <button class="sticker-btn" onclick="sendSticker('🔥')">🔥</button>
                <button class="sticker-btn" onclick="sendSticker('💀')">💀</button>
                <button class="sticker-btn" onclick="sendSticker('❤️')">❤️</button>
                <button class="sticker-btn" onclick="sendSticker('🎉')">🎉</button>
                <button class="sticker-btn" onclick="sendSticker('🤣')">🤣</button>
                <button class="sticker-btn" onclick="sendSticker('🙈')">🙈</button>
                <button class="sticker-btn" onclick="sendSticker('💪')">💪</button>
                <button class="sticker-btn" onclick="sendSticker('🤩')">🤩</button>
                <button class="sticker-btn" onclick="sendSticker('🥳')">🥳</button>
                <button class="sticker-btn" onclick="sendSticker('😎')">😎</button>
            </div>
            <div class="voice-panel">
                <button class="voice-circle-btn" id="voiceBtn">
                    <span class="voice-icon">🎤</span>
                    <span class="voice-label">Нажми и говори</span>
                </button>
            </div>
            <input type="file" id="fileInput" accept="image/*" multiple />
        </div>
    </div>

    <div class="msg-menu" id="msgMenu">
        <button class="msg-menu-item" onclick="editMessage()">✏️ Редактировать</button>
        <button class="msg-menu-item danger" onclick="deleteMessage()">🗑️ Удалить</button>
        <button class="msg-menu-item" onclick="replyToMessage()">↩️ Ответить</button>
    </div>

    <div class="tg-voice-circle" id="tgVoiceCircle">
        <div class="tg-circle-pulse"></div>
        <div class="tg-circle-inner">
            <div class="tg-wave">
                <span></span><span></span><span></span><span></span><span></span>
            </div>
            <span class="tg-voice-timer" id="voiceTimer">0:00</span>
        </div>
        <button class="tg-cancel-btn" onclick="stopRecording(true)">✕</button>
    </div>

    <script>
        const socket = io();
        let name = localStorage.getItem('chatName') || '';
        let isRecording = false;
        let mediaRecorder = null;
        let audioChunks = [];
        let typingTimeout = null;
        let voiceStartTime = null;
        let voiceTimerInterval = null;
        let selectedMsgId = null;
        let selectedMsgText = '';

        if (name) document.getElementById('nameInput').value = name;

        // ===== ПАРАЛЛАКС =====
        const isMobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
        const bg = document.getElementById('parallax-bg');
        if (window.DeviceOrientationEvent && isMobile) {
            window.addEventListener('deviceorientation', (e) => {
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

        // ===== ИМЯ =====
        document.getElementById('nameInput').addEventListener('change', function() {
            name = this.value.trim() || 'Аноним';
            localStorage.setItem('chatName', name);
            socket.emit('set_name', name);
        });

        // ===== ПЕЧАТАЕТ =====
        document.getElementById('input').addEventListener('input', function() {
            socket.emit('typing', { name, isTyping: this.value.length > 0 });
            clearTimeout(typingTimeout);
            if (this.value.length > 0) {
                typingTimeout = setTimeout(() => {
                    socket.emit('typing', { name, isTyping: false });
                }, 3000);
            }
        });

        // ===== СТИКЕРЫ (по кнопке) =====
        function toggleStickers() {
            const panel = document.getElementById('stickerPanel');
            const btn = document.getElementById('stickerToggle');
            panel.classList.toggle('open');
            btn.classList.toggle('active');
        }

        function sendSticker(emoji) {
            const sender = document.getElementById('nameInput').value.trim() || 'Аноним';
            fetch('/send_sticker', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sender, emoji })
            }).then(() => {
                loadMessages();
                // Закрываем панель после отправки
                document.getElementById('stickerPanel').classList.remove('open');
                document.getElementById('stickerToggle').classList.remove('active');
            });
        }

        // ===== ЗАГРУЗКА СООБЩЕНИЙ =====
        function loadMessages() {
            fetch('/messages')
                .then(r => r.json())
                .then(data => {
                    const msgs = document.getElementById('msgs');
                    msgs.innerHTML = '';
                    data.forEach(m => {
                        const wrapper = document.createElement('div');
                        wrapper.className = 'msg-wrapper';
                        const div = document.createElement('div');
                        div.className = 'msg ' + (m.sender === name ? 'own' : 'other');
                        div.dataset.msgId = m.id;

                        const nameDiv = document.createElement('div');
                        nameDiv.className = 'sender-name';
                        nameDiv.textContent = m.sender;
                        div.appendChild(nameDiv);

                        const contentDiv = document.createElement('div');
                        if (m.is_sticker) {
                            const sticker = document.createElement('span');
                            sticker.className = 'sticker';
                            sticker.textContent = m.sticker_emoji;
                            contentDiv.appendChild(sticker);
                        }
                        if (m.is_image && m.image_data) {
                            const img = document.createElement('img');
                            img.className = 'msg-image';
                            img.src = 'data:image/jpeg;base64,' + m.image_data;
                            img.style.maxWidth = '100%';
                            img.style.maxHeight = '300px';
                            img.style.borderRadius = '12px';
                            contentDiv.appendChild(img);
                        }
                        if (m.is_voice && m.voice_data) {
                            const voiceDiv = document.createElement('div');
                            voiceDiv.className = 'voice-circle';
                            voiceDiv.onclick = () => {
                                const audio = new Audio('data:audio/webm;base64,' + m.voice_data);
                                audio.play();
                            };
                            voiceDiv.innerHTML = `
                                <span>🔊</span>
                                <div class="wave">
                                    <span></span><span></span><span></span><span></span><span></span>
                                </div>
                                <span class="duration">0:03</span>
                            `;
                            contentDiv.appendChild(voiceDiv);
                        }
                        if (m.text && !m.is_sticker && !m.is_voice) {
                            const textSpan = document.createElement('span');
                            textSpan.textContent = m.text;
                            contentDiv.appendChild(textSpan);
                        }
                        div.appendChild(contentDiv);

                        const timeDiv = document.createElement('div');
                        timeDiv.className = 'time';
                        timeDiv.textContent = m.time;
                        div.appendChild(timeDiv);

                        const reactionsDiv = document.createElement('div');
                        reactionsDiv.className = 'reactions';
                        const reactions = m.reactions || {};
                        ['❤️', '👍', '😂', '😮', '😢'].forEach(emoji => {
                            const btn = document.createElement('button');
                            btn.className = 'reaction-btn';
                            btn.textContent = emoji + (reactions[emoji] || '');
                            btn.onclick = (e) => {
                                e.stopPropagation();
                                toggleReaction(m.id, emoji);
                            };
                            reactionsDiv.appendChild(btn);
                        });
                        div.appendChild(reactionsDiv);

                        div.oncontextmenu = (e) => {
                            e.preventDefault();
                            showMenu(e, m.id, m.text || m.sticker_emoji || '', div);
                            return false;
                        };
                        wrapper.appendChild(div);
                        msgs.appendChild(wrapper);
                    });
                    msgs.scrollTop = msgs.scrollHeight;
                });
        }

        // ===== ОТПРАВКА =====
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
                loadMessages();
            });
        }

        document.getElementById('input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); sendMessage(); }
        });

        document.getElementById('fileInput').addEventListener('change', function(e) {
            const files = e.target.files;
            for (let file of files) {
                if (!file.type.startsWith('image/')) continue;
                const reader = new FileReader();
                reader.onload = function(ev) {
                    const base64 = ev.target.result.split(',')[1];
                    const sender = document.getElementById('nameInput').value.trim() || 'Аноним';
                    fetch('/send_image', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sender, image: base64 })
                    }).then(() => loadMessages());
                };
                reader.readAsDataURL(file);
            }
            this.value = '';
        });

        // ===== КРУЖОК ЗАПИСИ =====
        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                audioChunks = [];
                voiceStartTime = Date.now();

                document.getElementById('tgVoiceCircle').style.display = 'flex';
                document.getElementById('voiceBtn').classList.add('recording');
                document.getElementById('voiceBtn').querySelector('.voice-label').textContent = '⏹ Отпусти';

                voiceTimerInterval = setInterval(() => {
                    const elapsed = Math.floor((Date.now() - voiceStartTime) / 1000);
                    const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
                    const secs = String(elapsed % 60).padStart(2, '0');
                    document.getElementById('voiceTimer').textContent = `${mins}:${secs}`;
                }, 100);

                mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
                mediaRecorder.onstop = () => {
                    clearInterval(voiceTimerInterval);
                    document.getElementById('tgVoiceCircle').style.display = 'none';
                    document.getElementById('voiceBtn').classList.remove('recording');
                    document.getElementById('voiceBtn').querySelector('.voice-label').textContent = 'Нажми и говори';

                    const duration = Math.floor((Date.now() - voiceStartTime) / 1000);
                    if (duration < 1) { stream.getTracks().forEach(t => t.stop()); return; }

                    const blob = new Blob(audioChunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onload = () => {
                        const base64 = reader.result.split(',')[1];
                        const sender = document.getElementById('nameInput').value.trim() || 'Аноним';
                        fetch('/send_voice', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ sender, voice: base64, duration })
                        }).then(() => loadMessages());
                    };
                    reader.readAsDataURL(blob);
                    stream.getTracks().forEach(t => t.stop());
                };
                mediaRecorder.start();
                isRecording = true;
            } catch(e) {
                alert('❌ Нет доступа к микрофону');
            }
        }

        function stopRecording(cancel = false) {
            if (mediaRecorder && isRecording) {
                if (cancel) {
                    mediaRecorder.onstop = () => {
                        document.getElementById('tgVoiceCircle').style.display = 'none';
                        document.getElementById('voiceBtn').classList.remove('recording');
                        document.getElementById('voiceBtn').querySelector('.voice-label').textContent = 'Нажми и говори';
                        isRecording = false;
                    };
                    mediaRecorder.stop();
                } else {
                    mediaRecorder.stop();
                    isRecording = false;
                }
            }
        }

        const voiceBtn = document.getElementById('voiceBtn');
        voiceBtn.addEventListener('mousedown', (e) => { e.preventDefault(); if (!isRecording) startRecording(); });
        voiceBtn.addEventListener('mouseup', (e) => { e.preventDefault(); if (isRecording) stopRecording(false); });
        voiceBtn.addEventListener('mouseleave', () => { if (isRecording) stopRecording(true); });

        let startY = 0;
        voiceBtn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            if (!isRecording) {
                startY = e.touches[0].clientY;
                startRecording();
            }
        });
        voiceBtn.addEventListener('touchmove', (e) => {
            e.preventDefault();
            if (isRecording && startY - e.touches[0].clientY > 80) {
                stopRecording(true);
            }
        });
        voiceBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            if (isRecording) stopRecording(false);
        });

        // ===== РЕАКЦИИ И МЕНЮ =====
        function toggleReaction(msgId, emoji) {
            fetch('/reaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ msg_id: msgId, emoji })
            }).then(() => loadMessages());
        }

        function showMenu(e, msgId, text, element) {
            const menu = document.getElementById('msgMenu');
            selectedMsgId = msgId;
            selectedMsgText = text;
            menu.style.display = 'block';
            let x = e.clientX || e.pageX;
            let y = e.clientY || e.pageY;
            if (x + 200 > window.innerWidth) x = window.innerWidth - 210;
            if (y + 120 > window.innerHeight) y = window.innerHeight - 130;
            menu.style.left = x + 'px';
            menu.style.top = y + 'px';
        }

        function hideMenu() {
            document.getElementById('msgMenu').style.display = 'none';
        }
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.msg-menu')) hideMenu();
        });

        window.editMessage = function() {
            if (!selectedMsgId) return;
            const newText = prompt('Редактировать:', selectedMsgText);
            if (newText !== null && newText.trim()) {
                fetch('/edit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ msg_id: selectedMsgId, text: newText.trim() })
                }).then(() => { loadMessages(); hideMenu(); });
            }
        };

        window.deleteMessage = function() {
            if (!selectedMsgId) return;
            if (confirm('Удалить?')) {
                fetch('/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ msg_id: selectedMsgId })
                }).then(() => { loadMessages(); hideMenu(); });
            }
        };

        window.replyToMessage = function() {
            if (!selectedMsgId) return;
            document.getElementById('input').value = `> ${selectedMsgText}\n\n`;
            document.getElementById('input').focus();
            hideMenu();
        };

        // ===== СОКЕТЫ =====
        socket.on('connect', () => {
            socket.emit('set_name', name);
            loadMessages();
        });
        socket.on('new_message', () => loadMessages());
        socket.on('online_update', (data) => {
            document.getElementById('onlineCount').textContent = data.count || 0;
        });
        socket.on('typing_update', (data) => {
            const el = document.getElementById('typingIndicator');
            if (data.isTyping && data.name !== name) {
                el.textContent = `✎ ${data.name} печатает...`;
            } else {
                el.textContent = '✎';
            }
        });

        setInterval(() => socket.emit('ping'), 30000);
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
        c.execute('SELECT id, sender, text, timestamp, is_voice, voice_data, is_image, image_data, is_sticker, sticker_emoji, reactions, edited FROM messages ORDER BY id DESC LIMIT 200')
        rows = c.fetchall()
        conn.close()
        result = []
        for r in rows[::-1]:
            reactions = json.loads(r[10]) if r[10] else {}
            result.append({
                'id': r[0],
                'sender': r[1],
                'text': r[2] if not r[4] and not r[6] and not r[8] else '',
                'time': r[3],
                'is_voice': bool(r[4]),
                'voice_data': r[5] if r[4] else None,
                'is_image': bool(r[6]),
                'image_data': r[7] if r[6] else None,
                'is_sticker': bool(r[8]),
                'sticker_emoji': r[9] if r[8] else None,
                'reactions': reactions,
                'edited': bool(r[11])
            })
        return jsonify(result)
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
        c.execute('INSERT INTO messages (sender, text, timestamp) VALUES (?, ?, ?)',
                  (sender, text, datetime.now().strftime('%H:%M:%S')))
        conn.commit()
        conn.close()
        socketio.emit('new_message')
        return 'ok'
    except:
        return 'error', 500

@app.route('/send_sticker', methods=['POST'])
def send_sticker():
    try:
        data = request.get_json()
        sender = data.get('sender', 'Аноним')
        emoji = data.get('emoji', '😊')
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT INTO messages (sender, text, timestamp, is_sticker, sticker_emoji) VALUES (?, ?, ?, 1, ?)',
                  (sender, '', datetime.now().strftime('%H:%M:%S'), emoji))
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
        duration = data.get('duration', 3)
        if not voice:
            return 'empty', 400
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT INTO messages (sender, text, timestamp, is_voice, voice_data) VALUES (?, ?, ?, 1, ?)',
                  (sender, f'🎤 {duration}s', datetime.now().strftime('%H:%M:%S'), voice))
        conn.commit()
        conn.close()
        socketio.emit('new_message')
        return 'ok'
    except:
        return 'error', 500

@app.route('/send_image', methods=['POST'])
def send_image():
    try:
        data = request.get_json()
        sender = data.get('sender', 'Аноним')
        image = data.get('image', '')
        if not image:
            return 'empty', 400
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT INTO messages (sender, text, timestamp, is_image, image_data) VALUES (?, ?, ?, 1, ?)',
                  (sender, '📷 Фото', datetime.now().strftime('%H:%M:%S'), image))
        conn.commit()
        conn.close()
        socketio.emit('new_message')
        return 'ok'
    except:
        return 'error', 500

@app.route('/reaction', methods=['POST'])
def reaction():
    try:
        data = request.get_json()
        msg_id = data.get('msg_id')
        emoji = data.get('emoji')
        if not msg_id or not emoji:
            return 'error', 400
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT reactions FROM messages WHERE id = ?', (msg_id,))
        row = c.fetchone()
        if row:
            reactions = json.loads(row[0]) if row[0] else {}
            if emoji in reactions and reactions[emoji] > 0:
                reactions[emoji] = 0
            else:
                reactions[emoji] = 1
            c.execute('UPDATE messages SET reactions = ? WHERE id = ?', (json.dumps(reactions), msg_id))
            conn.commit()
        conn.close()
        socketio.emit('new_message')
        return 'ok'
    except:
        return 'error', 500

@app.route('/edit', methods=['POST'])
def edit_message():
    try:
        data = request.get_json()
        msg_id = data.get('msg_id')
        text = data.get('text')
        if not msg_id or not text:
            return 'error', 400
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('UPDATE messages SET text = ?, edited = 1 WHERE id = ?', (text, msg_id))
        conn.commit()
        conn.close()
        socketio.emit('new_message')
        return 'ok'
    except:
        return 'error', 500

@app.route('/delete', methods=['POST'])
def delete_message():
    try:
        data = request.get_json()
        msg_id = data.get('msg_id')
        if not msg_id:
            return 'error', 400
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('DELETE FROM messages WHERE id = ?', (msg_id,))
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
    print(f"🚀 Чат запущен на порту {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)