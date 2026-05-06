import streamlit as st
import pandas as pd
import io
import json
import os
from decimal import Decimal, ROUND_HALF_UP

# --- Excel Tarzı Kesin Yuvarlama Fonksiyonu ---
def excel_yuvarla(deger, basamak=2):
    format_str = '1.' + '0' * basamak if basamak > 0 else '1'
    return float(Decimal(str(deger)).quantize(Decimal(format_str), rounding=ROUND_HALF_UP))

# --- Veri Saklama ve Sıralama ---
DATA_FILE = "endeksler.json"
AYLAR_SOZLUK = {"Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4, "Mayıs": 5, "Haziran": 6, "Temmuz": 7, "Ağustos": 8, "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12}

def kronolojik_sirala(endeks_dict):
    def siralama_anahtari(item):
        try:
            ay_isim, yil = item[0].split()
            return int(yil) * 100 + AYLAR_SOZLUK.get(ay_isim, 0)
        except:
            return 0
    return dict(sorted(endeks_dict.items(), key=siralama_anahtari, reverse=True))

def endeksleri_yukle():
    if not os.path.exists(DATA_FILE):
        varsayilan = {"Mart 2026": 4747.63, "Şubat 2026": 4620.50}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(varsayilan, f, ensure_ascii=False, indent=4)
        return kronolojik_sirala(varsayilan)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return kronolojik_sirala(json.load(f))

def endeks_kaydet(donem_adi, deger):
    veriler = endeksleri_yukle()
    veriler[donem_adi] = float(deger)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(kronolojik_sirala(veriler), f, ensure_ascii=False, indent=4)

AYLAR_LISTESI = list(AYLAR_SOZLUK.keys())
YILLAR_LISTESI = [str(y) for y in range(2022, 2035)]

# --- Sayfa Ayarları ---
st.set_page_config(page_title="AYAP Çoklu İş Maliyet Aracı", layout="wide")
st.title("📊 AYAP Çoklu İş & Kalem Maliyet Hesaplama Aracı")

# --- Sol Menü ---
st.sidebar.header("⚙️ Temel Parametreler")
st.sidebar.markdown("🔗 **[Yİ-ÜFE Endeksleri (hakedis.org)](https://www.hakedis.org/endeksler/yi-ufe-yurtici-uretici-fiyat-endeksi)**")
st.sidebar.markdown("---")

st.sidebar.subheader("🗺️ Pafta Üretim Tipi")
mesh_durumu = st.sidebar.radio("Mesh model üretimi yapılacak mı?", ("✅ Mesh Üretimli (Mevcut)", "❌ Mesh Üretimsiz (İptal Edilen)"))

base_endeks = 1210.60
base_bina = 76.82
base_pafta = 1247.814 if "Üretimli" in mesh_durumu else 1155.384

if "Üretimsiz" in mesh_durumu:
    st.sidebar.warning("⚠️ Mesh üretimi iptal edilmiş pafta baz fiyatı (1155.384 TL) kullanılır.")

st.sidebar.markdown("---")
endeks_verileri = endeksleri_yukle()
secenekler = list(endeks_verileri.keys())
secilen_donem = st.sidebar.selectbox("Endeks Seçin", options=secenekler, index=0)
guncel_endeks = endeks_verileri[secilen_donem]
st.sidebar.success(f"**{secilen_donem}:** {guncel_endeks}")

with st.sidebar.expander("➕ Yeni Endeks Ekle"):
    ay = st.selectbox("Ay", AYLAR_LISTESI)
    yil = st.selectbox("Yıl", YILLAR_LISTESI, index=4)
    deger = st.number_input("Değer", min_value=0.0, format="%.2f", step=10.0)
    if st.button("💾 Kaydet") and deger > 0:
        endeks_kaydet(f"{ay} {yil}", deger)
        st.rerun()

st.sidebar.markdown("---")
kar_orani = st.sidebar.number_input("Yüklenici Kârı (%)", value=20.0, step=1.0)
kdv_orani = st.sidebar.number_input("KDV Oranı (%)", value=20.0, step=1.0)

# --- Katsayı ve Fiyatlar ---
katsayi = guncel_endeks / base_endeks
guncel_bina = base_bina * katsayi
guncel_pafta = base_pafta * katsayi

st.markdown("### 📈 Güncel Baz Fiyatlar ve Çarpan")
m_col1, m_col2, m_col3 = st.columns(3)
m_col1.metric("Endeks Çarpanı", f"{katsayi:.5f}")
m_col2.metric("Güncel Bina B.F.", f"{guncel_bina:,.4f} ₺")
m_col3.metric("Güncel Pafta B.F.", f"{guncel_pafta:,.4f} ₺", delta=mesh_durumu.split("(")[0].strip(), delta_color="normal")
st.markdown("---")

# --- Senaryo Seçimi ---
st.markdown("### 🛠️ İş Türü ve Çoklu Veri Girişi")
is_senaryosu = st.radio("Hangi tür iş hesaplanacak?", ("🔧 İyileştirme İşi (Kontrol ve Revizyon)", "🏗️ Oluşturma İşi (Sıfırdan Üretim)"), horizontal=True)

# Tablo yapıları
if "df_iyilestirme" not in st.session_state:
    st.session_state.df_iyilestirme = pd.DataFrame({"İş Adı": ["1. Bölge"], "Pafta Sayısı": [7280], "Toplam Kontrol Bina": [172639], "Sıfırdan Üretilecek Bina": [55126]})
if "df_olusturma" not in st.session_state:
    st.session_state.df_olusturma = pd.DataFrame({"İş Adı": ["1. Bölge"], "Pafta Sayısı": [7280], "Toplam Bina": [172639]})

st.write("Aşağıdaki tabloya tıklayarak satır ekleyebilir ve **birden fazla işi aynı anda** hesaplayabilirsiniz.")

# --- Veri Giriş Tablosu ---
if "İyileştirme" in is_senaryosu:
    edited_df = st.data_editor(st.session_state.df_iyilestirme, num_rows="dynamic", use_container_width=True, hide_index=True)
else:
    edited_df = st.data_editor(st.session_state.df_olusturma, num_rows="dynamic", use_container_width=True, hide_index=True)

st.markdown("---")

# --- HESAPLAMA MOTORU ---
if not edited_df.empty:
    ozet_veriler = []
    tum_kalemler = []

    for index, row in edited_df.iterrows():
        is_adi = row.get("İş Adı", f"İş {index+1}")
        pafta_sayisi = float(row.get("Pafta Sayısı", 0))
        
        detay_satirlari = []
        is_ciplak_toplam = 0.0

        if "İyileştirme" in is_senaryosu:
            toplam_bina = float(row.get("Toplam Kontrol Bina", 0))
            sifir_bina = float(row.get("Sıfırdan Üretilecek Bina", 0))
            eski_bina = toplam_bina - sifir_bina

            kalemler = [
                {"Sıra": 1, "Ad": "Daha Önce Üretime Dahil Olan/Olmayan Mimari Kontrolü", "Tür": "Bina", "Oran": 0.05, "Mik": toplam_bina, "Bas": 2},
                {"Sıra": 2, "Ad": "Nadir ve Eğik Hava Fotoğraflarının Dengelenmesi", "Tür": "Pafta", "Oran": 0.10, "Mik": pafta_sayisi, "Bas": 2},
                {"Sıra": 3, "Ad": "SYM, SAM, Nokta Bulutu, Mesh Model Üretimi", "Tür": "Pafta", "Oran": 0.27, "Mik": pafta_sayisi, "Bas": 2},
                {"Sıra": 4, "Ad": "Eksik, Hatalı ve Yeni Yapılar 3B Vektör (%15)", "Tür": "Pafta", "Oran": 0.15, "Mik": pafta_sayisi, "Bas": 2},
                {"Sıra": 5, "Ad": "Yeni Yapıların Kaplanması ve CityGML Dönüşümü", "Tür": "Pafta", "Oran": 0.27, "Mik": pafta_sayisi, "Bas": 2},
                {"Sıra": 6, "Ad": "Mimari Projelerden Vektörel Veri Üretimi", "Tür": "Bina", "Oran": 0.40, "Mik": sifir_bina, "Bas": 2},
                {"Sıra": 7, "Ad": "Eski Modellerin Kontrolü ve İyileştirilmesi", "Tür": "Bina", "Oran": 0.20, "Mik": eski_bina, "Bas": 3},
                {"Sıra": 8, "Ad": "Karşılıklı Kontrol, Hataların Giderilmesi", "Tür": "Bina", "Oran": 0.20, "Mik": toplam_bina, "Bas": 3},
                {"Sıra": 9, "Ad": "TKGM CityGML Veri Modeline Dönüştürülmesi", "Tür": "Bina", "Oran": 0.35, "Mik": toplam_bina, "Bas": 2},
                {"Sıra": 10, "Ad": "Veri ve Modellerin İdareye Teslim Edilmesi", "Tür": "Pafta", "Oran": 0.06, "Mik": pafta_sayisi, "Bas": 2},
            ]
        else:
            toplam_bina = float(row.get("Toplam Bina", 0))
            kalemler = [
                {"Sıra": 1, "Ad": "Mimari Proje İnceleme ve Raporlama", "Tür": "Bina", "Oran": 0.05, "Mik": toplam_bina, "Bas": 2},
                {"Sıra": 2, "Ad": "Nadir ve Eğik Hava Fotoğraflarının Dengelenmesi", "Tür": "Pafta", "Oran": 0.10, "Mik": pafta_sayisi, "Bas": 2},
                {"Sıra": 3, "Ad": "SYM, SAM, Nokta Bulutu, Gerçek Ortofoto ve Mesh", "Tür": "Pafta", "Oran": 0.27, "Mik": pafta_sayisi, "Bas": 2},
                {"Sıra": 4, "Ad": "3B Vektör Verilerin Fotogrametrik Üretimi", "Tür": "Pafta", "Oran": 0.30, "Mik": pafta_sayisi, "Bas": 2},
                {"Sıra": 5, "Ad": "3B Fotogrametrik Yapı Modellerinin Kaplanması", "Tür": "Pafta", "Oran": 0.27, "Mik": pafta_sayisi, "Bas": 2},
                {"Sıra": 6, "Ad": "Mimari Projelerden Vektörel Veri Üretimi", "Tür": "Bina", "Oran": 0.40, "Mik": toplam_bina, "Bas": 2},
                {"Sıra": 7, "Ad": "3B Mimari Yapı Konumlandırma ve Kontrolü", "Tür": "Bina", "Oran": 0.20, "Mik": toplam_bina, "Bas": 3},
                {"Sıra": 8, "Ad": "Güncel Verilerle TKGM CityGML Dönüştürmesi", "Tür": "Bina", "Oran": 0.35, "Mik": toplam_bina, "Bas": 2},
                {"Sıra": 9, "Ad": "Veri ve Modellerin İdareye Teslim Edilmesi", "Tür": "Pafta", "Oran": 0.06, "Mik": pafta_sayisi, "Bas": 2},
            ]

        # Her kalem için hesaplama yap
        for k in kalemler:
            baz = guncel_pafta if k["Tür"] == "Pafta" else guncel_bina
            bf = excel_yuvarla(baz * k["Oran"], k["Bas"])
            toplam_tutar = excel_yuvarla(bf * k["Mik"], 2)
            is_ciplak_toplam += toplam_tutar
            
            tum_kalemler.append({
                "İş Adı": is_adi, "Sıra No": k["Sıra"], "İş Kalemi Açıklaması": k["Ad"], 
                "Birim": "Adet", "Miktar": k["Mik"], "Birim Fiyat (TL)": bf, "Toplam Tutar (TL)": toplam_tutar
            })

        # İşin genel özetini çıkar
        is_ciplak = excel_yuvarla(is_ciplak_toplam, 2)
        is_kar = excel_yuvarla(is_ciplak * (kar_orani / 100), 2)
        is_kdvsiz = excel_yuvarla(is_ciplak + is_kar, 2)
        is_kdv = excel_yuvarla(is_kdvsiz * (kdv_orani / 100), 2)
        is_kdvli = excel_yuvarla(is_kdvsiz + is_kdv, 2)

        ozet_veriler.append({
            "İş Adı": is_adi, 
            "Çıplak Maliyet (TL)": is_ciplak, 
            f"Kâr (+%{int(kar_orani)})": is_kar,
            "Y. Maliyet (KDV'siz)": is_kdvsiz,
            f"KDV (+%{int(kdv_orani)})": is_kdv,
            "Genel Toplam (KDV'li)": is_kdvli
        })

    # --- EKRAN ÇIKTILARI ---
    df_ozet = pd.DataFrame(ozet_veriler)
    df_detay = pd.DataFrame(tum_kalemler)

    st.subheader("💰 İş Bazlı Özet Tablo")
    st.dataframe(df_ozet.style.format(formatter={col: "{:,.2f} ₺" for col in df_ozet.columns if "TL" in col or "%" in col or "Maliyet" in col or "Toplam" in col}), use_container_width=True, hide_index=True)

    genel_kdv_siz = excel_yuvarla(df_ozet["Y. Maliyet (KDV'siz)"].sum(), 2)
    genel_kdv_li = excel_yuvarla(df_ozet["Genel Toplam (KDV'li)"].sum(), 2)
    
    col1, col2 = st.columns(2)
    col1.metric("TÜM İŞLER TOPLAMI (KDV'SİZ)", f"{genel_kdv_siz:,.2f} TL")
    col2.metric("TÜM İŞLER TOPLAMI (KDV'Lİ)", f"{genel_kdv_li:,.2f} TL")

    # --- EXCEL OLUŞTURMA ---
    st.markdown("---")
    st.subheader("📄 Gelişmiş Excel Çıktısı")
    st.write("Bu Excel dosyası iki sayfadan oluşur: İlk sayfa tüm işlerin özetini, ikinci sayfa ise her işin satır satır kalem hesaplarını içerir.")
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # 1. Sayfa: Özet
        df_ozet.to_excel(writer, index=False, sheet_name='Is_Ozetleri')
        ws_ozet = writer.sheets['Is_Ozetleri']
        for i in range(1, 7): ws_ozet.column_dimensions[chr(64+i)].width = 20
        
        # 2. Sayfa: Kalem Detayları
        df_detay.to_excel(writer, index=False, sheet_name='Kalem_Detaylari')
        ws_detay = writer.sheets['Kalem_Detaylari']
        ws_detay.column_dimensions['A'].width = 20
        ws_detay.column_dimensions['C'].width = 50
        ws_detay.column_dimensions['F'].width = 15
        ws_detay.column_dimensions['G'].width = 20

    st.download_button(
        label="📥 Detaylı ve Çoklu Excel Raporunu İndir",
        data=buffer.getvalue(),
        file_name=f"AYAP_Coklu_Maliyet_{'Iyilestirme' if 'İyileştirme' in is_senaryosu else 'Olusturma'}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
