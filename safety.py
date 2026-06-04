"""Turkce onay/ret tespiti. Belirsizse GUVENLI tarafta kal (fail-closed)."""
import re
import unicodedata

_APPROVE = {
    "evet", "tamam", "tamamdir", "olur", "onayla", "onayliyorum", "yap",
    "devam", "devam et", "kabul", "peki", "hadi", "basla", "ok", "okey",
    "tabii", "tabi", "elbette", "yapabilirsin", "yap bunu",
}
_REJECT = {
    "hayir", "iptal", "iptal et", "dur", "durdur", "vazgec", "vazgectim",
    "yapma", "istemiyorum", "olmaz", "yok", "bosver", "bos ver", "gerek yok",
}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    # Turkce karakterleri sadelestir (ascii'ye yaklastir)
    text = (text.replace("ı", "i").replace("ş", "s").replace("ğ", "g")
                .replace("ü", "u").replace("ö", "o").replace("ç", "c"))
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# Yikici / geri alinamaz niyet iceren Turkce kokler (normalize edilmis: ascii).
# Eslesme kelime basindan yapilir (\b...) ki yanlis pozitif azalsin.
_RISK_PATTERNS = [
    r"\bsil",            # sil, silecek, silmek, sildim...
    r"\bkaldir",         # kaldir (uninstall/kaldirma)
    r"\bformat",         # format, formatla
    r"\bbicimlendir",    # bicimlendir
    r"\bgonder",         # gonder (mail/mesaj)
    r"\byolla",          # yolla
    r"\bpaylas",         # paylas (gonderme benzeri)
    r"\bsatin",          # satin al
    r"\bsipari",         # siparis ver
    r"\bsatinal",
    r"\bodeme",          # odeme yap
    r"\bode\b",          # ode
    r"\bsifirla",        # sifirla (reset)
    r"\btemizle",        # temizle (cache, gecmis)
    r"\bbosalt",         # geri donusum kutusu bosalt
    r"\buzerine yaz",    # ustune yaz
    r"\bbilgisayari kapat",
    r"\boturumu kapat",
    r"\byeniden baslat",
    r"\bkapat",          # uygulama/pencere kapatma (kaydedilmemis is riski)
]


# Yikici / geri alinamaz PowerShell komut kaliplari (komut metni uzerinde).
_DANGEROUS_CMD = [
    r"\bremove-item\b", r"\brmdir\b", r"\brd\b", r"\bdel\b", r"\berase\b",
    r"\bri\b\s", r"\brm\b", r"\bunlink\b",
    r"\bformat-volume\b", r"\bformat\b", r"\bclear-disk\b", r"\bdiskpart\b",
    r"\bclear-content\b", r"\bset-content\b.*>",
    r"\bstop-computer\b", r"\brestart-computer\b", r"\bshutdown\b",
    r"\bstop-process\b", r"\btaskkill\b", r"\bkill\b",
    r"\bset-executionpolicy\b",
    r"\bremove-itemproperty\b", r"\bremove-item\w*\b",
    r"\buninstall-\w+\b",
    r"-recurse\b.*-force\b", r"-force\b.*-recurse\b",
    r"\bgit\b.*\breset\b.*--hard", r"\bgit\b.*\bpush\b.*--force", r"\bgit\b.*\bclean\b.*-[a-z]*f",
    r"\bnpm\b.*\bunpublish\b",
    r"\bcmd\b.*\b/c\b.*\bdel\b",
    r">\s*['\"]?[a-z]:[\\/]",  # bir dosya yoluna uzerine yazma (> C:\...); >$null degil
]


def dangerous_command(cmd: str) -> bool:
    """PowerShell komutu yikici/geri alinamaz bir desen iceriyor mu?"""
    if not cmd:
        return False
    low = cmd.lower()
    return any(re.search(p, low) for p in _DANGEROUS_CMD)


def is_risky(text: str) -> bool:
    """Komut yikici/geri alinamaz bir niyet iceriyor mu? (onay gerektirir)"""
    if not text:
        return False
    norm = _normalize(text)
    return any(re.search(p, norm) for p in _RISK_PATTERNS)


def is_approval(text: str) -> bool:
    """Onay mi? Belirsiz/bos => False (fail-closed)."""
    if not text:
        return False
    norm = _normalize(text)
    if not norm:
        return False
    words = set(norm.split())

    reject_hit = bool(words & _REJECT) or any(p in norm for p in _REJECT)
    approve_hit = bool(words & _APPROVE) or any(p in norm for p in _APPROVE)

    # Ret varsa her zaman ret (guvenli taraf)
    if reject_hit:
        return False
    if approve_hit:
        return True
    return False  # belirsiz => iptal
