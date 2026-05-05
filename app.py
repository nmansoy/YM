import streamlit as st
import pandas as pd
import io

# --- Sayfa Ayarları ---
st.set_page_config(page_title="Dinamik Maliyet Hesaplama", layout="wide")
st.title("📊 İş Bazlı Yaklaşık Maliyet Hesaplama Aracı")
st.markdown("Güncel Yİ-ÜFE verileriyle çoklu iş kalemlerini hesaplayıp Excel çıktısı alabilirsiniz.")

# --- Sol Menü (Parametreler) ---
st.sidebar.header("⚙️ Temel Parametreler")
st.sidebar.markdown("*(2022 Şubat Baz Verileri)*")
base_endeks = st.sidebar.number_input("Şubat 2022 Endeksi", value=1210.6, step=10.0, format="%.2f")
base_bina = st.sidebar.number_input("Şubat 2022 Bina B.F. (TL)", value=76.82, format="%.2f")
base_pafta = st.sidebar.number_input("Şubat 2022 Pafta B.F. (TL)", value=1247.814, format="%.3f")

st.sidebar.markdown("---")
st.sidebar.markdown("*(Güncel Veriler ve Oranlar)*")
guncel_endeks = st.sidebar.number_input("Güncel Endeks", value=4747.63, step=10.0, format="%.2f")
kar_orani = st.sidebar.number_input("Yüklenici Kârı (%)", value=20.0, step=1.0)
kdv_orani = st.sidebar.number_input("KDV Oranı (%)", value=20.0, step=1.0)

# --- 1. Adım: Güncel Katsayı ve Fiyat Hesaplaması ---
katsayi = guncel_endeks / base_endeks if base_endeks > 0 else 1.0
guncel_bina = base_bina * katsayi
guncel_pafta = base_pafta * katsayi

st.info(f"📈 **Güncel Endeks Çarpanı:** `{katsayi:.5f}` | "
        f"**Güncel Bina Fiyatı:** `{guncel_bina:,.2f} TL` | "
        f"**Güncel Pafta Fiyatı:** `{guncel_pafta:,.2f} TL`")

# --- 2. Adım: Dinamik İş Girişi (Veri Tablosu) ---
st.subheader("📋 İş Bilgileri ve Miktarlar")
st.write("Aşağıdaki tabloya tıklayarak iş adını değiştirebilir, sayıları girebilir veya en alttaki boş satıra tıklayarak **yeni işler ekleyebilirsiniz.**")

if "df_isler" not in st.session_state:
    st.session_state.df_isler = pd.DataFrame({
        "İş Bilgisi / Adı": ["1. Bölge Çalışması", "2. Bölge Çalışması"],
        "Bina Sayısı": [10, 5],
        "Pafta Sayısı": [2, 1]
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
        file_name="Gunluk_Maliyet_Hesabi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
else:
    st.warning("Lütfen hesaplama yapmak için tabloya en az 1 iş kalemi ekleyin.")