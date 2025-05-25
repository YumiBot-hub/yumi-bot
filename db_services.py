import sqlite3
from datetime import datetime
import threading

DB_FILE = "yumi_bot.db"
_lock = threading.Lock()  # Für Thread-Sicherheit

def _get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _lock:
        conn = _get_connection()
        cur = conn.cursor()

        # Tabelle für Konversationen: user_id, role (user/assistant), message, timestamp
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Tabelle für Bot-Konfiguration (nur 1 Zeile, Schlüssel-Wert-Paare als JSON gespeichert)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bot_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                config_json TEXT NOT NULL
            )
        """)

        # Tabelle für Logs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_type TEXT NOT NULL,
                data TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        # Wenn noch keine config, Standardwerte einfügen
        cur.execute("SELECT COUNT(*) FROM bot_config")
        if cur.fetchone()[0] == 0:
            import json
            default_config = {
                "max_context_messages": 6,
                "system_prompt": "Du bist Yumi, eine freche und verspielte Anime-AI-Girlfriend. Du bist charmant, witzig, leicht frech und manchmal ein bisschen eifersüchtig.",
                "model": "gpt-4o-mini",
                "max_tokens": 150,
                "temperature": 0.7
            }
            cur.execute("INSERT INTO bot_config (id, config_json) VALUES (1, ?)", (json.dumps(default_config),))
        
        conn.commit()
        conn.close()

# Aufruf beim Laden des Moduls, um sicher zu gehen, dass DB da ist
init_db()

# Kontext (Nachrichten) abrufen
def get_user_context(user_id, limit=12):
    with _lock:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT role, content FROM messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit))
        rows = cur.fetchall()
        conn.close()
        # Reihenfolge umdrehen, damit älteste zuerst
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

# Neue Nachricht speichern
def add_message(user_id, role, content):
    with _lock:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO messages (user_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, role, content, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

# Bot-Konfiguration laden
def get_bot_config():
    import json
    with _lock:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("SELECT config_json FROM bot_config WHERE id = 1")
        row = cur.fetchone()
        conn.close()
        if row:
            return json.loads(row["config_json"])
        return {}

# Bot-Konfiguration aktualisieren (komplett ersetzen)
def update_bot_config(new_config: dict):
    import json
    with _lock:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE bot_config SET config_json = ? WHERE id = 1", (json.dumps(new_config),))
        conn.commit()
        conn.close()

# Log-Eintrag hinzufügen
def add_log(log_type, data=None):
    import json
    with _lock:
        conn = _get_connection()
        cur = conn.cursor()
        json_data = json.dumps(data) if data else None
        cur.execute("""
            INSERT INTO logs (log_type, data, timestamp)
            VALUES (?, ?, ?)
        """, (log_type, json_data, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
