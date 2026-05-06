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
st.set_page_config(page_title="AYAP Maliyet Hesaplama", layout="wide")

# --- ANA EKRAN BAŞLIK VE UYARI ---
st.title("📊 AYAP Kalem Kalem Maliyet Hesaplama Aracı")

st.warning("""
🚨 **LÜTFEN DİKKAT - İŞLEME BAŞLAMADAN ÖNCE KONTROL EDİNİZ:**
1. Sol menüden **Mesh Üretimli** ya da **Mesh Üretimsiz** fiyat seçimini doğru yaptığınızdan emin olun.
2. Hesaplamanın doğru yapılabilmesi için sol menüdeki **Güncel Ay Endeksinin** çalışmanıza uygun ayı gösterdiğini teyit ediniz.
""", icon="⚠️")

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
st.markdown("### 🛠️ İş Türü (Senaryo) Seçimi")
is_senaryosu = st.radio("Hangi tür iş hesaplanacak?", ("🔧 İyileştirme İşi (Kontrol ve Revizyon)", "🏗️ Oluşturma İşi (Sıfırdan Üretim)"), horizontal=True)
st.markdown("---")

tum_kalemler = []
is_ciplak_toplam = 0.0

# --- TEKLİ İŞ VERİ GİRİŞİ VE HESAPLAMA MOTORU ---
if "İyileştirme" in is_senaryosu:
    st.subheader("📋 İyileştirme İşi Miktarları")
    col1, col2, col3 = st.columns(3)
    pafta_sayisi = col1.number_input("Pafta Sayısı", min_value=0, value=7280)
    toplam_bina = col2.number_input("Toplam Kontrol Edilecek Bina", min_value=0, value=172639)
    sifir_bina = col3.number_input("Sıfırdan Üretilecek Bina", min_value=0, value=55126)
    eski_bina = toplam_bina - sifir_bina
    
    st.info(f"ℹ️ **Eski Model Bina Sayısı (Otomatik):** {int(eski_bina)}")
    
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
    st.subheader("📋 Oluşturma İşi Miktarları")
    col1, col2 = st.columns(2)
    pafta_sayisi = col1.number_input("Pafta Sayısı", min_value=0, value=7280)
    toplam_bina = col2.number_input("Toplam Bina Sayısı", min_value=0, value=172639)
    
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
        "Sıra No": k["Sıra"], 
        "İş Kalemi Açıklaması": k["Ad"], 
        "Birim": "Adet", 
        "Miktar": int(k["Mik"]), 
        "Birim Fiyat (TL)": bf, 
        "Toplam Tutar (TL)": toplam_tutar
    })

# --- EKRAN ÇIKTILARI ---
if len(tum_kalemler) > 0:
    df_detay = pd.DataFrame(tum_kalemler)
    
    st.markdown("---")
    st.subheader("💰 Kalem Kalem Yaklaşık Maliyet Tablosu")
    st.dataframe(df_detay.style.format({"Birim Fiyat (TL)": "{:,.3f} ₺", "Toplam Tutar (TL)": "{:,.2f} ₺"}), use_container_width=True, hide_index=True)

    is_ciplak = excel_yuvarla(is_ciplak_toplam, 2)
    is_kar = excel_yuvarla(is_ciplak * (kar_orani / 100), 2)
    is_kdvsiz = excel_yuvarla(is_ciplak + is_kar, 2)
    is_kdv = excel_yuvarla(is_kdvsiz * (kdv_orani / 100), 2)
    is_kdvli = excel_yuvarla(is_kdvsiz + is_kdv, 2)
    
    st.markdown("### 🧾 Maliyet Özet Paneli")
    col1, col2, col3 = st.columns(3)
    col1.metric("ÇIPLAK MALİYET (KÂRSIZ)", f"{is_ciplak:,.2f} TL")
    col2.metric(f"YÜKLENİCİ KÂRI (+%{int(kar_orani)})", f"{is_kar:,.2f} TL")
    col3.metric("Y. MALİYET (KDV HARİÇ)", f"{is_kdvsiz:,.2f} TL")

    # --- EXCEL OLUŞTURMA ---
    st.markdown("---")
    st.subheader("📄 Excel Çıktısı Al")
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_detay.to_excel(writer, index=False, sheet_name='Kalem_Detaylari')
        ws_detay = writer.sheets['Kalem_Detaylari']
        ws_detay.column_dimensions['B'].width = 60
        ws_detay.column_dimensions['E'].width = 15
        ws_detay.column_dimensions['F'].width = 20
        
        # Alt toplamları Excel'e yazdırma
        son_satir = len(df_detay) + 2
        ws_detay.cell(row=son_satir+1, column=5, value="Çıplak Maliyet:")
        ws_detay.cell(row=son_satir+1, column=6, value=is_ciplak)
        ws_detay.cell(row=son_satir+2, column=5, value=f"Yüklenici Kârı (%{int(kar_orani)}):")
        ws_detay.cell(row=son_satir+2, column=6, value=is_kar)
        ws_detay.cell(row=son_satir+3, column=5, value="NİHAİ MALİYET (KDV'siz):")
        ws_detay.cell(row=son_satir+3, column=6, value=is_kdvsiz)

    st.download_button(
        label="📥 Tabloyu Excel Olarak İndir",
        data=buffer.getvalue(),
        file_name=f"Kalem_Maliyet_{'Iyilestirme' if 'İyileştirme' in is_senaryosu else 'Olusturma'}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
