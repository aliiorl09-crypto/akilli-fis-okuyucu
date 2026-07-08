import streamlit as st
import json
import pandas as pd
from google import genai
from google.genai import types
from PIL import Image
import io

# 1. Sayfa Tasarımı ve Ayarları
st.set_page_config(page_title="Yapay Zeka Fiş Okuyucu", page_icon="🧾", layout="centered")

st.title("🧾 Yapay Zeka Fiş Okuyucu")
st.write("Fişinizin fotoğrafını çekin veya yükleyin, yapay zeka saniyeler içinde kusursuz bir Excel tablosuna dönüştürsün!")

# 🔥 GÜVENLİK AYARI: API anahtarını koda yazmıyoruz, Streamlit bulutundan çekeceğiz:
API_KEY = st.secrets["GEMINI_API_KEY"]

yuklenen_dosya = st.file_uploader("Fiş Görseli Seçin veya Fotoğraf Çekin", type=["jpg", "jpeg", "png"])

if yuklenen_dosya is not None:
    resim = Image.open(yuklenen_dosya)
    st.image(resim, caption="Yüklenen Fiş Görseli", use_container_width=True)
    
    if st.button("Fişi Yapay Zeka ile Oku ✨", type="primary"):
        with st.spinner("Yapay zeka fişi satır satır inceliyor, lütfen bekleyin..."):
            try:
                client = genai.Client(api_key=API_KEY)
                
                prompt = """
                Bu fiş veya fatura görselini dikkatlice incele. 
                Aşağıdaki bilgileri hatasız bir şekilde tespit et. 
                Eğer resimde harf hatası veya silik çıkmış yerler varsa (örn: yapakredi -> Yapı Kredi) mantıksal olarak düzelt.
                
                Senden sadece ve sadece şu şablona uygun bir JSON objesi istiyorum, başka hiçbir açıklama veya markdown kodu yazma:
                {
                    "Firma_Ismi": "Tespit edilen temiz firma adı",
                    "Vergi_No": "10 haneli vergi numarası veya VKN",
                    "Tarih": "GG.AA.YYYY formatında tarih",
                    "Fis_No": "Fiş numarası",
                    "KDV_Orani": "Sadece rakam olarak genel KDV oranı (örn: 20)",
                    "KDV_Tutari": "KDV tutarı formatı (örn: 15.50)",
                    "Toplam_Tutar": "Toplam ödenecek tutar formatı (örn: 120.00)"
                }
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[resim, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                
                veri_json = json.loads(response.text)
                
                tablo_verisi = {
                    "Firma İsmi": [veri_json.get("Firma_Ismi", "Bulunamadı")],
                    "Vergi No / VD": [veri_json.get("Vergi_No", "Bulunamadı")],
                    "Tarih": [veri_json.get("Tarih", "Bulunamadı")],
                    "Fiş No": [veri_json.get("Fis_No", "Bulunamadı")],
                    "KDV Oranı (%)": [veri_json.get("KDV_Orani", "Bulunamadı")],
                    "KDV Tutarı": [veri_json.get("KDV_Tutari", "Bulunamadı")],
                    "Toplam Tutar": [veri_json.get("Toplam_Tutar", "Bulunamadı")]
                }
                df = pd.DataFrame(tablo_verisi)
                
                st.success("Fiş başarıyla okundu! 🎉")
                st.dataframe(df, hide_index=True)
                
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Fiş Verisi')
                excel_data = excel_buffer.getvalue()
                
                st.download_button(
                    label="📥 Excel Dosyasını İndir",
                    data=excel_data,
                    file_name="akilli_fis_verileri.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")