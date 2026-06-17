import sqlite3
from database import init_db, add_beneficiary, update_priority_score, add_inventory_item, get_all_beneficiaries

def calculate_priority_score(income, family_size, health, zone):
    MAX_INCOME = 5000
    MAX_FAMILY = 12
    HEALTH_SCORES = {"critical": 1.0, "moderate": 0.5, "stable": 0.1}
    ZONE_SCORES = {"Zone-C": 1.0, "Zone-B": 0.6, "Zone-A": 0.3}
    
    income_score = max(0, 1 - (income / MAX_INCOME))
    family_score = min(1, family_size / MAX_FAMILY)
    health_score = HEALTH_SCORES.get(health, 0.5)
    zone_score = ZONE_SCORES.get(zone, 0.3)
    
    final = (
        income_score * 0.35 +
        health_score * 0.30 +
        family_score * 0.25 +
        zone_score * 0.10
    ) * 100
    return round(final, 1)

def seed_all_data():
    print("🚀 Başlatılıyor: Veri Tohumlama...")
    
    init_db()
    print("✅ Veritabanı hazır.")
    
    # Temizleme (opsiyonel - yorumdan çıkarabilirsiniz)
    # conn = sqlite3.connect("aid_system.db")
    # conn.execute("DELETE FROM beneficiaries")
    # conn.execute("DELETE FROM inventory")
    # conn.execute("DELETE FROM distributions")
    # conn.commit()
    # conn.close()
    
    beneficiaries = [
        ("Ahmed Al-Rashid",  45, 7, 800,  "critical", "Zone-A", "05012345678", "Bağcılar, İstanbul",   "Kalp hastası, 3 çocuk 10 yaş altı", "Gıda"),
        ("Fatima Youssef",   32, 4, 1200, "moderate", "Zone-B", "05023456789", "Kadıköy, İstanbul",    "Bekar anne, engelli çocuk",          "Genel"),
        ("Yusuf Al-Amin",    41, 3, 2000, "stable",   "Zone-A", "05034567890", "Şişli, İstanbul",      "",                                   "Genel"),
        ("Maryam Ibrahim",   52, 8, 600,  "critical", "Zone-C", "05045678901", "Gaziantep, Merkez",    "Büyük aile, çatışma bölgesi",        "Gıda"),
        ("Sara Khalil",      28, 6, 950,  "moderate", "Zone-A", "05056789012", "Sultangazi, İstanbul", "Hamile, eşi işsiz",                  "Tıbbi"),
        ("Omar Hassan",      60, 2, 500,  "critical", "Zone-C", "05067890123", "Hatay, Merkez",        "Yaşlı, kronik hastalık",             "Tıbbi"),
        ("Layla Mohammed",   35, 9, 700,  "moderate", "Zone-B", "05078901234", "Esenyurt, İstanbul",   "9 kişilik aile, çok düşük gelir",    "Gıda"),
        ("Khalid Nasser",    38, 5, 1500, "stable",   "Zone-B", "05089012345", "Üsküdar, İstanbul",    "",                                   "Giyim"),
    ]
    
    for b in beneficiaries:
        beneficiary_id = add_beneficiary(b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7], b[8], b[9])
        skor = calculate_priority_score(b[3], b[2], b[4], b[5])
        update_priority_score(beneficiary_id, skor)
        print(f"✅ {b[0]} eklendi — Skor: {skor} — Kategori: {b[9]}")
    
    inventory = [
        ("Gıda Paketi",  150, "kutu"),
        ("Tıbbi Kit",     45, "adet"),
        ("Battaniye",    200, "adet"),
        ("Su (20L)",     300, "bidon"),
        ("Bebek Maması",  60, "kutu"),
    ]
    
    for item in inventory:
        add_inventory_item(item[0], item[1], item[2])
        print(f"📦 {item[0]} eklendi — {item[1]} {item[2]}")
    
    print("\n🎉 Tüm veriler başarıyla eklendi!")
    
    # İstatistikleri göster
    df = get_all_beneficiaries()
    print(f"\n📊 Toplam yararlanıcı: {len(df)}")
    print(f"📊 Ortalama skor: {df['priority_score'].mean():.1f}")
    print(f"📊 Kritik vakalar: {len(df[df['health'] == 'critical'])}")

if __name__ == "__main__":
    seed_all_data()