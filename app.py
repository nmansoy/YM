import streamlit as st
import pandas as pd
import io
import json
import os

# --- Veri Saklama (JSON) Fonksiyonları ---
DATA_FILE = "endeksler.json"

def endeksleri_yukle():
    """Kayıtlı endeksleri JSON dosyasından okur, yoksa varsayılanları oluşturur."""
    if not os.path.exists(DATA_FILE):
        # Dosya yoksa ilk kurulum için varsayılan veriler
        varsayilan_veriler = {
            "Mart 2026": 4747.63,
            "Şubat 2026": 4620.50,
            "Ocak 2026": 4500.00
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(varsayilan_veriler, f, ensure_ascii=False, indent=4)
        return varsayilan_veriler
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def endeks_kaydet(donem_adi, endeks_degeri):
    """Yeni girilen endeksi JSON dosyasına kalıcı olarak yazar."""
    mevcut_veriler = endeksleri_yukle()
    mevcut_veriler[donem_adi] = float(endeks_degeri)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(mevcut_veriler, f, ensure_ascii=False, indent=4)

# Sabit Listeler
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
YILLAR = [str(y) for y in range(2022, 2035)] # 2022'den 2034'e kadar yıllar

# --- Sayfa Ayarları ---
st.set_page_config(page_title="AYAP Maliyet Hesaplama", layout="wide")
st.title("📊 İş Bazlı Yaklaşık Maliyet Hesaplama Aracı")
st.markdown("Yİ-ÜFE verilerinizi yan menüden seçebilir veya yeni ayların verilerini kalıcı olarak ekleyebilirsiniz.")

# --- Sol Menü (Parametreler) ---
st.sidebar.header("⚙️ Temel Parametreler")

# Link Ekleme
st.sidebar.markdown("🔗 **[Güncel Yİ-ÜFE Endekslerine Ulaşmak İçin Tıklayın (hakedis.org)](https://www.hakedis.org/endeksler/yi-ufe-yurtici-uretici-fiyat-endeksi)**")
st.sidebar.markdown("---")

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

# Kayıtlı Endeksleri Listele ve Seç
endeks_verileri = endeksleri_yukle()
secenekler = list(endeks_verileri.keys())
secenekler.reverse() # En son eklenen en üstte görünsün

secilen_donem = st.sidebar.selectbox("Hesaplamada Kullanılacak Endeksi Seçin", options=secenekler)
guncel_endeks = endeks_verileri[secilen_donem]
st.sidebar.success(f"**{secilen_donem}** Endeksi: **{guncel_endeks}**")

# --- YENİ ENDEKS EKLEME ALANI (Seçmeli) ---
with st.sidebar.expander("➕ Yeni Endeks Ekle (Kalıcı Kayıt)"):
    secili_ay = st.selectbox("Ay Seçin", AYLAR)
    secili_yil = st.selectbox("Yıl Seçin", YILLAR, index=4) # Varsayılan olarak 2026 gelsin diye index=4
    
    yeni_deger = st.number_input("Endeks Değeri", min_value=0.0, format="%.2f", step=10.0)
    yeni_donem_adi = f"{secili_ay} {secili_yil}"
    
    if st.button("💾 Endeksi Kaydet"):
        if yeni_deger <= 0:
            st.error("Geçerli bir endeks değeri girin.")
        else:
            endeks_kaydet(yeni_donem_adi, yeni_deger)
            st.success(f"'{yeni_donem_adi}' dönemi başarıyla kaydedildi!")
            st.rerun()

st.sidebar.markdown("---")

# --- KAYITLI ENDEKSLERİ YILA GÖRE LİSTELEME ---
st.sidebar.subheader("📅 Yıla Göre Kayıtlı Endeksler")
filtre_yil = st.sidebar.selectbox("Görüntülenecek Yılı Seçin", YILLAR, index=4)

# Seçilen yıla ait verileri filtrele
yil_verileri = {k: v for k, v in endeks_verileri.items() if filtre_yil in k}

if yil_verileri:
    df_yil = pd.DataFrame(list(yil_verileri.items()), columns=["Dönem", "Endeks Değeri"])
    st.sidebar.dataframe(df_yil, hide_index=True, use_container_width=True)
else:
    st.sidebar.info(f"{filtre_yil} yılına ait kayıtlı endeks bulunmuyor.")

st.sidebar.markdown("---")
kar_orani = st.sidebar.number_input("Yüklenici Kârı (%)", value=20.0, step=1.0)
kdv_orani = st.sidebar.number_input("KDV Oranı (%)", value=20.0, step=1.0)

# --- 1. Adım: Güncel Katsayı ve Fiyat Hesaplaması ---
# ... (Kodun geri kalanı tamamen aynı) ...
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
