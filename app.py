import streamlit as st
import pandas as pd
import requests
import io

# --- Veri Çekme Fonksiyonu (Hakedis.org'dan) ---
@st.cache_data(ttl=86400) # Günde bir güncellenir ki siteyi yormasın
def endeks_verilerini_cek():
    url = "https://www.hakedis.org/endeksler/yi-ufe-yurtici-uretici-fiyat-endeksi"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        # Sitedeki tabloları Pandas ile otomatik oku
        tablolar = pd.read_html(response.text)
        df = tablolar[0]  # Genellikle sitedeki ilk tablo Yİ-ÜFE tablosudur
        
        endeks_sozluk = {}
        
        # Hakedis.org tablosunda ilk sütun Yıl, diğer sütunlar Aylardır
        yil_sutunu = df.columns[0]
        ay_sutunlari = df.columns[1:]
        
        # Tabloyu satır satır gezerek Yıl - Ay sözlüğü oluştur
        for index, row in df.iterrows():
            yil = str(row[yil_sutunu]).replace('.0', '').strip()
            # Genel tabloda 'Yıl' veya boş olmayanları alalım
            if yil.isdigit(): 
                for ay in ay_sutunlari:
                    deger = row[ay]
                    # Boş olan veya çizgi çekilmiş ayları atla
                    if pd.notna(deger) and str(deger).strip() not in ['-', '', 'NaN']:
                        deger_str = str(deger).strip()
                        # Türk tipi sayı formatını (4.747,63) evrensel formata (4747.63) çevirme
                        if ',' in deger_str and '.' in deger_str:
                            deger_str = deger_str.replace('.', '').replace(',', '.')
                        elif ',' in deger_str:
                            deger_str = deger_str.replace(',', '.')
                        
                        try:
                            float_deger = float(deger_str)
                            anahtar = f"{yil} - {ay}"
                            endeks_sozluk[anahtar] = float_deger
                        except ValueError:
                            pass
                            
        return endeks_sozluk
    except Exception as e:
        return None

# --- Sayfa Ayarları ---
st.set_page_config(page_title="AYAP Maliyet Hesaplama", layout="wide")
st.title("📊 İş Bazlı Yaklaşık Maliyet Hesaplama Aracı")
st.markdown("Yİ-ÜFE verileri otomatik olarak Hakedis.org'dan çekilmektedir.")

# --- Sol Menü (Parametreler) ---
st.sidebar.header("⚙️ Temel Parametreler")

# SABİT DEĞERLER (Kullanıcı değiştiremez)
st.sidebar.markdown("*(2022 Şubat Baz Verileri - Sabit)*")
base_endeks = 1210.60
base_bina = 76.82
base_pafta = 1247.814

st.sidebar.info(f"📌 **Şubat 2022 Endeksi:** `{base_endeks}`\n\n"
                f"🏛️ **Bina B.F:** `{base_bina} TL`\n\n"
                f"🗺️ **Pafta B.F:** `{base_pafta} TL`")

st.sidebar.markdown("---")
st.sidebar.markdown("*(Güncel Endeks Seçimi)*")

# Hakedis'ten verileri çek
endeks_verileri = endeks_verilerini_cek()

guncel_endeks = 4747.63 # Varsayılan (hata olursa)

if endeks_verileri:
    # Veriler başarıyla çekildiyse Selectbox göster
    # Sözlükteki verileri tersten sıralayalım (En güncel yıllar/aylar üstte görünsün diye)
    secenekler = list(endeks_verileri.keys())
    secenekler.reverse()
    
    secilen_donem = st.sidebar.selectbox("Endeks Dönemi (Hakedis.org)", options=secenekler)
    guncel_endeks = endeks_verileri[secilen_donem]
    st.sidebar.success(f"**{secilen_donem}** Endeksi: **{guncel_endeks}**")
else:
    st.sidebar.warning("Siteden veri çekilemedi. Lütfen manuel giriniz.")
    guncel_endeks = st.sidebar.number_input("Güncel Endeks (Manuel)", value=4747.63, step=10.0, format="%.2f")

# Acil durum için manuel giriş tik kutusu (Site güncellenirse fakat listede çıkmazsa diye)
manuel_giris_mi = st.sidebar.checkbox("Endeksi Elle Yazmak İstiyorum")
if manuel_giris_mi:
    guncel_endeks = st.sidebar.number_input("Endeks Değerini Girin", value=float(guncel_endeks), step=10.0, format="%.2f")

st.sidebar.markdown("---")
kar_orani = st.sidebar.number_input("Yüklenici Kârı (%)", value=20.0, step=1.0)
kdv_orani = st.sidebar.number_input("KDV Oranı (%)", value=20.0, step=1.0)

# --- 1. Adım: Güncel Katsayı ve Fiyat Hesaplaması ---
katsayi = guncel_endeks / base_endeks
guncel_bina = base_bina * katsayi
guncel_pafta = base_pafta * katsayi

st.info(f"📈 **Uygulanan Endeks Çarpanı:** `{katsayi:.5f}` | "
        f"**Güncel Bina Fiyatı:** `{guncel_bina:,.2f} TL` | "
        f"**Güncel Pafta Fiyatı:** `{guncel_pafta:,.2f} TL`")

# --- 2. Adım: Dinamik İş Girişi (Veri Tablosu) ---
st.subheader("📋 İş Bilgileri ve Miktarlar")
st.write("Aşağıdaki tabloya tıklayarak iş adını değiştirebilir, sayıları girebilir veya en alttaki boş satıra tıklayarak **yeni işler ekleyebilirsiniz.**")

if "df_isler" not in st.session_state:
    st.session_state.df_isler = pd.DataFrame({
        "İş Bilgisi / Adı": ["Örnek İlçe Çalışması"],
        "Bina Sayısı": [10],
        "Pafta Sayısı": [2]
    })

edited_df = st.data_editor(
    st.session_state.df_isler,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# --- 3. Adım: Maliyetlerin Otomatik Hesaplanması ---
if not edited_df.empty:
    sonuc_df = edited_df.copy()
    
    sonuc_df["Bina Sayısı"] = pd.to_numeric(sonuc_df["Bina Sayısı"]).fillna(0)
    sonuc_df["Pafta Sayısı"] = pd.to_numeric(sonuc_df["Pafta Sayısı"]).fillna(0)

    # Maliyet Formülleri
    sonuc_df["Çıplak Maliyet (TL)"] = (sonuc_df["Bina Sayısı"] * guncel_bina) + (sonuc_df["Pafta Sayısı"] * guncel_pafta)
    sonuc_df[f"Kar Dahil Y. Maliyet (KDV'siz) (+%{int(kar_orani)})"] = sonuc_df["Çıplak Maliyet (TL)"] * (1 + kar_orani / 100)
    sonuc_df[f"Toplam Tutar (KDV'li) (+%{int(kdv_orani)})"] = sonuc_df[f"Kar Dahil Y. Maliyet (KDV'siz) (+%{int(kar_orani)})"] * (1 + kdv_orani / 100)

    st.subheader("💰 Hesaplanan Kesin Maliyetler Tablosu")
    
    format_dict = {
        "Çıplak Maliyet (TL)": "{:,.2f} ₺",
        f"Kar Dahil Y. Maliyet (KDV'siz) (+%{int(kar_orani)})": "{:,.2f} ₺",
        f"Toplam Tutar (KDV'li) (+%{int(kdv_orani)})": "{:,.2f} ₺"
    }
    st.dataframe(sonuc_df.style.format(format_dict), use_container_width=True, hide_index=True)

    # --- Genel Toplamlar Paneli ---
    genel_kdv_siz = sonuc_df[f"Kar Dahil Y. Maliyet (KDV'siz) (+%{int(kar_orani)})"].sum()
    genel_kdv_li = sonuc_df[f"Toplam Tutar (KDV'li) (+%{int(kdv_orani)})"].sum()

    col1, col2 = st.columns(2)
    col1.metric("📌 GENEL TOPLAM (KDV'SİZ)", f"{genel_kdv_siz:,.2f} TL")
    col2.metric("📌 GENEL TOPLAM (KDV'Lİ)", f"{genel_kdv_li:,.2f} TL")

    # --- 4. Adım: Excel Çıktısı ---
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
        file_name="Guncel_Maliyet_Hesabi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
else:
    st.warning("Lütfen hesaplama yapmak için tabloya en az 1 iş kalemi ekleyin.")
