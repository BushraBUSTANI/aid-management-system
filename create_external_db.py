import sqlite3

def create_external_db():
    conn = sqlite3.connect("external_db.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS external_beneficiaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            family_size INTEGER,
            income REAL,
            health TEXT,
            zone TEXT,
            notes TEXT
        )
    """)

    # Önce tabloyu temizle (tekrarları önlemek için)
    cursor.execute("DELETE FROM external_beneficiaries")
    
    external_data = [
        ("Layla Mohammed",  35, 9, 700,  "moderate", "Zone-B", "9 kişilik aile, çok düşük gelir"),
        ("Khalid Nasser",   38, 5, 1500, "stable",   "Zone-B", ""),
        ("Maryam Ibrahim",  52, 8, 600,  "critical", "Zone-C", "Büyük aile, çatışma bölgesi"),
        ("Hassan Al-Omar",  44, 6, 850,  "critical", "Zone-C", "Kronik hastalık, işsiz"),
        ("Nour Al-Din",     29, 3, 1800, "stable",   "Zone-A", ""),
        ("Zainab Ali",      40, 5, 1100, "moderate", "Zone-B", "Dul, 5 çocuk"),
        ("Ibrahim Saleh",   33, 4, 650,  "critical", "Zone-C", "Engelli, işsiz"),
    ]

    cursor.executemany(
        "INSERT INTO external_beneficiaries (name, age, family_size, income, health, zone, notes) VALUES (?,?,?,?,?,?,?)",
        external_data
    )

    conn.commit()
    conn.close()
    print("✅ External DB oluşturuldu!")
    print(f"📊 {len(external_data)} kayıt eklendi.")

if __name__ == "__main__":
    create_external_db()