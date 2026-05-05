# İş Bazlı Yaklaşık Maliyet Hesaplama Aracı 📊

Bu proje, mimari bina ve fotogrametrik pafta üretim maliyetlerini Yİ-ÜFE (Yurt İçi Üretici Fiyat Endeksi) değişim oranlarına göre güncelleyerek yaklaşık maliyet hesaplaması yapan dinamik bir web uygulamasıdır. Streamlit ve Pandas kullanılarak geliştirilmiştir.

## 🚀 Özellikler
- **Dinamik Endeks Güncelleme:** Belirlenen baz ayına (örneğin Şubat 2022) ait Yİ-ÜFE ile güncel Yİ-ÜFE arasındaki katsayıyı otomatik hesaplar.
- **Çoklu İş Girişi:** Aynı anda birden fazla il/ilçe veya paket bazlı iş kalemi eklenebilir. Bina ve pafta sayıları doğrudan arayüz üzerinden düzenlenebilir.
- **Otomatik Kâr ve KDV İlavesi:** Çıplak maliyet üzerinden girilen yüzdelere göre yüklenici kârı ve KDV oranlarını anlık olarak tutarlara yansıtır.
- **Excel Çıktısı Alma:** Oluşturulan tablo, formatlı bir Excel `.xlsx` dosyası olarak doğrudan bilgisayara indirilebilir.

## 💻 Kurulum ve Çalıştırma

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin:

1. Depoyu bilgisayarınıza klonlayın:
```bash
git clone [https://github.com/KULLANICI_ADINIZ/yaklasik-maliyet-hesaplama.git](https://github.com/KULLANICI_ADINIZ/yaklasik-maliyet-hesaplama.git)
cd yaklasik-maliyet-hesaplama