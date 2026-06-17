import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os
from database import (
    init_db, get_all_beneficiaries, add_beneficiary,
    update_priority_score, delete_beneficiary,
    get_beneficiaries_by_status, update_beneficiary_status,
    update_beneficiary_aid_type, get_inventory, add_inventory_item, 
    update_inventory_quantity, delete_inventory_item,
    add_distribution, get_all_distributions, get_connection, get_statistics
)

# Page configuration
st.set_page_config(
    page_title="İnsani Yardım Yönetim Sistemi",
    page_icon="🤝",
    layout="wide"
)

# Initialize database
init_db()
st.markdown("<style>div.block-container{padding-top:1rem;}</style>", unsafe_allow_html=True)

# Session state initialization
if 'msg' not in st.session_state:
    st.session_state.msg = ""
if 'msg_type' not in st.session_state:
    st.session_state.msg_type = "success"

def show_message():
    if st.session_state.msg:
        if st.session_state.msg_type == "success":
            st.success(st.session_state.msg)
        elif st.session_state.msg_type == "error":
            st.error(st.session_state.msg)
        elif st.session_state.msg_type == "warning":
            st.warning(st.session_state.msg)
        st.session_state.msg = ""

# Constants for scoring
MAX_INCOME = 5000
MAX_FAMILY = 12
HEALTH_SCORES = {"critical": 1.0, "moderate": 0.5, "stable": 0.1}
ZONE_SCORES = {"Zone-C": 1.0, "Zone-B": 0.6, "Zone-A": 0.3}

def calculate_priority_score(income, family_size, health, zone):
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

def smart_fallback(row):
    score = row.get('priority_score', 0)
    health = row.get('health', 'stable')
    family = row.get('family_size', 1)
    income = row.get('income', 1000)
    notes = row.get('notes', '')
    
    if score >= 70:
        seviye = "🔴 Yüksek öncelikli — acil müdahale gerektirir"
        oneri = "48 saat içinde tam yardım paketi tahsis edilmelidir"
    elif score >= 45:
        seviye = "🟡 Orta öncelikli — haftalık takip önerilir"
        oneri = "Haftalık dağıtım listesine eklenmelidir"
    else:
        seviye = "🟢 Düşük öncelikli — aylık takip yeterlidir"
        oneri = "Aylık değerlendirme döngüsüne dahil edilmelidir"
    
    riskler = []
    if health == "critical":
        riskler.append("⚠️ Kritik sağlık durumu acil tıbbi destek gerektiriyor")
    if family >= 7:
        riskler.append(f"👨‍👩‍👧‍👦 Büyük aile yapısı ({family} kişi) yüksek ihtiyaç oluşturuyor")
    if income < 800:
        riskler.append("💰 Gelir seviyesi geçim sınırının altında")
    if notes:
        riskler.append(f"📝 Ek not: {notes[:60]}")
    
    if not riskler:
        riskler.append("✓ Belirgin risk faktörü tespit edilmedi")
    
    return f"""**🤖 Karar Destek Sistemi Analizi**

**Öncelik Seviyesi:** {seviye}

**Risk Faktörleri:** {' | '.join(riskler)}

**💡 Öneri:** {oneri}

---
*Skor: {score}/100 — Gelir (%35) + Sağlık (%30) + Aile (%25) + Bölge (%10)*"""

def get_ai_analysis(row):
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key and api_key.startswith("sk-ant") and len(api_key) > 20:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            prompt = f"""Sen bir insani yardım analisti olarak görev yapıyorsun.
Aşağıdaki yararlanıcı profilini analiz et ve kısa bir değerlendirme yap:

Ad: {row['name']}
Yaş: {row['age']}
Aile Büyüklüğü: {row['family_size']}
Aylık Gelir: {row['income']} TL
Sağlık Durumu: {row['health']}
Bölge: {row['zone']}
Notlar: {row.get('notes', '-')}
Öncelik Skoru: {row['priority_score']}/100

Lütfen Türkçe olarak 3-4 cümle ile yanıtla."""
            
            message = client.messages.create(
                model="claude-3-sonnet-20241022",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception:
            return smart_fallback(row)
    else:
        return smart_fallback(row)

def refresh_scores():
    df = get_all_beneficiaries()
    for _, row in df.iterrows():
        skor = calculate_priority_score(row['income'], row['family_size'], row['health'], row['zone'])
        update_priority_score(row['id'], skor)
    return get_all_beneficiaries()

# Sidebar
st.sidebar.title("🤝 Yardım Yönetim Sistemi")
st.sidebar.caption("Yapay Zeka Destekli | v2.0")
st.sidebar.divider()

rol = st.sidebar.selectbox("👤 Rol Seçin", ["🔑 Admin", "🔍 Denetçi"])
st.sidebar.divider()

if rol == "🔑 Admin":
    sayfa = st.sidebar.radio("📋 Menü", [
        "🏠 Ana Panel",
        "👥 Yararlanıcı Yönetimi",
        "🤖 Öncelik Analizi",
        "📦 Envanter Yönetimi",
        "📋 Dağıtım Kayıtları"
    ])
else:
    sayfa = "🔍 Denetçi Paneli"
    st.sidebar.info("🔍 Denetçi olarak giriş yaptınız.\nSadece denetim paneline erişebilirsiniz.")

# ==================== ANA PANEL ====================
if sayfa == "🏠 Ana Panel":
    st.title("🤝 Yapay Zeka Destekli İnsani Yardım Yönetim Sistemi")
    st.caption("AI-Driven Humanitarian Aid Management System")
    show_message()
    st.divider()
    
    # Refresh scores for beneficiaries with zero score
    df = get_all_beneficiaries()
    for _, row in df[df['priority_score'] == 0].iterrows():
        skor = calculate_priority_score(row['income'], row['family_size'], row['health'], row['zone'])
        update_priority_score(row['id'], skor)
    
    df = get_all_beneficiaries()
    inv = get_inventory()
    stats = get_statistics()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Toplam Yararlanıcı", len(df))
    col2.metric("🚨 Kritik Vakalar", len(df[df['health'] == 'critical']))
    col3.metric("📦 Envanter Kalemleri", len(inv))
    col4.metric("📊 Ortalama Skor", f"{df['priority_score'].mean():.1f}" if len(df) > 0 else "0")
    
    st.divider()
    
    # Status cards
    inceleme_count = len(df[df['status'] == 'İncelemede'])
    onay_count = len(df[df['status'] == 'Onaylandı'])
    red_count = len(df[df['status'] == 'Reddedildi'])
    dag_count = len(get_all_distributions())
    
    col5, col6, col7, col8 = st.columns(4)
    col5.markdown(f"""
    <div style='background-color:#EBF5FB;padding:16px;border-radius:10px;text-align:center;border-left:5px solid #2E86C1;border:1px solid #AED6F1'>
        <h4 style='color:#2E86C1;margin:0'>🔄 İncelemede</h4>
        <h2 style='color:#1A252F;margin:0'>{inceleme_count}</h2>
    </div>
    """, unsafe_allow_html=True)
    col6.markdown(f"""
    <div style='background-color:#EAFAF1;padding:16px;border-radius:10px;text-align:center;border-left:5px solid #1E8449;border:1px solid #A9DFBF'>
        <h4 style='color:#1E8449;margin:0'>✅ Onaylandı</h4>
        <h2 style='color:#1A252F;margin:0'>{onay_count}</h2>
    </div>
    """, unsafe_allow_html=True)
    col7.markdown(f"""
    <div style='background-color:#FDEDEC;padding:16px;border-radius:10px;text-align:center;border-left:5px solid #C0392B;border:1px solid #F1948A'>
        <h4 style='color:#C0392B;margin:0'>❌ Reddedildi</h4>
        <h2 style='color:#1A252F;margin:0'>{red_count}</h2>
    </div>
    """, unsafe_allow_html=True)
    col8.markdown(f"""
    <div style='background-color:#FEF9E7;padding:16px;border-radius:10px;text-align:center;border-left:5px solid #D4AC0D;border:1px solid #F9E79F'>
        <h4 style='color:#D4AC0D;margin:0'>📦 Dağıtıldı</h4>
        <h2 style='color:#1A252F;margin:0'>{dag_count}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    if len(df) > 0:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("🏥 Sağlık Durumu Dağılımı")
            saglik = df['health'].value_counts()
            fig = px.pie(
                values=saglik.values, 
                names=saglik.index,
                color=saglik.index,
                color_discrete_map={"critical": "#E74C3C", "moderate": "#F39C12", "stable": "#27AE60"},
                title="Sağlık Durumuna Göre Dağılım"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col_chart2:
            st.subheader("⭐ En Yüksek Öncelikli Yararlanıcılar")
            top = df.nlargest(8, 'priority_score')[['name', 'priority_score', 'health']]
            fig2 = px.bar(
                top, 
                x='priority_score', 
                y='name', 
                orientation='h', 
                color='health',
                color_discrete_map={"critical": "#E74C3C", "moderate": "#F39C12", "stable": "#27AE60"},
                title="Öncelik Skoruna Göre İlk 8",
                text='priority_score'
            )
            fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("📭 Henüz yararlanıcı kaydı bulunmamaktadır.")

# ==================== YARARLANICI YÖNETİMİ ====================
elif sayfa == "👥 Yararlanıcı Yönetimi":
    st.title("👥 Yararlanıcı Yönetimi")
    show_message()
    
    tab1, tab2, tab3 = st.tabs(["📋 Yararlanıcı Listesi", "➕ Manuel Ekle", "📥 Veri İçe Aktar"])
    
    with tab1:
        df = get_all_beneficiaries()
        if df.empty:
            st.info("📭 Henüz kayıtlı yararlanıcı bulunmamaktadır.")
        else:
            # Filters
            col_f1, col_f2, col_f3 = st.columns(3)
            saglik_filtre = col_f1.selectbox("🏥 Sağlık Durumu", ["Tümü", "critical", "moderate", "stable"])
            bolge_filtre = col_f2.selectbox("📍 Bölge", ["Tümü"] + sorted(df['zone'].unique().tolist()))
            durum_filtre = col_f3.selectbox("📌 Durum", ["Tümü", "İncelemede", "Onaylandı", "Reddedildi"])
            
            filtered = df.copy()
            if saglik_filtre != "Tümü":
                filtered = filtered[filtered['health'] == saglik_filtre]
            if bolge_filtre != "Tümü":
                filtered = filtered[filtered['zone'] == bolge_filtre]
            if durum_filtre != "Tümü":
                filtered = filtered[filtered['status'] == durum_filtre]
            
            # Display dataframe
            st.dataframe(
                filtered[['name', 'age', 'family_size', 'income', 'health', 'zone', 
                         'phone', 'status', 'aid_type', 'priority_score']].rename(columns={
                    'name': 'Ad', 'age': 'Yaş', 'family_size': 'Aile',
                    'income': 'Gelir', 'health': 'Sağlık', 'zone': 'Bölge',
                    'phone': 'Telefon', 'status': 'Durum',
                    'aid_type': 'Beyan Edilen İhtiyaç', 'priority_score': 'Skor'
                }),
                use_container_width=True, 
                hide_index=True
            )
            
            # Delete section
            st.divider()
            st.subheader("🗑️ Yararlanıcı Sil")
            if not filtered.empty:
                silinecek = st.selectbox("Silmek istediğiniz yararlanıcıyı seçin:", filtered['name'].tolist())
                if st.button("🗑️ Sil", type="primary"):
                    sil_id = int(filtered[filtered['name'] == silinecek]['id'].values[0])
                    delete_beneficiary(sil_id)
                    st.session_state.msg = f"✅ {silinecek} başarıyla silindi!"
                    st.session_state.msg_type = "success"
                    st.rerun()
    
    with tab2:
        st.subheader("➕ Yeni Yararlanıcı Kaydı")
        with st.form("yararlanici_form"):
            col1, col2 = st.columns(2)
            ad = col1.text_input("👤 Ad Soyad *")
            yas = col2.number_input("📅 Yaş", 1, 120, 30)
            aile = col1.number_input("👨‍👩‍👧‍👦 Aile Büyüklüğü", 1, 20, 4)
            gelir = col2.number_input("💰 Aylık Gelir (TL)", 0, 10000, 1000)
            saglik = col1.selectbox("🏥 Sağlık Durumu", ["stable", "moderate", "critical"])
            bolge = col2.selectbox("📍 Bölge", ["Zone-A", "Zone-B", "Zone-C"])
            telefon = col1.text_input("📞 Telefon")
            adres = col2.text_input("🏠 Adres")
            yardim = col1.selectbox("📦 Beyan Edilen İhtiyaç", ["Genel", "Gıda", "Tıbbi", "Giyim"])
            notlar = st.text_area("📝 Notlar")
            
            if st.form_submit_button("💾 Kaydet", use_container_width=True):
                if ad:
                    beneficiary_id = add_beneficiary(ad, yas, aile, gelir, saglik, bolge,
                                                    telefon, adres, notlar, yardim)
                    skor = calculate_priority_score(gelir, aile, saglik, bolge)
                    update_priority_score(beneficiary_id, skor)
                    st.session_state.msg = f"✅ {ad} başarıyla kaydedildi! Skor: {skor}/100"
                    st.session_state.msg_type = "success"
                    st.rerun()
                else:
                    st.error("❌ Ad Soyad alanı zorunludur.")
    
    with tab3:
        st.subheader("📥 Veri İçe Aktarma Seçenekleri")
        import_tab1, import_tab2 = st.tabs(["📊 Excel/CSV", "🔄 Harici Veritabanı"])
        
        with import_tab1:
            st.info("Excel/CSV dosyanızda şu sütunlar bulunmalıdır: name, age, family_size, income, health, zone, phone, address, notes, aid_type")
            
            # Template download
            ornek_data = pd.DataFrame([{
                "name": "Örnek Kişi", "age": 35, "family_size": 4,
                "income": 1000, "health": "moderate", "zone": "Zone-A",
                "phone": "05xx", "address": "İstanbul", "notes": "", "aid_type": "Genel"
            }])
            st.download_button(
                "📥 Örnek Şablonu İndir",
                ornek_data.to_csv(index=False).encode('utf-8'),
                "template.csv", 
                "text/csv", 
                use_container_width=True
            )
            
            st.divider()
            yuklenen = st.file_uploader("Excel veya CSV dosyası yükleyin", type=["xlsx", "csv"])
            if yuklenen:
                try:
                    if yuklenen.name.endswith('.csv'):
                        excel_df = pd.read_csv(yuklenen)
                    else:
                        excel_df = pd.read_excel(yuklenen)
                    
                    st.dataframe(excel_df, use_container_width=True, hide_index=True)
                    
                    if st.button("✅ Verileri İçe Aktar", type="primary", use_container_width=True):
                        mevcut_isimler = get_all_beneficiaries()['name'].tolist()
                        eklenen = atlan = 0
                        
                        for _, row in excel_df.iterrows():
                            if str(row.get('name', '')) not in mevcut_isimler:
                                bid = add_beneficiary(
                                    str(row.get('name', '')), int(row.get('age', 0)),
                                    int(row.get('family_size', 1)), float(row.get('income', 0)),
                                    str(row.get('health', 'stable')), str(row.get('zone', 'Zone-A')),
                                    str(row.get('phone', '')), str(row.get('address', '')),
                                    str(row.get('notes', '')), str(row.get('aid_type', 'Genel'))
                                )
                                skor = calculate_priority_score(
                                    float(row.get('income', 0)), int(row.get('family_size', 1)),
                                    str(row.get('health', 'stable')), str(row.get('zone', 'Zone-A'))
                                )
                                update_priority_score(bid, skor)
                                eklenen += 1
                            else:
                                atlan += 1
                        
                        st.session_state.msg = f"✅ {eklenen} yeni kayıt eklendi, {atlan} kayıt zaten mevcut."
                        st.session_state.msg_type = "success"
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Dosya okunamadı: {e}")
        
        with import_tab2:
            st.info("UNHCR veya WFP gibi harici organizasyonların veritabanından veri aktarımı simülasyonu.")
            try:
                ext_conn = sqlite3.connect("external_db.db")
                ext_df = pd.read_sql("SELECT * FROM external_beneficiaries", ext_conn)
                ext_conn.close()
                
                st.dataframe(
                    ext_df[['name', 'age', 'family_size', 'income', 'health', 'zone']].rename(columns={
                        'name': 'Ad', 'age': 'Yaş', 'family_size': 'Aile',
                        'income': 'Gelir', 'health': 'Sağlık', 'zone': 'Bölge'
                    }),
                    use_container_width=True, 
                    hide_index=True
                )
                
                if st.button("🔄 Verileri Senkronize Et", type="primary", use_container_width=True):
                    mevcut_isimler = get_all_beneficiaries()['name'].tolist()
                    eklenen = atlan = 0
                    
                    for _, row in ext_df.iterrows():
                        if row['name'] not in mevcut_isimler:
                            bid = add_beneficiary(
                                row['name'], row['age'], row['family_size'],
                                row['income'], row['health'], row['zone'],
                                "", "", row.get('notes', ''), "Genel"
                            )
                            skor = calculate_priority_score(
                                row['income'], row['family_size'], row['health'], row['zone']
                            )
                            update_priority_score(bid, skor)
                            eklenen += 1
                        else:
                            atlan += 1
                    
                    st.session_state.msg = f"✅ {eklenen} yeni kayıt eklendi, {atlan} zaten mevcut."
                    st.session_state.msg_type = "success"
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Harici veritabanına bağlanılamadı: {e}")
                st.info("Önce 'create_external_db.py' çalıştırın.")

# ==================== ÖNCELİK ANALİZİ ====================
elif sayfa == "🤖 Öncelik Analizi":
    st.title("🤖 Öncelik Analizi")
    st.caption("Ağırlıklı Puanlama Modeli + Yapay Zeka Analizi")
    show_message()
    
    df = get_all_beneficiaries()
    
    if df.empty:
        st.info("📭 Henüz kayıtlı yararlanıcı bulunmamaktadır.")
    else:
        if st.button("🔄 Tüm Skorları Yeniden Hesapla", use_container_width=True):
            df = refresh_scores()
            st.session_state.msg = "✅ Tüm skorlar başarıyla güncellendi!"
            st.session_state.msg_type = "success"
            st.rerun()
        
        st.divider()
        df = get_all_beneficiaries()
        
        for idx, (_, row) in enumerate(df.iterrows(), 1):
            skor = row['priority_score']
            durum_icon = "🔄" if row['status'] == 'İncelemede' else "✅" if row['status'] == 'Onaylandı' else "❌"
            
            with st.expander(f"#{idx} — {row['name']} | Skor: {skor}/100 | {durum_icon} {row['status']}"):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("💰 Gelir", f"{row['income']} TL")
                col2.metric("👨‍👩‍👧‍👦 Aile", f"{row['family_size']} kişi")
                col3.metric("🏥 Sağlık", row['health'].title())
                col4.metric("📍 Bölge", row['zone'])
                
                st.progress(int(skor), text=f"Öncelik Skoru: {skor}/100")
                
                st.info(f"🎯 Talep Edilen İhtiyaç: {row.get('aid_type', 'Genel')}")
                
                if st.button("🤖 AI Analizi Yap", key=f"ai_{row['id']}"):
                    with st.spinner("🧠 Analiz yapılıyor..."):
                        analiz = get_ai_analysis(row.to_dict())
                        st.markdown(analiz)

# ==================== ENVANTER YÖNETİMİ ====================
elif sayfa == "📦 Envanter Yönetimi":
    st.title("📦 Envanter Yönetimi")
    show_message()
    
    inv = get_inventory()
    tab1, tab2 = st.tabs(["📋 Mevcut Stok", "➕ Yeni Ürün Ekle"])
    
    with tab1:
        if inv.empty:
            st.info("📭 Henüz envanter kaydı bulunmamaktadır.")
        else:
            for _, item in inv.iterrows():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                col1.write(f"**{item['item_name']}** ({item['unit']})")
                
                yeni_miktar = col2.number_input(
                    "Miktar", 0, 9999, int(item['quantity']),
                    key=f"inv_{item['id']}", 
                    label_visibility="collapsed"
                )
                
                if col3.button("Güncelle", key=f"upd_{item['id']}"):
                    update_inventory_quantity(int(item['id']), yeni_miktar)
                    st.session_state.msg = f"✅ {item['item_name']} miktarı güncellendi!"
                    st.session_state.msg_type = "success"
                    st.rerun()
                
                if col4.button("🗑️ Sil", key=f"del_inv_{item['id']}"):
                    delete_inventory_item(int(item['id']))
                    st.session_state.msg = f"🗑️ {item['item_name']} envanterden silindi!"
                    st.session_state.msg_type = "success"
                    st.rerun()
    
    with tab2:
        with st.form("envanter_form"):
            col1, col2, col3 = st.columns(3)
            urun_adi = col1.text_input("📦 Ürün Adı *")
            miktar = col2.number_input("🔢 Miktar", 0, 9999, 100)
            birim = col3.text_input("📏 Birim", "adet")
            
            if st.form_submit_button("➕ Ekle", use_container_width=True):
                if urun_adi:
                    add_inventory_item(urun_adi, miktar, birim)
                    st.session_state.msg = f"✅ {urun_adi} envantere eklendi!"
                    st.session_state.msg_type = "success"
                    st.rerun()
                else:
                    st.error("❌ Ürün adı zorunludur.")

# ==================== DAĞITIM KAYITLARI ====================
elif sayfa == "📋 Dağıtım Kayıtları":
    st.title("📋 Dağıtım Kayıtları")
    show_message()
    st.subheader("📤 Yeni Dağıtım Kaydı Oluştur")
    df_ben = get_beneficiaries_by_status("Onaylandı")
    inv    = get_inventory()

    if not df_ben.empty and not inv.empty:
        secilen_ad = st.selectbox("👤 Yararlanıcı (Sadece Onaylananlar)", df_ben['name'].tolist(), key="dag_ben")
        st.session_state['dag_ben_selected'] = secilen_ad
        secilen_ben = df_ben[df_ben['name'] == secilen_ad].iloc[0]
        ben_aid_type = secilen_ben.get('aid_type', 'Genel')

        urun_options = [f"{row['item_name']} (Stok: {row['quantity']} {row['unit']})" for _, row in inv.iterrows()]
        default_idx = 0
        for i, opt in enumerate(urun_options):
            if ben_aid_type.lower() in opt.lower():
                default_idx = i
                break

        col2, col3 = st.columns(2)
        secilen_urun_full = col2.selectbox("📦 Ürün", urun_options, index=default_idx, key=f"dag_urun_{secilen_ad}")
        secilen_urun = secilen_urun_full.split(" (Stok:")[0]
        miktar_dag = col3.number_input("🔢 Miktar", 1, 999, 1)

        if st.button("✅ Dağıtımı Kaydet", use_container_width=True):
            ben_id   = int(df_ben[df_ben['name'] == secilen_ad]['id'].values[0])
            urun_row = inv[inv['item_name'] == secilen_urun].iloc[0]
            mevcut   = int(urun_row['quantity'])
            if miktar_dag > mevcut:
                st.error(f"❌ Yetersiz stok! Mevcut: {mevcut}")
            else:
                add_distribution(ben_id, secilen_urun, miktar_dag)
                update_inventory_quantity(int(urun_row['id']), mevcut - miktar_dag)
                st.session_state.msg = f"✅ {secilen_ad} adlı kişiye {miktar_dag} {secilen_urun} başarıyla dağıtıldı!"
                st.session_state.msg_type = "success"
                st.rerun()
    elif df_ben.empty:
        st.warning("⚠️ Dağıtım yapabilmek için önce Denetçi onayı gereklidir.")
    else:
        st.warning("⚠️ Envanter boş. Önce ürün ekleyin.")

    st.divider()
    st.subheader("📋 Geçmiş Dağıtım Kayıtları")
    dist = get_all_distributions()
    if dist.empty:
        st.info("Henüz dağıtım kaydı bulunmamaktadır.")
    else:
        st.dataframe(
            dist.rename(columns={
                'date': 'Tarih', 'yararlanici': 'Yararlanıcı',
                'item_name': 'Ürün', 'quantity': 'Miktar'
            }),
            use_container_width=True, hide_index=True
        )

# ==================== DENETÇİ PANELİ ====================
elif sayfa == "🔍 Denetçi Paneli":
    st.title("🔍 Denetçi Paneli")
    st.caption("Değerlendirme ve Onay Paneli")
    show_message()
    
    tab1, tab2 = st.tabs(["🔄 İnceleme Bekleyenler", "✅ Tamamlanan Denetimler"])
    
    with tab1:
        df_inc = get_beneficiaries_by_status("İncelemede")
        
        if df_inc.empty:
            st.success("✅ İnceleme bekleyen yararlanıcı bulunmamaktadır.")
        else:
            st.info(f"📋 {len(df_inc)} yararlanıcı denetim bekliyor.")
            
            for _, row in df_inc.iterrows():
                with st.expander(f"👤 {row['name']} | Skor: {row['priority_score']}/100 | 🏥 {row['health']}"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("📅 Yaş", row['age'])
                    col2.metric("👨‍👩‍👧‍👦 Aile Büyüklüğü", f"{row['family_size']} kişi")
                    col3.metric("💰 Gelir", f"{row['income']} TL")
                    
                    col4, col5 = st.columns(2)
                    col4.metric("🏥 Sağlık", row['health'].title())
                    col5.metric("📍 Bölge", row['zone'])
                    
                    st.info(f"🎯 Talep Edilen İhtiyaç: **{row.get('aid_type', 'Genel')}**")

                    if row.get('phone'):
                        st.write(f"📞 **Telefon:** {row['phone']}")
                    if row.get('address'):
                        st.write(f"🏠 **Adres:** {row['address']}")
                    if row.get('notes'):
                        st.write(f"📝 **Notlar:** {row['notes']}")
                    
                    st.divider()
                    
                    # Priority analysis
                    skor = row['priority_score']
                    if skor >= 70:
                        oncelik_seviye = "🔴 Yüksek Öncelik"
                        oncelik_renk = "#E74C3C"
                    elif skor >= 45:
                        oncelik_seviye = "🟡 Orta Öncelik"
                        oncelik_renk = "#F39C12"
                    else:
                        oncelik_seviye = "🟢 Düşük Öncelik"
                        oncelik_renk = "#27AE60"
                    
                    st.markdown(f"""
                    <div style='background-color:#EBF5FB;padding:14px;border-radius:8px;border-left:4px solid {oncelik_renk};margin-bottom:12px'>
                        <b style='color:{oncelik_renk}'>🤖 AI Analiz Özeti</b><br>
                        <span style='color:#1A252F'>Sistem bu vakayı <b>{oncelik_seviye}</b> olarak sınıflandırdı.</span><br>
                        <span style='color:#555555'>Skor: {skor}/100</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Review form
                    st.subheader("📋 Değerlendirme Formu")
                    denetim_notu = st.text_area(
                        "Değerlendirme Notları *",
                        placeholder="Değerlendirme bulgularını buraya yazın...",
                        key=f"not_{row['id']}"
                    )
                    
                    yardim_turu = st.selectbox(
                        "Onaylanan İhtiyaç Kategorisi",
                        ["Genel", "Gıda", "Tıbbi", "Giyim"],
                        key=f"yardim_{row['id']}"
                    )
                    
                    col_approve, col_reject = st.columns(2)
                    
                    with col_approve:
                        if st.button("✅ Onayla", key=f"onayla_{row['id']}", use_container_width=True, type="primary"):
                            if denetim_notu:
                                update_beneficiary_status(row['id'], "Onaylandı", denetim_notu)
                                update_beneficiary_aid_type(row['id'], yardim_turu)
                                st.session_state.msg = f"✅ {row['name']} başarıyla onaylandı!"
                                st.session_state.msg_type = "success"
                                st.rerun()
                            else:
                                st.error("❌ Lütfen değerlendirme notu girin.")
                    
                    with col_reject:
                        if st.button("❌ Reddet", key=f"reddet_{row['id']}", use_container_width=True):
                            if denetim_notu:
                                update_beneficiary_status(row['id'], "Reddedildi", denetim_notu)
                                st.session_state.msg = f"❌ {row['name']} reddedildi."
                                st.session_state.msg_type = "warning"
                                st.rerun()
                            else:
                                st.error("❌ Lütfen red gerekçesi girin.")
    
    with tab2:
        df_on = get_beneficiaries_by_status("Onaylandı")
        df_red = get_beneficiaries_by_status("Reddedildi")
        
        if not df_on.empty:
            st.subheader("✅ Onaylanan Yararlanıcılar")
            st.dataframe(
                df_on[['name', 'health', 'zone', 'priority_score', 'aid_type', 'reviewer_notes']].rename(columns={
                    'name': 'Ad', 'health': 'Sağlık', 'zone': 'Bölge',
                    'priority_score': 'Skor', 'aid_type': 'Onaylanan Kategori',
                    'reviewer_notes': 'Değerlendirme Notu'
                }),
                use_container_width=True, 
                hide_index=True
            )
        
        if not df_red.empty:
            st.subheader("❌ Reddedilen Yararlanıcılar")
            for _, red_row in df_red.iterrows():
                with st.expander(f"❌ {red_row['name']} | Skor: {red_row['priority_score']}/100"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("🏥 Sağlık", red_row['health'].title())
                    col2.metric("📍 Bölge", red_row['zone'])
                    col3.metric("📊 Skor", red_row['priority_score'])
                    
                    st.write(f"**📝 Red Gerekçesi:** {red_row['reviewer_notes']}")
                    st.divider()
                    st.write("**🔄 Yeniden Değerlendirme:**")
                    
                    yeni_not = st.text_area(
                        "Güncelleme Notu *",
                        placeholder="Neden yeniden değerlendiriliyor? (örn: Ekonomik koşullar değişti)",
                        key=f"yeni_not_{red_row['id']}"
                    )
                    
                    if st.button("🔄 Yeniden Değerlendir", key=f"yeniden_{red_row['id']}", use_container_width=True):
                        if yeni_not:
                            update_beneficiary_status(red_row['id'], "İncelemede", yeni_not)
                            st.session_state.msg = f"🔄 {red_row['name']} yeniden incelemeye alındı!"
                            st.session_state.msg_type = "success"
                            st.rerun()
                        else:
                            st.error("❌ Lütfen güncelleme notu girin.")