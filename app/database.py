def create_user(db_url, db_type, name, email, password_hash):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        p = ph(db_type)
        if db_type == "postgres":
            cur.execute(
                f"INSERT INTO users (name, email, password_hash) VALUES ({p},{p},{p}) RETURNING id",
                (name, email, password_hash))
            uid = cur.fetchone()[0]
        else:
            cur.execute(
                f"INSERT INTO users (name, email, password_hash) VALUES ({p},{p},{p})",
                (name, email, password_hash))
            uid = cur.lastrowid
        conn.commit()
        return uid
    finally:
        conn.close()

def get_user_by_email(db_url, db_type, email):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        p = ph(db_type)
        cur.execute(f"SELECT * FROM users WHERE email = {p}", (email,))
        row = cur.fetchone()
        return dict_row(cur, row, db_type)
    finally:
        conn.close()

def get_user_by_id(db_url, db_type, user_id):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        p = ph(db_type)
        cur.execute(f"SELECT * FROM users WHERE id = {p}", (user_id,))
        row = cur.fetchone()
        return dict_row(cur, row, db_type)
    finally:
        conn.close()

def get_sessions_by_user(db_url, db_type, user_id):
    conn, db_type = get_connection(db_url, db_type)
    try:
        cur = conn.cursor()
        p = ph(db_type)
        cur.execute(
            f"SELECT * FROM sessions WHERE user_id = {p} ORDER BY created_at DESC",
            (user_id,))
        rows = cur.fetchall()
        return dict_rows(cur, rows, db_type)
    finally:
        conn.close()
