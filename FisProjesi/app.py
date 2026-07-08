import streamlit as st
import json
import pandas as pd
from google import genai
from google.genai import types
from PIL import Image
import io
import time

# 1. Sayfa Tasarımı ve Kurumsal Kimlik
st.set_page_config(page_title="Ostim Teknopark | Fiş Okuyucu", page_icon="🧾", layout="centered")

# Üst Bilgi: Logo ve Başlık Yan Yana
col1, col2 = st.columns([1, 4])
with col1:
    # Ostim Teknopark Logosu (İnternet adresi üzerinden çekiyoruz)
    st.image("https://www.ostimteknopark.com.tr/content/images/logo.png", width=120)
with col2:
    st.title("Akıllı Fiş Okuma Sistemi")
    st.caption("Ostim Teknopark Destekli Yapay Zeka Çözümü")

st.info("Birden fazla fiş fotoğrafı yükleyebilirsiniz. Yapay zeka hepsini tek bir tabloda birleştirecektir.")

# 2. API Anahtarı (Streamlit Secrets'tan çekilir)
API_KEY = st.secrets["GEMINI_API_KEY"]

# 3. Çoklu Dosya Yükleme Alanı (accept_multiple_files=True eklendi!)
yuklenen_dosyalar = st.file_uploader("Fiş Görsellerini Seçin veya Çekin", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if yuklenen_dosyalar:
    st.write(f"📂 {len(yuklenen_dosyalar)} adet dosya seçildi.")
    
    # Analiz Butonu
    if st.button("Tüm Fişleri Toplu Oku ✨", type="primary"):
        client = genai.Client(api_key=API_KEY)
        toplam_liste = []
        
        # İlerleme çubuğu ekleyelim
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for index, dosya in enumerate(yuklenen_dosyalar):
            try:
                resim = Image.open(dosya)
                
                # Her fiş için durum güncellemesi
                status_text.text(f"İşleniyor: {dosya.name} ({index+1}/{len(yuklenen_dosyalar)})")
                
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
                
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[resim, prompt],
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                
                veri_json = json.loads(response.text)
                
                # Listeye ekliyoruz
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
                
                # İlerleme çubuğunu güncelle
                progress_bar.progress((index + 1) / len(yuklenen_dosyalar))
                
            except Exception as e:
                st.error(f"{dosya.name} okunurken hata oluştu: {e}")

        # Tüm işlemler bittiğinde
        if toplam_liste:
            status_text.success(f"✅ {len(toplam_liste)} fiş başarıyla okundu!")
            df = pd.DataFrame(toplam_liste)
            
            # Tabloyu göster
            st.subheader("📊 Toplu Sonuç Tablosu")
            st.dataframe(df, hide_index=True)
            
            # Excel Hazırlama
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Toplu Fiş Verisi')
            excel_data = excel_buffer.getvalue()
            
            # İndirme Butonu
            st.download_button(
                label="📥 Toplu Excel Dosyasını İndir",
                data=excel_data,
                file_name="ostim_teknopark_toplu_fisler.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
