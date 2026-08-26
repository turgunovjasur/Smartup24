"""Telegram bot orqali testlarni masofadan ishga tushirish/to'xtatish.

Bu ALOHIDA doimiy ishlab turadigan jarayon (conftest emas). Ishga tushiring:

    python tg_bot_runner.py

Keyin bot bilan Telegram'da yozishmadan boshqaring:
    start   — test_all_runner ni ishga tushiradi (agar ishlamayotgan bo'lsa)
    stop    — ishlab turgan testlarni (brauzerlari bilan) to'xtatadi
    status  — hozir test ishlayaptimi yoki yo'qligini aytadi
    help    — buyruqlar ro'yxati

Slash bilan ham bo'ladi: /start /stop /status.

SOZLAMA (.env):
    TG_BOT_TOKEN     — bot tokeni (BotFather)
    TG_CHAT_ID       — bildirishnoma boradigan chat (guruh/kanal/DM)
    TG_ADMIN_CHAT_ID — (ixtiyoriy) buyruq yuborishga RUXSAT etilgan chat.
                       Berilmasa TG_CHAT_ID ishlatiladi. Guruhga xabar yozib,
                       o'zingiz bilan DM'dan boshqarmoqchi bo'lsangiz — bu yerga
                       DM chat_id ni yozing.

XAVFSIZLIK: faqat ruxsat etilgan chat_id dan kelgan buyruqlar bajariladi.
Boshqalarnikini jim e'tiborsiz qoldiradi.
"""
from __future__ import annotations

import os
import sys
import time
import signal
import subprocess

import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")
# Buyruq yuborishga ruxsat etilgan chat(lar). Vergul bilan bir nechta bo'lishi mumkin.
_ADMIN = os.getenv("TG_ADMIN_CHAT_ID") or CHAT_ID
ALLOWED_CHATS = {c.strip() for c in (_ADMIN or "").split(",") if c.strip()}

API = f"https://api.telegram.org/bot{BOT_TOKEN}"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Ishga tushiriladigan test buyrug'i. TEST_CMD env bilan almashtirsa bo'ladi.
DEFAULT_TEST_ARGS = [
    "-m", "pytest", "tests/test_all_runner.py", "-v",
    "--alluredir=test-results/allure-results",
]

# Ishlab turgan test jarayoni (bir vaqtda faqat bitta)
_proc: subprocess.Popen | None = None


# ----------------------------------------------------------------------------------------------------------------------

def _send(text: str, chat_id: str | None = None) -> None:
    """Telegram'ga xabar yuboradi (javob uchun)."""
    if not BOT_TOKEN:
        return
    try:
        requests.post(
            f"{API}/sendMessage",
            data={"chat_id": chat_id or CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception as e:
        print(f"[bot] send xato: {e}")


def _is_running() -> bool:
    """Test jarayoni hozir ishlab turibdimi (tugagan bo'lsa holatni tozalaydi)."""
    global _proc
    if _proc is None:
        return False
    if _proc.poll() is not None:  # tugagan
        _proc = None
        return False
    return True


def _start_tests(chat_id: str) -> None:
    """Testlarni yangi subprocess'da ishga tushiradi."""
    global _proc
    if _is_running():
        _send("⚠️ Testlar allaqachon ishlab turibdi. Avval <b>stop</b> qiling.", chat_id)
        return

    args = os.getenv("TEST_CMD")
    cmd = [sys.executable] + (args.split() if args else DEFAULT_TEST_ARGS)

    env = os.environ.copy()
    # Bot fon rejimida ishlagani uchun allure brauzerini OCHMAYMIZ (osilib qolmasin) —
    # conftest _finish_allure_report shu env'ni tekshiradi. Natijalar baribir yoziladi.
    env["NO_ALLURE_SERVE"] = "1"

    # CREATE_NEW_PROCESS_GROUP: keyin butun daraxtni (pytest + playwright brauzerlari)
    # taskkill /T bilan o'chirish uchun alohida guruh.
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    try:
        _proc = subprocess.Popen(
            cmd, cwd=PROJECT_DIR, env=env, creationflags=creationflags,
        )
    except Exception as e:
        _send(f"❌ Ishga tushirib bo'lmadi: {e}", chat_id)
        return
    _send(
        "\U0001F680 <b>Testlar ishga tushdi.</b>\n"
        "Progress alohida xabar bo'lib yangilanib turadi. To'xtatish: <b>stop</b>",
        chat_id,
    )


def _stop_tests(chat_id: str) -> None:
    """Ishlab turgan test jarayonini (brauzerlari bilan birga) to'xtatadi."""
    global _proc
    if not _is_running():
        _send("ℹ️ Hozir ishlab turgan test yo'q.", chat_id)
        return
    pid = _proc.pid
    try:
        if os.name == "nt":
            # /T — butun daraxt (pytest + chromium jarayonlari), /F — majburiy
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True, timeout=30,
            )
        else:
            _proc.send_signal(signal.SIGTERM)
            try:
                _proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                _proc.kill()
    except Exception as e:
        _send(f"❌ To'xtatishda xato: {e}", chat_id)
        return
    finally:
        _proc = None
    _send("\U0001F6D1 <b>Testlar to'xtatildi.</b>", chat_id)


def _status(chat_id: str) -> None:
    if _is_running():
        _send("\U0001F7E2 Testlar hozir <b>ishlab turibdi</b>.", chat_id)
    else:
        _send("⚪ Hozir test ishlamayapti. Boshlash: <b>start</b>", chat_id)


HELP = (
    "\U0001F916 <b>Smartup24 test bot</b>\n"
    "<b>start</b> — testlarni ishga tushirish\n"
    "<b>stop</b> — ishlab turgan testlarni to'xtatish\n"
    "<b>status</b> — holatni ko'rish\n"
    "<b>help</b> — shu ro'yxat"
)


def _handle(text: str, chat_id: str) -> None:
    """Bitta buyruqni bajaradi (matn kichik harfga keltirilgan)."""
    cmd = text.strip().lstrip("/").split("@")[0].lower()  # "/start@bot" -> "start"
    if cmd == "start":
        _start_tests(chat_id)
    elif cmd == "stop":
        _stop_tests(chat_id)
    elif cmd == "status":
        _status(chat_id)
    elif cmd in ("help", "commands"):
        _send(HELP, chat_id)
    # boshqa matnlarga javob bermaymiz (shovqin bo'lmasin)


# ----------------------------------------------------------------------------------------------------------------------

def main() -> None:
    if not BOT_TOKEN or not ALLOWED_CHATS:
        print("XATO: .env da TG_BOT_TOKEN va TG_CHAT_ID (yoki TG_ADMIN_CHAT_ID) bo'lishi shart.")
        sys.exit(1)

    print(f"[bot] ishga tushdi. Ruxsat etilgan chat(lar): {ALLOWED_CHATS}")
    print("[bot] Telegram'da 'start' / 'stop' / 'status' yozing. To'xtatish: Ctrl+C")

    # Boshlanishida eski (kutib qolgan) xabarlarni tashlab yuboramiz — bot yopiq
    # turgan paytdagi 'stop' kabi buyruqlar qayta ishlamasin.
    offset = None
    try:
        r = requests.get(f"{API}/getUpdates", params={"timeout": 0}, timeout=15).json()
        if r.get("result"):
            offset = r["result"][-1]["update_id"] + 1
    except Exception as e:
        print(f"[bot] boshlang'ich getUpdates xato: {e}")

    while True:
        try:
            resp = requests.get(
                f"{API}/getUpdates",
                params={"timeout": 30, "offset": offset},
                timeout=40,
            ).json()
        except Exception as e:
            print(f"[bot] getUpdates xato (qayta urinamiz): {e}")
            time.sleep(3)
            continue

        for upd in resp.get("result", []):
            offset = upd["update_id"] + 1
            msg = upd.get("message") or upd.get("edited_message")
            if not msg:
                continue
            chat_id = str(msg.get("chat", {}).get("id"))
            text = msg.get("text", "") or ""
            if chat_id not in ALLOWED_CHATS:
                print(f"[bot] ruxsatsiz chat {chat_id} e'tiborsiz: {text!r}")
                continue
            print(f"[bot] buyruq {chat_id}: {text!r}")
            _handle(text, chat_id)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[bot] to'xtatildi (Ctrl+C).")
