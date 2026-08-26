"""Telegram bot orqali testlarni masofadan ishga tushirish/to'xtatish.

Bu ALOHIDA doimiy ishlab turadigan jarayon (conftest emas). Ishga tushiring:

    python tg_bot_runner.py

Keyin bot bilan Telegram'da yozishmadan boshqaring:
    start [env] [bo'lim] — testlarni ishga tushiradi (agar ishlamayotgan bo'lsa).
                           env: dev|prod (default dev). bo'lim: all|setup|
                           regression|main|document (default all = hamma test
                           bitta login bilan; setup = setup + group_a).
    stop    — ishlab turgan testlarni (brauzerlari bilan) to'xtatadi
    status  — hozir test ishlayaptimi + qaysi muhit/bo'lim ekanini aytadi
    help    — buyruqlar ro'yxati

Slash bilan ham bo'ladi: /start_dev /start_prod /stop /status.

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
import json
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

# Bo'lim runnerlari — har biri o'z login bilan, bitta seansda ishlaydi.
# "all" hammasini BITTA pytest chaqiruvida (bitta login) ketma-ket ishlatadi:
# setup → group_a → regression → main → document (fayl tartibi saqlanadi).
_SETUP = "tests/test_setup/test_all_setup.py"
_GROUPA = "tests/test_group_a/test_all_group_a.py"
_REGRESSION = "tests/test_regression/test_all_regression.py"
_MAIN = "tests/test_main/test_all_main.py"
_DOCUMENT = "tests/test_document/test_all_document_runner.py"

TARGETS = {
    "all":        [_SETUP, _GROUPA, _REGRESSION, _MAIN, _DOCUMENT],
    "setup":      [_SETUP, _GROUPA],   # 2 soatlik juftlik (GitHub avtomat ham shu)
    "regression": [_REGRESSION],
    "main":       [_MAIN],
    "document":   [_DOCUMENT],
}
DEFAULT_TARGET = "all"

# Ishga tushiriladigan test buyrug'i. TEST_CMD env bilan to'liq almashtirsa bo'ladi
# (u berilsa target e'tiborsiz qoladi).
_PYTEST_TAIL = ["-v", "--alluredir=test-results/allure-results"]

# Bot orqali tanlanadigan muhitlar (flow_authorization.TEST_ENV bilan bir xil).
# "start prod" / "start dev" — TEST_ENV env var'i orqali test qaysi serverga
# tegishini belgilaydi. Berilmasa DEV (sm24) — avvalgi default.
ENV_LABELS = {"dev": "DEV (sm24)", "prod": "PROD (test)"}
DEFAULT_ENV = "dev"

# Ishlab turgan test jarayoni (bir vaqtda faqat bitta) + qaysi muhit/bo'lim ekani
_proc: subprocess.Popen | None = None
_run_env: str = DEFAULT_ENV
_run_target: str = DEFAULT_TARGET


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


def _start_tests(chat_id: str, run_env: str = DEFAULT_ENV, target: str = DEFAULT_TARGET) -> None:
    """Testlarni yangi subprocess'da ishga tushiradi (``run_env`` muhitida,
    ``target`` bo'limi bilan)."""
    global _proc, _run_env, _run_target
    if _is_running():
        _send(
            f"⚠️ Testlar allaqachon ishlab turibdi "
            f"({ENV_LABELS[_run_env]} / {_run_target}). Avval <b>stop</b> qiling.",
            chat_id,
        )
        return
    if run_env not in ENV_LABELS:
        _send(
            f"❌ Noma'lum muhit: <code>{run_env}</code>. "
            "Ruxsat: <b>start dev</b> yoki <b>start prod</b>.",
            chat_id,
        )
        return
    if target not in TARGETS:
        _send(
            f"❌ Noma'lum bo'lim: <code>{target}</code>. "
            f"Ruxsat: <b>{', '.join(TARGETS)}</b>.",
            chat_id,
        )
        return

    args = os.getenv("TEST_CMD")
    if args:
        cmd = [sys.executable] + args.split()
    else:
        cmd = [sys.executable, "-m", "pytest"] + TARGETS[target] + _PYTEST_TAIL

    env = os.environ.copy()
    # Test qaysi serverga tegishini shu env var belgilaydi (flow_authorization o'qiydi).
    env["TEST_ENV"] = run_env
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
    _run_env = run_env
    _run_target = target
    warn = "\n\U0001F534 <b>DIQQAT: bu PROD (jonli) server!</b>" if run_env == "prod" else ""
    _send(
        f"\U0001F680 <b>Testlar ishga tushdi.</b>\n"
        f"\U0001F310 Muhit: <b>{ENV_LABELS[run_env]}</b>\n"
        f"\U0001F4E6 Bo'lim: <b>{target}</b>{warn}\n"
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
        _send(
            f"\U0001F7E2 Testlar hozir <b>ishlab turibdi</b> — "
            f"muhit: <b>{ENV_LABELS[_run_env]}</b>, bo'lim: <b>{_run_target}</b>.",
            chat_id,
        )
    else:
        _send(
            "⚪ Hozir test ishlamayapti. Boshlash: <b>start dev</b> yoki <b>start prod</b> "
            "(default: hammasi).",
            chat_id,
        )


HELP = (
    "\U0001F916 <b>Smartup24 test bot</b>\n"
    "/start_dev — HAMMA testni DEV (sm24) da boshlash\n"
    "/start_prod — HAMMA testni PROD (test, jonli!) da boshlash\n"
    "/stop — ishlab turgan testlarni to'xtatish\n"
    "/status — holat + qaysi muhit/bo'lim ekani\n"
    "/help — shu ro'yxat\n\n"
    "Bo'lim tanlab ham bo'ladi (default <b>all</b>):\n"
    f"<b>{', '.join(TARGETS)}</b>\n"
    "Masalan: <b>start dev regression</b>, <b>start prod setup</b>, "
    "<b>start dev document</b>.\n"
    "(<b>setup</b> = setup + group_a; <b>all</b> = hammasi bitta login bilan)"
)

# Telegram buyruq menyusi ("/" bosilganda chiqadi — setMyCommands bilan o'rnatiladi)
BOT_COMMANDS = [
    {"command": "start_dev",  "description": "HAMMA testni DEV (sm24) da boshlash"},
    {"command": "start_prod", "description": "HAMMA testni PROD (test, jonli!) da boshlash"},
    {"command": "stop",       "description": "Ishlab turgan testlarni to'xtatish"},
    {"command": "status",     "description": "Holat + qaysi muhit/bo'lim ekani"},
    {"command": "help",       "description": "Buyruqlar ro'yxati + bo'limlar"},
]


def _register_commands() -> None:
    """Telegram'da buyruq menyusini o'rnatadi — chatда "/" bosilганда ular
    ro'yxat bo'lib chiqadi (chalkashliksiz tanlash)."""
    if not BOT_TOKEN:
        return
    try:
        r = requests.post(
            f"{API}/setMyCommands",
            data={"commands": json.dumps(BOT_COMMANDS)},
            timeout=10,
        )
        print(f"[bot] setMyCommands: {'OK' if r.ok else r.text[:150]}")
    except Exception as e:
        print(f"[bot] setMyCommands xato: {e}")


def _handle(text: str, chat_id: str) -> None:
    """Bitta buyruqni bajaradi. Slash menyu: /start_dev /start_prod /stop /status
    /help. Slash'siz matn ham: 'start dev [bo'lim]', 'start prod [bo'lim]', 'stop'.
    Bo'lim (target) ixtiyoriy — berilmasa 'all' (hamma test bitta login bilan)."""
    parts = text.strip().split()
    if not parts:
        return
    cmd = parts[0].lstrip("/").split("@")[0].lower()  # "/start_dev@bot" -> "start_dev"
    rest = [p.lower() for p in parts[1:]]
    if cmd == "start_dev":
        _start_tests(chat_id, "dev", rest[0] if rest else DEFAULT_TARGET)
    elif cmd == "start_prod":
        _start_tests(chat_id, "prod", rest[0] if rest else DEFAULT_TARGET)
    elif cmd == "start":
        # "start [env] [bo'lim]" — env birinchi, bo'lim ixtiyoriy
        run_env = rest[0] if len(rest) > 0 else DEFAULT_ENV
        target = rest[1] if len(rest) > 1 else DEFAULT_TARGET
        _start_tests(chat_id, run_env, target)
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
    print("[bot] Telegram: /start_dev /start_prod /stop /status. To'xtatish: Ctrl+C")
    _register_commands()  # "/" menyusini o'rnatamiz

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
