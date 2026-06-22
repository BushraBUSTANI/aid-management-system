# Yapay Zeka Destekli İnsani Yardım Yönetim Sistemi

## Proje Hakkında

Bu proje, insani yardım kuruluşlarının başvuruları daha hızlı, düzenli ve sistematik şekilde değerlendirebilmesi amacıyla geliştirilmiştir. Sistem; başvuru yönetimi, yapay zeka destekli öncelik analizi ve yardım dağıtım süreçlerini tek bir platformda birleştirerek karar alma süreçlerini destekler.

Proje, farklı kullanıcı rollerine uygun arayüzler sunar:

- **Admin:** Tüm başvuruları yönetir, onaylar veya reddeder, dağıtım sürecini yürütür.
- **Denetçi:** Başvuruları inceler, yapay zeka analizlerini görüntüler ve yeniden değerlendirme talep eder.

## Temel Özellikler

- **Yararlanıcı Yönetimi:** Manuel giriş, Excel yükleme veya harici veritabanı bağlantısı ile veri ekleme.
- **Yapay Zeka Destekli Analiz:** Claude API ile her başvuru için otomatik öncelik ve ihtiyaç analizi.
- **Onay İş Akışı:** İncelemede → Onaylandı / Reddedildi → Dağıtım aşamalarından oluşan yapılandırılmış süreç.
- **Rol Bazlı Yetkilendirme:** Admin ve Denetçi için ayrı yetki seviyeleri ve arayüzler.
- **Gerçek Zamanlı Dashboard:** Canlı istatistikler ve görsel raporlar.
- **Yeniden Değerlendirme:** Reddedilen başvuruları tekrar inceleme imkânı.
- **Smart Fallback:** API erişimi olmadan da çalışabilen yedek analiz modu.

## Sistem Mimarisi

Sistem üç temel katmandan oluşur:

- **Arayüz Katmanı:** Streamlit tabanlı web arayüzü — Admin ve Denetçi panelleri.
- **İş Mantığı Katmanı:** Başvuru workflow'u, rol yönetimi ve Claude API entegrasyonu.
- **Veri Katmanı:** SQLite veritabanı ve harici veritabanı bağlantı desteği.

Temel akış: Başvuru Girişi → Yapay Zeka Analizi → İnceleme → Onay/Red → Dağıtım

## Kullanılan Teknolojiler

- **Arayüz:** Python 3.13 + Streamlit
- **Veritabanı:** SQLite
- **Yapay Zeka:** Anthropic Claude API
- **Veri İşleme:** Pandas
- **Görselleştirme:** Plotly
- **Excel Desteği:** openpyxl

## Proje Yapısı
aid_management_system/

├── app.py                 # Ana uygulama ve arayüz

├── database.py            # Veritabanı işlemleri

├── seed_data.py           # Örnek veri yükleme

├── create_external_db.py  # Harici DB entegrasyonu

├── requirements.txt       # Python bağımlılıkları

├── aid_system.db          # SQLite veritabanı

└── README.md

## Kurulum ve Çalıştırma

**1. Repoyu klonlayın:**
git clone https://github.com/BushraBUSTANI/aid-management-system.git

cd aid-management-system

**2. Sanal ortam oluşturun:**
python -m venv venv

venv\Scripts\activate

**3. Bağımlılıkları yükleyin:**
pip install -r requirements.txt

**4. API anahtarını ayarlayın:**
set ANTHROPIC_API_KEY=your_api_key_here

API anahtarı olmadan sistem **Smart Fallback** modunda çalışır.

**5. Uygulamayı başlatın:**
streamlit run app.py

Sistem giriş gerektirmez. Rol seçimi sidebar'dan yapılır (Admin / Denetçi).


## Geliştirici

**Bushra BUSTANI**

Danışman: **Prof. Dr. Ali BULDU**

Marmara Üniversitesi, Bilgisayar Mühendisliği — 2026
