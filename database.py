import sqlite3
import pandas as pd

DB_PATH = "aid_system.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS beneficiaries (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT NOT NULL,
            age              INTEGER,
            family_size      INTEGER,
            income           REAL,
            health           TEXT,
            zone             TEXT,
            phone            TEXT DEFAULT '',
            address          TEXT DEFAULT '',
            notes            TEXT DEFAULT '',
            aid_type         TEXT DEFAULT 'Genel',
            status           TEXT DEFAULT 'İncelemede',
            reviewer_notes   TEXT DEFAULT '',
            priority_score   REAL DEFAULT 0,
            created_at       TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS inventory (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name   TEXT NOT NULL,
            quantity    INTEGER DEFAULT 0,
            unit        TEXT DEFAULT '',
            updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS distributions (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            beneficiary_id   INTEGER,
            item_name        TEXT,
            quantity         INTEGER,
            date             TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()

def get_all_beneficiaries():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM beneficiaries ORDER BY priority_score DESC", conn)
    conn.close()
    return df

def get_beneficiaries_by_status(status):
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM beneficiaries WHERE status=? ORDER BY priority_score DESC", conn, params=(status,))
    conn.close()
    return df

def get_beneficiary_by_id(beneficiary_id):
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM beneficiaries WHERE id=?", conn, params=(beneficiary_id,))
    conn.close()
    return df.iloc[0] if not df.empty else None

def add_beneficiary(name, age, family_size, income, health, zone, phone="", address="", notes="", aid_type="Genel"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO beneficiaries (name, age, family_size, income, health, zone, phone, address, notes, aid_type, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'İncelemede')
    """, (name, age, family_size, income, health, zone, phone, address, notes, aid_type))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def update_priority_score(beneficiary_id, score):
    conn = get_connection()
    conn.execute("UPDATE beneficiaries SET priority_score=? WHERE id=?", (score, beneficiary_id))
    conn.commit()
    conn.close()

def update_beneficiary_status(beneficiary_id, status, reviewer_notes=""):
    conn = get_connection()
    conn.execute("UPDATE beneficiaries SET status=?, reviewer_notes=? WHERE id=?", (status, reviewer_notes, beneficiary_id))
    conn.commit()
    conn.close()

def update_beneficiary_aid_type(beneficiary_id, aid_type):
    conn = get_connection()
    conn.execute("UPDATE beneficiaries SET aid_type=? WHERE id=?", (aid_type, beneficiary_id))
    conn.commit()
    conn.close()

def delete_beneficiary(beneficiary_id):
    conn = get_connection()
    conn.execute("DELETE FROM beneficiaries WHERE id=?", (beneficiary_id,))
    conn.commit()
    conn.close()

def get_inventory():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM inventory ORDER BY item_name", conn)
    conn.close()
    return df

def add_inventory_item(item_name, quantity, unit):
    conn = get_connection()
    conn.execute("INSERT INTO inventory (item_name, quantity, unit) VALUES (?,?,?)", (item_name, quantity, unit))
    conn.commit()
    conn.close()

def update_inventory_quantity(item_id, new_quantity):
    conn = get_connection()
    conn.execute("UPDATE inventory SET quantity=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_quantity, item_id))
    conn.commit()
    conn.close()

def delete_inventory_item(item_id):
    conn = get_connection()
    conn.execute("DELETE FROM inventory WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def add_distribution(beneficiary_id, item_name, quantity):
    conn = get_connection()
    conn.execute("INSERT INTO distributions (beneficiary_id, item_name, quantity) VALUES (?,?,?)", (beneficiary_id, item_name, quantity))
    conn.commit()
    conn.close()

def get_all_distributions():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT d.date, b.name as yararlanici, d.item_name, d.quantity
        FROM distributions d
        JOIN beneficiaries b ON d.beneficiary_id = b.id
        ORDER BY d.date DESC
    """, conn)
    conn.close()
    return df

def get_statistics():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM beneficiaries")
    total_ben = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM beneficiaries WHERE health='critical'")
    critical = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM inventory")
    total_inv = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(priority_score) FROM beneficiaries WHERE priority_score > 0")
    avg_score = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM beneficiaries WHERE status='İncelemede'")
    pending = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM beneficiaries WHERE status='Onaylandı'")
    approved = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM beneficiaries WHERE status='Reddedildi'")
    rejected = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_ben': total_ben,
        'critical': critical,
        'total_inv': total_inv,
        'avg_score': round(avg_score, 1),
        'pending': pending,
        'approved': approved,
        'rejected': rejected
    }