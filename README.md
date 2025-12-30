# isthisai-bot

X (Twitter) üzerinde `@isthisai` etiketlendiğinde, paylaşılan görsel veya videoyu analiz edip AI ile üretilmiş olma ihtimalini değerlendiren bir bot.

## Ne Yapıyor?

Bot şu adımları takip ediyor:
1. X'te `@isthisai` etiketlendiğinde tetikleniyor
2. İlgili görsel/videoyu indiriyor
3. AI üretimi olup olmadığını analiz ediyor (şu an heuristic bazlı, ML modeli eklenebilir)
4. Sonucu tweet olarak yanıtlıyor

**Not:** AI tespiti zor bir problem. Şu anki detector basit heuristikler kullanıyor (watermark tespiti, texture analizi vb.). Daha iyi sonuçlar için gerçek bir ML modeli eklenebilir.

## Mimari

- **FastAPI**: İş kuyruğuna ekleme ve durum sorgulama için REST API
- **Redis**: Job queue ve cache (aynı medya tekrar analiz edilmez)
- **RQ Worker**: Kuyruktan işleri alıp medya analizini yapan worker'lar
- **Medya Pipeline**:
  - Görsel: normalize et → feature çıkar → skorla
  - Video: indir → ffmpeg ile frame'leri çıkar → her frame'i analiz et → sonuçları birleştir

## Kurulum

### Docker ile (Önerilen)

1. `.env` dosyası oluştur:

```bash
# Redis
REDIS_URL=redis://redis:6379/0

# X API credentials (kendi bilgilerinizi girin)
X_BEARER_TOKEN=...
X_CONSUMER_KEY=...
X_CONSUMER_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...

# Bot ayarları
BOT_USERNAME=isthisai
BOT_HANDLE=@isthisai

# Davranış ayarları
MAX_VIDEO_SECONDS=60
MAX_VIDEO_FRAMES=30
FRAME_FPS=1
REPLY_COOLDOWN_SECONDS=60
```

2. Çalıştır:

```bash
docker compose up --build
```

- API: http://localhost:8000
- Redis: localhost:6379

3. Test için iş ekle:

```bash
curl -X POST http://localhost:8000/enqueue \
  -H "Content-Type: application/json" \
  -d '{
    "tweet_id": "123",
    "author_id": "456",
    "media_url": "https://example.com/image.jpg",
    "media_type": "image",
    "reply_to_tweet_id": "123"
  }'
```

### Docker Olmadan

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export REDIS_URL=redis://localhost:6379/0

# API'yi başlat
uvicorn app.main:app --reload

# Başka bir terminalde worker'ı başlat
python scripts/worker.py
```

**Not:** Video analizi için `ffmpeg` kurulu olmalı.

## Detector Ekleme

Daha iyi bir detector eklemek için:

1. `app/detectors/base.py` içindeki `Detector` interface'ini implement et
2. `app/detectors/__init__.py` içinde kaydet

Örnekler:
- ONNX veya PyTorch modeli
- Ücretli bir API (API key'leri server-side tut)
- Ensemble (birden fazla detector'ı birleştir)

## X Entegrasyonu

X API entegrasyonu için `scripts/poll_mentions.py` dosyasına bak. Şu an placeholder, gerçek API çağrılarını eklemen gerekiyor.

Genel akış:
1. X API'den mention'ları çek (polling veya webhook)
2. Her mention için:
   - Hedef tweet'i bul (orijinal/quoted/replied)
   - Medya URL'lerini çıkar
   - Her medya için `/enqueue` endpoint'ine POST at

## Test

Test görselleri için:

```bash
# test_images/ klasörüne example1.jpg ve example2.jpg ekle
python scripts/test_images.py
```

## Lisans

MIT
