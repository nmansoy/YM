import streamlit as st
import pandas as pd
import io
import json
import os

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
st.set_page_config(page_title="AYAP Maliyet Hesaplama", layout="wide")
st.title("📊 İş Bazlı Yaklaşık Maliyet Hesaplama Aracı")

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

# --- 1. Adım: Güncel Katsayı ve Fiyat Hesaplaması ---
katsayi = guncel_endeks / base_endeks
guncel_bina = base_bina * katsayi
guncel_pafta = base_pafta * katsayi

st.info(f"📈 **Uygulanan Endeks Çarpanı:** `{katsayi:.5f}` | "
        f"**Güncel Bina Baz Fiyatı:** `{guncel_bina:,.4f} TL` | "
        f"**Güncel Pafta Baz Fiyatı:** `{guncel_pafta:,.4f} TL`")

# --- 2. Adım: Senaryo Seçimi ---
st.markdown("### 🛠️ İş Türü (Senaryo) Seçimi")
is_senaryosu = st.radio(
    "Hangi tür iş için yaklaşık maliyet hesaplıyorsunuz?",
    ("🏗️ Oluşturma İşi (Sıfırdan Üretim)", "🔧 İyileştirme İşi (Kontrol ve Revizyon)"),
    horizontal=True
)

st.markdown("---")
st.subheader("📋 İş Bilgileri ve Miktarlar")

# Senaryoya göre tablo veri yapısını belirle
if "df_olusturma" not in st.session_state:
    st.session_state.df_olusturma = pd.DataFrame({"İş Bilgisi / Adı": ["Örnek İlçe"], "Pafta Sayısı": [10], "Bina Sayısı": [500]})
if "df_iyilestirme" not in st.session_state:
    st.session_state.df_iyilestirme = pd.DataFrame({
        "İş Bilgisi / Adı": ["Örnek İlçe"], 
        "Pafta Sayısı": [10], 
        "Toplam Kontrol Bina": [172639], 
        "Sıfırdan Üretilecek Bina": [55126]
    })

# --- 3. Adım: Veri Girişi ve Hesaplamalar ---
if "Oluşturma" in is_senaryosu:
    st.write("Aşağıdaki tabloya **Oluşturma İşi** için geçerli Pafta ve Bina sayılarını girin.")
    edited_df = st.data_editor(st.session_state.df_olusturma, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if not edited_df.empty:
        sonuc_df = edited_df.copy()
        for col in ["Pafta Sayısı", "Bina Sayısı"]:
            sonuc_df[col] = pd.to_numeric(sonuc_df[col]).fillna(0)
            
        sonuc_df["Çıplak Maliyet (TL)"] = (sonuc_df["Bina Sayısı"] * guncel_bina) + (sonuc_df["Pafta Sayısı"] * guncel_pafta)

elif "İyileştirme" in is_senaryosu:
    st.write("Aşağıdaki tabloya **İyileştirme İşi** için sayıları girin. *(Eski model kontrol edilecek bina sayısı otomatik hesaplanır).*")
    edited_df = st.data_editor(st.session_state.df_iyilestirme, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if not edited_df.empty:
        sonuc_df = edited_df.copy()
        for col in ["Pafta Sayısı", "Toplam Kontrol Bina", "Sıfırdan Üretilecek Bina"]:
            sonuc_df[col] = pd.to_numeric(sonuc_df[col]).fillna(0)
        
        # Matematiksel Mantık
        sonuc_df["Eski Model Bina (Oto)"] = sonuc_df["Toplam Kontrol Bina"] - sonuc_df["Sıfırdan Üretilecek Bina"]
        
        # Pafta Maliyeti (Kalem 4 yarı yarıya düştüğü için %85)
        pafta_maliyeti = sonuc_df["Pafta Sayısı"] * (guncel_pafta * 0.85)
        
        # Bina Maliyeti (Parçalı)
        bina_maliyeti = (
            (sonuc_df["Toplam Kontrol Bina"] * guncel_bina * 0.60) +   # Kalem 1, 8, 9
            (sonuc_df["Sıfırdan Üretilecek Bina"] * guncel_bina * 0.40) + # Kalem 6
            (sonuc_df["Eski Model Bina (Oto)"] * guncel_bina * 0.20)     # Kalem 7 (Ekstra)
        )
        
        sonuc_df["Çıplak Maliyet (TL)"] = pafta_maliyeti + bina_maliyeti

# --- 4. Adım: Kâr/KDV Ekleme ve Gösterme ---
if not edited_df.empty:
    sonuc_df[f"Kar Dahil Y. Maliyet (KDV'siz) (+%{int(kar_orani)})"] = sonuc_df["Çıplak Maliyet (TL)"] * (1 + kar_orani / 100)
    sonuc_df[f"Toplam Tutar (KDV'li) (+%{int(kdv_orani)})"] = sonuc_df[f"Kar Dahil Y. Maliyet (KDV'siz) (+%{int(kar_orani)})"] * (1 + kdv_orani / 100)

    st.subheader("💰 Hesaplanan Kesin Maliyetler Tablosu")
    format_dict = {
        "Çıplak Maliyet (TL)": "{:,.2f} ₺",
        f"Kar Dahil Y. Maliyet (KDV'siz) (+%{int(kar_orani)})": "{:,.2f} ₺",
        f"Toplam Tutar (KDV'li) (+%{int(kdv_orani)})": "{:,.2f} ₺"
    }
    st.dataframe(sonuc_df.style.format(format_dict), use_container_width=True, hide_index=True)

    genel_kdv_siz = sonuc_df[f"Kar Dahil Y. Maliyet (KDV'siz) (+%{int(kar_orani)})"].sum()
    genel_kdv_li = sonuc_df[f"Toplam Tutar (KDV'li) (+%{int(kdv_orani)})"].sum()

    col1, col2 = st.columns(2)
    col1.metric("📌 GENEL TOPLAM (KDV'SİZ)", f"{genel_kdv_siz:,.2f} TL")
    col2.metric("📌 GENEL TOPLAM (KDV'Lİ)", f"{genel_kdv_li:,.2f} TL")

    # Excel İndirme
    st.markdown("---")
    st.subheader("📄 Excel Çıktısı Al")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        sonuc_df.to_excel(writer, index=False, sheet_name='Detayli_Maliyetler')
        worksheet = writer.sheets['Detayli_Maliyetler']
        for idx, col in enumerate(sonuc_df.columns):
            worksheet.column_dimensions[chr(65 + idx)].width = 25 
            
    st.download_button(
        label="📥 Tabloyu Excel Olarak İndir",
        data=buffer.getvalue(),
        file_name=f"Yaklasik_Maliyet_{'Olusturma' if 'Oluşturma' in is_senaryosu else 'Iyilestirme'}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
