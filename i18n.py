"""Basit arayuz cevirisi (Turkce / Ingilizce)."""
import config

STR = {
    "tr": {
        "app_name": "Sesli Dikte",
        "menu_hotkey": "Bas-konus: {key}",
        "menu_settings": "Ayarlar...",
        "menu_autopaste": "Otomatik yapistir",
        "menu_autoenter": "Otomatik Enter",
        "menu_quit": "Cikis",
        "set_title": "Sesli Dikte - Ayarlar",
        "lbl_key": "Deepgram API anahtari:",
        "chk_show": "Goster",
        "lbl_hotkey": "Bas-konus tusu:",
        "btn_capture": "Tusa bas, yakala",
        "btn_capturing": "Bir tusa bas...",
        "lbl_spoken": "Konusulan dil:",
        "lbl_ui": "Arayuz dili:",
        "opt_auto": "auto (algila)",
        "chk_paste": "Otomatik yapistir (Ctrl+V)",
        "chk_enter": "Yapistirinca Enter'a bas",
        "chk_autostart": "Windows acilisinda baslat",
        "chk_overlay": "Kayit gostergesini goster",
        "lbl_overlay_pos": "Gosterge konumu:",
        "pos_tr": "Sag ust", "pos_tl": "Sol ust", "pos_br": "Sag alt", "pos_bl": "Sol alt",
        "ov_processing": "Yaziliyor",
        "btn_apply": "Uygula",
        "btn_saveclose": "Kaydet ve Kapat",
        "msg_saved": "Kaydedildi.",
        "note_restart": "Arayuz dili degisikligi menuye hemen, acik pencereye sonraki acilista yansir.",
    },
    "en": {
        "app_name": "Voice Dictation",
        "menu_hotkey": "Push-to-talk: {key}",
        "menu_settings": "Settings...",
        "menu_autopaste": "Auto-paste",
        "menu_autoenter": "Auto-Enter",
        "menu_quit": "Quit",
        "set_title": "Voice Dictation - Settings",
        "lbl_key": "Deepgram API key:",
        "chk_show": "Show",
        "lbl_hotkey": "Push-to-talk key:",
        "btn_capture": "Press a key to capture",
        "btn_capturing": "Press a key...",
        "lbl_spoken": "Spoken language:",
        "lbl_ui": "Interface language:",
        "opt_auto": "auto (detect)",
        "chk_paste": "Auto-paste (Ctrl+V)",
        "chk_enter": "Press Enter after paste",
        "chk_autostart": "Start with Windows",
        "chk_overlay": "Show recording indicator",
        "lbl_overlay_pos": "Indicator position:",
        "pos_tr": "Top-right", "pos_tl": "Top-left", "pos_br": "Bottom-right", "pos_bl": "Bottom-left",
        "ov_processing": "Transcribing",
        "btn_apply": "Apply",
        "btn_saveclose": "Save & Close",
        "msg_saved": "Saved.",
        "note_restart": "UI language applies to the menu immediately, to an open window on next open.",
    },
}


def t(str_key, ui=None, **kw):
    ui = (ui or getattr(config, "UI_LANGUAGE", "tr"))
    table = STR.get(ui, STR["en"])
    s = table.get(str_key) or STR["en"].get(str_key, str_key)
    return s.format(**kw) if kw else s
