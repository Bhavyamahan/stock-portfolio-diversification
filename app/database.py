import sqlite3

def get_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(db_path):
    with get_connection(db_path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')))""")
        conn.execute("""CREATE TABLE IF NOT EXISTS target_allocation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            sector TEXT NOT NULL,
            target_pct REAL NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            quantity REAL NOT NULL,
            sector TEXT NOT NULL,
            added_at TEXT NOT NULL DEFAULT (datetime('now')))""")
        conn.execute("""CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            sector TEXT NOT NULL,
            actual_pct REAL NOT NULL,
            target_pct REAL NOT NULL,
            gap_pct REAL NOT NULL,
            status TEXT NOT NULL,
            computed_at TEXT NOT NULL DEFAULT (datetime('now')))""")
        conn.commit()

def create_session(db_path, label=None):
    with get_connection(db_path) as conn:
        cur = conn.execute("INSERT INTO sessions (label) VALUES (?)", (label,))
        conn.commit()
        return cur.lastrowid

def get_session(db_path, session_id):
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None

def get_all_sessions(db_path):
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM sessions ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

def save_target_allocations(db_path, session_id, allocations):
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM target_allocation WHERE session_id = ?", (session_id,))
        conn.executemany(
            "INSERT INTO target_allocation (session_id, sector, target_pct) VALUES (?, ?, ?)",
            [(session_id, a["sector"], float(a["target_pct"])) for a in allocations])
        conn.commit()

def get_target_allocations(db_path, session_id):
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM target_allocation WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
        return [dict(r) for r in rows]

def add_stock(db_path, session_id, name, quantity, sector):
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO stocks (session_id, name, quantity, sector) VALUES (?, ?, ?, ?)",
            (session_id, name, quantity, sector))
        conn.commit()
        return cur.lastrowid

def get_stocks(db_path, session_id):
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM stocks WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
        return [dict(r) for r in rows]

def delete_stock(db_path, stock_id):
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM stocks WHERE id = ?", (stock_id,))
        conn.commit()

def save_analysis_results(db_path, session_id, results):
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM analysis_results WHERE session_id = ?", (session_id,))
        conn.executemany(
            "INSERT INTO analysis_results (session_id, sector, actual_pct, target_pct, gap_pct, status) VALUES (?, ?, ?, ?, ?, ?)",
            [(session_id, r["sector"], r["actual_pct"], r["target_pct"], r["gap_pct"], r["status"]) for r in results])
        conn.commit()

def get_analysis_results(db_path, session_id):
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM analysis_results WHERE session_id = ? ORDER BY gap_pct DESC", (session_id,)).fetchall()
        return [dict(r) for r in rows]
