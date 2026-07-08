import streamlit as st
import json
import pandas as pd
from google import genai
from google.genai import types
from PIL import Image
import io
import time  # Google hız limitine takılmamak için

# 1. Sayfa Tasarımı ve Başlık
st.set_page_config(page_title="Yapay Zeka Fiş Okuyucu", page_icon="🧾", layout="centered")

st.title("🧾 Akıllı Fiş Okuma Sistemi")
st.write("Fişlerinizin fotoğrafını çekin veya yükleyin, yapay zeka saniyeler içinde kusursuz bir Excel tablosuna dönüştürsün!")
st.info("Birden fazla fiş fotoğrafı yükleyebilirsiniz. Yapay zeka hepsini tek bir tabloda birleştirecektir.")

# 2. API Anahtarı (Streamlit Secrets'tan çekilir)
API_KEY = st.secrets["GEMINI_API_KEY"]

# 3. Çoklu Dosya Yükleme Alanı
yuklanan_dosyalar = st.file_uploader("Fiş Görsellerini Seçin veya Çekin", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if yuklanan_dosyalar:
    st.write(f"📂 {len(yuklanan_dosyalar)} adet dosya seçildi.")
    
    if st.button("Tüm Fişleri Toplu Oku ✨", type="primary"):
        client = genai.Client(api_key=API_KEY)
        toplam_liste = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for index, dosya in enumerate(yuklanan_dosyalar):
            try:
                resim = Image.open(dosya)
                status_text.text(f"🔍 İşleniyor: {dosya.name} ({index+1}/{len(yuklanan_dosyalar)})")
                
                prompt = """
                Bu görsel bir fiş veya faturadır. Bilgileri tespit et ve düzelt.
                Sadece şu JSON şablonunu döndür:
                {
                    "Firma_Ismi": "Temiz ad",
                    "Vergi_No": "VKN",
                    "Tarih": "GG.AA.YYYY",
                    "Fis_No": "No",
                    "KDV_Orani": "Rakam",
                    "KDV_Tutari": "Tutar",
                    "Toplam_Tutar": "Tutar"
                }
                """
                
                # Kota sorunu olmayan gemini-2.5-flash modeli
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[resim, prompt],
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                
                veri_json = json.loads(response.text)
                
                toplam_liste.append({
                    "Dosya Adı": dosya.name,
                    "Firma İsmi": veri_json.get("Firma_Ismi", "-"),
                    "Vergi No": veri_json.get("Vergi_No", "-"),
                    "Tarih": veri_json.get("Tarih", "-"),
                    "Fiş No": veri_json.get("Fis_No", "-"),
                    "KDV Oranı (%)": veri_json.get("KDV_Orani", "-"),
                    "KDV Tutarı": veri_json.get("KDV_Tutari", "-"),
                    "Toplam Tutar": veri_json.get("Toplam_Tutar", "-")
                })
                
                progress_bar.progress((index + 1) / len(yuklanan_dosyalar))
                
                # Ücretsiz kotada peş peşe hızlı istek atınca hata vermemesi için 3 saniye bekleme süresi
                if index < len(yuklanan_dosyalar) - 1:
                    time.sleep(3)
                    
            except Exception as e:
                st.error(f"❌ {dosya.name} okunurken hata oluştu: {e}")

        if toplam_liste:
            status_text.success(f"✅ {len(toplam_liste)} fiş başarıyla okundu!")
            df = pd.DataFrame(toplam_liste)
            
            st.subheader("📊 Toplu Sonuç Tablosu")
            st.dataframe(df, hide_index=True)
            
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Toplu Fiş Verisi')
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📥 Toplu Excel Dosyasını İndir",
                data=excel_data,
                file_name="toplu_fis_verileri.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
