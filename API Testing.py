import google.generativeai as genai
import PIL.Image
import re
import config

# BURAYA KENDİ API ANAHTARINIZI GİRİN
# ÖNEMLİ: Bu anahtarı kimseyle paylaşmayın!
GOOGLE_API_KEY = config.Google_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)

# Hata ayıklama ve model yapılandırması
generation_config = {
  "temperature": 0.1, # Daha kesin ve "sıkıcı" cevaplar için düşük sıcaklık
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}

# Gemini 2.5 Flash modelini kullanalım (hızlı ve yetenekli)
model = genai.GenerativeModel(model_name="gemini-2.5-flash",
                              generation_config=generation_config)

# 1. Girdi olarak bir Sudoku resmi yükle [cite: 9]
try:
    img = PIL.Image.open('sudoku1.png')
except FileNotFoundError:
    print("HATA: 'Sudoku1.png' dosyası bulunamadı.")
    print("Lütfen resim dosyasının kodla aynı klasörde olduğundan emin olun.")
    exit()


# 2. API için istem (prompt) oluşturma
# API'ye tam olarak ne yapmasını istediğimizi söylüyoruz.
prompt_metni = """
Bu görüntüdeki Sudoku bulmacasını analiz et.
Görevin, bu ızgarayı bir 9x9 matrise dönüştürmek.
- Boş hücreler için 0 rakamını kullan.
- Dolu hücreler için gördüğün rakamı kullan.
- Çıktı olarak SADECE 9 satırlık rakam dizisi ver.
- Rakamların arasında virgül olsun.
- Başka hiçbir açıklama, yorum veya giriş cümlesi yazma.

Örnek Çıktı Formatı:
0,0,3,0,2,0,6,0,0
9,0,0,3,0,5,0,0,1
0,0,1,8,0,6,4,0,0
0,0,8,1,0,2,9,0,0
7,0,0,0,0,0,0,0,8
0,0,6,7,0,8,2,0,0
0,0,2,6,0,9,5,0,0
8,0,0,2,0,3,0,0,9
0,0,5,0,1,0,3,0,0
"""

# 3. API'ye hem metin istemini hem de resmi gönder
print("Sudoku resmi API'ye gönderiliyor, lütfen bekleyin...")
response = model.generate_content([prompt_metni, img])

# 4. API'den gelen metin yanıtını işleme
try:
    api_cevabi = response.text
    print("\n--- API'den Gelen Ham Metin ---")
    print(api_cevabi)
    print("---------------------------------")

    # Gelen metni 9x9 matrise (Python listesi) dönüştürme 
    sudoku_matrisi = []
    
    # Metni satırlara ayır
    satirlar = api_cevabi.strip().split('\n')
    
    if len(satirlar) != 9:
        print(f"HATA: API 9 satır döndürmedi. Dönen satır: {len(satirlar)}")
        print("Lütfen prompt'u veya resmi kontrol edin.")
        exit()

    for satir_str in satirlar:
        # Satırdaki sayıları ayır (virgüle göre)
        hucreler = satir_str.split(',')
        
        # Her bir hücreyi integer'a (tam sayıya) çevir
        satir_listesi = [int(re.sub(r'\D', '', hucre)) for hucre in hucreler if hucre.strip().isdigit()]
        
        if len(satir_listesi) != 9:
            print(f"HATA: Bir satırda 9 hücre bulunamadı. Bulunan: {len(satir_listesi)}")
            print(f"Sorunlu satır: {satir_str}")
            continue

        sudoku_matrisi.append(satir_listesi)

    # 5. Sonucu (9x9 matrisi) ekrana yazdırma
    print("\n=== Başarıyla Oluşturulan 9x9 Matris ===")
    for row in sudoku_matrisi:
        print(row)

except Exception as e:
    print(f"\nBir hata oluştu: {e}")
    print("\nAPI'den gelen yanıt işlenemedi. API yanıtının tamamı:")
    print(response.text)