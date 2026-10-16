# name=main_13.py
import sys
import os
import sqlite3
import requests
import uuid
import webbrowser
import subprocess
import re
import time
import secrets
import shutil
import json
import logging
import traceback
import urllib.request
import urllib.parse
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.serving import make_server
from PySide6.QtCore import Qt, QTimer, QSize, QThread, Signal, QRectF, QPointF
from PySide6.QtGui import (QIcon, QPixmap, QAction, QPainter, QColor, QFont, QPen, QBrush, QPolygonF, QKeySequence,
                           QTextCursor)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QDialog, QFormLayout, QMessageBox, QComboBox,
                               QListWidget, QListWidgetItem, QMenu, QCheckBox,
                               QFrame, QTabWidget, QStyledItemDelegate, QStyle,
                               QTextEdit, QProgressBar, QStackedWidget, QSplitter, QGridLayout, QKeySequenceEdit,
                               QColorDialog, QScrollArea, QInputDialog, QFileDialog)

CLIENT_DB = "client_servers.db"
DB_NAME = "server_library.db"
LOG_FILE = "server_activity.log"
BACKUP_DIR = "backups"

# --- PERSISTENT LOGGING SETUP ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def log_event(message):
    logging.info(message)


# --- GLOBAL DEBUG TRACING & PROFILING SYSTEM ---
DEBUG_TRACING_ENABLED = True


def trace_execution(cls_name=None):
    """Decorator to trace method entry, successful exit, or runtime crashes with exact timestamps."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            name = cls_name or (args[0].__class__.__name__ if args else "GlobalContext")
            method_name = func.__name__
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

            if DEBUG_TRACING_ENABLED:
                log_event(f"[DEBUG-TRACE START] [{timestamp}] Class: {name} | Method: {method_name} running...")
            try:
                result = func(*args, **kwargs)
                if DEBUG_TRACING_ENABLED:
                    end_timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    log_event(
                        f"[DEBUG-TRACE END] [{end_timestamp}] Class: {name} | Method: {method_name} finished successfully.")
                return result
            except Exception as e:
                err_timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                error_trace = traceback.format_exc()
                log_event(
                    f"[CRASH-TRACE ERROR] [{err_timestamp}] CRASH in Class: {name} | Method: {method_name} -> {e}\n{error_trace}")
                raise e

        return wrapper

    return decorator


# --- THEMES ---
DARK_STYLESHEET = """
QMainWindow {
    background-color: #0B130F;
}
QWidget {
    color: #F1F5F9;
    font-family: 'Segoe UI', SF Pro Display, Helvetica, Arial, sans-serif;
}
QFrame#MetricCard, QFrame#DashboardCard, QFrame#PanelFrame, QFrame#SidebarFrame {
    background-color: #132219;
    border: 1px solid #1E3A29;
    border-radius: 12px;
}
QFrame#SidebarFrame {
    border-top: none;
    border-bottom: none;
    border-left: none;
    border-right: 1px solid #1E3A29;
    border-radius: 0px;
}
QLabel#MetricValue {
    font-size: 20px;
    font-weight: bold;
    color: %ACCENT_COLOR%;
}
QLabel#MetricLabel, QLabel {
    color: #A3B8CC;
    font-weight: 600;
}
QLabel#PanelHeader, QLabel#CardTitle {
    font-weight: bold;
    color: %ACCENT_COLOR%;
}
QLineEdit, QComboBox, QTextEdit {
    background-color: #0B130F;
    border: 1px solid #1E3A29;
    border-radius: 8px;
    padding: 8px 12px;
    color: #F1F5F9;
    selection-background-color: %ACCENT_COLOR%;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid %ACCENT_COLOR%;
}
QLineEdit:read-only {
    background-color: #132219;
    color: #22C55E;
}
QPushButton {
    background-color: %ACCENT_COLOR%;
    color: #FFFFFF;
    font-weight: bold;
    border: 1px solid #22C55E;
    border-radius: 8px;
    padding: 8px 16px;
}
QPushButton:hover {
    background-color: #008000;
}
QPushButton#SecondaryBtn {
    background-color: #1E3A29;
    color: %ACCENT_COLOR%;
    border: 1px solid #2D5A3C;
}
QPushButton#SecondaryBtn:hover {
    background-color: #2D5A3C;
}
QPushButton#StopBtn {
    background-color: #7F1D1D;
    border: 1px solid #EF4444;
    color: #FFFFFF;
}
QPushButton#StopBtn:hover {
    background-color: #991B1B;
}
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}
QListWidget#SidebarList::item {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 4px;
    color: #A3B8CC;
    font-weight: bold;
}
QListWidget#SidebarList::item:hover {
    background-color: #1E3A29;
    color: %ACCENT_COLOR%;
}
QListWidget#SidebarList::item:selected {
    background-color: %ACCENT_COLOR%;
    color: #FFFFFF;
    border: 1px solid %ACCENT_COLOR%;
}
QListWidget::item {
    background-color: #0B130F;
    border: 1px solid #1E3A29;
    border-radius: 8px;
    padding: 8px;
    margin-bottom: 6px;
    color: #F1F5F9;
}
QListWidget::item:hover {
    background-color: #132219;
    border-color: %ACCENT_COLOR%;
}
QListWidget::item:selected {
    background-color: %ACCENT_COLOR%;
    border-color: %ACCENT_COLOR%;
    color: #FFFFFF;
}
QTabWidget::pane {
    border: 1px solid #1E3A29;
    background-color: transparent;
    border-radius: 8px;
}
QTabBar::tab {
    background-color: #0B130F;
    color: #A3B8CC;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background-color: #132219;
    color: %ACCENT_COLOR%;
    border-bottom: 2px solid %ACCENT_COLOR%;
}
QMenu {
    background-color: #132219;
    border: 1px solid #1E3A29;
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    padding: 6px 20px 6px 10px;
    border-radius: 4px;
    color: #F1F5F9;
}
QMenu::item:selected {
    background-color: %ACCENT_COLOR%;
    color: #FFFFFF;
}
QDialog {
    background-color: #132219;
}
QCheckBox {
    color: #F1F5F9;
}
QTextEdit {
    color: #22C55E;
    font-family: 'Consolas', 'Courier New', monospace;
}
QListWidget#HostingServersList::item {
    background-color: transparent;
    border: none;
    padding: 0px;
    margin-bottom: 6px;
}
"""

LIGHT_STYLESHEET = """
QMainWindow {
    background-color: #F8FAFC;
}
QWidget {
    color: #0F172A;
    font-family: 'Segoe UI', SF Pro Display, Helvetica, Arial, sans-serif;
}
QFrame#MetricCard, QFrame#DashboardCard, QFrame#PanelFrame, QFrame#SidebarFrame {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 12px;
}
QFrame#SidebarFrame {
    border-top: none;
    border-bottom: none;
    border-left: none;
    border-right: 1px solid #CBD5E1;
    border-radius: 0px;
}
QLabel#MetricValue {
    font-size: 20px;
    font-weight: bold;
    color: %ACCENT_COLOR%;
}
QLabel#MetricLabel, QLabel {
    color: #475569;
    font-weight: 600;
}
QLabel#PanelHeader, QLabel#CardTitle {
    font-weight: bold;
    color: %ACCENT_COLOR%;
}
QLineEdit, QComboBox, QTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px 12px;
    color: #0F172A;
    selection-background-color: %ACCENT_COLOR%;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid %ACCENT_COLOR%;
}
QLineEdit:read-only {
    background-color: #F1F5F9;
    color: #16A34A;
}
QPushButton {
    background-color: %ACCENT_COLOR%;
    color: #FFFFFF;
    font-weight: bold;
    border: 1px solid #16A34A;
    border-radius: 8px;
    padding: 8px 16px;
}
QPushButton:hover {
    opacity: 0.9;
}
QPushButton#SecondaryBtn {
    background-color: #E2E8F0;
    color: %ACCENT_COLOR%;
    border: 1px solid #CBD5E1;
}
QPushButton#SecondaryBtn:hover {
    background-color: #CBD5E1;
}
QPushButton#StopBtn {
    background-color: #DC2626;
    border: 1px solid #B91C1C;
    color: #FFFFFF;
}
QPushButton#StopBtn:hover {
    background-color: #B91C1C;
}
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}
QListWidget#SidebarList::item {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 4px;
    color: #475569;
    font-weight: bold;
}
QListWidget#SidebarList::item:hover {
    background-color: #E2E8F0;
    color: %ACCENT_COLOR%;
}
QListWidget#SidebarList::item:selected {
    background-color: %ACCENT_COLOR%;
    color: #FFFFFF;
    border: 1px solid %ACCENT_COLOR%;
}
QListWidget::item {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px;
    margin-bottom: 6px;
    color: #0F172A;
}
QListWidget::item:hover {
    background-color: #F1F5F9;
    border-color: %ACCENT_COLOR%;
}
QListWidget::item:selected {
    background-color: %ACCENT_COLOR%;
    border-color: %ACCENT_COLOR%;
    color: #FFFFFF;
}
QTabWidget::pane {
    border: 1px solid #CBD5E1;
    background-color: transparent;
    border-radius: 8px;
}
QTabBar::tab {
    background-color: #E2E8F0;
    color: #475569;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: %ACCENT_COLOR%;
    border-bottom: 2px solid %ACCENT_COLOR%;
}
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    padding: 6px 20px 6px 10px;
    border-radius: 4px;
    color: #0F172A;
}
QMenu::item:selected {
    background-color: %ACCENT_COLOR%;
    color: #FFFFFF;
}
QDialog {
    background-color: #FFFFFF;
}
QCheckBox {
    color: #0F172A;
}
QTextEdit {
    color: #16A34A;
    font-family: 'Consolas', 'Courier New', monospace;
}
QListWidget#HostingServersList::item {
    background-color: transparent;
    border: none;
    padding: 0px;
    margin-bottom: 6px;
}
"""


# --- DATABASE INITIALIZATIONS ---
def init_client_db():
    conn = sqlite3.connect(CLIENT_DB, timeout=30.0)
    cursor = conn.cursor()
    cursor.execute('PRAGMA journal_mode=WAL;')
    cursor.execute('PRAGMA busy_timeout=5000;')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS connected_servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_name TEXT UNIQUE NOT NULL,
            url TEXT NOT NULL,
            server_key TEXT,
            session_token TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_config (
            client_id TEXT PRIMARY KEY,
            username TEXT,
            dob TEXT DEFAULT '2000-01-01'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorite_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_name TEXT NOT NULL,
            link_id INTEGER NOT NULL,
            title TEXT,
            url TEXT,
            item_type TEXT,
            UNIQUE(server_name, link_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS offline_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_name TEXT NOT NULL,
            link_id INTEGER NOT NULL,
            title TEXT,
            url TEXT,
            item_type TEXT,
            is_public INTEGER,
            username TEXT,
            UNIQUE(server_name, link_id)
        )
    ''')
    cursor.execute('SELECT client_id, username FROM client_config')
    if not cursor.fetchone():
        c_id = f"user_{uuid.uuid4().hex[:8]}"
        cursor.execute('INSERT INTO client_config (client_id, username, dob) VALUES (?, ?, ?)',
                       (c_id, f"User_{c_id[5:]}", '2000-01-01'))
    conn.commit()
    conn.close()


def init_server_db():
    conn = sqlite3.connect(DB_NAME, timeout=30.0)
    cursor = conn.cursor()
    cursor.execute('PRAGMA journal_mode=WAL;')
    cursor.execute('PRAGMA busy_timeout=5000;')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shared_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            item_type TEXT NOT NULL,
            is_public INTEGER NOT NULL,
            parent_path TEXT DEFAULT '/',
            is_hidden INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            role TEXT CHECK(role IN ('user', 'moderator')) DEFAULT 'user',
            can_write INTEGER DEFAULT 1,
            can_read INTEGER DEFAULT 1,
            is_banned INTEGER DEFAULT 0,
            timeout_until REAL DEFAULT 0,
            session_token TEXT,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            dob TEXT DEFAULT '2000-01-01',
            is_host INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()


init_client_db()
init_server_db()


def get_setting(key, default=""):
    conn = sqlite3.connect(CLIENT_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM app_settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default


def save_setting(key, value):
    conn = sqlite3.connect(CLIENT_DB)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()


def reset_all_settings():
    conn = sqlite3.connect(CLIENT_DB)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM app_settings')
    conn.commit()
    conn.close()


def perform_sqlite_backup():
    if not os.path.exists(DB_NAME):
        return
    storage_dir = get_setting("storage_dir", "")
    target_backup_dir = os.path.join(storage_dir, BACKUP_DIR) if storage_dir else BACKUP_DIR

    if not os.path.exists(target_backup_dir):
        os.makedirs(target_backup_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(target_backup_dir, f"backup_{timestamp}.db")
    try:
        src = sqlite3.connect(DB_NAME)
        dst = sqlite3.connect(backup_path)
        with dst:
            src.backup(dst)
        dst.close()
        src.close()
        log_event(f"Automated SQLite backup successfully created: {backup_path}")
    except Exception as e:
        log_event(f"Failed to perform automated SQLite backup: {e}")


# --- FLASK APP & BACKEND LOGIC ---
flask_app = Flask(__name__)
CURRENT_SERVER_KEY = secrets.token_hex(8).upper()
CLIENT_REQUEST_TIMES = {}
RATE_LIMIT_MAX_REQUESTS = 30
RATE_LIMIT_WINDOW = 60


@flask_app.before_request
def apply_rate_limit():
    if request.method == 'OPTIONS':
        return
    client_ip = request.remote_addr or "127.0.0.1"
    client_id = request.headers.get('X-Client-ID') or client_ip
    now = time.time()
    history = CLIENT_REQUEST_TIMES.get(client_id, [])
    history = [t for t in history if now - t < RATE_LIMIT_WINDOW]
    if len(history) >= RATE_LIMIT_MAX_REQUESTS:
        return jsonify({"error": "Rate limit exceeded. Try again later."}), 429
    history.append(now)
    CLIENT_REQUEST_TIMES[client_id] = history


@flask_app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        response = flask_app.make_default_options_response()
        headers = response.headers
        headers['Access-Control-Allow-Origin'] = '*'
        headers[
            'Access-Control-Allow-Headers'] = 'Content-Type, bypass-tunnel-reminder, X-Client-ID, X-Server-Key, X-Session-Token, User-Agent'
        headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        return response, 200


@flask_app.after_request
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers[
        'Access-Control-Allow-Headers'] = 'Content-Type, bypass-tunnel-reminder, X-Client-ID, X-Server-Key, X-Session-Token, User-Agent'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['bypass-tunnel-reminder'] = 'true'
    return response


def verify_client_access(req):
    client_id = req.headers.get('X-Client-ID') or req.args.get('user_id')
    provided_key = req.headers.get('X-Server-Key')
    session_token = req.headers.get('X-Session-Token')

    if not client_id:
        return False, "Missing User ID", None

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT user_id, role, can_write, can_read, is_banned, timeout_until, session_token, dob, is_host FROM users WHERE user_id = ?',
        (client_id,))
    user = cursor.fetchone()

    if user:
        if user[4] == 1:
            conn.close()
            return False, "User is banned from this server", None
        if user[5] and user[5] > time.time():
            conn.close()
            return False, f"User is timed out until {datetime.fromtimestamp(user[5]).strftime('%H:%M:%S')}", user

        new_token = secrets.token_hex(16)
        cursor.execute('UPDATE users SET session_token = ?, last_seen = CURRENT_TIMESTAMP WHERE user_id = ?',
                       (new_token, client_id))
        conn.commit()
        conn.close()
        return True, new_token, user

    if provided_key == CURRENT_SERVER_KEY:
        new_token = secrets.token_hex(16)
        assigned_role = 'moderator'

        cursor.execute('''
            INSERT INTO users (user_id, role, can_write, can_read, is_banned, timeout_until, session_token, last_seen, dob, is_host) 
            VALUES (?, ?, 1, 1, 0, 0, ?, CURRENT_TIMESTAMP, '2000-01-01', 0)
            ON CONFLICT(user_id) DO UPDATE SET session_token=?, last_seen=CURRENT_TIMESTAMP
        ''', (client_id, assigned_role, new_token, new_token))
        conn.commit()

        cursor.execute(
            'SELECT user_id, role, can_write, can_read, is_banned, timeout_until, session_token, dob, is_host FROM users WHERE user_id = ?',
            (client_id,))
        user = cursor.fetchone()
        conn.close()
        return True, new_token, user

    conn.close()
    return False, "Invalid Space Key. New users require the current server key to register.", None


@flask_app.route('/api/auth/connect', methods=['POST', 'OPTIONS'])
def auth_connect():
    auth_ok, message_or_token, user_data = verify_client_access(request)
    if not auth_ok:
        return jsonify({"error": message_or_token}), 401
    data = request.json or {}
    custom_username = data.get('username')
    if custom_username:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (custom_username, user_data[0]))
        conn.commit()
        conn.close()
    return jsonify({
        "status": "connected",
        "session_token": message_or_token,
        "role": user_data[1] if user_data else "user",
        "can_write": bool(user_data[2]) if user_data else True,
        "can_read": bool(user_data[3]) if user_data else True
    }), 200


@flask_app.route('/api/user/profile', methods=['GET', 'POST', 'OPTIONS'])
def user_profile():
    auth_ok, token_or_err, user_data = verify_client_access(request)
    if not auth_ok:
        return jsonify({"error": token_or_err}), 401
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json or {}
        new_username = data.get('username', '')
        new_dob = data.get('dob', '')
        if new_username:
            cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (new_username, user_data[0]))
        if new_dob:
            cursor.execute('UPDATE users SET dob = ? WHERE user_id = ?', (new_dob, user_data[0]))
        conn.commit()
    cursor.execute('SELECT user_id, username, role, can_write, can_read, dob FROM users WHERE user_id = ?',
                   (user_data[0],))
    u = cursor.fetchone()
    conn.close()
    return jsonify({
        "user_id": u[0],
        "username": u[1] or u[0],
        "role": u[2],
        "can_write": bool(u[3]),
        "can_read": bool(u[4]),
        "dob": u[5] or '2000-01-01',
        "session_token": token_or_err
    }), 200


@flask_app.route('/api/links', methods=['GET', 'OPTIONS'])
def get_links():
    auth_ok, err_or_token, user_data = verify_client_access(request)
    if not auth_ok:
        return jsonify({"error": err_or_token}), 401
    if user_data[5] and user_data[5] > time.time():
        return jsonify(
            {"error": f"User is timed out until {datetime.fromtimestamp(user_data[5]).strftime('%H:%M:%S')}"}), 403
    if user_data[3] == 0 and user_data[1] != 'moderator':
        return jsonify({"error": "Read access revoked by moderator"}), 403

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    user_role = user_data[1] if user_data else 'user'
    if user_role == 'moderator':
        cursor.execute('''
            SELECT l.id, l.user_id, COALESCE(u.username, l.user_id), l.title, l.url, l.item_type, l.is_public, l.parent_path, l.is_hidden 
            FROM shared_links l
            LEFT JOIN users u ON l.user_id = u.user_id
        ''')
    else:
        cursor.execute('''
            SELECT l.id, l.user_id, COALESCE(u.username, l.user_id), l.title, l.url, l.item_type, l.is_public, l.parent_path, l.is_hidden 
            FROM shared_links l
            LEFT JOIN users u ON l.user_id = u.user_id
            WHERE l.is_hidden = 0 AND (l.is_public = 1 OR l.user_id = ?)
        ''', (user_data[0],))
    rows = cursor.fetchall()
    conn.close()
    links = [{
        "id": row[0],
        "user_id": row[1],
        "username": row[2],
        "title": row[3],
        "url": row[4],
        "item_type": row[5],
        "is_public": bool(row[6]),
        "parent_path": row[7],
        "is_hidden": bool(row[8]),
        "session_token": err_or_token
    } for row in rows]
    return jsonify(links), 200


@flask_app.route('/api/links', methods=['POST', 'PUT', 'DELETE', 'OPTIONS'])
def manage_links():
    auth_ok, err_or_token, user_data = verify_client_access(request)
    if not auth_ok:
        return jsonify({"error": err_or_token}), 401
    if user_data[5] and user_data[5] > time.time():
        return jsonify({"error": "User is timed out"}), 403
    if not user_data[2] and user_data[1] != 'moderator':
        return jsonify({"error": "Upload/Write access revoked by moderator"}), 403

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json or {}
        url = data.get('url', '')
        if not url:
            conn.close()
            return jsonify({"error": "URL cannot be empty"}), 400
        cursor.execute('''
            INSERT INTO shared_links (user_id, title, url, item_type, is_public, parent_path, is_hidden)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (user_data[0], data['title'], url, data.get('item_type', 'file'), int(data.get('is_public', 1)),
              data.get('parent_path', '/')))
        conn.commit()
        conn.close()
        return jsonify({"message": "Attached successfully", "session_token": err_or_token}), 201
    elif request.method == 'PUT':
        data = request.json or {}
        link_id = data.get('id')
        cursor.execute('SELECT user_id FROM shared_links WHERE id = ?', (link_id,))
        row = cursor.fetchone()
        if not row or (row[0] != user_data[0] and user_data[1] != 'moderator'):
            conn.close()
            return jsonify({"error": "Permission denied."}), 403

        cursor.execute('''
            UPDATE shared_links SET title = ?, url = ?, item_type = ?, is_public = ? WHERE id = ?
        ''', (data['title'], data['url'], data.get('item_type', 'file'), int(data.get('is_public', 1)), link_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Attachment updated successfully", "session_token": err_or_token}), 200
    elif request.method == 'DELETE':
        link_id = request.args.get('id')
        cursor.execute('SELECT user_id FROM shared_links WHERE id = ?', (link_id,))
        row = cursor.fetchone()
        if row and row[0] != user_data[0] and user_data[1] != 'moderator':
            conn.close()
            return jsonify({"error": "Permission denied."}), 403

        cursor.execute('DELETE FROM shared_links WHERE id = ?', (link_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Attachment deleted successfully", "session_token": err_or_token}), 200


@flask_app.route('/api/moderator/user_action', methods=['POST', 'OPTIONS'])
def moderator_user_action():
    auth_ok, _, user_data = verify_client_access(request)
    if not auth_ok or (user_data and user_data[1] != 'moderator'):
        return jsonify({"error": "Unauthorized moderator action"}), 403

    data = request.json or {}
    target_user_id = data.get('user_id')
    action = data.get('action')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT is_host FROM users WHERE user_id = ?', (target_user_id,))
    target_user = cursor.fetchone()
    is_target_host = target_user and target_user[0] == 1

    if action == 'toggle_moderator':
        if is_target_host:
            conn.close()
            return jsonify({"error": "Cannot change permissions of the host moderator."}), 400
        cursor.execute('SELECT role FROM users WHERE user_id = ?', (target_user_id,))
        row = cursor.fetchone()
        if row:
            new_role = 'user' if row[0] == 'moderator' else 'moderator'
            cursor.execute('UPDATE users SET role = ? WHERE user_id = ?', (new_role, target_user_id))
            conn.commit()
    elif action == 'revoke_access':
        if is_target_host:
            conn.close()
            return jsonify({"error": "Cannot revoke access from the host."}), 400
        can_read = data.get('can_read', 1)
        can_write = data.get('can_write', 1)
        cursor.execute('UPDATE users SET can_read = ?, can_write = ? WHERE user_id = ?',
                       (can_read, can_write, target_user_id))
        conn.commit()
    elif action == 'ban':
        if is_target_host:
            conn.close()
            return jsonify({"error": "Cannot ban the host."}), 400
        is_banned = data.get('is_banned', 1)
        cursor.execute('UPDATE users SET is_banned = ? WHERE user_id = ?', (is_banned, target_user_id))
        conn.commit()
    elif action == 'timeout':
        if is_target_host:
            conn.close()
            return jsonify({"error": "Cannot timeout the host."}), 400
        duration = data.get('duration_seconds', 0)
        timeout_until = time.time() + duration if duration > 0 else 0
        cursor.execute('UPDATE users SET timeout_until = ? WHERE user_id = ?', (timeout_until, target_user_id))
        conn.commit()
    elif action == 'remove_user':
        if is_target_host:
            conn.close()
            return jsonify({"error": "Cannot remove the host from the server."}), 400
        cursor.execute('UPDATE users SET is_banned = 1, session_token = NULL WHERE user_id = ?', (target_user_id,))
        conn.commit()

    conn.close()
    return jsonify({"status": "success"}), 200


@flask_app.route('/api/moderator/file_action', methods=['POST', 'OPTIONS'])
def moderator_file_action():
    auth_ok, _, user_data = verify_client_access(request)
    if not auth_ok or (user_data and user_data[1] != 'moderator'):
        return jsonify({"error": "Unauthorized moderator action"}), 403

    data = request.json or {}
    link_id = data.get('link_id')
    action = data.get('action')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if action == 'hide':
        is_hidden = data.get('is_hidden', 1)
        cursor.execute('UPDATE shared_links SET is_hidden = ? WHERE id = ?', (is_hidden, link_id))
        conn.commit()
    elif action == 'remove':
        cursor.execute('DELETE FROM shared_links WHERE id = ?', (link_id,))
        conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 200


class FlaskThread(QThread):
    def __init__(self):
        super().__init__()
        self.server = None

    @trace_execution("FlaskThread")
    def run(self):
        self.server = make_server('0.0.0.0', 5000, flask_app, threaded=True)
        self.server.serve_forever()

    @trace_execution("FlaskThread")
    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server = None


class TunnelThread(QThread):
    url_found = Signal(str)
    log_signal = Signal(str)

    def __init__(self, subdomain=None):
        super().__init__()
        self.process = None
        self.subdomain = subdomain
        self.running = True

    @trace_execution("TunnelThread")
    def run(self):
        cmd = ["lt", "--port", "5000"]
        if self.subdomain:
            cmd.extend(["--subdomain", self.subdomain])
        while self.running:
            self.log_signal.emit("Launching connection tunnel...")
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=(sys.platform == 'win32')
            )
            while self.running and self.process and self.process.poll() is None:
                line = self.process.stdout.readline()
                if line:
                    stripped = line.strip()
                    self.log_signal.emit(stripped)
                    match = re.search(r'https://[a-zA-Z0-9-]+\.loca\.lt', stripped)
                    if match:
                        self.url_found.emit(match.group(0))
            if self.running:
                self.log_signal.emit("Connection dropped. Reconnecting in 3s...")
                time.sleep(3)

    @trace_execution("TunnelThread")
    def stop(self):
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.kill()
            except Exception:
                pass
            self.process = None


class ChannelSearchThread(QThread):
    server_found = Signal(str, str, int)
    search_finished = Signal()

    def __init__(self, query="", parent=None):
        super().__init__(parent)
        self.query = query.strip().lower()

    @trace_execution("ChannelSearchThread")
    def run(self):
        common_names = ["nairobi-hub", "nairobi-drive-hub", "nairobi-county", "dev-hub", "shared-space", "hub",
                        "test-server"]
        if self.query and self.query not in common_names:
            common_names.insert(0, self.query)

        client_id, _, _ = get_client_info()
        for name in common_names:
            base_url = f"https://{name}.loca.lt"
            api_url = f"{base_url}/api/links"
            try:
                req = urllib.request.Request(
                    api_url,
                    headers={
                        'bypass-tunnel-reminder': 'true',
                        'X-Client-ID': client_id,
                        'User-Agent': 'NairobiHubSearch/1.0'
                    }
                )
                with urllib.request.urlopen(req, timeout=2.5) as resp:
                    if resp.getcode() == 200:
                        self.server_found.emit(name, base_url, 200)
            except Exception:
                try:
                    req_base = urllib.request.Request(
                        base_url,
                        headers={'bypass-tunnel-reminder': 'true', 'User-Agent': 'NairobiHubSearch/1.0'}
                    )
                    with urllib.request.urlopen(req_base, timeout=2) as resp:
                        if resp.getcode() == 200:
                            self.server_found.emit(name, base_url, 200)
                except Exception:
                    pass
        self.search_finished.emit()


class UnifiedWorkerThread(QThread):
    tick_4s = Signal()
    tick_5s = Signal()
    tick_6s = Signal()
    tick_600s = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.counter = 0

    @trace_execution("UnifiedWorkerThread")
    def run(self):
        while self.running:
            time.sleep(1)
            if not self.running:
                break
            self.counter += 1
            if self.counter % 4 == 0:
                self.tick_4s.emit()
            if self.counter % 5 == 0:
                self.tick_5s.emit()
            if self.counter % 6 == 0:
                self.tick_6s.emit()
            if self.counter % 600 == 0:
                self.tick_600s.emit()

    @trace_execution("UnifiedWorkerThread")
    def stop(self):
        self.running = False
        self.quit()
        self.wait()


def get_client_info():
    conn = sqlite3.connect(CLIENT_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT client_id, username, dob FROM client_config')
    row = cursor.fetchone()
    conn.close()
    return row[0], row[1], row[2]


def update_client_profile(new_username, new_dob):
    c_id, _, _ = get_client_info()
    conn = sqlite3.connect(CLIENT_DB)
    cursor = conn.cursor()
    cursor.execute('UPDATE client_config SET username = ?, dob = ? WHERE client_id = ?', (new_username, new_dob, c_id))
    conn.commit()
    conn.close()


def get_auth_headers(srv_data):
    client_id, _, _ = get_client_info()
    return {
        'X-Client-ID': client_id,
        'X-Session-Token': srv_data.get('session_token', '') or '',
        'X-Server-Key': srv_data.get('server_key', '') or '',
        'bypass-tunnel-reminder': 'true'
    }


def add_favorite(server_name, link_id, title, url, item_type):
    conn = sqlite3.connect(CLIENT_DB)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO favorite_resources (server_name, link_id, title, url, item_type) VALUES (?, ?, ?, ?, ?)',
        (server_name, link_id, title, url, item_type))
    conn.commit()
    conn.close()


def remove_favorite(server_name, link_id):
    conn = sqlite3.connect(CLIENT_DB)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM favorite_resources WHERE server_name = ? AND link_id = ?', (server_name, link_id))
    conn.commit()
    conn.close()


def get_favorites():
    conn = sqlite3.connect(CLIENT_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT server_name, link_id, title, url, item_type FROM favorite_resources')
    rows = cursor.fetchall()
    conn.close()
    return set((r[0], r[1]) for r in rows)


def add_offline_resource(item):
    if not item or item.get('origin_server') is None or item.get('id') is None:
        return
    try:
        conn = sqlite3.connect(CLIENT_DB, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO offline_resources (server_name, link_id, title, url, item_type, is_public, username)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.get('origin_server'),
            item.get('id'),
            item.get('title'),
            item.get('url'),
            item.get('item_type', 'file'),
            1 if item.get('is_public', True) else 0,
            item.get('username', 'Unknown')
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        log_event(f"Error adding offline resource: {e}")


def remove_offline_resource(server_name, link_id):
    conn = sqlite3.connect(CLIENT_DB)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM offline_resources WHERE server_name = ? AND link_id = ?', (server_name, link_id))
    conn.commit()
    conn.close()


def get_offline_resources():
    conn = sqlite3.connect(CLIENT_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT server_name, link_id, title, url, item_type, is_public, username FROM offline_resources')
    rows = cursor.fetchall()
    conn.close()
    items = []
    for r in rows:
        items.append({
            "origin_server": r[0],
            "id": r[1],
            "title": r[2],
            "url": r[3],
            "item_type": r[4],
            "is_public": bool(r[5]),
            "username": r[6]
        })
    return items


def update_server_token(server_name, token):
    conn = sqlite3.connect(CLIENT_DB)
    cursor = conn.cursor()
    cursor.execute('UPDATE connected_servers SET session_token = ? WHERE server_name = ?', (token, server_name))
    conn.commit()
    conn.close()


class ToastContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(6)
        self.setLayout(self.layout)

    def show_toast(self, message):
        if get_setting("notif_banner", "True") == "False":
            return
        if get_setting("notif_sound", "True") == "True":
            QApplication.beep()

        toast = QLabel(message, self)
        toast.setStyleSheet("""
            background-color: #132219;
            color: #FFD700;
            border: 1px solid #1E3A29;
            border-radius: 8px;
            padding: 8px 12px;
            font-weight: bold;
            font-size: 12px;
        """)
        toast.setWordWrap(True)
        toast.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(toast)
        toast.show()
        toast.raise_()

        timer = QTimer(toast)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.remove_toast(toast))
        timer.start(4000)

    def remove_toast(self, toast):
        self.layout.removeWidget(toast)
        toast.deleteLater()


class RealtimeChartWidget(QFrame):
    def __init__(self, title="Real-Time Network Telemetry", parent=None):
        super().__init__(parent)
        self.setObjectName("DashboardCard")
        self.setMinimumHeight(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        title_lbl = QLabel(title.upper())
        title_lbl.setObjectName("CardTitle")
        layout.addWidget(title_lbl)

        self.canvas = ChartCanvas(self)
        layout.addWidget(self.canvas)


class ChartCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_points = [20, 35, 40, 30, 55, 70, 65, 80, 50, 60, 75, 90, 85, 60, 45, 65, 80]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

    def update_data(self):
        if get_setting("animations", "True") == "False":
            return
        import random
        new_val = random.randint(25, 95)
        self.data_points.pop(0)
        self.data_points.append(new_val)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        painter.setPen(QPen(QColor("#1E3A29"), 1, Qt.DashLine))
        for i in range(1, 4):
            y = int(h * i / 4)
            painter.drawLine(0, y, w, y)

        if not self.data_points:
            return

        step = w / float(max(1, len(self.data_points) - 1))

        polygon = QPolygonF()
        polygon.append(QPointF(0, h))
        for idx, val in enumerate(self.data_points):
            x = idx * step
            y = h - (val / 100.0) * (h - 10)
            polygon.append(QPointF(x, y))
        polygon.append(QPointF(w, h))

        accent = get_setting("accent_color", "#006400")
        ac_color = QColor(accent)
        ac_color.setAlpha(40)
        painter.setBrush(QBrush(ac_color))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(polygon)

        path_pen = QPen(QColor(accent), 2)
        painter.setPen(path_pen)
        painter.setBrush(Qt.NoBrush)

        for idx in range(len(self.data_points) - 1):
            x1 = idx * step
            y1 = h - (self.data_points[idx] / 100.0) * (h - 10)
            x2 = (idx + 1) * step
            y2 = h - (self.data_points[idx + 1] / 100.0) * (h - 10)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))


class ServerStatusWorker(QThread):
    status_checked = Signal(list)

    def __init__(self, servers, parent=None):
        super().__init__(parent)
        self.servers = servers

    @trace_execution("ServerStatusWorker")
    def run(self):
        results = []
        for srv in self.servers:
            try:
                if isinstance(srv, dict):
                    server_name = srv.get('server_name', '')
                    url = srv.get('url', '')
                    server_key = srv.get('server_key', '')
                    session_token = srv.get('session_token', '')
                else:
                    server_name, url, server_key, session_token = srv[0], srv[1], srv[2], srv[3]
            except Exception:
                continue

            is_online = False
            try:
                resp = requests.get(
                    f"{url}/api/user/profile",
                    headers={
                        'X-Client-ID': get_client_info()[0],
                        'X-Session-Token': session_token,
                        'X-Server-Key': server_key,
                        'bypass-tunnel-reminder': 'true',
                        'User-Agent': 'NairobiHubClient/1.0'
                    },
                    timeout=1.5
                )
                if resp.status_code == 200:
                    is_online = True
                    token = resp.json().get('session_token')
                    if token:
                        update_server_token(server_name, token)
            except Exception:
                is_online = False
            results.append((server_name, url, server_key, session_token, is_online))
        self.status_checked.emit(results)


class ServerItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        is_online = index.data(Qt.UserRole + 1)
        selected = option.state & QStyle.State_Selected

        accent = get_setting("accent_color", "#006400")
        rect = option.rect.adjusted(4, 4, -4, -4)
        painter.setBrush(QBrush(QColor(accent if selected else "#132219")))
        painter.setPen(QPen(QColor("#FFD700" if selected else "#1E3A29"), 1))
        painter.drawRoundedRect(rect, 8, 8)

        status_color = QColor("#22C55E") if is_online else QColor("#EF4444")
        icon_rect = QRectF(rect.left() + 12, rect.center().y() - 16, 32, 32)
        painter.setBrush(QBrush(status_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(icon_rect, 6, 6)

        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.setPen(QPen(QColor("#FFFFFF" if selected else "#F1F5F9")))
        painter.drawText(QRectF(rect.left() + 56, rect.top() + 8, rect.width() - 70, 20),
                         Qt.AlignLeft | Qt.AlignVCenter, index.data(Qt.DisplayRole))

        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(QPen(status_color))
        painter.drawText(QRectF(rect.left() + 56, rect.top() + 28, rect.width() - 70, 20),
                         Qt.AlignLeft | Qt.AlignVCenter, "ONLINE" if is_online else "OFFLINE")
        painter.restore()

    def sizeHint(self, option, index):
        density = get_setting("density", "Spacious")
        h = 50 if density == "Compact" else 64
        return QSize(option.rect.width(), h)


class LinkModal(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Attached Item" if initial_data else "Upload / Attach Resource")
        self.resize(440, 300)
        layout = QFormLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.title_input = QLineEdit()
        self.url_input = QLineEdit()
        self.provider_box = QComboBox()
        self.provider_box.addItems(["Google Drive", "Dropbox", "OneDrive", "Mega", "Direct/Other"])
        self.type_box = QComboBox()
        self.type_box.addItems(
            ["folder", "unknown file", "audio", "video", "word", "excel", "powerpoint", "image", "txt document"])
        self.public_check = QCheckBox("Make Publicly Accessible")
        self.public_check.setChecked(True)

        layout.addRow("Title:", self.title_input)
        layout.addRow("Link / Address:", self.url_input)
        layout.addRow("Provider:", self.provider_box)
        layout.addRow("Item Type:", self.type_box)
        layout.addRow("Access Level:", self.public_check)

        if initial_data:
            self.title_input.setText(initial_data.get('title', ''))
            self.url_input.setText(initial_data.get('url', ''))
            self.type_box.setCurrentText(initial_data.get('item_type', 'unknown file'))
            self.public_check.setChecked(bool(initial_data.get('is_public', 1)))

        save_btn = QPushButton("Save Attachment")
        save_btn.clicked.connect(self.accept)
        layout.addRow(save_btn)
        self.setLayout(layout)

    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "url": self.url_input.text().strip(),
            "item_type": self.type_box.currentText(),
            "is_public": 1 if self.public_check.isChecked() else 0
        }


class ConnectionWorker(QThread):
    finished = Signal(bool, int, int, str)

    def __init__(self, target_url, parent=None):
        super().__init__(parent)
        self.target_url = target_url

    @trace_execution("ConnectionWorker")
    def run(self):
        parsed = urllib.parse.urlparse(self.target_url)
        scheme = parsed.scheme.upper() if parsed.scheme else "HTTP"
        start_time = time.time()
        connected = False
        status_code = 0
        try:
            req = urllib.request.Request(
                self.target_url,
                headers={'bypass-tunnel-reminder': 'true', 'User-Agent': 'ConnectionMeter/1.0'}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                status_code = resp.getcode()
                connected = True
        except urllib.error.HTTPError as e:
            connected = True
            status_code = e.code
        except Exception:
            connected = False

        latency = int((time.time() - start_time) * 1000)
        self.finished.emit(connected, status_code, latency, scheme)


class ConnectionMeterDialog(QDialog):
    def __init__(self, user_data, target_url="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Connection Quality - {user_data['username']}")
        self.resize(380, 260)
        self.user_data = user_data
        self.target_url = target_url.strip() if target_url else "http://127.0.0.1:5000"
        self.worker = None

        layout = QVBoxLayout()
        info_lbl = QLabel(f"Checking connection status for <b>{user_data['username']}</b>...")
        info_lbl.setStyleSheet("font-size: 14px;")
        layout.addWidget(info_lbl)

        self.meter = QProgressBar()
        self.meter.setRange(0, 100)
        self.meter.setValue(0)
        self.meter.setTextVisible(True)
        self.meter.setFormat("Testing... %p%")
        self.meter.setStyleSheet("""
            QProgressBar {
                border: 1px solid #1E3A29;
                border-radius: 6px;
                text-align: center;
                background-color: #0B130F;
                color: #FFD700;
                font-weight: bold;
                height: 24px;
            }
            QProgressBar::chunk {
                background-color: #006400;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.meter)

        self.network_info_lbl = QLabel("Target Address: Initializing...")
        self.network_info_lbl.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(self.network_info_lbl)

        self.status_details = QLabel("Latency: -- ms | Status: Querying")
        self.status_details.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.status_details)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        self.setLayout(layout)

        self.sim_step = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_meter)
        self.timer.start(80)

    def update_meter(self):
        self.sim_step += 10
        if self.sim_step < 90:
            self.meter.setValue(self.sim_step)
        elif self.sim_step == 90:
            self.timer.stop()
            parsed = urllib.parse.urlparse(self.target_url)
            domain = parsed.netloc or "127.0.0.1:5000"
            scheme = parsed.scheme.upper() if parsed.scheme else "HTTP"
            self.network_info_lbl.setText(f"Target Address: {scheme} -> {domain}")

            self.worker = ConnectionWorker(self.target_url, self)
            self.worker.finished.connect(self.on_network_check_finished)
            self.worker.start()

    def on_network_check_finished(self, connected, status_code, latency, scheme):
        if connected:
            self.meter.setValue(100)
            self.meter.setFormat("Signal: Connected & Active (100%)")
            self.status_details.setText(
                f"Latency: {latency} ms | Protocol: {scheme} | Status: Active (HTTP {status_code or 200})")
        else:
            self.meter.setValue(30)
            self.meter.setFormat("Signal: Disconnected")
            self.status_details.setText(f"Status: Offline / Unreachable")


class TimeoutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Timeout")
        self.resize(300, 150)
        layout = QFormLayout(self)

        self.time_combo = QComboBox()
        self.time_combo.addItems(["30 seconds", "1 minute", "5 minutes", "15 minutes", "1 hour"])
        layout.addRow("Timeout Duration:", self.time_combo)

        btn = QPushButton("Apply Timeout")
        btn.clicked.connect(self.accept)
        layout.addRow(btn)

    def get_duration_seconds(self):
        text = self.time_combo.currentText()
        if "seconds" in text:
            return int(text.split()[0])
        elif "minute" in text:
            return int(text.split()[0]) * 60
        elif "hour" in text:
            return int(text.split()[0]) * 3600
        return 60


class RevokeAccessDialog(QDialog):
    def __init__(self, can_read, can_write, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Revoke Read / Write Access")
        self.resize(320, 180)
        layout = QVBoxLayout(self)

        self.read_check = QCheckBox("Allow Read Access")
        self.read_check.setChecked(bool(can_read))
        layout.addWidget(self.read_check)

        self.write_check = QCheckBox("Allow Write Access")
        self.write_check.setChecked(bool(can_write))
        layout.addWidget(self.write_check)

        btn = QPushButton("Save Access Rules")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def get_access_flags(self):
        return 1 if self.read_check.isChecked() else 0, 1 if self.write_check.isChecked() else 0


class SharePopup(QDialog):
    def __init__(self, share_url="", server_code="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Share Space & Invite")
        self.resize(420, 380)
        self.share_url = share_url
        self.server_code = server_code

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header_lbl = QLabel("<b>Share Space & Server Details</b>")
        header_lbl.setStyleSheet("font-size: 16px; color: #22C55E;")
        layout.addWidget(header_lbl)

        buttons_info = [
            ("Share via Email", self.share_via_email),
            ("Share via WhatsApp", self.share_via_whatsapp),
            ("Share via Facebook", self.share_via_facebook),
            ("Copy Link & Server Code", self.copy_link_and_code),
            ("Share via Text File", self.share_via_text_file)
        ]

        for text, handler in buttons_info:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #132219;
                    color: #F1F5F9;
                    border: 1px solid #1E3A29;
                    border-radius: 8px;
                    padding: 10px;
                    font-weight: bold;
                    text-align: left;
                    padding-left: 15px;
                }
                QPushButton:hover {
                    background-color: #1E3A29;
                    border-color: #22C55E;
                }
            """)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        layout.addStretch()

    def get_share_content(self):
        return f"Nairobi County DES File Hub Space:\nURL: {self.share_url}\nServer Key / Code: {self.server_code}"

    def share_via_email(self):
        subject = urllib.parse.quote("Nairobi County DES File Hub Invite")
        body = urllib.parse.quote(self.get_share_content())
        webbrowser.open(f"mailto:?subject={subject}&body={body}")

    def share_via_whatsapp(self):
        text = urllib.parse.quote(self.get_share_content())
        webbrowser.open(f"https://wa.me/?text={text}")

    def share_via_facebook(self):
        url = urllib.parse.quote(self.share_url)
        webbrowser.open(f"https://www.facebook.com/sharer/sharer.php?u={url}")

    def copy_link_and_code(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.get_share_content())
        QMessageBox.information(self, "Copied", "URL and Server Code copied to clipboard successfully!")

    def share_via_text_file(self):
        file_path, _ = QInputDialog.getText(self, "Export Text File", "Enter filename for export:", QLineEdit.Normal,
                                            "space_invite.txt")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.get_share_content())
                QMessageBox.information(self, "Success", f"Exported successfully to {os.path.abspath(file_path)}")
                webbrowser.open(os.path.dirname(os.path.abspath(file_path)))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create text file: {e}")


# --- MAIN COMBINED APPLICATION WINDOW WITH SIDEBAR ---
class CombinedAppWindow(QMainWindow):
    @trace_execution("CombinedAppWindow")
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nairobi County DES File Hub - Shared Spaces & Attachments")
        self.resize(1300, 850)

        self.flask_thread = None
        self.tunnel_thread = None
        self.fetch_thread = None
        self.channel_thread = None

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- SIDEBAR NAVIGATION ---
        sidebar_outer_layout = QVBoxLayout()
        sidebar_outer_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_outer_layout.setSpacing(0)

        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("SidebarFrame")
        sidebar_frame.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(10)

        app_title_lbl = QLabel("Nairobi Hub")
        app_title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; padding-left: 8px;")
        sidebar_layout.addWidget(app_title_lbl)
        sidebar_layout.addSpacing(10)

        self.sidebar_list = QListWidget()
        self.sidebar_list.setObjectName("SidebarList")
        self.sidebar_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.sidebar_list.addItem("Dashboard")
        self.sidebar_list.addItem("My Device")
        self.sidebar_list.addItem("Shared Space Hosting")
        self.sidebar_list.addItem("Settings")
        self.sidebar_list.setCurrentRow(0)
        self.sidebar_list.currentRowChanged.connect(self.change_sidebar_section)

        sidebar_layout.addWidget(self.sidebar_list)
        sidebar_layout.addStretch()
        sidebar_outer_layout.addWidget(sidebar_frame)

        self.toast_container = ToastContainer()
        self.toast_container.setFixedWidth(240)
        sidebar_outer_layout.addWidget(self.toast_container)

        main_layout.addLayout(sidebar_outer_layout)

        # --- CONTENT STACKED WIDGET ---
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        # ==========================================
        # SECTION 1: DASHBOARD
        # ==========================================
        dash_container = QWidget()
        dash_layout = QVBoxLayout(dash_container)
        dash_layout.setContentsMargins(24, 24, 24, 24)
        dash_layout.setSpacing(16)

        dash_header = QLabel("Nairobi County File Hub Operations Dashboard")
        dash_header.setStyleSheet("font-size: 22px; font-weight: bold;")
        dash_layout.addWidget(dash_header)

        d_metrics_1 = QHBoxLayout()
        d_metrics_1.setSpacing(12)
        self.card_servers = MetricCard("Linked Spaces", "0")
        self.card_links = MetricCard("Attached Items", "0")
        self.card_public = MetricCard("Public Items", "0")
        self.card_private = MetricCard("Private Items", "0")
        d_metrics_1.addWidget(self.card_servers)
        d_metrics_1.addWidget(self.card_links)
        d_metrics_1.addWidget(self.card_public)
        d_metrics_1.addWidget(self.card_private)
        dash_layout.addLayout(d_metrics_1)

        d_metrics_2 = QHBoxLayout()
        d_metrics_2.setSpacing(12)
        self.dash_card_users = MetricCard("Hosting Registered Users", "0")
        self.dash_card_hosting_links = MetricCard("Hosting Attached Files", "0")
        self.dash_card_hosting_status = MetricCard("Hosting Status", "Offline")
        d_metrics_2.addWidget(self.dash_card_users)
        d_metrics_2.addWidget(self.dash_card_hosting_links)
        d_metrics_2.addWidget(self.dash_card_hosting_status)
        dash_layout.addLayout(d_metrics_2)

        self.realtime_chart = RealtimeChartWidget("Real-Time Telemetry & Throughput Monitor", self)
        dash_layout.addWidget(self.realtime_chart)

        dash_summary_card = QFrame()
        dash_summary_card.setObjectName("DashboardCard")
        dsc_l = QVBoxLayout(dash_summary_card)
        dsc_l.addWidget(QLabel("Unified System Overview", objectName="CardTitle"))
        self.unified_summary_lbl = QLabel("Monitoring client spaces and local server operations concurrently.")
        self.unified_summary_lbl.setWordWrap(True)
        self.unified_summary_lbl.setStyleSheet("font-size: 13px;")
        dsc_l.addWidget(self.unified_summary_lbl)
        dash_layout.addWidget(dash_summary_card)

        self.content_stack.addWidget(dash_container)

        # ==========================================
        # SECTION 2: MY DEVICE (CLIENT)
        # ==========================================
        self.client_tab_container = QWidget()
        client_layout = QVBoxLayout(self.client_tab_container)
        client_layout.setSpacing(14)
        client_layout.setContentsMargins(20, 20, 20, 20)

        client_top_bar = QHBoxLayout()
        client_title_lbl = QLabel("My Device & Spaces Explorer")
        client_title_lbl.setStyleSheet("font-size: 20px; font-weight: bold;")
        client_top_bar.addWidget(client_title_lbl)
        client_top_bar.addStretch()

        self.add_all_offline_btn = QPushButton("Add All Server Items to Offline Read")
        self.add_all_offline_btn.clicked.connect(self.add_all_current_server_to_offline)
        client_top_bar.addWidget(self.add_all_offline_btn)

        self.profile_btn = QPushButton("My Profile")
        self.profile_btn.setObjectName("SecondaryBtn")
        self.profile_btn.clicked.connect(self.open_profile)
        client_top_bar.addWidget(self.profile_btn)

        self.add_srv_btn = QPushButton("+ Connect New Space")
        self.add_srv_btn.clicked.connect(self.add_server)
        client_top_bar.addWidget(self.add_srv_btn)
        client_layout.addLayout(client_top_bar)

        self.client_tab_widget = QTabWidget()

        self.c_tab_spaces = QWidget()
        c2_layout = QVBoxLayout(self.c_tab_spaces)
        c2_layout.addWidget(
            QLabel("<b>Linked Spaces Network</b> (Right-click to Edit or Remove)", objectName="PanelHeader"))
        self.server_list = QListWidget()
        self.server_list.setItemDelegate(ServerItemDelegate(self.server_list))
        self.server_list.setViewMode(QListWidget.IconMode)
        self.server_list.setResizeMode(QListWidget.Adjust)
        self.server_list.setGridSize(QSize(220, 100))
        self.server_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.server_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.server_list.customContextMenuRequested.connect(self.show_server_context_menu)
        c2_layout.addWidget(self.server_list)
        self.client_tab_widget.addTab(self.c_tab_spaces, "Spaces")

        self.c_tab_explore = QWidget()
        c3_layout = QVBoxLayout(self.c_tab_explore)
        c3_search = QHBoxLayout()
        c3_search.addWidget(QLabel("Filter Space:"))
        self.server_filter = QComboBox()
        self.server_filter.setFixedWidth(180)
        self.server_filter.currentIndexChanged.connect(self.load_all_links)
        c3_search.addWidget(self.server_filter)
        c3_search.addWidget(QLabel("Search Items:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, owner, or space...")
        self.search_input.textChanged.connect(self.filter_explorer)
        c3_search.addWidget(self.search_input)
        c3_layout.addLayout(c3_search)

        self.explorer_sub_tabs = QTabWidget()

        self.explorer_tab = QWidget()
        exp_layout = QVBoxLayout(self.explorer_tab)
        exp_hdr = QHBoxLayout()
        exp_hdr.addWidget(QLabel("Attached Files & Folders", objectName="PanelHeader"))
        self.add_link_btn = QPushButton("+ Upload / Attach Link")
        self.add_link_btn.clicked.connect(self.add_drive_link)
        exp_hdr.addWidget(self.add_link_btn)
        exp_layout.addLayout(exp_hdr)
        self.explorer_list = QListWidget()
        self.explorer_list.setViewMode(QListWidget.IconMode)
        self.explorer_list.setIconSize(QSize(56, 56))
        self.explorer_list.setGridSize(QSize(150, 115))
        self.explorer_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.explorer_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.explorer_list.customContextMenuRequested.connect(lambda pos, lw=self.explorer_list: self.show_explorer_context_menu(lw, pos))

        self.explorer_list.itemDoubleClicked.connect(self.open_link_in_browser)
        exp_layout.addWidget(self.explorer_list)
        self.explorer_sub_tabs.addTab(self.explorer_tab, "Explorer")

        self.fav_tab = QWidget()
        fav_layout = QVBoxLayout(self.fav_tab)
        fav_layout.addWidget(QLabel("Bookmarked Items (Quick Access)", objectName="PanelHeader"))
        self.fav_list = QListWidget()
        self.fav_list.setViewMode(QListWidget.IconMode)
        self.fav_list.setIconSize(QSize(56, 56))
        self.fav_list.setGridSize(QSize(150, 115))
        self.fav_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.fav_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.fav_list.customContextMenuRequested.connect(lambda pos, lw=self.fav_list: self.show_explorer_context_menu(lw, pos))
        self.fav_list.itemDoubleClicked.connect(self.open_link_in_browser)
        fav_layout.addWidget(self.fav_list)
        self.explorer_sub_tabs.addTab(self.fav_tab, "Bookmarks")

        self.offline_tab = QWidget()
        off_layout = QVBoxLayout(self.offline_tab)
        off_layout.addWidget(
            QLabel("Saved for Offline Mode (Accessible even when server is offline)", objectName="PanelHeader"))
        self.offline_list = QListWidget()
        self.offline_list.setViewMode(QListWidget.IconMode)
        self.offline_list.setIconSize(QSize(56, 56))
        self.offline_list.setGridSize(QSize(150, 115))
        self.offline_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.offline_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.offline_list.customContextMenuRequested.connect(lambda pos, lw=self.offline_list: self.show_explorer_context_menu(lw, pos))
        self.offline_list.itemDoubleClicked.connect(self.open_link_in_browser)
        off_layout.addWidget(self.offline_list)
        self.explorer_sub_tabs.addTab(self.offline_tab, "Save for Offline Mode")

        c3_layout.addWidget(self.explorer_sub_tabs)
        self.client_tab_widget.addTab(self.c_tab_explore, "Explore Spaces")

        # Search Channels Tab
        self.c_tab_search_channels = QWidget()
        cs_layout = QVBoxLayout(self.c_tab_search_channels)
        cs_layout.addWidget(
            QLabel("<b>Search & Discover Active Spaces (loca.lt Channels)</b>", objectName="PanelHeader"))
        cs_layout.addWidget(QLabel(
            "Search for active public spaces emitting signals across the network, similar to discovering channels."))

        cs_bar = QHBoxLayout()
        self.channel_search_input = QLineEdit()
        self.channel_search_input.setPlaceholderText("Enter space name or keyword (e.g. nairobi-hub)...")
        self.scan_channels_btn = QPushButton("Scan / Search Channels")
        self.scan_channels_btn.clicked.connect(self.start_channel_scan)
        cs_bar.addWidget(self.channel_search_input)
        cs_bar.addWidget(self.scan_channels_btn)
        cs_layout.addLayout(cs_bar)

        self.channels_result_list = QListWidget()
        self.channels_result_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.channels_result_list.itemDoubleClicked.connect(self.connect_discovered_channel)
        cs_layout.addWidget(self.channels_result_list)

        self.client_tab_widget.addTab(self.c_tab_search_channels, "Search Channels")

        # Client Moderator Tab
        self.client_mod_tab = QWidget()
        cm_layout = QVBoxLayout(self.client_mod_tab)
        cm_layout.addWidget(QLabel("<b>Moderator Panel (Client Privileges Active)</b>", objectName="PanelHeader"))
        cm_layout.addWidget(QLabel("You have been granted moderator privileges on the active space."))

        self.client_mod_explorer = QListWidget()
        self.client_mod_explorer.setViewMode(QListWidget.IconMode)
        self.client_mod_explorer.setIconSize(QSize(56, 56))
        self.client_mod_explorer.setGridSize(QSize(150, 115))
        self.client_mod_explorer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.client_mod_explorer.customContextMenuRequested.connect(lambda pos, lw=self.client_mod_explorer: self.show_moderator_explorer_context_menu(lw, pos))
        cm_layout.addWidget(self.client_mod_explorer)

        client_layout.addWidget(self.client_tab_widget)
        self.content_stack.addWidget(self.client_tab_container)

        # ==========================================
        # SECTION 3: SHARED SPACE HOSTING (SERVER)
        # ==========================================
        self.server_tab_container = QWidget()
        server_layout = QVBoxLayout(self.server_tab_container)
        server_layout.setSpacing(14)
        server_layout.setContentsMargins(20, 20, 20, 20)

        self.control_card = QFrame()
        self.control_card.setObjectName("DashboardCard")
        card_layout = QVBoxLayout(self.control_card)
        title_lbl = QLabel("Hosting & Connection Settings")
        title_lbl.setObjectName("CardTitle")
        card_layout.addWidget(title_lbl)

        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Space Access Key:"))
        self.key_display = QLineEdit(CURRENT_SERVER_KEY)
        self.key_display.setReadOnly(True)
        key_layout.addWidget(self.key_display)
        card_layout.addLayout(key_layout)

        subdomain_layout = QHBoxLayout()
        subdomain_layout.addWidget(QLabel("Space Custom Subdomain:"))
        self.subdomain_input = QLineEdit()
        self.subdomain_input.setPlaceholderText("e.g. nairobi-drive-hub")
        subdomain_layout.addWidget(self.subdomain_input)
        subdomain_layout.addWidget(QLabel(".loca.lt"))
        card_layout.addLayout(subdomain_layout)

        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Public Connection Address:"))
        self.url_input = QLineEdit()
        self.url_input.setReadOnly(True)
        info_layout.addWidget(self.url_input)
        card_layout.addLayout(info_layout)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Go Live & Start Hosting")
        self.start_btn.clicked.connect(self.start_server)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Hosting")
        self.stop_btn.setObjectName("StopBtn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_tunnel)
        btn_layout.addWidget(self.stop_btn)

        self.share_btn = QPushButton("Shares/Invite")
        self.share_btn.setObjectName("SecondaryBtn")
        self.share_btn.clicked.connect(self.open_share_invite_dialog)
        btn_layout.addWidget(self.share_btn)

        card_layout.addLayout(btn_layout)

        self.server_tabs = QTabWidget()

        self.s_gateway_tab = QWidget()
        gw_l = QVBoxLayout(self.s_gateway_tab)
        gw_l.addWidget(self.control_card)
        gw_l.addSpacing(10)
        gw_l.addWidget(QLabel("<b>Previously Added Servers & Gateways:</b>", objectName="PanelHeader"))

        self.hosting_servers_list = QListWidget()
        self.hosting_servers_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.hosting_servers_list.setMinimumHeight(100)
        gw_l.addWidget(self.hosting_servers_list)

        gw_l.addStretch()
        self.server_tabs.addTab(self.s_gateway_tab, "Hosting Controls")

        self.s_files_tab = QWidget()
        sf_l = QVBoxLayout(self.s_files_tab)
        sc = QFrame()
        sc.setObjectName("DashboardCard")
        sc_l = QHBoxLayout(sc)
        sc_l.addWidget(QLabel("Search:"))
        self.file_search_input = QLineEdit()
        self.file_search_input.setPlaceholderText("Type name, user, or file type...")
        self.file_search_input.textChanged.connect(self.filter_files)
        sc_l.addWidget(self.file_search_input)
        sc_l.addWidget(QLabel("Filter By:"))
        self.file_type_filter = QComboBox()
        self.file_type_filter.addItems(
            ["All Types", "folder", "file", "word", "excel", "powerpoint", "image", "audio", "video", "txt document"])
        self.file_type_filter.currentIndexChanged.connect(self.filter_files)
        sc_l.addWidget(self.file_type_filter)
        sf_l.addWidget(sc)

        self.files_list = QListWidget()
        self.files_list.setViewMode(QListWidget.IconMode)
        self.files_list.setIconSize(QSize(64, 64))
        self.files_list.setGridSize(QSize(140, 110))
        self.files_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.files_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.files_list.customContextMenuRequested.connect(self.show_server_file_context_menu)
        sf_l.addWidget(self.files_list)
        self.server_tabs.addTab(self.s_files_tab, "Managed Attachment")

        self.s_users_tab = QWidget()
        su_l = QVBoxLayout(self.s_users_tab)
        usc = QFrame()
        usc.setObjectName("DashboardCard")
        usc_l = QHBoxLayout(usc)
        usc_l.addWidget(QLabel("Search Users:"))
        self.user_search_input = QLineEdit()
        self.user_search_input.setPlaceholderText("Search by User ID, Username...")
        self.user_search_input.textChanged.connect(self.filter_users)
        usc_l.addWidget(self.user_search_input)
        su_l.addWidget(usc)

        self.users_list = QListWidget()
        self.users_list.setViewMode(QListWidget.IconMode)
        self.users_list.setIconSize(QSize(64, 64))
        self.users_list.setGridSize(QSize(140, 110))
        self.users_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.users_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.users_list.customContextMenuRequested.connect(self.show_user_context_menu)
        su_l.addWidget(self.users_list)
        self.server_tabs.addTab(self.s_users_tab, "User Permissions App")

        self.server_mod_tab = QWidget()
        sm_layout = QVBoxLayout(self.server_mod_tab)
        sm_layout.addWidget(QLabel("<b>Server Moderator Explorer & Oversight</b>", objectName="PanelHeader"))
        self.server_mod_explorer = QListWidget()
        self.server_mod_explorer.setViewMode(QListWidget.IconMode)
        self.server_mod_explorer.setIconSize(QSize(56, 56))
        self.server_mod_explorer.setGridSize(QSize(150, 115))
        self.server_mod_explorer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.server_mod_explorer.customContextMenuRequested.connect(lambda pos, lw=self.server_mod_explorer: self.show_moderator_explorer_context_menu(lw, pos))
        sm_layout.addWidget(self.server_mod_explorer)
        self.server_tabs.addTab(self.server_mod_tab, "Moderator Tab")

        server_layout.addWidget(self.server_tabs)
        self.content_stack.addWidget(self.server_tab_container)

        # ==========================================
        # SECTION 4: SETTINGS APP
        # ==========================================
        self.settings_container = QWidget()
        set_main_layout = QVBoxLayout(self.settings_container)
        set_main_layout.setContentsMargins(20, 20, 20, 20)
        set_main_layout.setSpacing(14)

        set_header_layout = QHBoxLayout()
        set_header = QLabel("Settings App & System Preferences")
        set_header.setStyleSheet("font-size: 20px; font-weight: bold;")
        set_header_layout.addWidget(set_header)
        set_header_layout.addStretch()

        self.reset_all_btn = QPushButton("Reset All to Default")
        self.reset_all_btn.setObjectName("StopBtn")
        self.reset_all_btn.clicked.connect(self.reset_settings_to_defaults)
        set_header_layout.addWidget(self.reset_all_btn)
        set_main_layout.addLayout(set_header_layout)

        self.settings_tabs = QTabWidget()

        app_tab = QWidget()
        app_form = QFormLayout(app_tab)
        app_form.setSpacing(12)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Mode", "Light Mode"])
        self.theme_combo.setCurrentText(get_setting("theme", "Dark Mode"))
        app_form.addRow("Color Theme:", self.theme_combo)

        accent_layout = QHBoxLayout()
        self.accent_input = QLineEdit(get_setting("accent_color", "#006400"))
        accent_btn = QPushButton("Pick Color...")
        accent_btn.setObjectName("SecondaryBtn")
        accent_btn.clicked.connect(self.pick_accent_color)
        accent_layout.addWidget(self.accent_input)
        accent_layout.addWidget(accent_btn)
        app_form.addRow("Accent Color Customization:", accent_layout)

        self.font_scale_combo = QComboBox()
        self.font_scale_combo.addItems(["Small", "Medium", "Large", "Custom"])
        self.font_scale_combo.setCurrentText(get_setting("font_scale", "Medium"))
        app_form.addRow("Font Size & Scaling:", self.font_scale_combo)

        self.density_combo = QComboBox()
        self.density_combo.addItems(["Spacious", "Compact"])
        self.density_combo.setCurrentText(get_setting("density", "Spacious"))
        app_form.addRow("Density / Compact Mode:", self.density_combo)

        self.anim_check = QCheckBox("Enable UI animations and fading effects")
        self.anim_check.setChecked(get_setting("animations", "True") == "True")
        app_form.addRow("Animations & Transitions:", self.anim_check)

        global DEBUG_TRACING_ENABLED
        self.debug_trace_check = QCheckBox("Enable application-wide class & crash tracing (to server_activity.log)")
        self.debug_trace_check.setChecked(DEBUG_TRACING_ENABLED)
        app_form.addRow("Debug & Crash Tracing:", self.debug_trace_check)

        save_app_btn = QPushButton("Save Appearance Settings")
        save_app_btn.clicked.connect(self.save_appearance_settings)
        app_form.addRow(save_app_btn)
        self.settings_tabs.addTab(app_tab, "Appearance & Display")

        beh_tab = QWidget()
        beh_form = QFormLayout(beh_tab)
        beh_form.setSpacing(12)

        self.startup_combo = QComboBox()
        self.startup_combo.addItems(["Restore previous session", "Open dashboard", "Start minimized to system tray"])
        self.startup_combo.setCurrentText(get_setting("startup_behavior", "Open dashboard"))
        beh_form.addRow("Startup Behavior:", self.startup_combo)

        self.win_mgmt_combo = QComboBox()
        self.win_mgmt_combo.addItems(["Open in new tabs", "Open in separate windows", "Open in inline panels"])
        self.win_mgmt_combo.setCurrentText(get_setting("win_management", "Open in new tabs"))
        beh_form.addRow("Tab / Window Management:", self.win_mgmt_combo)

        self.default_view_combo = QComboBox()
        self.default_view_combo.addItems(["Dashboard", "My Device", "Shared Space Hosting", "Settings App"])
        self.default_view_combo.setCurrentText(get_setting("default_view", "Dashboard"))
        beh_form.addRow("Default Views (Landing Page):", self.default_view_combo)

        save_beh_btn = QPushButton("Save Behavior Settings")
        save_beh_btn.clicked.connect(self.save_behavior_settings)
        beh_form.addRow(save_beh_btn)
        self.settings_tabs.addTab(beh_tab, "Behavior & Navigation")

        data_tab = QWidget()
        data_form = QFormLayout(data_tab)
        data_form.setSpacing(12)

        cache_layout = QHBoxLayout()
        clear_cache_btn = QPushButton("Clear Local Cache")
        clear_cache_btn.setObjectName("SecondaryBtn")
        clear_cache_btn.clicked.connect(self.clear_cache)
        export_btn = QPushButton("Export Data (JSON/CSV)")
        export_btn.setObjectName("SecondaryBtn")
        export_btn.clicked.connect(self.export_data)
        cache_layout.addWidget(clear_cache_btn)
        cache_layout.addWidget(export_btn)
        data_form.addRow("Local Data Management:", cache_layout)

        storage_layout = QHBoxLayout()
        self.storage_input = QLineEdit(get_setting("storage_dir", os.getcwd()))
        storage_btn = QPushButton("Browse...")
        storage_btn.setObjectName("SecondaryBtn")
        storage_btn.clicked.connect(self.browse_storage_directory)
        storage_layout.addWidget(self.storage_input)
        storage_layout.addWidget(storage_btn)
        data_form.addRow("Storage Location (SQLite / Assets):", storage_layout)

        self.autosave_combo = QComboBox()
        self.autosave_combo.addItems(["Every 5 minutes", "Every 15 minutes", "Every 30 minutes", "Manual only"])
        self.autosave_combo.setCurrentText(get_setting("autosave_freq", "Every 15 minutes"))
        data_form.addRow("Auto-Save Frequency:", self.autosave_combo)

        save_data_btn = QPushButton("Save Storage Settings")
        save_data_btn.clicked.connect(self.save_storage_settings)
        data_form.addRow(save_data_btn)
        self.settings_tabs.addTab(data_tab, "Data, Storage & Sync")

        notif_tab = QWidget()
        notif_form = QFormLayout(notif_tab)
        notif_form.setSpacing(12)

        self.sound_check = QCheckBox("Enable sound alerts")
        self.sound_check.setChecked(get_setting("notif_sound", "True") == "True")
        notif_form.addRow("Sound Alerts:", self.sound_check)

        self.desktop_check = QCheckBox("Enable desktop / system notifications")
        self.desktop_check.setChecked(get_setting("notif_desktop", "True") == "True")
        notif_form.addRow("Desktop Notifications:", self.desktop_check)

        self.banner_check = QCheckBox("Enable in-app banner alert toasts")
        self.banner_check.setChecked(get_setting("notif_banner", "True") == "True")
        notif_form.addRow("In-App Banner Alerts:", self.banner_check)

        self.event_filter_combo = QComboBox()
        self.event_filter_combo.addItems(
            ["All System Events", "Errors & Warnings Only", "Connection State Changes Only"])
        self.event_filter_combo.setCurrentText(get_setting("notif_filter", "All System Events"))
        notif_form.addRow("Event Filters:", self.event_filter_combo)

        save_notif_btn = QPushButton("Save Notification Settings")
        save_notif_btn.clicked.connect(self.save_notification_settings)
        notif_form.addRow(save_notif_btn)
        self.settings_tabs.addTab(notif_tab, "Notifications & Alerts")

        acc_tab = QWidget()
        acc_form = QFormLayout(acc_tab)
        acc_form.setSpacing(12)

        self.shortcut_edit = QKeySequenceEdit(QKeySequence(get_setting("app_hotkey", "Ctrl+K")))
        acc_form.addRow("Dedicated Keybindings Manager (Hotkey):", self.shortcut_edit)

        self.contrast_check = QCheckBox("Enable high contrast assistant mode")
        self.contrast_check.setChecked(get_setting("high_contrast", "False") == "True")
        acc_form.addRow("Screen Reader & High Contrast:", self.contrast_check)

        save_acc_btn = QPushButton("Save Accessibility Settings")
        save_acc_btn.clicked.connect(self.save_accessibility_settings)
        acc_form.addRow(save_acc_btn)
        self.settings_tabs.addTab(acc_tab, "Accessibility & Input")

        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        log_layout.addWidget(self.log_box)
        self.settings_tabs.addTab(log_tab, "Activity Log")

        set_main_layout.addWidget(self.settings_tabs)
        self.content_stack.addWidget(self.settings_container)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.apply_theme_and_styles()
        self.load_persistent_logs()
        self.refresh_servers()

        self.unified_worker = UnifiedWorkerThread(self)
        self.unified_worker.tick_6s.connect(self.trigger_async_link_refresh)
        self.unified_worker.tick_4s.connect(self.trigger_async_server_data_refresh)
        self.unified_worker.tick_600s.connect(self.trigger_async_backup)
        self.unified_worker.tick_5s.connect(self.trigger_async_server_status_check)
        self.unified_worker.start()

        startup_view = get_setting("default_view", "Dashboard")
        view_map = {"Dashboard": 0, "My Device": 1, "Shared Space Hosting": 2, "Settings App": 3}

        startup_behavior = get_setting("startup_behavior", "Open dashboard")
        if startup_behavior == "Start minimized to system tray":
            self.showMinimized()
        elif startup_view in view_map:
            self.sidebar_list.setCurrentRow(view_map[startup_view])

    @trace_execution("CombinedAppWindow")
    def trigger_async_link_refresh(self, *args, **kwargs):
        QTimer.singleShot(0, self.load_all_links)

    @trace_execution("CombinedAppWindow")
    def trigger_async_server_data_refresh(self, *args, **kwargs):
        QTimer.singleShot(0, self.refresh_server_data)

    @trace_execution("CombinedAppWindow")
    def trigger_async_backup(self, *args, **kwargs):
        QThread.msleep(1)
        perform_sqlite_backup()

    @trace_execution("CombinedAppWindow")
    def trigger_async_server_status_check(self, *args, **kwargs):
        servers = self.get_connected_servers()
        if servers and not (hasattr(self, 'status_worker') and self.status_worker and self.status_worker.isRunning()):
            self.status_worker = ServerStatusWorker(servers, self)
            self.status_worker.status_checked.connect(self.update_server_list_ui)
            self.status_worker.start()

    @trace_execution("CombinedAppWindow")
    def change_sidebar_section(self, index):
        self.content_stack.setCurrentIndex(index)

    @trace_execution("CombinedAppWindow")
    def load_persistent_logs(self):
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, 'r') as f:
                    self.log_box.setText(f.read())
                    self.log_box.moveCursor(QTextCursor.End)
                    scrollbar = self.log_box.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
            except Exception:
                pass

    @trace_execution("CombinedAppWindow")
    def append_log(self, message):
        log_event(message)
        if hasattr(self, 'log_box'):
            self.log_box.append(message)
            self.log_box.moveCursor(QTextCursor.End)
            scrollbar = self.log_box.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    @trace_execution("CombinedAppWindow")
    def apply_theme_and_styles(self):
        theme = get_setting("theme", "Dark Mode")
        accent = get_setting("accent_color", "#006400")
        high_contrast = get_setting("high_contrast", "False") == "True"

        if high_contrast:
            accent = "#FFFF00" if theme == "Dark Mode" else "#0000FF"

        template = DARK_STYLESHEET if theme == "Dark Mode" else LIGHT_STYLESHEET
        final_sheet = template.replace("%ACCENT_COLOR%", accent)

        app_inst = QApplication.instance()
        if app_inst:
            app_inst.setStyleSheet(final_sheet)

        font_scale = get_setting("font_scale", "Medium")
        base_pt = 10
        if font_scale == "Small":
            base_pt = 9
        elif font_scale == "Large":
            base_pt = 13
        elif font_scale == "Custom":
            base_pt = 11

        f = self.font()
        f.setPointSize(base_pt)
        if app_inst:
            app_inst.setFont(f)
        self.setFont(f)

    @trace_execution("CombinedAppWindow")
    def pick_accent_color(self):
        color = QColorDialog.getColor(QColor(get_setting("accent_color", "#006400")), self, "Choose Accent Color")
        if color.isValid():
            self.accent_input.setText(color.name())

    @trace_execution("CombinedAppWindow")
    def save_appearance_settings(self):
        global DEBUG_TRACING_ENABLED
        DEBUG_TRACING_ENABLED = self.debug_trace_check.isChecked()

        save_setting("theme", self.theme_combo.currentText())
        save_setting("accent_color", self.accent_input.text().strip())
        save_setting("font_scale", self.font_scale_combo.currentText())
        save_setting("density", self.density_combo.currentText())
        save_setting("animations", "True" if self.anim_check.isChecked() else "False")
        save_setting("debug_tracing", "True" if DEBUG_TRACING_ENABLED else "False")

        self.apply_theme_and_styles()
        self.toast_container.show_toast("Appearance settings saved and applied!")

    @trace_execution("CombinedAppWindow")
    def save_behavior_settings(self):
        save_setting("startup_behavior", self.startup_combo.currentText())
        save_setting("win_management", self.win_mgmt_combo.currentText())
        save_setting("default_view", self.default_view_combo.currentText())
        self.toast_container.show_toast("Behavior settings saved successfully!")

    @trace_execution("CombinedAppWindow")
    def reset_settings_to_defaults(self):
        confirm = QMessageBox.question(self, "Reset Settings",
                                       "Are you sure you want to reset all settings to default values?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            reset_all_settings()
            self.theme_combo.setCurrentText("Dark Mode")
            self.accent_input.setText("#006400")
            self.font_scale_combo.setCurrentText("Medium")
            self.density_combo.setCurrentText("Spacious")
            self.anim_check.setChecked(True)
            self.debug_trace_check.setChecked(True)
            self.startup_combo.setCurrentText("Open dashboard")
            self.win_mgmt_combo.setCurrentText("Open in new tabs")
            self.default_view_combo.setCurrentText("Dashboard")
            self.storage_input.setText(os.getcwd())
            self.autosave_combo.setCurrentText("Every 15 minutes")
            self.sound_check.setChecked(True)
            self.desktop_check.setChecked(True)
            self.banner_check.setChecked(True)
            self.event_filter_combo.setCurrentText("All System Events")
            self.shortcut_edit.setKeySequence(QKeySequence("Ctrl+K"))
            self.contrast_check.setChecked(False)
            self.apply_theme_and_styles()
            self.toast_container.show_toast("All settings reset to default successfully!")

    @trace_execution("CombinedAppWindow")
    def clear_cache(self):
        try:
            conn = sqlite3.connect(CLIENT_DB)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM offline_resources')
            cursor.execute('DELETE FROM favorite_resources')
            conn.commit()
            conn.close()
            self.toast_container.show_toast("Local cache cleared successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed clearing cache: {e}")

    @trace_execution("CombinedAppWindow")
    def export_data(self):
        try:
            export_path = "nairobi_hub_export.json"
            data = {"servers": self.get_connected_servers(), "offline": get_offline_resources()}
            with open(export_path, 'w') as f:
                json.dump(data, f, indent=2)
            self.toast_container.show_toast(f"Data exported successfully to {export_path}!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {e}")

    @trace_execution("CombinedAppWindow")
    def browse_storage_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Storage Directory", self.storage_input.text())
        if dir_path:
            self.storage_input.setText(dir_path)

    @trace_execution("CombinedAppWindow")
    def save_storage_settings(self):
        save_setting("storage_dir", self.storage_input.text().strip())
        save_setting("autosave_freq", self.autosave_combo.currentText())
        self.toast_container.show_toast("Storage settings saved successfully!")

    @trace_execution("CombinedAppWindow")
    def save_notification_settings(self):
        save_setting("notif_sound", "True" if self.sound_check.isChecked() else "False")
        save_setting("notif_desktop", "True" if self.desktop_check.isChecked() else "False")
        save_setting("notif_banner", "True" if self.banner_check.isChecked() else "False")
        save_setting("notif_filter", self.event_filter_combo.currentText())
        self.toast_container.show_toast("Notification settings saved successfully!")

    @trace_execution("CombinedAppWindow")
    def save_accessibility_settings(self):
        save_setting("app_hotkey", self.shortcut_edit.keySequence().toString())
        save_setting("high_contrast", "True" if self.contrast_check.isChecked() else "False")
        self.toast_container.show_toast("Accessibility settings saved successfully!")

    @trace_execution("CombinedAppWindow")
    def start_server(self):
        if not self.flask_thread:
            self.flask_thread = FlaskThread()
            self.flask_thread.start()
            self.append_log("Local listener started on port 5000...")
        subdomain = self.subdomain_input.text().strip().lower()
        subdomain = re.sub(r'[^a-z0-9-]', '', subdomain)
        if subdomain:
            self.subdomain_input.setText(subdomain)
            self.tunnel_thread = TunnelThread(subdomain=subdomain)
        else:
            self.tunnel_thread = TunnelThread()

        self.tunnel_thread.url_found.connect(self.on_url_found)
        self.tunnel_thread.log_signal.connect(self.append_log)
        self.tunnel_thread.start()

        self.start_btn.setEnabled(False)
        self.subdomain_input.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.dash_card_hosting_status.set_value("Connecting")

    @trace_execution("CombinedAppWindow")
    def stop_tunnel(self):
        if self.tunnel_thread:
            self.tunnel_thread.stop()
            self.tunnel_thread.quit()
            self.tunnel_thread = None
            self.url_input.clear()
            self.append_log("Hosting tunnel stopped.")
            self.start_btn.setEnabled(True)
            self.subdomain_input.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.dash_card_hosting_status.set_value("Offline")

    @trace_execution("CombinedAppWindow")
    def open_share_invite_dialog(self):
        url = self.url_input.text().strip() or "https://nairobi-hub.loca.lt"
        code = self.key_display.text().strip() or CURRENT_SERVER_KEY
        dialog = SharePopup(share_url=url, server_code=code, parent=self)
        dialog.exec()

    @trace_execution("CombinedAppWindow")
    def on_url_found(self, url):
        self.url_input.setText(url)
        self.append_log(f"Public Link Active: {url}")
        self.dash_card_hosting_status.set_value("Online")

        server_name = self.subdomain_input.text().strip().lower() or "nairobi-hub"
        server_key = CURRENT_SERVER_KEY
        client_id, _, _ = get_client_info()

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, username, role, can_write, can_read, is_banned, timeout_until, session_token, last_seen, dob, is_host)
            VALUES (?, ?, 'moderator', 1, 1, 0, 0, ?, CURRENT_TIMESTAMP, '2000-01-01', 1)
            ON CONFLICT(user_id) DO UPDATE SET role='moderator', is_host=1, can_write=1, can_read=1, is_banned=0
        ''', (client_id, get_client_info()[1], secrets.token_hex(16)))
        conn.commit()
        conn.close()

        QTimer.singleShot(100, lambda: self._sync_local_server(server_name, url, server_key, client_id))

    @trace_execution("CombinedAppWindow")
    def _sync_local_server(self, server_name, url, server_key, client_id):
        try:
            res = requests.post(
                f"{url}/api/auth/connect",
                headers={
                    'X-Client-ID': client_id,
                    'X-Server-Key': server_key,
                    'bypass-tunnel-reminder': 'true'
                },
                json={"username": get_client_info()[1]},
                timeout=3
            )
            token = ""
            if res.status_code == 200:
                token = res.json().get('session_token', '')

            conn = sqlite3.connect(CLIENT_DB)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO connected_servers (server_name, url, server_key, session_token) VALUES (?, ?, ?, ?)',
                (server_name, url, server_key, token)
            )
            conn.commit()
            conn.close()
            self.refresh_servers()
        except Exception as e:
            self.append_log(f"Failed auto-adding local hosted server to client: {e}")

    @trace_execution("CombinedAppWindow")
    def start_channel_scan(self):
        self.channels_result_list.clear()
        query = self.channel_search_input.text()
        self.scan_channels_btn.setEnabled(False)
        self.scan_channels_btn.setText("Scanning Signals...")

        self.channel_thread = ChannelSearchThread(query, self)
        self.channel_thread.server_found.connect(self.on_channel_found)
        self.channel_thread.search_finished.connect(lambda: [
            self.scan_channels_btn.setEnabled(True),
            self.scan_channels_btn.setText("Scan / Search Channels")
        ])
        self.channel_thread.start()

    @trace_execution("CombinedAppWindow")
    def on_channel_found(self, name, url, code):
        item = QListWidgetItem(f"Discovered Active Space: {name}\nURL: {url} | Signal: Verified (HTTP {code})")
        item.setData(Qt.UserRole, {"server_name": name, "url": url})
        self.channels_result_list.addItem(item)

    @trace_execution("CombinedAppWindow")
    def connect_discovered_channel(self, item):
        data = item.data(Qt.UserRole)
        if not data: return
        key, ok = QInputDialog.getText(self, "Connect to Space", f"Enter Space Key for '{data['server_name']}':",
                                       QLineEdit.Password)
        if ok and key:
            try:
                res = requests.post(f"{data['url']}/api/auth/connect",
                                    headers={'X-Client-ID': get_client_info()[0], 'X-Server-Key': key.strip(),
                                             'bypass-tunnel-reminder': 'true'}, json={"username": get_client_info()[1]},
                                    timeout=3)
                if res.status_code == 200:
                    token = res.json().get('session_token', '')
                    conn = sqlite3.connect(CLIENT_DB)
                    cursor = conn.cursor()
                    cursor.execute(
                        'INSERT OR REPLACE INTO connected_servers (server_name, url, server_key, session_token) VALUES (?, ?, ?, ?)',
                        (data['server_name'], data['url'], key.strip(), token))
                    conn.commit()
                    conn.close()
                    QMessageBox.information(self, "Success",
                                            f"Successfully connected to space '{data['server_name']}'!")
                    self.refresh_servers()
                else:
                    QMessageBox.critical(self, "Failed", f"Connection rejected: {res.text}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not connect: {e}")

    @trace_execution("CombinedAppWindow")
    def refresh_server_data(self, *args, **kwargs):
        self.load_users()
        self.load_server_files()
        self.load_server_moderator_explorer()
        self.update_dashboard_metrics()
        self.load_all_links()

    @trace_execution("CombinedAppWindow")
    def update_dashboard_metrics(self):
        user_count = self.users_list.count()
        link_count = self.files_list.count()
        self.dash_card_users.set_value(str(user_count))
        self.dash_card_hosting_links.set_value(str(link_count))

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE last_seen >= datetime('now', '-60 seconds')")
        active_count = cursor.fetchone()[0]
        conn.close()

        url = self.url_input.text().strip()
        if url:
            self.unified_summary_lbl.setText(
                f"Active hosting address: {url} | Space Key: {CURRENT_SERVER_KEY} | Online Users: {active_count}")
        else:
            self.unified_summary_lbl.setText(
                f"Space Key: {CURRENT_SERVER_KEY} | Not currently hosting publicly. | Online Users: {active_count}")

    @trace_execution("CombinedAppWindow")
    def create_user_icon(self, role, can_write, is_host=False):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        accent = get_setting("accent_color", "#006400")
        color = QColor("#FFD700") if is_host else (QColor(accent) if role == 'moderator' else QColor("#2D5A3C"))
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(12, 4, 40, 40)
        painter.setBrush(QColor("#FFD700") if can_write else QColor("#EF4444"))
        painter.drawEllipse(42, 42, 18, 18)
        painter.end()
        return QIcon(pixmap)

    @trace_execution("CombinedAppWindow")
    def create_item_icon(self, itype, is_public=True):
        pixmap = QPixmap(56, 56)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        itype = str(itype).lower()

        painter.setBrush(QBrush(QColor("#132219")))
        painter.setPen(QPen(QColor("#1E3A29"), 1))
        painter.drawRoundedRect(4, 4, 48, 48, 8, 8)

        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(QPen(QColor("#F1F5F9")))

        if "folder" in itype:
            painter.setBrush(QBrush(QColor("#FFD700")))
            painter.setPen(Qt.NoPen)
            painter.drawRect(12, 18, 32, 24)
            painter.drawRect(12, 14, 12, 6)
        elif "word" in itype or "doc" in itype:
            painter.setBrush(QBrush(QColor("#2563EB")))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(16, 10, 24, 36, 4, 4)
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawText(QRectF(16, 10, 24, 36), Qt.AlignCenter, "W")
        elif "excel" in itype or "sheet" in itype:
            painter.setBrush(QBrush(QColor("#16A34A")))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(16, 10, 24, 36, 4, 4)
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawText(QRectF(16, 10, 24, 36), Qt.AlignCenter, "X")
        elif "powerpoint" in itype or "ppt" in itype:
            painter.setBrush(QBrush(QColor("#DC2626")))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(16, 10, 24, 36, 4, 4)
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawText(QRectF(16, 10, 24, 36), Qt.AlignCenter, "P")
        elif "image" in itype or "photo" in itype:
            painter.setBrush(QBrush(QColor("#9333EA")))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(14, 12, 28, 32, 4, 4)
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(22, 20, 6, 6)
        elif "audio" in itype or "music" in itype:
            painter.setBrush(QBrush(QColor("#EA580C")))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(14, 12, 28, 32, 4, 4)
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawText(QRectF(14, 12, 28, 32), Qt.AlignCenter, "♪")
        elif "video" in itype or "movie" in itype:
            painter.setBrush(QBrush(QColor("#0284C7")))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(14, 12, 28, 32, 4, 4)
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawText(QRectF(14, 12, 28, 32), Qt.AlignCenter, "▶")
        elif "txt" in itype or "document" in itype:
            painter.setBrush(QBrush(QColor("#64748B")))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(16, 10, 24, 36, 4, 4)
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawText(QRectF(16, 10, 24, 36), Qt.AlignCenter, "TXT")
        else:
            painter.setBrush(QBrush(QColor("#475569")))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(16, 10, 24, 36, 4, 4)
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawText(QRectF(16, 10, 24, 36), Qt.AlignCenter, "?")

        status_color = QColor("#22C55E") if is_public else QColor("#EF4444")
        painter.setBrush(QBrush(status_color))
        painter.setPen(QPen(QColor("#132219"), 1))
        painter.drawEllipse(38, 38, 14, 14)

        painter.end()
        return QIcon(pixmap)

    @trace_execution("CombinedAppWindow")
    def load_users(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, COALESCE(username, user_id), role, can_write, can_read, is_banned, timeout_until, is_host FROM users")
        rows = cursor.fetchall()
        conn.close()
        self.users_list.clear()
        for uid, uname, role, can_write, can_read, is_banned, timeout_until, is_host in rows:
            icon = self.create_user_icon(role, can_write, is_host)
            status_text = f"{uname}\n[{'HOST' if is_host else role.upper()}]"
            if is_banned:
                status_text += " [BANNED]"
            elif timeout_until and timeout_until > time.time():
                rem = int(timeout_until - time.time())
                status_text += f" [TIMEOUT: {rem}s]"

            item = QListWidgetItem(icon, status_text)
            item.setData(Qt.UserRole,
                         {"user_id": uid, "username": uname, "role": role, "can_write": can_write, "can_read": can_read,
                          "is_banned": is_banned, "timeout_until": timeout_until, "is_host": is_host})
            self.users_list.addItem(item)
        self.filter_users()

    @trace_execution("CombinedAppWindow")
    def filter_users(self, *args, **kwargs):
        query = self.user_search_input.text().strip().lower()
        for i in range(self.users_list.count()):
            item = self.users_list.item(i)
            data = item.data(Qt.UserRole)
            matches = not query or query in str(data.get("user_id", "")).lower() or query in str(
                data.get("username", "")).lower()
            item.setHidden(not matches)

    @trace_execution("CombinedAppWindow")
    def load_server_files(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.id, l.title, l.item_type, l.is_public, l.user_id, l.url, COALESCE(u.username, l.user_id), l.is_hidden
            FROM shared_links l
            LEFT JOIN users u ON l.user_id = u.user_id
        """)
        rows = cursor.fetchall()
        conn.close()
        self.files_list.clear()
        for lid, title, itype, is_pub, uid, url, uname, is_hidden in rows:
            icon = self.create_item_icon(itype, is_pub)
            lbl = f"{title}\nBy: {uname}\n({'Hidden' if is_hidden else ('Public' if is_pub else 'Private')})"
            item = QListWidgetItem(icon, lbl)
            item.setData(Qt.UserRole,
                         {"id": lid, "title": title, "item_type": itype, "is_public": is_pub, "user_id": uid,
                          "username": uname, "url": url, "is_hidden": is_hidden})
            self.files_list.addItem(item)

    @trace_execution("CombinedAppWindow")
    def load_server_moderator_explorer(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.id, l.title, l.item_type, l.is_public, l.user_id, l.url, COALESCE(u.username, l.user_id), l.is_hidden
            FROM shared_links l
            LEFT JOIN users u ON l.user_id = u.user_id
        """)
        rows = cursor.fetchall()
        conn.close()
        self.server_mod_explorer.clear()
        for lid, title, itype, is_pub, uid, url, uname, is_hidden in rows:
            icon = self.create_item_icon(itype, is_pub)
            lbl = f"{title}\nBy: {uname}\n({'Hidden' if is_hidden else 'Visible'})"
            item = QListWidgetItem(icon, lbl)
            item.setData(Qt.UserRole,
                         {"id": lid, "title": title, "item_type": itype, "is_public": is_pub, "user_id": uid,
                          "username": uname, "url": url, "is_hidden": is_hidden})
            self.server_mod_explorer.addItem(item)

    @trace_execution("CombinedAppWindow")
    def filter_files(self, *args, **kwargs):
        query = self.file_search_input.text().strip().lower()
        selected_type = self.file_type_filter.currentText().lower()
        for i in range(self.files_list.count()):
            item = self.files_list.item(i)
            data = item.data(Qt.UserRole)
            matches = (not query or query in str(data.get("title", "")).lower()) and (
                    selected_type == "all types" or selected_type == str(data.get("item_type", "")).lower())
            item.setHidden(not matches)

    @trace_execution("CombinedAppWindow")
    def show_user_context_menu(self, pos):
        item = self.users_list.itemAt(pos)
        if not item: return
        data = item.data(Qt.UserRole)
        menu = QMenu(self)

        if not data.get('is_host'):
            if data['role'] == 'moderator':
                mod_action = QAction("Revoke Moderator", self)
                mod_action.triggered.connect(
                    lambda: self.execute_moderator_user_action(data['user_id'], 'toggle_moderator'))
            else:
                mod_action = QAction("Add Moderator", self)
                mod_action.triggered.connect(
                    lambda: self.execute_moderator_user_action(data['user_id'], 'toggle_moderator'))
            menu.addAction(mod_action)

            rw_action = QAction("Revoke Read / Write Access...", self)
            rw_action.triggered.connect(lambda: self.open_revoke_access_dialog(data))
            menu.addAction(rw_action)

            if data.get('is_banned', 0):
                ban_action = QAction("Unban User", self)
                ban_action.triggered.connect(
                    lambda: self.execute_moderator_user_action(data['user_id'], 'ban', {'is_banned': 0}))
            else:
                ban_action = QAction("Ban User", self)
                ban_action.triggered.connect(
                    lambda: self.execute_moderator_user_action(data['user_id'], 'ban', {'is_banned': 1}))
            menu.addAction(ban_action)

            if data.get('timeout_until', 0) and data['timeout_until'] > time.time():
                to_action = QAction("Remove Timeout", self)
                to_action.triggered.connect(
                    lambda: self.execute_moderator_user_action(data['user_id'], 'timeout', {'duration_seconds': 0}))
            else:
                to_action = QAction("Timeout User...", self)
                to_action.triggered.connect(lambda: self.open_timeout_dialog(data['user_id']))
            menu.addAction(to_action)

            remove_user_action = QAction("Remove User from Server", self)
            remove_user_action.triggered.connect(
                lambda: self.execute_moderator_user_action(data['user_id'], 'remove_user'))
            menu.addAction(remove_user_action)
        else:
            host_lbl = QAction("Host User (Protected)", self)
            host_lbl.setEnabled(False)
            menu.addAction(host_lbl)

        menu.addSeparator()
        meter_action = QAction("Test Connection Quality...", self)
        meter_action.triggered.connect(lambda: ConnectionMeterDialog(data, self.url_input.text().strip(), self).exec())
        menu.addAction(meter_action)

        menu.exec(self.users_list.mapToGlobal(pos))

    @trace_execution("CombinedAppWindow")
    def execute_moderator_user_action(self, user_id, action, extra_payload=None):
        payload = {"user_id": user_id, "action": action}
        if extra_payload:
            payload.update(extra_payload)
        try:
            url = f"http://127.0.0.1:5000/api/moderator/user_action"
            headers = {'X-Client-ID': get_client_info()[0], 'X-Server-Key': CURRENT_SERVER_KEY}
            res = requests.post(url, json=payload, headers=headers, timeout=2)
            if res.status_code == 200:
                self.toast_container.show_toast("User action applied successfully!")
                self.refresh_server_data()
            else:
                content_type = res.headers.get('content-type', '')
                error_msg = res.json().get('error', res.text) if 'json' in content_type else res.text
                QMessageBox.critical(self, "Error", f"Failed: {error_msg}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection error: {e}")

    @trace_execution("CombinedAppWindow")
    def open_timeout_dialog(self, user_id):
        dlg = TimeoutDialog(self)
        if dlg.exec() == QDialog.Accepted:
            secs = dlg.get_duration_seconds()
            self.execute_moderator_user_action(user_id, 'timeout', {'duration_seconds': secs})

    @trace_execution("CombinedAppWindow")
    def open_revoke_access_dialog(self, data):
        dlg = RevokeAccessDialog(data.get('can_read', 1), data.get('can_write', 1), self)
        if dlg.exec() == QDialog.Accepted:
            r, w = dlg.get_access_flags()
            self.execute_moderator_user_action(data['user_id'], 'revoke_access', {'can_read': r, 'can_write': w})

    @trace_execution("CombinedAppWindow")
    def show_moderator_explorer_context_menu(self, list_widget, pos):
        item = list_widget.itemAt(pos)
        if not item: return
        data = item.data(Qt.UserRole)
        if not data: return

        menu = QMenu(self)

        read_action = QAction("Read File", self)
        read_action.triggered.connect(lambda: webbrowser.open(data.get('url', '')))
        menu.addAction(read_action)

        if data.get('is_hidden', 0):
            hide_action = QAction("Unhide from Users", self)
            hide_action.triggered.connect(
                lambda: self.execute_moderator_file_action(data['id'], 'hide', {'is_hidden': 0}))
        else:
            hide_action = QAction("Hide from Users", self)
            hide_action.triggered.connect(
                lambda: self.execute_moderator_file_action(data['id'], 'hide', {'is_hidden': 1}))
        menu.addAction(hide_action)

        remove_action = QAction("Remove the File", self)
        remove_action.triggered.connect(lambda: self.execute_moderator_file_action(data['id'], 'remove'))
        menu.addAction(remove_action)

        menu.exec(list_widget.mapToGlobal(pos))


    @trace_execution("CombinedAppWindow")
    def execute_moderator_file_action(self, link_id, action, extra_payload=None):
        payload = {"link_id": link_id, "action": action}
        if extra_payload:
            payload.update(extra_payload)
        try:
            url = f"http://127.0.0.1:5000/api/moderator/file_action"
            headers = {'X-Client-ID': get_client_info()[0], 'X-Server-Key': CURRENT_SERVER_KEY}
            res = requests.post(url, json=payload, headers=headers, timeout=2)
            if res.status_code == 200:
                self.toast_container.show_toast("File action applied successfully!")
                self.refresh_server_data()
                self.load_all_links()
            else:
                content_type = res.headers.get('content-type', '')
                error_msg = res.json().get('error', res.text) if 'json' in content_type else res.text
                QMessageBox.critical(self, "Error", f"Failed: {error_msg}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection error: {e}")

    @trace_execution("CombinedAppWindow")
    def show_server_file_context_menu(self, pos):
        item = self.files_list.itemAt(pos)
        if not item: return
        data = item.data(Qt.UserRole)
        menu = QMenu(self)
        open_action = QAction("Open Link in Browser", self)
        open_action.triggered.connect(lambda: webbrowser.open(data.get('url', '')))
        menu.addAction(open_action)

        edit_action = QAction("Edit Attachment", self)
        edit_action.triggered.connect(lambda: self.edit_server_file(data))
        menu.addAction(edit_action)

        del_action = QAction("Delete Attachment", self)
        del_action.triggered.connect(lambda: self.delete_server_file(data))
        menu.addAction(del_action)

        menu.exec(self.files_list.mapToGlobal(pos))

    @trace_execution("CombinedAppWindow")
    def edit_server_file(self, data):
        modal = LinkModal(self, data)
        if modal.exec() == QDialog.Accepted:
            res_data = modal.get_data()
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE shared_links SET title = ?, url = ?, item_type = ?, is_public = ? WHERE id = ?",
                           (res_data['title'], res_data['url'], res_data['item_type'], res_data['is_public'],
                            data['id']))
            conn.commit()
            conn.close()
            self.load_server_files()
            self.toast_container.show_toast("Server attachment updated successfully!")

    @trace_execution("CombinedAppWindow")
    def delete_server_file(self, data):
        confirm = QMessageBox.question(self, "Delete Attachment", f"Are you sure you want to delete '{data['title']}'?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM shared_links WHERE id = ?", (data['id'],))
            conn.commit()
            conn.close()
            self.load_server_files()
            self.toast_container.show_toast("Server attachment deleted successfully!")

    @trace_execution("CombinedAppWindow")
    def show_explorer_context_menu(self, list_widget, pos):
        item = list_widget.itemAt(pos)
        if not item: return
        data = item.data(Qt.UserRole)
        if not data: return

        menu = QMenu(self)
        open_action = QAction("Open Link in Browser", self)
        open_action.triggered.connect(lambda: self.open_link_in_browser(item))
        menu.addAction(open_action)

        favs = get_favorites()
        is_fav = (data.get('origin_server'), data.get('id')) in favs
        fav_action = QAction("Remove from Bookmarks" if is_fav else "Add to Bookmarks", self)
        if is_fav:
            fav_action.triggered.connect(
                lambda: [remove_favorite(data.get('origin_server'), data.get('id')), self.load_all_links()])
        else:
            fav_action.triggered.connect(lambda: [
                add_favorite(data.get('origin_server'), data.get('id'), data.get('title'), data.get('url'),
                             data.get('item_type')), self.load_all_links()])
        menu.addAction(fav_action)

        offline_items = get_offline_resources()
        is_off = any(o.get('origin_server') == data.get('origin_server') and o.get('id') == data.get('id') for o in
                     offline_items)
        off_action = QAction("Remove from Offline Mode" if is_off else "Save for Offline Mode", self)
        if is_off:
            off_action.triggered.connect(
                lambda: [remove_offline_resource(data.get('origin_server'), data.get('id')), self.load_all_links()])
        else:
            off_action.triggered.connect(lambda: [add_offline_resource(data), self.load_all_links()])
        menu.addAction(off_action)

        menu.addSeparator()
        edit_action = QAction("Edit Attachment", self)
        edit_action.triggered.connect(lambda: self.edit_link(data))
        menu.addAction(edit_action)

        del_action = QAction("Delete Attachment", self)
        del_action.triggered.connect(lambda: self.delete_link(data))
        menu.addAction(del_action)

        menu.exec(list_widget.mapToGlobal(pos))

    @trace_execution("CombinedAppWindow")
    def open_link_in_browser(self, item):
        data = item.data(Qt.UserRole)
        if data and data.get('url'):
            webbrowser.open(data.get('url'))

    @trace_execution("CombinedAppWindow")
    def add_drive_link(self):
        servers = self.get_connected_servers()
        if not servers:
            QMessageBox.warning(self, "No Spaces", "Please connect to at least one space first.")
            return
        modal = LinkModal(self)
        if modal.exec() == QDialog.Accepted:
            d = modal.get_data()
            srv = servers[0]
            try:
                res = requests.post(f"{srv['url']}/api/links", json=d, headers=get_auth_headers(srv), timeout=3)
                if res.status_code == 201:
                    self.toast_container.show_toast("Resource attached successfully!")
                    self.load_all_links()
                else:
                    QMessageBox.critical(self, "Error", f"Failed: {res.text}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Connection error: {e}")

    @trace_execution("CombinedAppWindow")
    def edit_link(self, data):
        modal = LinkModal(self, data)
        if modal.exec() == QDialog.Accepted:
            d = modal.get_data()
            d['id'] = data.get('id')
            srv = self.get_server_by_name(data.get('origin_server'))
            if srv:
                try:
                    res = requests.put(f"{srv['url']}/api/links", json=d, headers=get_auth_headers(srv), timeout=3)
                    if res.status_code == 200:
                        self.toast_container.show_toast("Attachment updated successfully!")
                        self.load_all_links()
                    else:
                        QMessageBox.critical(self, "Error", f"Failed: {res.text}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error: {e}")

    @trace_execution("CombinedAppWindow")
    def delete_link(self, data):
        confirm = QMessageBox.question(self, "Delete Attachment",
                                       f"Are you sure you want to delete '{data.get('title')}'?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            srv = self.get_server_by_name(data.get('origin_server'))
            if srv:
                try:
                    res = requests.delete(f"{srv['url']}/api/links?id={data.get('id')}", headers=get_auth_headers(srv),
                                          timeout=3)
                    if res.status_code == 200:
                        self.toast_container.show_toast("Attachment deleted successfully!")
                        self.load_all_links()
                    else:
                        QMessageBox.critical(self, "Error", f"Failed: {res.text}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error: {e}")

    @trace_execution("CombinedAppWindow")
    def get_connected_servers(self):
        conn = sqlite3.connect(CLIENT_DB)
        cursor = conn.cursor()
        cursor.execute('SELECT server_name, url, server_key, session_token FROM connected_servers')
        rows = cursor.fetchall()
        conn.close()
        servers = []
        for r in rows:
            servers.append({
                "server_name": r[0],
                "url": r[1],
                "server_key": r[2],
                "session_token": r[3]
            })
        return servers

    @trace_execution("CombinedAppWindow")
    def get_server_by_name(self, s_name):
        for srv in self.get_connected_servers():
            if srv['server_name'] == s_name:
                return srv
        return None

    @trace_execution("CombinedAppWindow")
    def refresh_servers(self):
        servers = self.get_connected_servers()
        self.server_list.clear()
        self.hosting_servers_list.clear()
        self.server_filter.blockSignals(True)
        self.server_filter.clear()
        self.server_filter.addItem("All Spaces")

        for srv in servers:
            self.server_filter.addItem(srv['server_name'])

            item = QListWidgetItem(srv['server_name'])
            item.setData(Qt.UserRole, srv)
            item.setData(Qt.UserRole + 1, False)
            self.server_list.addItem(item)

            card = QFrame()
            card.setObjectName("DashboardCard")
            card.setMinimumHeight(72)

            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(16, 18, 16, 18)
            card_layout.setSpacing(14)

            info_lbl = QLabel(f"<b>{srv['server_name']}</b><br><span style='color: #A3B8CC;'>{srv['url']}</span>")
            info_lbl.setWordWrap(True)
            card_layout.addWidget(info_lbl, 1)

            reconn_btn = QPushButton("Reconnect")
            reconn_btn.setMinimumHeight(38)
            reconn_btn.clicked.connect(lambda checked=False, s=srv: self.reconnect_hosting_server(s))

            rem_btn = QPushButton("Remove")
            rem_btn.setObjectName("StopBtn")
            rem_btn.setMinimumHeight(38)
            rem_btn.clicked.connect(lambda checked=False, name=srv['server_name']: self.remove_hosting_server(name))

            card_layout.addWidget(reconn_btn)
            card_layout.addWidget(rem_btn)

            card.adjustSize()
            h_item = QListWidgetItem(self.hosting_servers_list)
            h_item.setSizeHint(card.sizeHint())
            self.hosting_servers_list.addItem(h_item)
            self.hosting_servers_list.setItemWidget(h_item, card)

        self.server_filter.blockSignals(False)
        self.card_servers.set_value(str(len(servers)))
        self.load_all_links()

    @trace_execution("CombinedAppWindow")
    def update_server_list_ui(self, results):
        current_selection = self.server_filter.currentText()
        self.server_list.clear()
        self.server_filter.blockSignals(True)
        self.server_filter.clear()
        self.server_filter.addItem("All Spaces")

        for server_name, url, server_key, session_token, is_online in results:
            item = QListWidgetItem(server_name)
            item.setData(Qt.UserRole, {
                "server_name": server_name,
                "url": url,
                "server_key": server_key,
                "session_token": session_token
            })
            item.setData(Qt.UserRole + 1, is_online)
            self.server_list.addItem(item)
            self.server_filter.addItem(server_name)

        if current_selection in [self.server_filter.itemText(i) for i in range(self.server_filter.count())]:
            self.server_filter.setCurrentText(current_selection)
        self.server_filter.blockSignals(False)

    @trace_execution("CombinedAppWindow")
    def reconnect_hosting_server(self, srv_data):
        self.stop_tunnel()
        time.sleep(0.5)
        self.subdomain_input.setText(srv_data['server_name'])
        self.start_server()
        self.toast_container.show_toast(f"Terminated existing session and reconnected to '{srv_data['server_name']}'!")

    @trace_execution("CombinedAppWindow")
    def remove_hosting_server(self, server_name):
        conn = sqlite3.connect(CLIENT_DB)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM connected_servers WHERE server_name = ?', (server_name,))
        conn.commit()
        conn.close()
        self.toast_container.show_toast(f"Removed server '{server_name}' from hosting history.")
        self.refresh_servers()

    @trace_execution("CombinedAppWindow")
    def load_all_links(self, *args, **kwargs):
        servers = self.get_connected_servers()
        if not servers:
            self.explorer_list.clear()
            self.fav_list.clear()
            self.offline_list.clear()
            self.client_mod_explorer.clear()
            return

        selected_srv = self.server_filter.currentText() if hasattr(self, 'server_filter') else "All Spaces"

        if self.fetch_thread and self.fetch_thread.isRunning():
            return

        self.fetch_thread = LinkFetcherThread(servers, selected_srv, self)
        self.fetch_thread.links_fetched.connect(self.populate_explorer_lists)
        self.fetch_thread.start()

        self.check_client_moderator_privilege_async(servers)

    @trace_execution("CombinedAppWindow")
    def check_client_moderator_privilege_async(self, servers):
        class ModCheckThread(QThread):
            mod_status_ready = Signal(bool, list)

            def __init__(self, srvs):
                super().__init__()
                self.srvs = srvs

            @trace_execution("ModCheckThread")
            def run(self):
                is_mod = False
                for srv in self.srvs:
                    try:
                        res = requests.get(f"{srv['url']}/api/user/profile", headers=get_auth_headers(srv), timeout=1.5)
                        if res.status_code == 200:
                            data = res.json()
                            if data.get('role') == 'moderator':
                                is_mod = True
                                break
                    except Exception:
                        pass
                self.mod_status_ready.emit(is_mod, self.srvs)

        self.mod_check_thread = ModCheckThread(servers)
        self.mod_check_thread.mod_status_ready.connect(self.on_mod_status_checked)
        self.mod_check_thread.start()

    @trace_execution("CombinedAppWindow")
    def on_mod_status_checked(self, is_mod, servers):
        tab_index = -1
        for i in range(self.client_tab_widget.count()):
            if self.client_tab_widget.tabText(i) == "Moderator Panel":
                tab_index = i
                break

        if is_mod and tab_index == -1:
            self.client_tab_widget.addTab(self.client_mod_tab, "Moderator Panel")
            self.load_client_moderator_explorer(servers)
        elif not is_mod and tab_index != -1:
            self.client_tab_widget.removeTab(tab_index)

    @trace_execution("CombinedAppWindow")
    def load_client_moderator_explorer(self, servers):
        self.client_mod_explorer.clear()
        for srv in servers:
            try:
                res = requests.get(f"{srv['url']}/api/links", headers=get_auth_headers(srv), timeout=2)
                if res.status_code == 200:
                    for item_data in res.json():
                        item_data['origin_server'] = srv['server_name']
                        icon = self.create_item_icon(item_data.get('item_type'), item_data.get('is_public', True))
                        item = QListWidgetItem(icon, f"{item_data.get('title')}\n[{srv['server_name']}]")
                        item.setData(Qt.UserRole, item_data)
                        self.client_mod_explorer.addItem(item)
            except Exception:
                pass

    @trace_execution("CombinedAppWindow")
    def populate_explorer_lists(self, links, statuses):
        self.explorer_list.clear()
        self.fav_list.clear()
        self.offline_list.clear()

        favs = get_favorites()
        offline_items = {(o['origin_server'], o['id']): o for o in get_offline_resources()}

        pub_count = 0
        priv_count = 0

        for item_data in links:
            if item_data.get('is_public'):
                pub_count += 1
            else:
                priv_count += 1

            icon = self.create_item_icon(item_data.get('item_type'), item_data.get('is_public', True))
            label_text = f"{item_data.get('title')}\nBy: {item_data.get('username')}\nSpace: {item_data.get('origin_server')}"

            item = QListWidgetItem(icon, label_text)
            item.setData(Qt.UserRole, item_data)
            self.explorer_list.addItem(item)

            if (item_data.get('origin_server'), item_data.get('id')) in favs:
                fav_item = QListWidgetItem(icon, label_text)
                fav_item.setData(Qt.UserRole, item_data)
                self.fav_list.addItem(fav_item)

        for (srv_name, lid), o_data in offline_items.items():
            icon = self.create_item_icon(o_data.get('item_type'), o_data.get('is_public', True))
            label_text = f"{o_data.get('title')}\nBy: {o_data.get('username')}\n[OFFLINE COPY]"
            off_item = QListWidgetItem(icon, label_text)
            off_item.setData(Qt.UserRole, o_data)
            self.offline_list.addItem(off_item)

        self.card_links.set_value(str(len(links)))
        self.card_public.set_value(str(pub_count))
        self.card_private.set_value(str(priv_count))

    @trace_execution("CombinedAppWindow")
    def filter_explorer(self, *args, **kwargs):
        query = self.search_input.text().strip().lower()
        for i in range(self.explorer_list.count()):
            item = self.explorer_list.item(i)
            data = item.data(Qt.UserRole)
            matches = not query or query in str(data.get("title", "")).lower() or query in str(
                data.get("username", "")).lower() or query in str(data.get("origin_server", "")).lower()
            item.setHidden(not matches)

    @trace_execution("CombinedAppWindow")
    def add_all_current_server_to_offline(self):
        try:
            conn = sqlite3.connect(CLIENT_DB, timeout=30.0)
            cursor = conn.cursor()
            count = 0
            for i in range(self.explorer_list.count()):
                item = self.explorer_list.item(i)
                data = item.data(Qt.UserRole)
                if data and data.get('origin_server') is not None and data.get('id') is not None:
                    cursor.execute('''
                            INSERT OR REPLACE INTO offline_resources (server_name, link_id, title, url, item_type, is_public, username)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                        data.get('origin_server'),
                        data.get('id'),
                        data.get('title'),
                        data.get('url'),
                        data.get('item_type', 'file'),
                        1 if data.get('is_public', True) else 0,
                        data.get('username', 'Unknown')
                    ))
                    count += 1
            conn.commit()
            conn.close()
            self.toast_container.show_toast(f"Saved {count} resource(s) for offline mode successfully!")
            self.load_all_links()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save resources for offline mode: {e}")


    @trace_execution("CombinedAppWindow")
    def show_server_context_menu(self, pos):
        item = self.server_list.itemAt(pos)
        if not item: return
        srv_data = item.data(Qt.UserRole)

        menu = QMenu(self)
        edit_action = QAction("Edit Space Details", self)
        edit_action.triggered.connect(lambda: self.edit_server(srv_data))
        menu.addAction(edit_action)

        rem_action = QAction("Remove Space", self)
        rem_action.triggered.connect(lambda: self.remove_hosting_server(srv_data['server_name']))
        menu.addAction(rem_action)

        menu.exec(self.server_list.mapToGlobal(pos))

    @trace_execution("CombinedAppWindow")
    def add_server(self):
        modal = ServerModal(self)
        if modal.exec() == QDialog.Accepted:
            name, url, key = modal.get_data()
            if not name:
                return
            client_id, _, _ = get_client_info()
            try:
                res = requests.post(
                    f"{url}/api/auth/connect",
                    headers={
                        'X-Client-ID': client_id,
                        'X-Server-Key': key,
                        'bypass-tunnel-reminder': 'true'
                    },
                    json={"username": get_client_info()[1]},
                    timeout=3
                )

                if res.status_code == 200:
                    token = res.json().get('session_token', '')

                    conn = sqlite3.connect(CLIENT_DB)
                    cursor = conn.cursor()
                    cursor.execute(
                        'INSERT OR REPLACE INTO connected_servers (server_name, url, server_key, session_token) VALUES (?, ?, ?, ?)',
                        (name, url, key, token))
                    conn.commit()
                    conn.close()
                    self.toast_container.show_toast(f"Successfully connected to space '{name}'!")
                    self.refresh_servers()
                else:
                    QMessageBox.warning(
                        self,
                        "Connection Rejected",
                        f"The space '{name}' rejected the connection or provided an invalid key (HTTP {res.status_code})."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Space Not Found / Offline",
                    f"Could not connect to space '{name}'. The server does not exist or is currently offline.\n\nDetails: {e}"
                )


    @trace_execution("CombinedAppWindow")
    def edit_server(self, srv_data):
        modal = ServerModal(self, srv_data)
        if modal.exec() == QDialog.Accepted:
            name, url, key = modal.get_data()
            conn = sqlite3.connect(CLIENT_DB)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE connected_servers SET server_name = ?, url = ?, server_key = ? WHERE server_name = ?',
                (name, url, key, srv_data['server_name']))
            conn.commit()
            conn.close()
            self.refresh_servers()
            self.toast_container.show_toast("Space connection details updated successfully!")

    @trace_execution("CombinedAppWindow")
    def open_profile(self):
        dlg = ProfileDialog(self.get_connected_servers(), self)
        dlg.exec()

    @trace_execution("CombinedAppWindow")
    def closeEvent(self, event):
        try:
            if hasattr(self, 'unified_worker') and self.unified_worker:
                self.unified_worker.running = False
                self.unified_worker.quit()
                self.unified_worker.wait(1000)

            self.stop_tunnel()

            if self.flask_thread:
                self.flask_thread.stop()
                self.flask_thread.quit()
                self.flask_thread.wait(1000)
                self.flask_thread = None
        except Exception as e:
            log_event(f"Error during graceful shutdown: {e}")

        event.accept()

class LinkFetcherThread(QThread):
    links_fetched = Signal(list, dict)

    def __init__(self, servers, selected_server="All Spaces", parent=None):
        super().__init__(parent)
        self.servers = servers
        self.selected_server = selected_server

    @trace_execution("LinkFetcherThread")
    def run(self):
        all_links = []
        statuses = {}
        for srv in self.servers:
            s_name = srv['server_name']
            if self.selected_server != "All Spaces" and s_name != self.selected_server:
                continue
            headers = get_auth_headers(srv)
            try:
                res = requests.get(f"{srv['url']}/api/links", headers=headers, timeout=2.5)
                if res.status_code == 200:
                    statuses[s_name] = True
                    for item in res.json():
                        item['origin_server'] = s_name
                        item['server_url'] = srv['url']
                        item['server_key'] = srv['server_key']
                        item['session_token'] = srv['session_token']
                        all_links.append(item)
                else:
                    statuses[s_name] = False
            except Exception:
                statuses[s_name] = False
        self.links_fetched.emit(all_links, statuses)


class ServerModal(QDialog):
    def __init__(self, parent=None, server_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Linked Space" if server_data else "Connect New Space")
        self.resize(400, 240)
        layout = QFormLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. nairobi-hub")
        self.key_input = QLineEdit()
        self.url_display = QLineEdit()
        self.url_display.setReadOnly(True)

        layout.addRow("Space Name:", self.name_input)
        layout.addRow("Connection Address:", self.url_display)
        layout.addRow("Space Key:", self.key_input)

        if server_data:
            self.name_input.setText(server_data['server_name'])
            self.key_input.setText(server_data['server_key'])
            self.url_display.setText(server_data['url'])

        self.name_input.textChanged.connect(
            lambda t: self.url_display.setText(f"https://{t.strip().lower()}.loca.lt" if t.strip() else ""))
        save_btn = QPushButton("Connect & Save")
        save_btn.clicked.connect(self.accept)
        layout.addRow(save_btn)
        self.setLayout(layout)

    def accept(self):
        name, _, _ = self.get_data()
        if len(name) < 3 or len(name) > 16:
            QMessageBox.warning(
                self,
                "Invalid Space Name Length",
                "Space name must be between 3 and 16 characters long."
            )
            return
        super().accept()

    def get_data(self):
        s_name = self.name_input.text().strip().lower().replace("https://", "").replace(".loca.lt", "")
        return s_name, f"https://{s_name}.loca.lt", self.key_input.text().strip()


class ProfileDialog(QDialog):
    def __init__(self, active_servers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Profile & Accounts")
        self.resize(480, 340)
        self.active_servers = active_servers
        client_id, username, dob = get_client_info()

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        form = QFormLayout()
        form.addRow("User ID:", QLabel(client_id))
        self.uname_input = QLineEdit(username)
        form.addRow("Username:", self.uname_input)
        self.dob_input = QLineEdit(dob)
        self.dob_input.setPlaceholderText("YYYY-MM-DD")
        form.addRow("Date of Birth:", self.dob_input)

        save_btn = QPushButton("Update Profile")
        save_btn.clicked.connect(self.save_profile)
        form.addRow(save_btn)
        layout.addLayout(form)

        layout.addWidget(QLabel("<b>Connected Spaces Status:</b>"))
        self.status_list = QListWidget()
        layout.addWidget(self.status_list)
        self.setLayout(layout)
        self.load_status()

    def load_status(self):
        self.status_list.clear()
        for srv in self.active_servers:
            headers = get_auth_headers(srv)
            try:
                res = requests.get(f"{srv['url']}/api/user/profile", headers=headers, timeout=2)
                if res.status_code == 200:
                    data = res.json()
                    self.status_list.addItem(
                        f"Space: {srv['server_name']} | Role: {data.get('role')} | Uploads: {'Allowed' if data.get('can_write') else 'Revoked'}")
            except Exception:
                self.status_list.addItem(f"Space: {srv['server_name']} | Offline")

    def save_profile(self):
        new_uname = self.uname_input.text().strip()
        new_dob = self.dob_input.text().strip()
        if new_uname:
            update_client_profile(new_uname, new_dob)
            for srv in self.active_servers:
                try:
                    requests.post(f"{srv['url']}/api/user/profile", json={"username": new_uname, "dob": new_dob},
                                  headers=get_auth_headers(srv), timeout=2)
                except Exception:
                    pass
            QMessageBox.information(self, "Success", "Profile updated successfully.")
            self.accept()


class MetricCard(QFrame):
    def __init__(self, title, value="0", parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        self.val_label = QLabel(value)
        self.val_label.setObjectName("MetricValue")
        title_label = QLabel(title.upper())
        title_label.setObjectName("MetricLabel")
        layout.addWidget(self.val_label)
        layout.addWidget(title_label)
        self.setLayout(layout)

    def set_value(self, value):
        self.val_label.setText(str(value))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CombinedAppWindow()
    window.show()
    sys.exit(app.exec())