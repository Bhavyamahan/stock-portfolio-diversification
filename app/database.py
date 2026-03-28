import os
import sqlite3

def get_connection(db_url, db_type="sqlite"):
    if db_type == "postgres":
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        return conn, "postgres"
    else:
        conn = sqlite3.connect(db_url)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn, "sqlite"

def dict_rows(cursor, rows, db_type):
    if db_type == "postgres":
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in rows]
    else:
        return [dict(r) for r in rows]

def dict_row(cursor, row, db_type):
    if row is None:
        return None
    if db_type == "postgres":
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, row))
    else:
        return dict(row)

def ph(db_type):
    return "%s" if db_type == "postgres" else "?"

def init_db(db_url, db_type="sqlite"):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            label TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )""" if db_type == "postgres" else """CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS target_allocation (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            sector TEXT NOT NULL,
            target_pct REAL NOT NULL
        )""" if db_type == "postgres" else """CREATE TABLE IF NOT EXISTS target_allocation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            sector TEXT NOT NULL,
            target_pct REAL NOT NULL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS stocks (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            quantity REAL NOT NULL,
            buy_price REAL NOT NULL DEFAULT 0,
            sector TEXT NOT NULL,
            added_at TIMESTAMP NOT NULL DEFAULT NOW()
        )""" if db_type == "postgres" else """CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            quantity REAL NOT NULL,
            buy_price REAL NOT NULL DEFAULT 0,
            sector TEXT NOT NULL,
            added_at TEXT NOT NULL DEFAULT (datetime('now')))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS analysis_results (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            sector TEXT NOT NULL,
            actual_pct REAL NOT NULL,
            target_pct REAL NOT NULL,
            gap_pct REAL NOT NULL,
            status TEXT NOT NULL,
            computed_at TIMESTAMP NOT NULL DEFAULT NOW()
        )""" if db_type == "postgres" else """CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            sector TEXT NOT NULL,
            actual_pct REAL NOT NULL,
            target_pct REAL NOT NULL,
            gap_pct REAL NOT NULL,
            status TEXT NOT NULL,
            computed_at TEXT NOT NULL DEFAULT (datetime('now')))""")
        conn.commit()
        print(f"[DB] Tables ready ({db_type})")
    finally:
        conn.close()

def create_session(db_url, db_type, label=None):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        p = ph(db_type)
        if db_type == "postgres":
            cur.execute(f"INSERT INTO sessions (label) VALUES ({p}) RETURNING id", (label,))
            sid = cur.fetchone()[0]
        else:
            cur.execute(f"INSERT INTO sessions (label) VALUES ({p})", (label,))
            sid = cur.lastrowid
        conn.commit()
        return sid
    finally:
        conn.close()

def get_session(db_url, db_type, session_id):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        p = ph(db_type)
        cur.execute(f"SELECT * FROM sessions WHERE id = {p}", (session_id,))
        row = cur.fetchone()
        return dict_row(cur, row, db_type)
    finally:
        conn.close()

def get_all_sessions(db_url, db_type):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sessions ORDER BY created_at DESC")
        rows = cur.fetchall()
        return dict_rows(cur, rows, db_type)
    finally:
        conn.close()

def save_target_allocations(db_url, db_type, session_id, allocations):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        p = ph(db_type)
        cur.execute(f"DELETE FROM target_allocation WHERE session_id = {p}", (session_id,))
        for a in allocations:
            cur.execute(
                f"INSERT INTO target_allocation (session_id, sector, target_pct) VALUES ({p},{p},{p})",
                (session_id, a["sector"], float(a["target_pct"])))
        conn.commit()
    finally:
        conn.close()

def get_target_allocations(db_url, db_type, session_id):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        p = ph(db_type)
        cur.execute(f"SELECT * FROM target_allocation WHERE session_id = {p} ORDER BY id", (session_id,))
        rows = cur.fetchall()
        return dict_rows(cur, rows, db_type)
    finally:
        conn.close()

def add_stock(db_url, db_type, session_id, name, quantity, buy_price, sector):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        p = ph(db_type)
        if db_type == "postgres":
            cur.execute(
                f"INSERT INTO stocks (session_id, name, quantity, buy_price, sector) VALUES ({p},{p},{p},{p},{p}) RETURNING id",
                (session_id, name, quantity, buy_price, sector))
            sid = cur.fetchone()[0]
        else:
            cur.execute(
                f"INSERT INTO stocks (session_id, name, quantity, buy_price, sector) VALUES ({p},{p},{p},{p},{p})",
                (session_id, name, quantity, buy_price, sector))
            sid = cur.lastrowid
        conn.commit()
        return sid
    finally:
        conn.close()

def get_stocks(db_url, db_type, session_id):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        p = ph(db_type)
        cur.execute(f"SELECT * FROM stocks WHERE session_id = {p} ORDER BY id", (session_id,))
        rows = cur.fetchall()
        return dict_rows(cur, rows, db_type)
    finally:
        conn.close()

def delete_stock(db_url, db_type, stock_id):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        p = ph(db_type)
        cur.execute(f"DELETE FROM stocks WHERE id = {p}", (stock_id,))
        conn.commit()
    finally:
        conn.close()

def save_analysis_results(db_url, db_type, session_id, results):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        p = ph(db_type)
        cur.execute(f"DELETE FROM analysis_results WHERE session_id = {p}", (session_id,))
        for r in results:
            cur.execute(
                f"""INSERT INTO analysis_results
                    (session_id, sector, actual_pct, target_pct, gap_pct, status)
                    VALUES ({p},{p},{p},{p},{p},{p})""",
                (session_id, r["sector"], r["actual_pct"],
                 r["target_pct"], r["gap_pct"], r["status"]))
        conn.commit()
    finally:
        conn.close()

def get_analysis_results(db_url, db_type, session_id):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        p = ph(db_type)
        cur.execute(
            f"SELECT * FROM analysis_results WHERE session_id = {p} ORDER BY gap_pct DESC",
            (session_id,))
        rows = cur.fetchall()
        return dict_rows(cur, rows, db_type)
    finally:
        conn.close()
