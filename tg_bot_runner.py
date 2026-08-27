"""Telegram bot orqali testlarni masofadan ishga tushirish/to'xtatish.

Bu ALOHIDA doimiy ishlab turadigan jarayon (conftest emas). Ishga tushiring:

    python tg_bot_runner.py

Keyin bot bilan Telegram'da yozishmadan boshqaring. Har bo'lim uchun alohida
slash buyrug'i bor (<bo'lim>_<env>):
    /start_dev  /start_prod       — All test (barcha bo'lim, bitta login)
    /setup_groupa_dev  /setup_groupa_prod — Setup + Group A
    /regression_dev  /regression_prod — Regression
    /main_dev  /main_prod         — Main
    /document_dev  /document_prod — Document
    /stop    — ishlab turgan testlarni (brauzerlari bilan) to'xtatadi
    /status  — test ishlayaptimi + qaysi muhit/bo'lim ekanini aytadi
    /help    — buyruqlar ro'yxati

Matn shakli ham bor: "start [env] [bo'lim]" — masalan "start dev main",
"start prod regression" (env default dev, bo'lim default all).

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
import threading
import subprocess

import requests
from dotenv import load_dotenv

# .env ni SKRIPT joylashgan papkadan o'qiymiz — Task Scheduler bot'ni boshqa
# ish-papkadan ishga tushirsa ham (masalan C:\Windows\System32), token/chat_id
# baribir topiladi.
_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_HERE, ".env"))

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
    "all":          [_SETUP, _GROUPA, _REGRESSION, _MAIN, _DOCUMENT],
    "setup_groupa": [_SETUP, _GROUPA],   # 2 soatlik juftlik (GitHub avtomat ham shu)
    "regression":   [_REGRESSION],
    "main":         [_MAIN],
    "document":     [_DOCUMENT],
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

# Bo'lim (target) nomlarining o'qishli ko'rinishi — xabarlarda "all" o'rniga.
TARGET_LABELS = {
    "all":          "All test (5 bo'lim)",
    "setup_groupa": "Setup + Group A",
    "regression":   "Regression",
    "main":         "Main",
    "document":     "Document",
}

# Ishlab turgan test jarayoni (bir vaqtda faqat bitta) + qaysi muhit/bo'lim ekani
_proc: subprocess.Popen | None = None
_run_env: str = DEFAULT_ENV
_run_target: str = DEFAULT_TARGET


# ----------------------------------------------------------------------------------------------------------------------

def _send(text: str, chat_id: str | None = None, reply_to: int | None = None) -> None:
    """Telegram'ga xabar yuboradi — NON-BLOKING (tarmoq chaqiruvi fon thread'ida).
    Polling loop Telegram javobini KUTMAYDI, shuning uchun bot keyingi buyruqni
    DARHOL qayta ishlaydi (sekin tarmoqда ham tez his qilinadi)."""
    if not BOT_TOKEN:
        return
    data = {"chat_id": chat_id or CHAT_ID, "text": text, "parse_mode": "HTML"}
    if reply_to:
        data["reply_to_message_id"] = reply_to

    def _do():
        try:
            requests.post(f"{API}/sendMessage", data=data, timeout=10)
        except Exception as e:
            print(f"[bot] send xato: {e}")

    threading.Thread(target=_do, daemon=True).start()


def _run_block(env: str, target: str) -> str:
    """Muhit + bo'lim ma'lumot bloki (xabarlarda bir xil ko'rinadi)."""
    return (
        f"\U0001F310 Muhit: <b>{ENV_LABELS.get(env, env)}</b>\n"
        f"\U0001F4E6 Bo'lim: <b>{TARGET_LABELS.get(target, target)}</b>"
    )


# conftest jonli progress xabarining {msg_id, text} ni shu faylga yozadi — bot
# uni o'qib, band holatda O'SHA xabarning o'ziga flash qiladi (yangi xabar emas).
_PROGRESS_FILE = os.path.join(PROJECT_DIR, "test-results", "tg_progress.json")


def _read_progress_file() -> dict | None:
    """conftest yozgan progress {msg_id, text} — yo'q/xato bo'lsa None."""
    try:
        with open(_PROGRESS_FILE, encoding="utf-8-sig") as f:  # -sig: BOM'ga chidamli
            d = json.load(f)
        if d.get("msg_id") and d.get("text") is not None:
            return d
    except Exception:
        return None
    return None


def _flash_busy(chat_id: str, reply_to: int | None = None) -> None:
    """Test ishlab turganда yangi start bosilsa — ALOHIDA, lekin TO'LIQ MA'LUMOTLI
    xabar: parallel imkonsizligini aytadi va hozirgi run holatini (foiz, passed,
    failed, joriy test) ko'rsatadi (progress fayldan). Ko'rinadigan va foydali —
    reply/edit emas (foydalanuvchi tanlovi)."""
    info = _read_progress_file()
    head = "🚫 <b>Parallel run imkonsiz</b> — hozir test ishlab turibdi:\n\n"
    tail = "\n\nYangisini boshlash uchun avval /stop bosing."
    if info and info.get("text"):
        _send(head + info["text"] + tail, chat_id)
    else:
        _send(
            head + f"{_run_block(_run_env, _run_target)}" + tail,
            chat_id,
        )


# Ishlab turgan run holatini FAYLga ham yozamiz — bot qayta ishga tushsa
# (kod yangilash / crash / logon), xotiradagi _proc yo'qoladi, lekin marker
# fayl orqali run'ni ADOPT qiladi (aks holda ishlab turgan test ustiga ikkinchi
# parallel run boshlanib, ulashilgan akkaunt ikkalasini yiqitardi).
_RUN_MARKER = os.path.join(PROJECT_DIR, "test-results", "bot_run.json")


def _write_marker(pid: int, env: str, target: str) -> None:
    try:
        os.makedirs(os.path.dirname(_RUN_MARKER), exist_ok=True)
        with open(_RUN_MARKER, "w", encoding="utf-8") as f:
            json.dump({"pid": pid, "env": env, "target": target, "ts": time.time()}, f)
    except Exception as e:
        print(f"[bot] marker yozish xato: {e}")


def _read_marker() -> dict | None:
    try:
        with open(_RUN_MARKER, encoding="utf-8-sig") as f:  # -sig: BOM'ga chidamli
            return json.load(f)
    except Exception:
        return None


def _clear_marker() -> None:
    try:
        if os.path.exists(_RUN_MARKER):
            os.remove(_RUN_MARKER)
    except Exception as e:
        print(f"[bot] marker o'chirish xato: {e}")


def _pid_alive(pid: int) -> bool:
    """PID hozir tirikmi — TEZ native tekshiruv. Avval `tasklist` (subprocess)
    ishlatilardi, u HAR buyruqda ~1-3s sekinlashtirardi (bot sekin javob berardi).
    Windows: OpenProcess + WaitForSingleObject (mikrosekund, subprocess YO'Q)."""
    if not pid or pid < 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
    try:
        import ctypes
        SYNCHRONIZE = 0x00100000
        WAIT_TIMEOUT = 0x00000102   # hali ishlayapti (signal berilmagan)
        k = ctypes.windll.kernel32
        h = k.OpenProcess(SYNCHRONIZE, False, int(pid))
        if not h:
            return False
        res = k.WaitForSingleObject(h, 0)
        k.CloseHandle(h)
        return res == WAIT_TIMEOUT
    except Exception:
        return False


def _is_running() -> bool:
    """Test jarayoni hozir ishlab turibdimi. Avval xotiradagi _proc, keyin
    marker fayl (bot qayta ishga tushган bo'lса run'ni adopt qiladi)."""
    global _proc, _run_env, _run_target
    if _proc is not None:
        if _proc.poll() is None:
            return True
        _proc = None  # tugagan
    # _proc yo'q — marker fayldan tekshiramiz
    m = _read_marker()
    if m and _pid_alive(m.get("pid", -1)):
        _run_env = m.get("env", _run_env)
        _run_target = m.get("target", _run_target)
        return True
    _clear_marker()  # eskirgan/tugagan marker
    return False


def _running_pid() -> int | None:
    """To'xtatish uchun ishlab turgan run PID'i (proc yoki marker)."""
    if _proc is not None and _proc.poll() is None:
        return _proc.pid
    m = _read_marker()
    if m and _pid_alive(m.get("pid", -1)):
        return m["pid"]
    return None


def _start_tests(chat_id: str, run_env: str = DEFAULT_ENV, target: str = DEFAULT_TARGET,
                 reply_to: int | None = None) -> None:
    """Testlarni yangi subprocess'da ishga tushiradi (``run_env`` muhitida,
    ``target`` bo'limi bilan)."""
    global _proc, _run_env, _run_target
    if _is_running():
        _flash_busy(chat_id, reply_to)   # buyruqqa aniq JAVOB (parallel imkonsiz)
        return
    if run_env not in ENV_LABELS:
        _send(
            f"❌ Noma'lum muhit: <code>{run_env}</code>\n"
            "Ruxsat: <b>dev</b> · <b>prod</b>",
            chat_id,
        )
        return
    if target not in TARGETS:
        _send(
            f"❌ Noma'lum bo'lim: <code>{target}</code>\n"
            f"Ruxsat: <b>{', '.join(TARGET_LABELS)}</b>",
            chat_id,
        )
        return

    # MUHIM: Task Scheduler bot'ni pythonw.exe (oynasiz) bilan ishga tushiradi,
    # shuning uchun sys.executable = pythonw.exe. Agar pytest'ni pythonw bilan
    # ishga tushirsak — u stdout/stderr'siz DARHOL qulaydi (progress chiqmaydi,
    # bot qayta-qayta urinadi). Konsolli python.exe ishlatamiz.
    py = sys.executable
    if py.lower().endswith("pythonw.exe"):
        cand = py[:-len("pythonw.exe")] + "python.exe"
        if os.path.exists(cand):
            py = cand

    args = os.getenv("TEST_CMD")
    if args:
        cmd = [py] + args.split()
    else:
        cmd = [py, "-m", "pytest"] + TARGETS[target] + _PYTEST_TAIL

    env = os.environ.copy()
    # Test qaysi serverga tegishini shu env var belgilaydi (flow_authorization o'qiydi).
    env["TEST_ENV"] = run_env
    # Bot runlari HEADLESS — foydalanuvchi Telegram orqali kuzatadi, brauzer
    # ko'rinishi shart emas; headless ~30-40% TEZROQ (render yo'q) va CI'da
    # allaqachon sinalgan. (Lokal terminal runlarida brauzer ko'rinadi — o'zgармaydi.)
    env["HEADLESS"] = "1"
    # Bot fon rejimida ishlagani uchun allure brauzerini OCHMAYMIZ (osilib qolmasin) —
    # conftest _finish_allure_report shu env'ni tekshiradi. Natijalar baribir yoziladi.
    env["NO_ALLURE_SERVE"] = "1"

    # CREATE_NEW_PROCESS_GROUP: daraxtni (pytest + brauzerlar) taskkill /T bilan
    # o'chirish uchun. CREATE_NO_WINDOW: python.exe konsol oynasi chiqmasin
    # (chiqish baribir log faylga yo'naltiriladi).
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW

    # Chiqishni log faylga yo'naltiramiz — pytest DOIM yaroqli stdout oladi (pythonw
    # ostidagi qulash oldini oladi) va debug uchun log qoladi.
    try:
        os.makedirs(os.path.join(PROJECT_DIR, "test-results"), exist_ok=True)
        logf = open(os.path.join(PROJECT_DIR, "test-results", "last_bot_run.log"),
                    "w", encoding="utf-8", errors="replace")
        _proc = subprocess.Popen(
            cmd, cwd=PROJECT_DIR, env=env, creationflags=creationflags,
            stdout=logf, stderr=subprocess.STDOUT,
        )
    except Exception as e:
        _send(f"❌ Ishga tushirib bo'lmadi: {e}", chat_id)
        return
    _run_env = run_env
    _run_target = target
    _write_marker(_proc.pid, run_env, target)  # bot qayta ishga tushса adopt qilsin
    # DOIMIY qisqa log qatori (senior yondashuv: chat = audit log, o'chirmaymiz).
    # Jonli progress esa alohida BITTA xabar bo'lib quyida yangilanadi.
    warn = "\n\U0001F534 <b>DIQQAT: PROD — jonli server!</b>" if run_env == "prod" else ""
    _send(
        "\U0001F680 <b>Ishga tushdi</b>\n"
        f"{_run_block(run_env, target)}{warn}\n\n"
        "Jonli progress quyida yangilanadi. To'xtatish: /stop",
        chat_id,
    )


def _stop_tests(chat_id: str) -> None:
    """Ishlab turgan test jarayonini (brauzerlari bilan birga) to'xtatadi.
    PID xotiradagi _proc'dan YOKI marker fayldan olinadi (bot qayta ishga
    tushган bo'lса ham to'xtata oladi)."""
    global _proc
    if not _is_running():
        _send("ℹ️ Hozir ishlab turgan test yo'q.", chat_id)
        return
    pid = _running_pid()
    try:
        if os.name == "nt":
            # /T — butun daraxt (pytest + chromium jarayonlari), /F — majburiy.
            # CREATE_NO_WINDOW: bot pythonw (oynasiz) bo'lgani uchun taskkill konsol
            # OYNA chaqnatmasligi uchun (foydalanuvchi kuzatuvi: "terminal ochilyapti").
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        elif _proc is not None:
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
        _clear_marker()
    _send(
        "\U0001F6D1 <b>To'xtatildi</b>\n"
        f"{_run_block(_run_env, _run_target)}",
        chat_id,
    )


def _status(chat_id: str) -> None:
    if _is_running():
        # To'liq jonli progress (foiz, passed/failed, joriy test) conftest yozgan
        # progress faylida — o'shani ko'rsatamiz. Yo'q bo'lsa (run endigina
        # boshlangan yoki eski kodli run) asosiy ma'lumot bilan cheklanamiz.
        info = _read_progress_file()
        if info and info.get("text"):
            _send(f"{info['text']}\n\nTo'xtatish: /stop", chat_id)
        else:
            _send(
                "\U0001F7E2 <b>Ishlamoqda</b>\n"
                f"{_run_block(_run_env, _run_target)}\n\n"
                "(jonli progress hali tayyor emas — bir zumdan keyin /status)\n"
                "To'xtatish: /stop",
                chat_id,
            )
    else:
        _send(
            "⚪️ <b>Bo'sh</b> — test ishlamayapti\n"
            "Boshlash: /start_dev (hammasi) yoki bo'lim buyrug'i — /help",
            chat_id,
        )


HELP = (
    "\U0001F916 <b>Smartup24 test bot</b>\n"
    "<b>All test:</b> /start_dev · /start_prod\n"
    "<b>Setup + Group A:</b> /setup_groupa_dev · /setup_groupa_prod\n"
    "<b>Regression:</b> /regression_dev · /regression_prod\n"
    "<b>Main:</b> /main_dev · /main_prod\n"
    "<b>Document:</b> /document_dev · /document_prod\n"
    "/stop · /status · /servers · /help · /start\n\n"
    "Matn shakli ham bor: <b>start dev main</b>, <b>start prod regression</b>.\n"
    "(<b>prod</b> = jonli server!)"
)

# /start — onboarding (bot nima qiladi, qanday ishlatiladi, serverlar, avtomat run)
START_MSG = (
    "\U0001F44B <b>Salom!</b> Bu — Smartup24 (x24) Playwright UI avtotestlarini "
    "ishga tushiradigan bot.\n\n"
    "\U0001F4CC <b>Nima qiladi:</b>\n"
    "Testlarni ishga tushiradi va jonli natijani shu chatga yuboradi — bitta xabar "
    "foiz + passed/failed + joriy test bilan yangilanadi, oxirida yakuniy natija "
    "(+ yiqilgan testlar va screenshot) chiqadi.\n\n"
    "\U0001F680 <b>Qanday ishga tushiriladi:</b>\n"
    "1. Bo'lim buyrug'ini yuboring (masalan /start_dev)\n"
    "2. Jonli progress bitta xabarda yangilanib turadi\n"
    "3. Tugagach yakuniy natija shu xabarda chiqadi\n\n"
    "\U0001F4C2 <b>Bo'limlar (DEV):</b>\n"
    "• /start_dev — <b>Hammasi</b> (5 bo'lim, bitta login)\n"
    "• /setup_groupa_dev — Setup + Group A\n"
    "• /regression_dev — Regression\n"
    "• /main_dev — Main\n"
    "• /document_dev — Document\n"
    "\U0001F534 PROD uchun <b>_prod</b>: /start_prod, /main_prod … (jonli server!)\n\n"
    "\U0001F310 <b>Serverlar:</b>\n"
    "• DEV — app3.greenwhite.uz/x24 (sm24)\n"
    "• PROD — app.smartup24.com (test) \U0001F534 jonli\n\n"
    "⚠️ Bir vaqtda faqat <b>bitta</b> run — test ketayotganda yangi start rad "
    "etiladi (avval /stop).\n\n"
    "⏰ <b>Avtomat run (GitHub bulut):</b>\n"
    "• Har 2 soatda → Setup + Group A\n"
    "• Har 12 soatda → Regression\n\n"
    "<b>Buyruqlar:</b> /start_dev · /stop · /status · /servers · /help"
)

# /servers — muhitlar/serverlar ro'yxati
SERVERS_MSG = (
    "\U0001F310 <b>Serverlar</b>\n\n"
    "\U0001F7E2 <b>DEV</b> (test muhiti)\n"
    "https://app3.greenwhite.uz/x24\n"
    "Kompaniya: <b>sm24</b>\n\n"
    "\U0001F534 <b>PROD</b> (jonli server!)\n"
    "https://app.smartup24.com\n"
    "Kompaniya: <b>test</b>\n\n"
    "Muhitni buyruqда tanlaysiz: <b>_dev</b> yoki <b>_prod</b> "
    "(masalan /main_dev yoki /main_prod)."
)

# Telegram buyruq menyusi ("/" bosilganда chiqadi — setMyCommands bilan o'rnatiladi).
# Har bo'lim uchun DEV va PROD variantlari — bittasini alohida ishga tushirish uchun.
# start_dev/start_prod = All test (barcha bo'lim bitta login bilan).
_MENU_SECTIONS = [
    ("start", "All test"),
    ("setup_groupa", "Setup + Group A"),
    ("regression", "Regression"),
    ("main", "Main"),
    ("document", "Document"),
]
BOT_COMMANDS = []
for _key, _label in _MENU_SECTIONS:
    BOT_COMMANDS.append({"command": f"{_key}_dev",  "description": f"{_label} — DEV"})
    BOT_COMMANDS.append({"command": f"{_key}_prod", "description": f"{_label} — PROD (jonli!)"})
BOT_COMMANDS += [
    {"command": "stop",    "description": "Ishlab turgan testlarni to'xtatish"},
    {"command": "status",  "description": "Holat + qaysi muhit/bo'lim ekani"},
    {"command": "servers", "description": "Serverlar ro'yxati (DEV/PROD)"},
    {"command": "help",    "description": "Buyruqlar ro'yxati"},
    {"command": "start",   "description": "Bot haqida — to'liq ma'lumot"},
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


def _handle(text: str, chat_id: str, msg_id: int | None = None) -> None:
    """Bitta buyruqni bajaradi. ``msg_id`` — buyruq xabari (band bo'lsa unga reply).
    Slash menyu: /start_dev /start_prod /stop /status /help. Slash'siz matn ham:
    'start dev [bo'lim]'. Bo'lim ixtiyoriy — berilmasa 'all'."""
    parts = text.strip().split()
    if not parts:
        return
    cmd = parts[0].lstrip("/").split("@")[0].lower()  # "/main_dev@bot" -> "main_dev"
    rest = [p.lower() for p in parts[1:]]
    # Ixtiyoriy "start_" prefiksni yechamiz: "/start_main_dev" == "/main_dev"
    # (start_dev/start_prod = All bundan mustasno). Chalkashlik kamayadi.
    if cmd.startswith("start_") and cmd not in ("start_dev", "start_prod"):
        stripped = cmd[len("start_"):]
        if stripped.rsplit("_", 1)[-1] in ENV_LABELS:
            cmd = stripped
    # "<bo'lim>_<env>" slash buyruqlari: start_dev, setup_prod, main_dev, ...
    sub = cmd.rsplit("_", 1)
    if cmd in ("start_dev", "start_prod"):
        env = "dev" if cmd == "start_dev" else "prod"
        _start_tests(chat_id, env, rest[0] if rest else DEFAULT_TARGET, reply_to=msg_id)
    elif len(sub) == 2 and sub[1] in ENV_LABELS and sub[0] in TARGETS:
        _start_tests(chat_id, sub[1], sub[0], reply_to=msg_id)   # main_dev -> dev/main
    elif cmd == "start":
        if rest:
            # "start dev main" — matn shakli: test ishga tushiradi
            run_env = rest[0]
            target = rest[1] if len(rest) > 1 else DEFAULT_TARGET
            _start_tests(chat_id, run_env, target, reply_to=msg_id)
        else:
            # yakka /start — onboarding (to'liq ma'lumot)
            _send(START_MSG, chat_id)
    elif cmd == "stop":
        _stop_tests(chat_id)
    elif cmd == "status":
        _status(chat_id)
    elif cmd == "servers":
        _send(SERVERS_MSG, chat_id)
    elif cmd in ("help", "commands"):
        _send(HELP, chat_id)
    elif text.strip().startswith("/"):
        _send("❓ Noma'lum buyruq. /help bosing.", chat_id)
    # slash'siz begona matnga javob bermaymiz (shovqin bo'lmasin)


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
            # Bitta xato buyruq BUTUN botni yiqitmasin — handler himoyalanadi.
            try:
                _handle(text, chat_id, msg.get("message_id"))
            except Exception as e:
                print(f"[bot] handler xato: {e}")
                _send(f"❌ Ichki xato: {e}", chat_id)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[bot] to'xtatildi (Ctrl+C).")
