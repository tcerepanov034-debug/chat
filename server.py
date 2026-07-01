from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime
import os
import sys
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
            edited BOOLEAN DEFAULT 0,
            reply_to INTEGER DEFAULT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()
active_users = {}

# ============================================
# HTML — СТИКЕРЫ + КРУЖОЧКИ
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
            min-height: 100dvh;
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
                radial-gradient(ellipse at 20% 30%, rgba(100, 116, 139, 0.06) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 70%, rgba(148, 163, 184, 0.04) 0%, transparent 60%),
                #f0f2f5;
            z-index: 0;
            transition: transform 0.1s ease-out;
            pointer-events: none;
            will-change: transform;
        }

        .chat {
            position: relative;
            z-index: 1;
            width: 100%;
            max-width: 560px;
            height: 94vh;
            height: 94dvh;
            background: rgba(255,255,255,0.92);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 32px;
            padding: 16px 16px 14px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.06);
            display: flex;
            flex-direction: column;
            animation: fadeUp 0.4s ease;
        }
        @keyframes fadeUp {
            0% { opacity:0; transform:translateY(20px) scale(0.97); }
            100% { opacity:1; transform:translateY(0) scale(1); }
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-shrink: 0;
            padding: 0 4px;
        }
        .header h1 {
            font-size: 20px;
            font-weight: 600;
            color: #1e293b;
        }
        .header h1 span { color: #64748b; font-weight: 400; }
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
            font-weight: 500;
            outline: none;
            min-height: 44px;
            transition: border-color 0.2s;
        }
        .name-row input:focus {
            border-color: #94a3b8;
            background: #ffffff;
        }

        .msgs {
            flex: 1;
            overflow-y: auto;
            padding: 6px 0 8px;
            display: flex;
            flex-direction: column;
            gap: 4px;
            -webkit-overflow-scrolling: touch;
            scroll-behavior: smooth;
            min-height: 0;
        }
        .msgs::-webkit-scrollbar { width: 4px; }
        .msgs::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 20px; }

        .msg-wrapper {
            display: flex;
            flex-direction: column;
            animation: slideIn 0.25s ease;
            position: relative;
        }
        @keyframes slideIn {
            0% { opacity:0; transform:translateY(8px) scale(0.96); }
            100% { opacity:1; transform:translateY(0) scale(1); }
        }

        .msg {
            max-width: 82%;
            padding: 8px 14px;
            border-radius: 18px;
            font-size: 15px;
            line-height: 1.5;
            word-break: break-word;
            cursor: pointer;
            transition: background 0.15s;
            position: relative;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
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
        .msg.own .sender-name {
            color: #475569;
            text-align: right;
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
        .msg .edited-badge {
            font-size: 10px;
            color: #94a3b8;
            margin-left: 4px;
        }
        .msg .msg-image {
            max-width: 100%;
            max-height: 300px;
            border-radius: 12px;
            margin-top: 4px;
            cursor: pointer;
        }
        .msg .sticker {
            font-size: 48px;
            line-height: 1.2;
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
            transition: background 0.2s;
        }
        .msg .voice-circle:hover { background: rgba(0,0,0,0.08); }
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
            animation: wave 1s ease-in-out infinite;
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
        .msg .voice-circle .duration {
            font-size: 12px;
            color: #64748b;
            font-weight: 500;
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
            transition: background 0.15s;
            line-height: 1.4;
        }
        .reaction-btn:hover { background: rgba(0,0,0,0.1); }
        .reaction-btn.active { background: rgba(99,102,241,0.15); }

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
            backdrop-filter: blur(20px);
            background: rgba(255,255,255,0.95);
        }
        .msg-menu-item {
            padding: 10px 20px;
            font-size: 14px;
            color: #1e293b;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: background 0.1s;
            border: none;
            background: none;
            width: 100%;
            text-align: left;
        }
        .msg-menu-item:hover { background: #f1f5f9; }
        .msg-menu-item.danger { color: #ef4444; }
        .msg-menu-item .icon { font-size: 16px; }

        .typing-indicator {
            color: #94a3b8;
            font-size: 13px;
            padding: 4px 6px;
            min-height: 28px;
            font-weight: 400;
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
        .input-row input[type="text"] {
            flex: 1;
            padding: 12px 18px;
            border-radius: 24px;
            border: 1.5px solid #e2e8f0;
            background: #f8fafc;
            color: #1e293b;
            font-size: 15px;
            outline: none;
            min-height: 48px;
            transition: border-color 0.2s;
        }
        .input-row input:focus {
            border-color: #94a3b8;
            background: #ffffff;
        }
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
            transition: all 0.15s;
        }
        .input-row .icon-btn:active { transform: scale(0.92); }
        .input-row .send-btn {
            padding: 0 20px;
            border: none;
            border-radius: 24px;
            background: #1e293b;
            color: #ffffff;
            font-weight: 500;
            font-size: 15px;
            cursor: pointer;
            min-height: 48px;
            min-width: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s;
        }
        .input-row .send-btn:active { transform: scale(0.92); }

        /* ===== СТИКЕР-ПАНЕЛЬ ===== */
        .sticker-panel {
            display: flex;
            gap: 6px;
            padding: 8px 0 4px;
            flex-wrap: wrap;
            justify-content: center;
            border-top: 1px solid rgba(0,0,0,0.04);
            margin-top: 6px;
        }
        .sticker-btn {
            font-size: 28px;
            padding: 4px 8px;
            border: none;
            background: rgba(0,0,0,0.02);
            border-radius: 12px;
            cursor: pointer;
            transition: transform 0.15s, background 0.15s;
            line-height: 1.2;
        }
        .sticker-btn:hover {
            transform: scale(1.15);
            background: rgba(0,0,0,0.05);
        }
        .sticker-btn:active { transform: scale(0.9); }

        /* ===== КРУЖОК ЗАПИСИ (ТГ-СТИЛЬ) ===== */
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
            -webkit-backdrop-filter: blur(20px);
            padding: 16px 24px 16px 20px;
            border-radius: 60px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            animation: fadeUp 0.3s ease;
        }
        .tg-circle-pulse {
            position: absolute;
            top: -8px;
            left: -8px;
            right: -8px;
            bottom: -8px;
            border-radius: 60px;
            border: 2px solid rgba(239, 68, 68, 0.3);
            animation: pulseCircle 1.5s ease-out infinite;
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
            animation: tgWave 0.8s ease-in-out infinite;
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
            color: #ffffff;
            font-size: 16px;
            font-weight: 600;
            min-width: 40px;
            font-variant-numeric: tabular-nums;
        }
        .tg-cancel-btn {
            background: rgba(255,255,255,0.1);
            border: none;
            border-radius: 50%;
            color: #ffffff;
            font-size: 16px;
            cursor: pointer;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
            position: relative;
            z-index: 1;
        }
        .tg-cancel-btn:hover { background: rgba(255,255,255,0.2); }
        .tg-cancel-btn:active { transform: scale(0.9); }

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
            transition: all 0.2s;
            min-height: 44px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            user-select: none;
            -webkit-user-select: none;
        }
        .voice-circle-btn:active { transform: scale(0.95); }
        .voice-circle-btn .voice-icon { font-size: 18px; }
        .voice-circle-btn .voice-label {
            font-size: 13px;
            color: #64748b;
            font-weight: 500;
        }
        .voice-circle-btn.recording {
            background: #fee2e2;
            animation: pulseRed 1s ease-in-out infinite;
        }
        @keyframes pulseRed {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(0.98); }
        }

        #fileInput { display: none; }

        @media (max-width: 480px) {
            .chat { padding: 12px 12px 12px; border-radius: 24px; height: 98vh; height: 98dvh; }
            .msg { max-width: 88%; font-size: 14px; padding: 7px 12px; }
            .msg .sticker { font-size: 40px; }
            .input-row input { font-size: 14px; min-height: 44px; }
            .input-row .icon-btn, .input-row .send-btn { min-height: 44px; min-width: 44px; font-size: 14px; }
            .sticker-btn { font-size: 24px; padding: 2px 6px; }
            .voice-circle-btn { padding: 6px 14px; min-height: 38px; }
            .voice-circle-btn .voice-label { font-size: 12px; }
            .tg-voice-circle { bottom: 80px; padding: 12px 16px; }
        }

        @media (prefers-color-scheme: dark) {
            body { background: #0f172a; }
            #parallax-bg {
                background: radial-gradient(ellipse at 20% 30%, rgba(100,116,139,0.06) 0%, transparent 60%),
                            radial-gradient(ellipse at 80% 70%, rgba(148,163,184,0.04) 0%, transparent 60%),
                            #0f172a;
            }
            .chat { background: rgba(30,41,59,0.92); box-shadow: 0 20px 60px rgba(0,0,0,0.4); }
            .header h1 { color: #f1f5f9; }
            .header h1 span { color: #94a3b8; }
            .badge { color: #94a3b8; }
            .name-row input { background: #1e293b; border-color: #334155; color: #f1f5f9; }
            .name-row input:focus { background: #1e293b; border-color: #64748b; }
            .msg.own { background: #334155; color: #f1f5f9; }
            .msg.other { background: #1e293b; color: #f1f5f9; border-color: #334155; }
            .msg .sender-name { color: #94a3b8; }
            .msg.own .sender-name { color: #94a3b8; }
            .msg .time { color: #64748b; }
            .msg .voice-circle { background: rgba(255,255,255,0.06); }
            .msg .voice-circle .wave span { background: #94a3b8; }
            .msg .voice-circle .duration { color: #94a3b8; }
            .msg-menu { background: rgba(30,41,59,0.95); border-color: #334155; }
            .msg-menu-item { color: #f1f5f9; }
            .msg-menu-item:hover { background: #1e293b; }
            .typing-indicator { color: #64748b; }
            .input-area { border-color: #1e293b; }
            .input-row input { background: #1e293b; border-color: #334155; color: #f1f5f9; }
            .input-row input:focus { background: #1e293b; border-color: #64748b; }
            .input-row .icon-btn { background: #1e293b; color: #f1f5f9; }
            .input-row .icon-btn:active { background: #334155; }
            .input-row .send-btn { background: #334155; color: #f1f5f9; }
            .input-row .send-btn:active { background: #475569; }
            .voice-circle-btn { background: #1e293b; border-color: #334155; }
            .voice-circle-btn .voice-label { color: #94a3b8; }
            .voice-circle-btn.recording { background: #7f1d1d; }
            .sticker-btn { background: rgba(255,255,255,0.03); }
            .sticker-btn:hover { background: rgba(255,255,255,0.08); }
            .reaction-btn { background: rgba(255,255,255,0.06); }
            .reaction-btn:hover { background: rgba(255,255,255,0.1); }
            .tg-voice-circle { background: rgba(15, 23, 42, 0.95); border-color: #334155; }
            .sticker-panel { border-color: #1e293b; }
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
                <button class="icon-btn" onclick="document.getElementById('fileInput').click()" title="Фото">📷</button>
                <button onclick="sendMessage()" class="send-btn">→</button>
            </div>
            
            <!-- ===== СТИКЕР-ПАНЕЛЬ ===== -->
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

    <!-- ===== МЕНЮ ===== -->
    <div class="msg-menu" id="msgMenu">
        <button class="msg-menu-item" onclick="editMessage()"><span class="icon">✏️</span> Редактировать</button>
        <button class="msg-menu-item danger" onclick="deleteMessage()"><span class="icon">🗑️</span> Удалить</button>
        <button class="msg-menu-item" onclick="replyToMessage()"><span class="icon">↩️</span> Ответить</button>
    </div>

    <!-- ===== КРУЖОК ЗАПИСИ ===== -->
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
        // ============================================
        // ОСНОВНАЯ ЛОГИКА
        // ============================================

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

        const socket = io({ transports: ['websocket', 'polling'], upgrade: true });
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

        document.getElementById('nameInput').addEventListener('change', function() {
            name = this.value.trim() || 'Аноним';
            localStorage.setItem('chatName', name);
            socket.emit('set_name', name);
        });

        document.getElementById('input').addEventListener('input', function() {
            const isTyping = this.value.length > 0;
            socket.emit('typing', { name: name, isTyping });
            clearTimeout(typingTimeout);
            if (isTyping) {
                typingTimeout = setTimeout(() => {
                    socket.emit('typing', { name: name, isTyping: false });
                }, 3000);
            }
        });

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

        // ============================================
        // СООБЩЕНИЯ
        // ============================================
        function loadMessages() {
            fetch('/messages')
                .then(r => r.json())
                .then(data => {
                    const msgs = document.getElementById('msgs');
                    msgs.innerHTML = '';
                    data.forEach(m => {
                        const wrapper = createMessageElement(m);
                        msgs.appendChild(wrapper);
                    });
                    msgs.scrollTop = msgs.scrollHeight;
                })
                .catch(() => {});
        }

        function createMessageElement(m) {
            const wrapper = document.createElement('div');
            wrapper.className = 'msg-wrapper';
            wrapper.dataset.msgId = m.id;

            const div = document.createElement('div');
            div.className = 'msg ' + (m.sender === name ? 'own' : 'other');
            div.dataset.msgId = m.id;

            const nameDiv = document.createElement('div');
            nameDiv.className = 'sender-name';
            nameDiv.textContent = m.sender;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'msg-content';

            // === СТИКЕР ===
            if (m.is_sticker && m.sticker_emoji) {
                const stickerSpan = document.createElement('span');
                stickerSpan.className = 'sticker';
                stickerSpan.textContent = m.sticker_emoji;
                contentDiv.appendChild(stickerSpan);
            }

            // === ИЗОБРАЖЕНИЕ ===
            if (m.is_image && m.image_data) {
                const img = document.createElement('img');
                img.className = 'msg-image';
                img.src = 'data:image/jpeg;base64,' + m.image_data;
                img.alt = 'Изображение';
                img.onclick = () => window.open(img.src, '_blank');
                contentDiv.appendChild(img);
            }

            // === ГОЛОСОВОЕ ===
            if (m.is_voice && m.voice_data) {
                const voiceDiv = document.createElement('div');
                voiceDiv.className = 'voice-circle';
                voiceDiv.onclick = () => playVoice(m.voice_data);
                voiceDiv.innerHTML = `
                    <span>🔊</span>
                    <div class="wave">
                        <span></span><span></span><span></span><span></span><span></span>
                    </div>
                    <span class="duration">${m.voice_duration || '0:03'}</span>
                `;
                contentDiv.appendChild(voiceDiv);
            }

            // === ТЕКСТ ===
            if (m.text && !m.is_voice && !m.is_sticker) {
                const textSpan = document.createElement('span');
                textSpan.textContent = m.text;
                contentDiv.appendChild(textSpan);
            }

            if (m.edited) {
                const editBadge = document.createElement('span');
                editBadge.className = 'edited-badge';
                editBadge.textContent = '(ред.)';
                contentDiv.appendChild(editBadge);
            }

            const timeDiv = document.createElement('div');
            timeDiv.className = 'time';
            timeDiv.textContent = m.time;

            const reactionsDiv = document.createElement('div');
            reactionsDiv.className = 'reactions';
            const reactions = m.reactions || {};
            const emojis = ['❤️', '👍', '😂', '😮', '😢'];
            emojis.forEach(emoji => {
                const btn = document.createElement('button');
                btn.className = 'reaction-btn';
                btn.textContent = emoji + (reactions[emoji] || '');
                btn.onclick = (e) => {
                    e.stopPropagation();
                    toggleReaction(m.id, emoji);
                };
                reactionsDiv.appendChild(btn);
            });

            div.appendChild(nameDiv);
            div.appendChild(contentDiv);
            div.appendChild(timeDiv);
            div.appendChild(reactionsDiv);

            div.oncontextmenu = (e) => {
                e.preventDefault();
                e.stopPropagation();
                showMenu(e, m.id, m.text || m.sticker_emoji || '', div);
                return false;
            };
            div.onclick = (e) => {
                if (e.target.closest('.reaction-btn') || e.target.closest('.voice-circle')) return;
                hideMenu();
            };

            wrapper.appendChild(div);
            return wrapper;
        }

        // ============================================
        // ОТПРАВКА (текст, стикеры, фото)
        // ============================================
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
                if (isMobile && navigator.vibrate) navigator.vibrate(10);
                loadMessages();
            });
        }

        function sendSticker(emoji) {
            const sender = document.getElementById('nameInput').value.trim() || 'Аноним';
            fetch('/send_sticker', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sender, emoji })
            }).then(() => {
                if (isMobile && navigator.vibrate) navigator.vibrate(10);
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
                    }).then(() => { loadMessages(); });
                };
                reader.readAsDataURL(file);
            }
            this.value = '';
        });

        // ============================================
        // ГОЛОСОВЫЕ КРУЖКИ (ТГ-СТИЛЬ — РАБОТАЕТ)
        // ============================================
        function toggleVoice() {
            if (isRecording) {
                stopRecording(false);
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
                voiceStartTime = Date.now();
                
                // === ПОКАЗЫВАЕМ КРУЖОК ===
                const circle = document.getElementById('tgVoiceCircle');
                circle.style.display = 'flex';
                circle.style.animation = 'none';
                circle.offsetHeight;
                circle.style.animation = 'fadeUp 0.3s ease';
                
                // === МЕНЯЕМ КНОПКУ ===
                const btn = document.getElementById('voiceBtn');
                btn.classList.add('recording');
                btn.querySelector('.voice-label').textContent = '⏹ Отпусти для отправки';
                
                // === ТАЙМЕР ===
                voiceTimerInterval = setInterval(() => {
                    const elapsed = Math.floor((Date.now() - voiceStartTime) / 1000);
                    const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
                    const secs = String(elapsed % 60).padStart(2, '0');
                    document.getElementById('voiceTimer').textContent = `${mins}:${secs}`;
                }, 100);
                
                mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
                mediaRecorder.onstop = () => {
                    clearInterval(voiceTimerInterval);
                    
                    // === СКРЫВАЕМ КРУЖОК ===
                    document.getElementById('tgVoiceCircle').style.display = 'none';
                    document.getElementById('voiceBtn').classList.remove('recording');
                    document.getElementById('voiceBtn').querySelector('.voice-label').textContent = 'Нажми и говори';
                    
                    const duration = Math.floor((Date.now() - voiceStartTime) / 1000);
                    if (duration < 1) {
                        stream.getTracks().forEach(t => t.stop());
                        return;
                    }
                    
                    const blob = new Blob(audioChunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onload = () => {
                        const base64 = reader.result.split(',')[1];
                        const sender = document.getElementById('nameInput').value.trim() || 'Аноним';
                        fetch('/send_voice', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ sender, voice: base64, duration })
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
                if (isMobile && navigator.vibrate) navigator.vibrate(20);
            } catch(e) {
                alert('❌ Нет доступа к микрофону');
            }
        }

        function stopRecording(cancel = false) {
            if (mediaRecorder && isRecording) {
                if (cancel) {
                    mediaRecorder.onstop = () => {
                        clearInterval(voiceTimerInterval);
                        document.getElementById('tgVoiceCircle').style.display = 'none';
                        document.getElementById('voiceBtn').classList.remove('recording');
                        document.getElementById('voiceBtn').querySelector('.voice-label').textContent = 'Нажми и говори';
                        isRecording = false;
                    };
                    mediaRecorder.stop();
                    if (mediaRecorder.stream) {
                        mediaRecorder.stream.getTracks().forEach(t => t.stop());
                    }
                } else {
                    mediaRecorder.stop();
                    isRecording = false;
                }
            }
        }

        // === ОБРАБОТЧИКИ ДЛЯ КНОПКИ ===
        const voiceBtn = document.getElementById('voiceBtn');
        voiceBtn.addEventListener('mousedown', function(e) {
            e.preventDefault();
            if (!isRecording) startRecording();
        });
        voiceBtn.addEventListener('mouseup', function(e) {
            e.preventDefault();
            if (isRecording) stopRecording(false);
        });
        voiceBtn.addEventListener('mouseleave', function(e) {
            if (isRecording) stopRecording(true);
        });

        let startY = 0;
        voiceBtn.addEventListener('touchstart', function(e) {
            e.preventDefault();
            if (!isRecording) {
                startY = e.touches[0].clientY;
                startRecording();
            }
        });
        voiceBtn.addEventListener('touchmove', function(e) {
            e.preventDefault();
            if (isRecording) {
                const deltaY = startY - e.touches[0].clientY;
                if (deltaY > 80) {
                    stopRecording(true);
                    document.getElementById('voiceBtn').style.transform = 'scale(0.9)';
                    setTimeout(() => {
                        document.getElementById('voiceBtn').style.transform = 'scale(1)';
                    }, 200);
                }
            }
        });
        voiceBtn.addEventListener('touchend', function(e) {
            e.preventDefault();
            if (isRecording) stopRecording(false);
        });

        window.playVoice = function(data) {
            try {
                const audio = new Audio('data:audio/webm;base64,' + data);
                audio.play().catch(() => {});
            } catch(e) {}
        };

        // ============================================
        // РЕАКЦИИ И МЕНЮ
        // ============================================
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
            const menuWidth = 200;
            if (x + menuWidth > window.innerWidth) x = window.innerWidth - menuWidth - 10;
            if (y + 120 > window.innerHeight) y = window.innerHeight - 130;
            menu.style.left = x + 'px';
            menu.style.top = y + 'px';
        }

        function hideMenu() {
            document.getElementById('msgMenu').style.display = 'none';
        }

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.msg-menu') && !e.target.closest('.msg')) {
                hideMenu();
            }
        });

        window.editMessage = function() {
            if (!selectedMsgId) return;
            const newText = prompt('Редактировать сообщение:', selectedMsgText);
            if (newText !== null && newText.trim()) {
                fetch('/edit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ msg_id: selectedMsgId, text: newText.trim() })
                }).then(() => {
                    loadMessages();
                    hideMenu();
                });
            }
        };

        window.deleteMessage = function() {
            if (!selectedMsgId) return;
            if (confirm('Удалить сообщение?')) {
                fetch('/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ msg_id: selectedMsgId })
                }).then(() => {
                    loadMessages();
                    hideMenu();
                });
            }
        };

        window.replyToMessage = function() {
            if (!selectedMsgId) return;
            const input = document.getElementById('input');
            input.value = `> ${selectedMsgText}\n\n`;
            input.focus();
            hideMenu();
        };

        socket.on('connect', () => {
            socket.emit('set_name', name);
            loadMessages();
        });

        socket.on('new_message', () => {
            loadMessages();
        });

        setInterval(() => socket.emit('ping'), 30000);
        loadMessages();
    </script>
</body>
</html>
'''

# ============================================
# МАРШРУТЫ (с поддержкой стикеров)
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
                'voice_duration': '0:03' if r[4] else None,
                'is_image': bool(r[6]),
                'image_data': r[7] if r[6] else None,
                'is_sticker': bool(r[8]),
                'sticker_emoji': r[9] if r[8] else None,
                'reactions': reactions,
                'edited': bool(r[11])
            })
        return jsonify(result)
    except Exception as e:
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
        if not emoji:
            return 'empty', 400
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT INTO messages (sender, text, timestamp, is_sticker, sticker_emoji) VALUES (?, ?, ?, 1, ?)',
                  (sender, f'😍 {emoji}', datetime.now().strftime('%H:%M:%S'), emoji))
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
    print(f"🚀 Чат со стикерами и кружочками на порту {port}")
    print("🎨 Стикеры: 😊😂🔥💀❤️🎉🤣🙈💪🤩🥳😎")
    print("🎤 Кружочки: зажми кнопку и говори")
    print("📷 Отправка фото")
    print("❤️ Реакции")
    print("✏️ Редактирование/удаление")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)