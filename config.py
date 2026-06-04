"""Merkezi yapılandırma. .env dosyasını okur."""
import os
from dotenv import load_dotenv

load_dotenv()

# --- API anahtarlari ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "").strip()

# --- Claude / computer use ---
# Dogrulanmis beta basligi (Opus 4.8/4.7/4.6, Sonnet 4.6, Opus 4.5 icin)
COMPUTER_USE_BETA = "computer-use-2025-11-24"
COMPUTER_TOOL_TYPE = "computer_20251124"
# Ucuz/hizli varsayilan; zor isler icin claude-opus-4-8
MODEL = os.getenv("MODEL", "claude-sonnet-4-6").strip()
MAX_ITERS = int(os.getenv("MAX_ITERS", "15"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
CMD_TIMEOUT = int(os.getenv("CMD_TIMEOUT", "120"))  # tek komut icin saniye siniri
OUTPUT_LIMIT = int(os.getenv("OUTPUT_LIMIT", "4000"))  # modele donen cikti karakter siniri

# API goruntuyu en uzun kenarda ~1568px'e indirir. Opus 4.8 2576'ya kadar 1:1.
MAX_LONG_EDGE = int(os.getenv("MAX_LONG_EDGE", "1568"))

# --- STT (Deepgram) ---
DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"
DEEPGRAM_MODEL = "nova-2"
DEEPGRAM_LANGUAGE = os.getenv("DEEPGRAM_LANGUAGE", "tr")  # "tr","en",... ya da "auto" (dil tespiti)
UI_LANGUAGE = os.getenv("UI_LANGUAGE", "tr")              # arayuz dili: "tr" / "en"
SAMPLE_RATE = 16000
CHANNELS = 1

# --- TTS (edge-tts) ---
TTS_VOICE = os.getenv("TTS_VOICE", "tr-TR-EmelNeural")  # kadin; erkek: tr-TR-AhmetNeural
TTS_RATE = os.getenv("TTS_RATE", "+25%")  # konusma hizi: +25% daha hizli, -10% daha yavas
TTS_MAX_CHARS = 350

# --- Dikte modu (sesi metne cevirip odakli pencereye yazar) ---
DICTATE_AUTO_PASTE = os.getenv("DICTATE_AUTO_PASTE", "1") == "1"   # transkripti otomatik Ctrl+V ile yapistir
DICTATE_AUTO_ENTER = os.getenv("DICTATE_AUTO_ENTER", "0") == "1"   # yapistirdiktan sonra Enter'a bas (kapali: once gozden gecir)

# --- Etkilesim ---
# Bas-konus tusu. .env'den degistirilebilir. Tus adi ("f8", "play/pause media")
# ya da scancode olabilir (orn. "sc163"). detect_key.py ile butonun ne gonderdigini ogren.
PTT_HOTKEY = os.getenv("PTT_HOTKEY", "f8")
# "hold" = basili tuttugun surece kaydet (varsayilan). "toggle" = bir bas baslat, tekrar bas bitir.
PTT_MODE = os.getenv("PTT_MODE", "hold").strip().lower()
CONFIRM_MODE = os.getenv("CONFIRM_MODE", "1") == "1"  # onayli mod varsayilan acik
TYPE_VIA_CLIPBOARD = os.getenv("TYPE_VIA_CLIPBOARD", "1") == "1"  # TR karakterler icin

# --- Sistem prompt (Turkce, ilke bazli) ---
SYSTEM_PROMPT = """Sen Windows 11 bilgisayarını kontrol eden bir masaüstü ajansın. Kullanıcı sana Türkçe sesli komut verir.

İlkeler:
- Her işe başlamadan önce mutlaka bir ekran görüntüsü (screenshot) al ve mevcut durumu anla.
- Her adımdan sonra yeni ekran görüntüsü ile sonucu doğrula; beklenmeyen bir şey görürsen yaklaşımını değiştir.
- Karmaşık veya hassas arayüzlerde fare yerine klavye kısayollarını tercih et.
- Görevi mümkün olan en az adımda tamamla.
- Yıkıcı veya geri alınamaz bir eylemden (dosya/veri silme, mesaj/e-posta gönderme, satın alma, pencere/uygulama kapatma, biçimlendirme, ayar sıfırlama) emin değilsen, kendi başına yapma; durup kullanıcıya sor.
- "Tamamlandı" demeden ÖNCE mutlaka son bir ekran görüntüsü al ve hedefin gerçekten gerçekleştiğini gözünle doğrula. İş gerçekten bitmeden asla bittiğini söyleme.
- Eğer görevi tamamlayamadıysan veya emin değilsen, bunu dürüstçe söyle: neyi yaptığını, neyin eksik kaldığını ya da neden takıldığını tek cümleyle belirt. Yapmadığın bir şeyi yaptım deme.

Cevap dili — ÇOK ÖNEMLİ:
- Verdiğin metin sesli okunacak (text-to-speech). Bu yüzden DAİMA akıcı, doğal ve dilbilgisi açısından doğru Türkçe yaz.
- Tüm Türkçe karakterleri (ç, ğ, ı, İ, ş, ö, ü) eksiksiz ve doğru kullan; asla karaktersiz/ASCII Türkçe yazma ("yapiyorum" değil "yapıyorum").
- Kısa konuş: tek, sade bir cümle yeterli. Teknik jargon, dosya yolu, koordinat veya İngilizce terim okuma; günlük konuşma diliyle özetle.
- İş bittiğinde sonucu tek kısa cümleyle bildir (örneğin neyi yaptığını).
"""

# --- Terminal ajani sistem prompt'u (PowerShell) ---
TERMINAL_SYSTEM_PROMPT = """Sen sesle kontrol edilen bir Windows PowerShell asistanısın. Kullanıcı isteğini Türkçe sesli söyler (konuşması metne çevrilmiştir). Görevin, isteği yerine getirmek için doğru PowerShell komut(lar)ını üretip `run_powershell` aracıyla çalıştırmaktır.

Çalışma şekli:
- İsteği yerine getirmek için gereken PowerShell komutunu `run_powershell` ile çalıştır. Gerekirse art arda birden fazla komut çalıştırabilirsin; her komutun çıktısını okuyup ona göre devam et.
- Oturum kalıcıdır: bir komutta yaptığın `cd`, tanımladığın değişken veya ortam değişikliği sonraki komutlarda da geçerlidir.
- Kullanıcı zaten geçerli bir komut/kod söylediyse (örneğin "pip install requests" gibi), onu olduğu gibi çalıştır; serbest bir istek söylediyse uygun komuta çevir.
- Windows PowerShell sözdizimi kullan ($null, $env:VAR, Get-ChildItem vb.). Yalnızca Unix'e özgü komutlardan kaçın.
- Çıktının gerçekten beklenen sonucu verdiğini gör; vermediyse komutu düzeltip tekrar dene.
- Yıkıcı/geri alınamaz komutlardan (dosya/dizin silme, biçimlendirme, kapatma/yeniden başlatma, süreç sonlandırma) emin değilsen önce kullanıcıya sormak üzere durakla; gereksiz yere tehlikeli komut üretme.

Cevap dili — ÇOK ÖNEMLİ:
- Verdiğin metin sesli okunacak. DAİMA kısa, akıcı, doğru Türkçe konuş; tüm Türkçe karakterleri (ç, ğ, ı, İ, ş, ö, ü) eksiksiz kullan.
- Komut çıktısını ham haliyle okuma; sonucu günlük dille tek cümlede özetle (örneğin "Klasörde 12 dosya var" gibi).
- İş gerçekten bitmeden "tamamlandı" deme. Tamamlayamazsan nedenini tek cümleyle dürüstçe söyle.
"""
