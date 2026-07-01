from flask import Flask, request, render_template_string, Response
import subprocess
import threading
import socket
import time
import os
import sys
import pyautogui
import psutil
import io
from PIL import Image
import ctypes
import mss
import qrcode
import pygetwindow as gw

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# ПУТИ К ПРИЛОЖЕНИЯМ (проверь свои пути!)
# ═══════════════════════════════════════════════════════════════════════════
MINECRAFT_PATH = r"C:\Users\уебище\Desktop\TLauncher.lnk"
YANDEX_MUSIC_PATH = r"C:\Users\уебище\Desktop\Яндекс Музыка.lnk"
YANDEX_BROWSER_PATH = r"C:\Users\уебище\Desktop\Yandex.lnk"
VPN_PATH = r"C:\Users\Public\Desktop\Happ.lnk"
TELEGRAM_PATH = r"C:\Users\уебище\Desktop\Telegram.lnk"
DEEPSEEK_APP_PATH = r"C:\Users\уебище\Desktop\deepsek.lnk"

# ═══════════════════════════════════════════════════════════════════════════
# КООРДИНАТЫ ЯНДЕКС МУЗЫКИ
# ═══════════════════════════════════════════════════════════════════════════
YANDEX_MY_WAVE_X = 850
YANDEX_MY_WAVE_Y = 512
YANDEX_PLAYLIST_X = 109
YANDEX_PLAYLIST_Y = 410
YANDEX_PLAYLIST_OFF_X = 268
YANDEX_PLAYLIST_OFF_Y = 294
YANDEX_TO_MY_WAVE_X = 131
YANDEX_TO_MY_WAVE_Y = 198
PLAYLIST_OFF_CUSTOM_X = 943
PLAYLIST_OFF_CUSTOM_Y = 125
YANDEX_LIKE_X = 1014
YANDEX_LIKE_Y = 434
YANDEX_LYRICS_X = 266
YANDEX_LYRICS_Y = 687
YANDEX_CLOSE_LYRICS_X = 1251
YANDEX_CLOSE_LYRICS_Y = 73
VPN_CLICK_X = 1033
VPN_CLICK_Y = 218

# ═══════════════════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════════
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def show_qr_code():
    try:
        ip = get_ip()
        url = f"http://{ip}:5000"
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(url)
        qr.make()
        qr_path = r"C:\Users\уебище\Desktop\пульт_qr.png"
        qr.make_image().save(qr_path)
        print(f"\n✅ QR-код сохранён: {qr_path}")
        print("\n📱 НАВЕДИ ТЕЛЕФОН НА QR-КОД:\n")
        qr.print_ascii()
        print(f"\n🌐 ИЛИ ПЕРЕЙДИ ПО ССЫЛКЕ: {url}\n")
    except Exception as e:
        print(f"⚠️ Ошибка QR: {e}")

def click_at(x, y):
    pyautogui.moveTo(x, y, duration=0.05)
    pyautogui.click()

def safe_startfile(path):
    if os.path.exists(path):
        os.startfile(path)
        return True
    print(f"⚠️ Файл не найден: {path}")
    return False

# ═══════════════════════════════════════════════════════════════════════════
# УПРАВЛЕНИЕ ОКНАМИ (через pygetwindow)
# ═══════════════════════════════════════════════════════════════════════════
def get_windows_list():
    windows = []
    try:
        for win in gw.getAllWindows():
            if win.title and win.visible:
                windows.append({'hwnd': win._hWnd, 'title': win.title[:40]})
    except:
        pass
    return windows[:20]

def close_window(hwnd):
    try:
        for win in gw.getAllWindows():
            if win._hWnd == hwnd:
                win.close()
                return True
    except:
        pass
    return False

def minimize_window(hwnd):
    try:
        for win in gw.getAllWindows():
            if win._hWnd == hwnd:
                win.minimize()
                return True
    except:
        pass
    return False

def maximize_window(hwnd):
    try:
        for win in gw.getAllWindows():
            if win._hWnd == hwnd:
                win.maximize()
                return True
    except:
        pass
    return False

def restore_window(hwnd):
    try:
        for win in gw.getAllWindows():
            if win._hWnd == hwnd:
                win.restore()
                return True
    except:
        pass
    return False

def minimize_all_windows():
    pyautogui.hotkey('win', 'd')

def show_desktop():
    pyautogui.hotkey('win', 'd')

# ═══════════════════════════════════════════════════════════════════════════
# ДЕЙСТВИЯ ДЛЯ КНОПОК
# ═══════════════════════════════════════════════════════════════════════════
def action_minecraft(): safe_startfile(MINECRAFT_PATH)
def action_yandex_open(): safe_startfile(YANDEX_MUSIC_PATH)
def action_yandex_my_wave(): click_at(YANDEX_MY_WAVE_X, YANDEX_MY_WAVE_Y)
def action_yandex_playlist(): click_at(YANDEX_PLAYLIST_X, YANDEX_PLAYLIST_Y)
def action_yandex_playlist_off(): click_at(YANDEX_PLAYLIST_OFF_X, YANDEX_PLAYLIST_OFF_Y)
def action_yandex_to_my_wave(): click_at(YANDEX_TO_MY_WAVE_X, YANDEX_TO_MY_WAVE_Y)
def action_yandex_browser(): safe_startfile(YANDEX_BROWSER_PATH)
def action_playlist_off_custom(): click_at(PLAYLIST_OFF_CUSTOM_X, PLAYLIST_OFF_CUSTOM_Y)
def action_yandex_like(): click_at(YANDEX_LIKE_X, YANDEX_LIKE_Y)
def action_yandex_lyrics(): click_at(YANDEX_LYRICS_X, YANDEX_LYRICS_Y)
def action_yandex_close_lyrics(): click_at(YANDEX_CLOSE_LYRICS_X, YANDEX_CLOSE_LYRICS_Y)
def action_deepseek_app(): safe_startfile(DEEPSEEK_APP_PATH)
def action_telegram(): safe_startfile(TELEGRAM_PATH)
def action_vpn(): safe_startfile(VPN_PATH); time.sleep(1); click_at(VPN_CLICK_X, VPN_CLICK_Y)
def action_new_notepad(): subprocess.Popen(['notepad.exe'])
def action_calc(): subprocess.Popen(['calc.exe'])
def action_cmd(): subprocess.Popen(['cmd.exe'])
def action_browser(): subprocess.Popen('start chrome', shell=True)
def action_screenshot(): pyautogui.screenshot(f'screenshot_{time.strftime("%Y%m%d_%H%M%S")}.png')
def action_lock(): ctypes.windll.user32.LockWorkStation()
def action_shutdown(): subprocess.run(['shutdown', '/s', '/t', '0'])
def action_restart(): subprocess.run(['shutdown', '/r', '/t', '0'])
def action_sleep(): subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0', '1', '0'])
def monitor_off(): ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
def monitor_on(): ctypes.windll.user32.keybd_event(0x10, 0, 0, 0); time.sleep(0.05); ctypes.windll.user32.keybd_event(0x10, 0, 2, 0)
def empty_recycle_bin(): ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0)
def volume_up(): pyautogui.press('volumeup')
def volume_down(): pyautogui.press('volumedown')
def volume_mute(): pyautogui.press('volumemute')
def media_play_pause(): pyautogui.press('playpause')
def media_next(): pyautogui.press('nexttrack')
def media_prev(): pyautogui.press('prevtrack')
def action_osk(): subprocess.Popen(r'C:\Windows\System32\osk.exe', shell=True)

# ═══════════════════════════════════════════════════════════════════════════
# СЦЕНАРИИ
# ═══════════════════════════════════════════════════════════════════════════
def scenario_gaming():
    safe_startfile(YANDEX_MUSIC_PATH)
    time.sleep(2)
    click_at(YANDEX_MY_WAVE_X, YANDEX_MY_WAVE_Y)
    time.sleep(1)
    safe_startfile(MINECRAFT_PATH)

def scenario_work():
    safe_startfile(YANDEX_MUSIC_PATH)
    time.sleep(2)
    click_at(YANDEX_MY_WAVE_X, YANDEX_MY_WAVE_Y)
    time.sleep(1)
    safe_startfile(DEEPSEEK_APP_PATH)

def panic():
    os.system('taskkill /f /im chrome.exe >nul 2>&1')
    os.system('taskkill /f /im notepad.exe >nul 2>&1')
    os.system('taskkill /f /im calc.exe >nul 2>&1')
    os.system('taskkill /f /im explorer.exe >nul 2>&1')
    time.sleep(0.5)
    os.system('start explorer.exe')

# ═══════════════════════════════════════════════════════════════════════════
# МУЗЫКАЛЬНЫЙ МОДУЛЬ (распознавание по заголовку окна)
# ═══════════════════════════════════════════════════════════════════════════
current_track = {
    "title": "Неизвестно",
    "artist": "",
    "album": "",
    "cover": "",
    "url": "",
    "from": "none"
}

def get_music_from_window():
    global current_track
    players = ["Яндекс Музыка", "Spotify", "VLC", "YouTube", "Music", "Плеер", "Player"]
    try:
        windows = gw.getWindowsWithTitle('')
        for win in windows:
            title = win.title
            if title and any(p in title for p in players):
                parts = title.split(' — ')
                if len(parts) >= 2:
                    current_track = {
                        "title": parts[0].strip(),
                        "artist": parts[1].strip() if len(parts) > 1 else "",
                        "album": "",
                        "cover": "",
                        "url": "",
                        "from": "window"
                    }
                    return current_track
                elif ' - ' in title:
                    parts = title.split(' - ')
                    if len(parts) >= 2:
                        current_track = {
                            "title": parts[0].strip(),
                            "artist": parts[1].strip() if len(parts) > 1 else "",
                            "album": "",
                            "cover": "",
                            "url": "",
                            "from": "window"
                        }
                        return current_track
    except Exception as e:
        print(f"⚠️ Ошибка чтения окон: {e}")
    return None

def get_current_track():
    track = get_music_from_window()
    if track:
        return current_track
    return current_track

# ═══════════════════════════════════════════════════════════════════════════
# СТРИМ ЭКРАНА
# ═══════════════════════════════════════════════════════════════════════════
def generate_screen_stream():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        while True:
            try:
                img = sct.grab(monitor)
                pil_img = Image.frombytes("RGB", (img.width, img.height), img.rgb)
                if pil_img.size[0] > 640:
                    pil_img.thumbnail((640, 480))
                buffer = io.BytesIO()
                pil_img.save(buffer, format='JPEG', quality=60)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.getvalue() + b'\r\n')
            except:
                time.sleep(0.05)

# ═══════════════════════════════════════════════════════════════════════════
# HTML — ВЕСЬ ИНТЕРФЕЙС (такой же как в прошлой версии)
# ═══════════════════════════════════════════════════════════════════════════
HTML = r'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>PULSE</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0b0d15;
            font-family: 'Inter', sans-serif;
            padding: 16px;
            padding-bottom: 90px;
            color: #e8edf5;
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }
        #particlesCanvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
        }
        .parallax-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 120%;
            height: 120%;
            background: radial-gradient(ellipse at 20% 30%, #1a1a2e, #0b0d15);
            z-index: 0;
            transition: transform 0.1s ease-out;
            pointer-events: none;
        }
        .container {
            max-width: 520px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }
        .header {
            text-align: center;
            padding: 28px 20px 20px;
            background: rgba(255,255,255,0.03);
            border-radius: 28px;
            border: 1px solid rgba(255,255,255,0.06);
            margin-bottom: 20px;
            backdrop-filter: blur(12px);
            position: relative;
            overflow: hidden;
        }
        .header .logo {
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(135deg, #818cf8, #6366f1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: glowPulse 3s ease-in-out infinite;
        }
        @keyframes glowPulse {
            0%, 100% { text-shadow: 0 0 20px rgba(99,102,241,0.1); }
            50% { text-shadow: 0 0 40px rgba(99,102,241,0.2); }
        }
        .header .subtitle {
            font-size: 12px;
            color: rgba(255,255,255,0.35);
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-top: 4px;
        }
        .header .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #34d399;
            margin-right: 8px;
            animation: pulse-dot 2s infinite;
        }
        @keyframes pulse-dot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.8); }
        }
        .ip-box {
            background: rgba(255,255,255,0.03);
            border-radius: 14px;
            padding: 12px 16px;
            margin-top: 12px;
            border: 1px solid rgba(255,255,255,0.05);
            font-family: monospace;
            font-size: 14px;
            color: #818cf8;
            text-align: center;
            word-break: break-all;
        }
        .ip-box .label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: rgba(255,255,255,0.25);
            display: block;
            margin-bottom: 4px;
        }
        .qr-container {
            text-align: center;
            margin-top: 12px;
            padding: 12px;
            background: rgba(255,255,255,0.02);
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.04);
        }
        .qr-container img {
            max-width: 180px;
            border-radius: 12px;
            background: white;
            padding: 8px;
        }
        .qr-container .qr-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: rgba(255,255,255,0.25);
            display: block;
            margin-bottom: 8px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 18px;
        }
        .stat-card {
            background: rgba(255,255,255,0.03);
            border-radius: 16px;
            padding: 14px 10px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.05);
            backdrop-filter: blur(8px);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .stat-card::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(ellipse, rgba(99,102,241,0.03), transparent 70%);
            animation: statGlow 4s ease-in-out infinite;
            pointer-events: none;
        }
        @keyframes statGlow {
            0%, 100% { transform: translate(0,0); }
            50% { transform: translate(10%,10%); }
        }
        .stat-card:hover {
            border-color: rgba(99,102,241,0.2);
            transform: translateY(-2px);
        }
        .stat-card .value {
            font-size: 22px;
            font-weight: 600;
            background: linear-gradient(135deg, #e8edf5, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            position: relative;
        }
        .stat-card .value.animate {
            animation: numberPop 0.5s ease;
        }
        @keyframes numberPop {
            0% { transform: scale(0.5); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
        }
        .stat-card .label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: rgba(255,255,255,0.3);
            margin-top: 4px;
            position: relative;
        }
        .section {
            background: rgba(255,255,255,0.03);
            border-radius: 20px;
            padding: 16px 14px;
            margin-bottom: 14px;
            border: 1px solid rgba(255,255,255,0.05);
            backdrop-filter: blur(8px);
            transition: all 0.3s ease;
            animation: fadeUp 0.5s ease forwards;
            opacity: 0;
            transform: translateY(10px);
        }
        .section:nth-child(2) { animation-delay: 0.05s; }
        .section:nth-child(3) { animation-delay: 0.1s; }
        .section:nth-child(4) { animation-delay: 0.15s; }
        .section:nth-child(5) { animation-delay: 0.2s; }
        .section:nth-child(6) { animation-delay: 0.25s; }
        .section:nth-child(7) { animation-delay: 0.3s; }
        .section:nth-child(8) { animation-delay: 0.35s; }
        .section:nth-child(9) { animation-delay: 0.4s; }
        .section:nth-child(10) { animation-delay: 0.45s; }
        .section:hover {
            border-color: rgba(255,255,255,0.08);
        }
        @keyframes fadeUp {
            to { opacity: 1; transform: translateY(0); }
        }
        .section-title {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: rgba(255,255,255,0.3);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: color 0.3s ease;
        }
        .section:hover .section-title { color: rgba(255,255,255,0.5); }
        .section-title .icon { font-size: 14px; }
        .grid-2 { display: grid; grid-template-columns: repeat(2,1fr); gap: 8px; }
        .grid-3 { display: grid; grid-template-columns: repeat(3,1fr); gap: 8px; }
        .grid-4 { display: grid; grid-template-columns: repeat(4,1fr); gap: 8px; }
        .btn {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.06);
            padding: 12px 6px;
            border-radius: 14px;
            color: #e8edf5;
            font-size: 13px;
            font-weight: 500;
            text-align: center;
            cursor: pointer;
            transition: all 0.15s ease;
            font-family: inherit;
            letter-spacing: 0.3px;
            position: relative;
            overflow: hidden;
            -webkit-tap-highlight-color: transparent;
            user-select: none;
        }
        .btn::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(ellipse, rgba(99,102,241,0.05), transparent 70%);
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        }
        .btn:hover::after { opacity: 1; }
        .btn:active {
            transform: scale(0.94);
            background: rgba(99,102,241,0.15);
            border-color: rgba(99,102,241,0.3);
            box-shadow: 0 0 30px rgba(99,102,241,0.08);
        }
        .btn .emoji {
            display: block;
            font-size: 18px;
            margin-bottom: 2px;
            transition: transform 0.3s ease;
        }
        .btn:hover .emoji { transform: scale(1.1); }
        .btn .label {
            font-size: 10px;
            opacity: 0.6;
            display: block;
            margin-top: 1px;
        }
        .btn-primary { background: rgba(99,102,241,0.12); border-color: rgba(99,102,241,0.2); }
        .btn-success { background: rgba(52,211,153,0.08); border-color: rgba(52,211,153,0.15); }
        .btn-danger { background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.15); }
        .btn-warning { background: rgba(251,191,36,0.08); border-color: rgba(251,191,36,0.15); }
        .btn-purple { background: rgba(168,85,247,0.08); border-color: rgba(168,85,247,0.15); }
        .btn-pink { background: rgba(236,72,153,0.08); border-color: rgba(236,72,153,0.15); }
        .btn-cyan { background: rgba(6,182,212,0.08); border-color: rgba(6,182,212,0.15); }
        .stream-container {
            margin-top: 12px;
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.06);
            display: none;
        }
        .stream-container.active { display: block; animation: streamFade 0.5s ease; }
        @keyframes streamFade {
            0% { opacity: 0; transform: scale(0.95); }
            100% { opacity: 1; transform: scale(1); }
        }
        .stream-container img { width: 100%; display: block; border-radius: 16px; }
        .window-list {
            max-height: 140px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .window-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 8px 12px;
            border: 1px solid rgba(255,255,255,0.04);
            font-size: 12px;
        }
        .window-item .title {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 140px;
            opacity: 0.8;
        }
        .window-item .actions { display: flex; gap: 4px; }
        .window-item .win-btn {
            background: rgba(255,255,255,0.06);
            border: none;
            border-radius: 8px;
            padding: 4px 8px;
            color: #94a3b8;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .window-item .win-btn:active {
            background: rgba(99,102,241,0.2);
            color: #e8edf5;
            transform: scale(0.9);
        }
        .window-item .win-btn.close { color: #ef4444; }
        .window-item .win-btn.close:active { background: rgba(239,68,68,0.2); }
        .status-bar {
            text-align: center;
            margin-top: 16px;
            font-size: 12px;
            color: rgba(255,255,255,0.2);
            letter-spacing: 1px;
            padding: 12px;
            border-top: 1px solid rgba(255,255,255,0.03);
        }

        /* Музыкальный блок */
        .music-info {
            margin-top: 12px;
            padding: 14px 16px;
            background: rgba(255,255,255,0.03);
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.05);
            text-align: center;
            transition: all 0.3s ease;
        }
        .music-info:hover {
            border-color: rgba(99,102,241,0.2);
        }
        .music-info .track-name {
            font-size: 18px;
            font-weight: 600;
            color: #e8edf5;
        }
        .music-info .track-artist {
            font-size: 14px;
            color: rgba(255,255,255,0.4);
            margin-top: 4px;
        }
        .music-info .track-album {
            font-size: 12px;
            color: rgba(255,255,255,0.25);
            margin-top: 2px;
        }
        .music-info .track-cover {
            margin-top: 10px;
        }
        .music-info .track-cover img {
            max-width: 100px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }

        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }

        @media (max-width: 480px) {
            .grid-4 { grid-template-columns: repeat(3,1fr); }
            .header .logo { font-size: 22px; }
            .btn { font-size: 12px; padding: 10px 4px; }
            .btn .emoji { font-size: 16px; }
            .stat-card .value { font-size: 18px; }
            .window-item .title { max-width: 100px; font-size: 11px; }
        }
        @media (max-width: 380px) {
            .grid-3 { grid-template-columns: repeat(2,1fr); }
            .grid-4 { grid-template-columns: repeat(2,1fr); }
            .stats-grid { gap: 6px; }
            .stat-card { padding: 10px 6px; }
            .stat-card .value { font-size: 16px; }
            .btn { font-size: 11px; padding: 8px 4px; }
        }
    </style>
</head>
<body>

    <div class="parallax-bg" id="parallaxBg"></div>
    <canvas id="particlesCanvas"></canvas>

    <div class="container">
        <div class="header">
            <div class="logo">✦ PULSE</div>
            <div class="subtitle"><span class="status-dot"></span>Connected</div>
            <div class="ip-box">
                <span class="label">🌐 IP-АДРЕС</span>
                <span id="ipDisplay">Загрузка...</span>
            </div>
            <div class="qr-container">
                <span class="qr-label">📱 СКАНИРУЙ QR</span>
                <img id="qrImage" src="" alt="QR" />
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="value" id="cpuStat">0%</div>
                <div class="label">CPU</div>
            </div>
            <div class="stat-card">
                <div class="value" id="ramStat">0%</div>
                <div class="label">RAM</div>
            </div>
            <div class="stat-card">
                <div class="value" id="batteryStat">--</div>
                <div class="label">BATTERY</div>
            </div>
        </div>

        <!-- ====== МУЗЫКАЛЬНЫЙ МОДУЛЬ ====== -->
        <div class="section">
            <div class="section-title"><span class="icon">🎵</span> Music Recognition</div>
            <div class="grid-2">
                <button class="btn btn-primary" onclick="getCurrentMusic()">🎵 Текущий трек</button>
            </div>
            <div class="music-info" id="musicInfo">
                <div class="track-name" id="trackName">—</div>
                <div class="track-artist" id="trackArtist">—</div>
                <div class="track-album" id="trackAlbum">—</div>
                <div class="track-cover" id="trackCover"></div>
            </div>
        </div>

        <!-- ====== СТРИМ ЭКРАНА ====== -->
        <div class="section">
            <div class="section-title"><span class="icon">🖥️</span> Screen Stream</div>
            <div class="grid-2">
                <button class="btn btn-primary" onclick="startStream()">▶ Activate</button>
                <button class="btn btn-danger" onclick="stopStream()">■ Deactivate</button>
            </div>
            <div class="stream-container" id="streamContainer">
                <img id="streamImg" src="" alt="Screen" />
            </div>
        </div>

        <!-- ====== МУЗЫКА ====== -->
        <div class="section">
            <div class="section-title"><span class="icon">🎵</span> Media</div>
            <div class="grid-4">
                <button class="btn" onclick="send('prev')">◀◀</button>
                <button class="btn btn-primary" onclick="send('playpause')">▶⏸</button>
                <button class="btn" onclick="send('next')">▶▶</button>
                <button class="btn btn-success" onclick="send('volup')">🔊+</button>
                <button class="btn" onclick="send('voldown')">🔉−</button>
                <button class="btn btn-warning" onclick="send('volmute')">🔇</button>
            </div>
        </div>

        <!-- ====== YANDEX MUSIC ====== -->
        <div class="section">
            <div class="section-title"><span class="icon">🎧</span> Yandex Music</div>
            <div class="grid-3">
                <button class="btn btn-pink" onclick="send('yandex_open')">Open</button>
                <button class="btn btn-cyan" onclick="send('yandex_my_wave')">🌊 Wave</button>
                <button class="btn" onclick="send('yandex_playlist')">📋 List</button>
                <button class="btn" onclick="send('yandex_to_my_wave')">🔄 Swap</button>
                <button class="btn btn-success" onclick="send('yandex_playlist_off')">▶ Start</button>
                <button class="btn btn-danger" onclick="send('playlist_off_custom')">⏹ Stop</button>
                <button class="btn btn-pink" onclick="send('yandex_like')">❤️ Like</button>
                <button class="btn" onclick="send('yandex_lyrics')">📝 Text</button>
                <button class="btn btn-warning" onclick="send('yandex_close_lyrics')">✕ Close</button>
            </div>
        </div>

        <!-- ====== ПРИЛОЖЕНИЯ ====== -->
        <div class="section">
            <div class="section-title"><span class="icon">🤖</span> Apps</div>
            <div class="grid-3">
                <button class="btn" onclick="send('minecraft')">⛏ MC</button>
                <button class="btn btn-purple" onclick="send('deepseek_app')">🧠 DS</button>
                <button class="btn btn-cyan" onclick="send('telegram')">📱 TG</button>
                <button class="btn btn-warning" onclick="send('vpn')">🔒 VPN</button>
                <button class="btn" onclick="send('yandex_browser')">🌐 Ya</button>
                <button class="btn" onclick="send('new_notepad')">📝 NP</button>
                <button class="btn" onclick="send('calc')">🧮 Calc</button>
                <button class="btn" onclick="send('cmd')">💻 CMD</button>
                <button class="btn btn-primary" onclick="send('browser')">🌍 Chrome</button>
            </div>
        </div>

        <!-- ====== СИСТЕМА ====== -->
        <div class="section">
            <div class="section-title"><span class="icon">⚙️</span> System</div>
            <div class="grid-3">
                <button class="btn btn-warning" onclick="send('monitor_off')">🖥️ Off</button>
                <button class="btn btn-primary" onclick="send('monitor_on')">🖥️ On</button>
                <button class="btn" onclick="send('lock')">🔒 Lock</button>
                <button class="btn" onclick="send('minimize_all')">⬜ Mini</button>
                <button class="btn" onclick="send('show_desktop')">🖥️ Desk</button>
                <button class="btn btn-primary" onclick="send('screenshot')">📸 Shot</button>
                <button class="btn" onclick="send('empty_recycle_bin')">🗑️ Trash</button>
                <button class="btn btn-warning" onclick="send('sleep')">💤 Sleep</button>
                <button class="btn btn-danger" onclick="if(confirm('Restart PC?')) send('restart')">🔄 Restart</button>
                <button class="btn btn-danger" onclick="if(confirm('SHUTDOWN PC?')) send('shutdown')">⛔ Shutdown</button>
            </div>
        </div>

        <!-- ====== ОКНА ====== -->
        <div class="section">
            <div class="section-title"><span class="icon">🪟</span> Windows</div>
            <button class="btn btn-primary" onclick="refreshWindows()" style="width:100%;margin-bottom:10px;">↻ Scan</button>
            <div class="window-list" id="windowList"></div>
        </div>

        <!-- ====== СЦЕНАРИИ ====== -->
        <div class="section">
            <div class="section-title"><span class="icon">🎮</span> Scenarios</div>
            <div class="grid-3">
                <button class="btn btn-success" onclick="send('scenario_gaming')">🎮 Gaming</button>
                <button class="btn btn-primary" onclick="send('scenario_work')">💼 Work</button>
                <button class="btn btn-danger" onclick="send('panic')">💀 Panic</button>
                <button class="btn btn-purple" onclick="send('osk')">📋 Keyboard</button>
            </div>
        </div>

        <div class="status-bar">● SYSTEM READY</div>
    </div>

    <script>
        // ========== ПАРАЛЛАКС ==========
        document.addEventListener('mousemove', function(e) {
            const x = (e.clientX / window.innerWidth - 0.5) * 20;
            const y = (e.clientY / window.innerHeight - 0.5) * 20;
            document.getElementById('parallaxBg').style.transform = `translate(${x}px, ${y}px) scale(1.02)`;
        });
        if (window.DeviceOrientationEvent) {
            window.addEventListener('deviceorientation', function(e) {
                const x = (e.gamma || 0) / 30;
                const y = (e.beta || 0) / 30 - 15;
                document.getElementById('parallaxBg').style.transform = `translate(${x}px, ${y}px) scale(1.02)`;
            });
        }

        // ========== ЧАСТИЦЫ ==========
        const canvas = document.getElementById('particlesCanvas');
        const ctx = canvas.getContext('2d');
        let particles = [];
        let mouseX = 0, mouseY = 0;

        function resizeCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();

        class Particle {
            constructor() { this.reset(); }
            reset() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.size = Math.random() * 2 + 1;
                this.speedX = (Math.random() - 0.5) * 0.5;
                this.speedY = (Math.random() - 0.5) * 0.5;
                this.opacity = Math.random() * 0.5 + 0.2;
            }
            update() {
                this.x += this.speedX;
                this.y += this.speedY;
                const dx = mouseX - this.x;
                const dy = mouseY - this.y;
                const dist = Math.sqrt(dx*dx + dy*dy);
                if (dist < 200) {
                    const force = (200 - dist) / 200 * 0.02;
                    this.x += dx * force;
                    this.y += dy * force;
                }
                if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) this.reset();
            }
            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(129, 140, 248, ${this.opacity})`;
                ctx.fill();
            }
        }

        for (let i = 0; i < 80; i++) particles.push(new Particle());

        function animateParticles() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach(p => { p.update(); p.draw(); });
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx*dx + dy*dy);
                    if (dist < 120) {
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = `rgba(129, 140, 248, ${0.08 * (1 - dist / 120)})`;
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    }
                }
            }
            requestAnimationFrame(animateParticles);
        }
        animateParticles();

        document.addEventListener('mousemove', function(e) { mouseX = e.clientX; mouseY = e.clientY; });
        document.addEventListener('touchmove', function(e) {
            const touch = e.touches[0];
            mouseX = touch.clientX;
            mouseY = touch.clientY;
        });

        // ========== ОСНОВНОЙ JS ==========
        function fetchIP() {
            fetch('/get_ip').then(r => r.text()).then(ip => {
                document.getElementById('ipDisplay').innerText = ip;
                document.getElementById('qrImage').src = '/qr?t=' + Date.now();
            });
        }

        function send(cmd) { fetch('/cmd?action=' + cmd); }

        // ========== МУЗЫКА ==========
        function getCurrentMusic() {
            const nameEl = document.getElementById('trackName');
            const artistEl = document.getElementById('trackArtist');
            const albumEl = document.getElementById('trackAlbum');
            const coverEl = document.getElementById('trackCover');
            nameEl.innerText = '🔍 Поиск...';
            artistEl.innerText = '—';
            albumEl.innerText = '—';
            coverEl.innerHTML = '';

            fetch('/music')
                .then(r => r.json())
                .then(track => {
                    nameEl.innerText = track.title || 'Неизвестно';
                    artistEl.innerText = track.artist || '—';
                    albumEl.innerText = track.album || '—';
                    if (track.cover) {
                        coverEl.innerHTML = `<img src="${track.cover}" alt="Cover" />`;
                    }
                })
                .catch(() => {
                    nameEl.innerText = '❌ Ошибка';
                    artistEl.innerText = 'Попробуйте снова';
                });
        }

        // ========== СТРИМ ==========
        function startStream() {
            const container = document.getElementById('streamContainer');
            const img = document.getElementById('streamImg');
            img.src = '/screen?' + Date.now();
            container.classList.add('active');
        }
        function stopStream() {
            document.getElementById('streamContainer').classList.remove('active');
            document.getElementById('streamImg').src = '';
        }

        // ========== ОКНА ==========
        function refreshWindows() {
            fetch('/get_windows').then(r => r.json()).then(w => {
                document.getElementById('windowList').innerHTML = w.map(win =>
                    `<div class="window-item">
                        <span class="title">📌 ${win.title}</span>
                        <div class="actions">
                            <button class="win-btn" onclick="windowAction('focus',${win.hwnd})">👁</button>
                            <button class="win-btn" onclick="windowAction('minimize',${win.hwnd})">−</button>
                            <button class="win-btn" onclick="windowAction('maximize',${win.hwnd})">🗖</button>
                            <button class="win-btn close" onclick="windowAction('close',${win.hwnd})">✕</button>
                        </div>
                    </div>`
                ).join('');
            });
        }
        function windowAction(a, h) { fetch('/window?action=' + a + '&hwnd=' + h); setTimeout(refreshWindows, 500); }

        // ========== СТАТИСТИКА ==========
        let prevCpu = 0, prevRam = 0;
        function updateStats() {
            fetch('/stats').then(r => r.json()).then(s => {
                const cpuEl = document.getElementById('cpuStat');
                const ramEl = document.getElementById('ramStat');
                const batteryEl = document.getElementById('batteryStat');
                if (s.cpu !== prevCpu) { cpuEl.classList.remove('animate'); setTimeout(() => cpuEl.classList.add('animate'), 10); prevCpu = s.cpu; }
                if (s.ram !== prevRam) { ramEl.classList.remove('animate'); setTimeout(() => ramEl.classList.add('animate'), 10); prevRam = s.ram; }
                cpuEl.innerText = s.cpu + '%';
                ramEl.innerText = s.ram + '%';
                batteryEl.innerText = s.battery ? s.battery + '%' : '--';
            });
        }

        // ========== АВТОЗАПУСК ==========
        fetchIP();
        setInterval(fetchIP, 30000);
        setInterval(updateStats, 2000);
        refreshWindows();
        updateStats();
        setInterval(getCurrentMusic, 10000);
        console.log('✨ PULSE ACTIVATED');
    </script>

</body>
</html>
'''

# ═══════════════════════════════════════════════════════════════════════════
# МАРШРУТЫ
# ═══════════════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/get_ip')
def get_ip_route():
    return get_ip()

@app.route('/qr')
def qr_route():
    try:
        ip = get_ip()
        url = f"http://{ip}:5000"
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(url)
        qr.make()
        img = qr.make_image()
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return Response(buffer.getvalue(), mimetype='image/png')
    except Exception as e:
        return '', 500

@app.route('/music')
def music_route():
    track = get_current_track()
    return {
        "title": track.get("title", "Неизвестно"),
        "artist": track.get("artist", ""),
        "album": track.get("album", ""),
        "cover": track.get("cover", ""),
        "url": track.get("url", "")
    }

@app.route('/cmd')
def cmd_route():
    action = request.args.get('action')
    print(f"🔘 НАЖАТА КНОПКА: {action}")
    
    actions = {
        'volup': volume_up, 'voldown': volume_down, 'volmute': volume_mute,
        'playpause': media_play_pause, 'next': media_next, 'prev': media_prev,
        'minecraft': action_minecraft, 'yandex_open': action_yandex_open, 'yandex_my_wave': action_yandex_my_wave,
        'yandex_playlist': action_yandex_playlist, 'yandex_playlist_off': action_yandex_playlist_off,
        'yandex_to_my_wave': action_yandex_to_my_wave, 'yandex_like': action_yandex_like, 'yandex_lyrics': action_yandex_lyrics,
        'yandex_close_lyrics': action_yandex_close_lyrics, 'playlist_off_custom': action_playlist_off_custom,
        'deepseek_app': action_deepseek_app, 'telegram': action_telegram, 'vpn': action_vpn,
        'yandex_browser': action_yandex_browser, 'new_notepad': action_new_notepad, 'calc': action_calc, 'cmd': action_cmd, 'browser': action_browser,
        'monitor_off': monitor_off, 'monitor_on': monitor_on, 'minimize_all': minimize_all_windows, 'show_desktop': show_desktop,
        'lock': action_lock, 'screenshot': action_screenshot, 'empty_recycle_bin': empty_recycle_bin,
        'sleep': action_sleep, 'restart': action_restart, 'shutdown': action_shutdown,
        'scenario_gaming': scenario_gaming, 'scenario_work': scenario_work, 'panic': panic, 'osk': action_osk,
    }
    if action in actions:
        threading.Thread(target=actions[action]).start()
    return 'OK'

@app.route('/window')
def window_route():
    action = request.args.get('action')
    hwnd = int(request.args.get('hwnd', 0))
    if action == 'close':
        close_window(hwnd)
    elif action == 'minimize':
        minimize_window(hwnd)
    elif action == 'maximize':
        maximize_window(hwnd)
    elif action == 'focus':
        restore_window(hwnd)
    return 'OK'

@app.route('/get_windows')
def get_windows():
    return get_windows_list()

@app.route('/stats')
def stats():
    return {
        'cpu': psutil.cpu_percent(),
        'ram': psutil.virtual_memory().percent,
        'battery': psutil.sensors_battery().percent if psutil.sensors_battery() else None
    }

@app.route('/screen')
def screen():
    return Response(generate_screen_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    ip = get_ip()
    print("=" * 60)
    print("  ██████╗██╗   ██╗██╗     ███████╗███████╗")
    print("  ██╔════╝╚██╗ ██╔╝██║     ██╔════╝██╔════╝")
    print("  ██║      ╚████╔╝ ██║     █████╗  ███████╗")
    print("  ██║       ╚██╔╝  ██║     ██╔══╝  ╚════██║")
    print("  ╚██████╗   ██║   ███████╗███████╗███████║")
    print("   ╚═════╝   ╚═╝   ╚══════╝╚══════╝╚══════╝")
    print("=" * 60)
    print(f"  🔥 PULSE ЗАПУЩЕН: http://{ip}:5000")
    print("=" * 60)
    show_qr_code()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)