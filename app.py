import streamlit as st
import pandas as pd
import io
import json
import os
from decimal import Decimal, ROUND_HALF_UP

# --- Excel Tarzı Kesin Yuvarlama Fonksiyonu ---
def excel_yuvarla(deger, basamak=2):
    """Excel'in YUVARLA formülü ile birebir aynı çalışan fonksiyon"""
    format_str = '1.' + '0' * basamak if basamak > 0 else '1'
    return float(Decimal(str(deger)).quantize(Decimal(format_str), rounding=ROUND_HALF_UP))

# --- Veri Saklama (JSON) Fonksiyonları ---
DATA_FILE = "endeksler.json"

def endeksleri_yukle():
    if not os.path.exists(DATA_FILE):
        varsayilan_veriler = {"Mart 2026": 4747.63, "Şubat 2026": 4620.50}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(varsayilan_veriler, f, ensure_ascii=False, indent=4)
        return varsayilan_veriler
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def endeks_kaydet(donem_adi, endeks_degeri):
    mevcut_veriler = endeksleri_yukle()
    mevcut_veriler[donem_adi] = float(endeks_degeri)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(mevcut_veriler, f, ensure_ascii=False, indent=4)

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
YILLAR = [str(y) for y in range(2022, 2035)]

# --- Sayfa Ayarları ---
st.set_page_config(page_title="AYAP Detaylı Maliyet Hesaplama", layout="wide")
st.title("📊 AYAP Kalem Kalem Maliyet Hesaplama Aracı")

# --- Sol Menü (Parametreler) ---
st.sidebar.header("⚙️ Temel Parametreler")
st.sidebar.markdown("🔗 **[Güncel Yİ-ÜFE Endeksleri (hakedis.org)](https://www.hakedis.org/endeksler/yi-ufe-yurtici-uretici-fiyat-endeksi)**")
st.sidebar.markdown("---")

base_endeks = 1210.60
base_bina = 76.82
base_pafta = 1247.814

endeks_verileri = endeksleri_yukle()
secenekler = list(endeks_verileri.keys())
secenekler.reverse()

secilen_donem = st.sidebar.selectbox("Hesaplamada Kullanılacak Endeksi Seçin", options=secenekler)
guncel_endeks = endeks_verileri[secilen_donem]
st.sidebar.success(f"**{secilen_donem}** Endeksi: **{guncel_endeks}**")

with st.sidebar.expander("➕ Yeni Endeks Ekle"):
    secili_ay = st.selectbox("Ay Seçin", AYLAR)
    secili_yil = st.selectbox("Yıl Seçin", YILLAR, index=4)
    yeni_deger = st.number_input("Endeks Değeri", min_value=0.0, format="%.2f", step=10.0)
    yeni_donem_adi = f"{secili_ay} {secili_yil}"
    
    if st.button("💾 Endeksi Kaydet"):
        if yeni_deger > 0:
            endeks_kaydet(yeni_donem_adi, yeni_deger)
            st.success("Kaydedildi!")
            st.rerun()

st.sidebar.markdown("---")
kar_orani = st.sidebar.number_input("Yüklenici Kârı (%)", value=20.0, step=1.0)
kdv_orani = st.sidebar.number_input("KDV Oranı (%)", value=20.0, step=1.0)

# --- Güncel Katsayı ve Fiyat Hesaplaması ---
katsayi = guncel_endeks / base_endeks
guncel_bina = base_bina * katsayi
guncel_pafta = base_pafta * katsayi

st.info(f"📈 **Uygulanan Endeks Çarpanı:** `{katsayi:.5f}` | "
        f"**Güncel Bina Baz Fiyatı:** `{guncel_bina:,.4f} TL` | "
        f"**Güncel Pafta Baz Fiyatı:** `{guncel_pafta:,.4f} TL`")

# --- Senaryo Seçimi ve Veri Girişi ---
st.markdown("### 🛠️ İş Türü (Senaryo) Seçimi")
is_senaryosu = st.radio(
    "Hangi tür iş için kalem kalem maliyet hesaplıyorsunuz?",
    ("🔧 İyileştirme İşi (Kontrol ve Revizyon)", "🏗️ Oluşturma İşi (Sıfırdan Üretim)"),
    horizontal=True
)
st.markdown("---")

detaylar = [] # Tablo verilerini tutacağımız liste

# --- İYİLEŞTİRME SENARYOSU HESAPLAMALARI ---
if is_senaryosu == "🔧 İyileştirme İşi (Kontrol ve Revizyon)":
    st.subheader("📋 İyileştirme İşi Miktarları")
    col1, col2, col3 = st.columns(3)
    pafta_sayisi = col1.number_input("Pafta Sayısı", min_value=0, value=7280)
    toplam_bina = col2.number_input("Toplam Kontrol Edilecek Bina Sayısı", min_value=0, value=172639)
    sifir_bina = col3.number_input("Sıfırdan Üretilecek Bina Sayısı", min_value=0, value=55126)
    
    eski_bina = toplam_bina - sifir_bina
    st.info(f"ℹ️ **Eski Model Bina Sayısı (Otomatik Hesaplandı):** {eski_bina}")
    
    iyilestirme_kalemleri = [
        {"Sıra": 1, "İş Kalemi": "Daha Önce Üretime Dahil Olan/Olmayan Mimari Kontrolü", "Tür": "Bina", "Oran": 0.05, "Miktar_Tipi": "Toplam", "Basamak": 2},
        {"Sıra": 2, "İş Kalemi": "Nadir ve Eğik Hava Fotoğraflarının Dengelenmesi", "Tür": "Pafta", "Oran": 0.10, "Miktar_Tipi": "Pafta", "Basamak": 2},
        {"Sıra": 3, "İş Kalemi": "SYM, SAM, Nokta Bulutu, Mesh Model Üretimi", "Tür": "Pafta", "Oran": 0.27, "Miktar_Tipi": "Pafta", "Basamak": 2},
        {"Sıra": 4, "İş Kalemi": "Eksik, Hatalı ve Yeni Yapılar 3B Vektör (%15)", "Tür": "Pafta", "Oran": 0.15, "Miktar_Tipi": "Pafta", "Basamak": 2},
        {"Sıra": 5, "İş Kalemi": "Yeni Yapıların Kaplanması ve CityGML Dönüşümü", "Tür": "Pafta", "Oran": 0.27, "Miktar_Tipi": "Pafta", "Basamak": 2},
        {"Sıra": 6, "İş Kalemi": "Mimari Projelerden Vektörel Veri Üretimi", "Tür": "Bina", "Oran": 0.40, "Miktar_Tipi": "Sıfır", "Basamak": 2},
        {"Sıra": 7, "İş Kalemi": "Eski Modellerin Kontrolü ve İyileştirilmesi", "Tür": "Bina", "Oran": 0.20, "Miktar_Tipi": "Eski", "Basamak": 3},
        {"Sıra": 8, "İş Kalemi": "Karşılıklı Kontrol, Hataların Giderilmesi", "Tür": "Bina", "Oran": 0.20, "Miktar_Tipi": "Toplam", "Basamak": 3},
        {"Sıra": 9, "İş Kalemi": "TKGM CityGML Veri Modeline Dönüştürülmesi", "Tür": "Bina", "Oran": 0.35, "Miktar_Tipi": "Toplam", "Basamak": 2},
        {"Sıra": 10, "İş Kalemi": "Veri ve Modellerin İdareye Teslim Edilmesi", "Tür": "Pafta", "Oran": 0.06, "Miktar_Tipi": "Pafta", "Basamak": 2},
    ]
    
    for k in iyilestirme_kalemleri:
        if k["Miktar_Tipi"] == "Pafta": miktar = pafta_sayisi
        elif k["Miktar_Tipi"] == "Toplam": miktar = toplam_bina
        elif k["Miktar_Tipi"] == "Sıfır": miktar = sifir_bina
        elif k["Miktar_Tipi"] == "Eski": miktar = eski_bina
        
        baz_fiyat = guncel_pafta if k["Tür"] == "Pafta" else guncel_bina
        birim_fiyat = excel_yuvarla(baz_fiyat * k["Oran"], k["Basamak"])
        toplam_fiyat = excel_yuvarla(birim_fiyat * miktar, 2)
        
        detaylar.append({
            "Sıra No": k["Sıra"],
            "İş Kalemi Açıklaması": k["İş Kalemi"],
            "Birim": "Adet",
            "Miktar": miktar,
            "Birim Fiyat (TL)": birim_fiyat,
            "Toplam Tutar (TL)": toplam_fiyat
        })

# --- OLUŞTURMA SENARYOSU HESAPLAMALARI ---
elif is_senaryosu == "🏗️ Oluşturma İşi (Sıfırdan Üretim)":
    st.subheader("📋 Oluşturma İşi Miktarları")
    col1, col2 = st.columns(2)
    pafta_sayisi = col1.number_input("Pafta Sayısı", min_value=0, value=7280)
    bina_sayisi = col2.number_input("Toplam Bina Sayısı", min_value=0, value=172639)
    
    olusturma_kalemleri = [
        {"Sıra": 1, "İş Kalemi": "Mimari Proje İnceleme ve Raporlama", "Tür": "Bina", "Oran": 0.05, "Basamak": 2},
        {"Sıra": 2, "İş Kalemi": "Nadir ve Eğik Hava Fotoğraflarının Dengelenmesi", "Tür": "Pafta", "Oran": 0.10, "Basamak": 2},
        {"Sıra": 3, "İş Kalemi": "SYM, SAM, Nokta Bulutu, Gerçek Ortofoto ve Mesh", "Tür": "Pafta", "Oran": 0.27, "Basamak": 2},
        {"Sıra": 4, "İş Kalemi": "3B Vektör Verilerin Fotogrametrik Üretimi", "Tür": "Pafta", "Oran": 0.30, "Basamak": 2},
        {"Sıra": 5, "İş Kalemi": "3B Fotogrametrik Yapı Modellerinin Kaplanması", "Tür": "Pafta", "Oran": 0.27, "Basamak": 2},
        {"Sıra": 6, "İş Kalemi": "Mimari Projelerden Vektörel Veri Üretimi", "Tür": "Bina", "Oran": 0.40, "Basamak": 2},
        {"Sıra": 7, "İş Kalemi": "3B Mimari Yapı Konumlandırma ve Kontrolü", "Tür": "Bina", "Oran": 0.20, "Basamak": 3},
        {"Sıra": 8, "İş Kalemi": "Güncel Verilerle TKGM CityGML Dönüştürmesi", "Tür": "Bina", "Oran": 0.35, "Basamak": 2},
        {"Sıra": 9, "İş Kalemi": "Veri ve Modellerin İdareye Teslim Edilmesi", "Tür": "Pafta", "Oran": 0.06, "Basamak": 2},
    ]
    
    for k in olusturma_kalemleri:
        miktar = pafta_sayisi if k["Tür"] == "Pafta" else bina_sayisi
        baz_fiyat = guncel_pafta if k["Tür"] == "Pafta" else guncel_bina
        birim_fiyat = excel_yuvarla(baz_fiyat * k["Oran"], k["Basamak"])
        toplam_fiyat = excel_yuvarla(birim_fiyat * miktar, 2)
        
        detaylar.append({
            "Sıra No": k["Sıra"],
            "İş Kalemi Açıklaması": k["İş Kalemi"],
            "Birim": "Adet",
            "Miktar": miktar,
            "Birim Fiyat (TL)": birim_fiyat,
            "Toplam Tutar (TL)": toplam_fiyat
        })

# --- SONUÇ EKRANI VE EXCEL ÇIKTISI ---
if len(detaylar) > 0:
    df_detay = pd.DataFrame(detaylar)
    
    st.markdown("---")
    st.subheader("💰 Kalem Kalem Yaklaşık Maliyet Tablosu")
    
    # Ekranda güzel görünmesi için TL formatı ayarlama
    st.dataframe(df_detay.style.format({
        "Birim Fiyat (TL)": "{:,.3f} ₺",
        "Toplam Tutar (TL)": "{:,.2f} ₺"
    }), use_container_width=True, hide_index=True)

    # Toplamların Paketlenmesi
    toplam_ciplak = excel_yuvarla(df_detay["Toplam Tutar (TL)"].sum(), 2)
    yuklenici_kari_tutari = excel_yuvarla(toplam_ciplak * (kar_orani / 100), 2)
    genel_toplam_kdv_siz = toplam_ciplak + yuklenici_kari_tutari
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("📌 ÇIPLAK MALİYET TOPLAMI", f"{toplam_ciplak:,.2f} TL")
    m_col2.metric(f"📌 YÜKLENİCİ KÂRI (+%{int(kar_orani)})", f"{yuklenici_kari_tutari:,.2f} TL")
    m_col3.metric("📌 YAKLAŞIK MALİYET (KDV HARİÇ)", f"{genel_toplam_kdv_siz:,.2f} TL")

    # Excel Olarak Çıktı Alma İşlemleri
    st.markdown("---")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_detay.to_excel(writer, index=False, sheet_name='Kalem_Detaylari')
        worksheet = writer.sheets['Kalem_Detaylari']
        worksheet.column_dimensions['B'].width = 50
        worksheet.column_dimensions['E'].width = 15
        worksheet.column_dimensions['F'].width = 20
        
        # Toplam satırlarını Excel'in en altına ekleme
        son_satir = len(df_detay) + 2
        worksheet.cell(row=son_satir+1, column=5, value="Çıplak Maliyet:")
        worksheet.cell(row=son_satir+1, column=6, value=toplam_ciplak)
        
        worksheet.cell(row=son_satir+2, column=5, value=f"Yüklenici Kârı (%{int(kar_orani)}):")
        worksheet.cell(row=son_satir+2, column=6, value=yuklenici_kari_tutari)
        
        worksheet.cell(row=son_satir+3, column=5, value="NİHAİ MALİYET:")
        worksheet.cell(row=son_satir+3, column=6, value=genel_toplam_kdv_siz)
            
    st.download_button(
        label="📥 Bu Tabloyu Excel Olarak İndir",
        data=buffer.getvalue(),
        file_name=f"Kalem_Kalem_Maliyet_{'Iyilestirme' if 'İyileştirme' in is_senaryosu else 'Olusturma'}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
