import os
import re
import sys
import json
import time
import shutil
import socket
import random
import threading
import allure
import pytest
import requests
from dotenv import load_dotenv
from typing import Any, Generator
from playwright.sync_api import sync_playwright, Browser, Page, expect

from flows.flow_authorization import logout, TEST_ENV, COMPANY_CODE
from utils.qa_report import current_step_desc, friendly_reason

# .env fayldan Telegram bildirishnoma sozlamalarini o'qiymiz (fayl bo'lmasa jim o'tadi)
load_dotenv()
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID   = os.getenv("TG_CHAT_ID")

# Telegram xabari va Allure hisobotida ko'rinadigan "Host" nomi. Default —
# kompyuterning Windows nomi (socket.gethostname(), masalan "sm24-akmal-hr").
# .env da HOST_LABEL bilan istalgan nom qo'yish mumkin (Windows nomini
# o'zgartirmasdan), masalan HOST_LABEL=Bahriddinov-PC.
HOST_LABEL = os.getenv("HOST_LABEL") or socket.gethostname()

TRACE_DIR = "test-results/traces"
ALLURE_RESULTS_DIR = "test-results/allure-results"
ALLURE_REPORT_DIR = "test-results/allure-report"

# GLOBAL RUN-LOCK: ulashilgan ERP akkaunt — bir vaqtda faqat BITTA test run
# ishlashi mumkin (ikkitasi parallel yursa ikkalasi ham yiqiladi). Bu qulf
# conftest'да (har qanday pytest run'ning O'ZIDA) tekshiriladi — shuning uchun
# terminal ham, bot ham, CI ham — bittasi ishlab tursa ikkinchisi RAD etiladi
# (faqat botning marker'i emas, universal himoya). 2026-08-27 bug: terminaldan
# ishga tushirilgan run bot marker'ini bilmay parallel ketardi.
_RUN_LOCK = "test-results/run.lock"


def _lock_pid_alive(pid: int) -> bool:
    """PID hozir tirikmi — tez native tekshiruv (Windows: OpenProcess)."""
    if not pid or pid < 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, OSError):
            return False
        except PermissionError:
            return True
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x00100000, False, int(pid))  # SYNCHRONIZE
        if not h:
            return False
        res = k.WaitForSingleObject(h, 0)
        k.CloseHandle(h)
        return res == 0x00000102  # WAIT_TIMEOUT = hali ishlayapti
    except Exception:
        return False

# Timeout konstantalari — bitta joyda, butun loyiha bo'ylab ishlatiladi
# DIQQAT: sessiya qulfi handleri (_auto_continue_session) bajarilish vaqti uni
# chaqirgan amalning TIMEOUT'iga KIRADI (Playwright add_locator_handler
# hujjatlashtirilgan xatti-harakati). Qulfning countdown bosqichi ~30s ekranni
# to'sadi — 10s timeout bilan qulf ustiga tushgan har qanday amal handler
# yechishga ulgurmasdan yiqilar edi (2026-07-10 run: open_create 37-daqiqada).
# Shu sabab 60s: qulf yechilishini ham qamraydi; haqiqiy xato esa 10s o'rniga
# 60s da qayd etiladi, xolos.
DEFAULT_TIMEOUT    = 60_000    # click, fill, expect va boshqa locator amallari (ms)
NAVIGATION_TIMEOUT = 60_000    # page.goto, wait_for_load_state (ms)

# ----------------------------------------------------------------------------------------------------------------------
# QISQA GURUH NOMLARI — `pytest setup`, `pytest visit`, `pytest all` ...
# ----------------------------------------------------------------------------------------------------------------------
# Har guruh mos runner fayl(lar)iga xaritalanadi. DIQQAT: buni `-p` plagin bilan
# qilib bo'lmaydi — bare `pytest` (console-script) joriy papkani sys.path'ga
# QO'SHMAYDI, shuning uchun `-p modul` importi yiqiladi (faqat `python -m pytest`
# ishlardi). conftest.py esa bare `pytest`da ham DOIM yuklanadi — shu sabab
# almashtirishni `pytest_configure`da (collection'dan oldin) qilamiz: argument
# tanish guruh nomi bo'lsa VA haqiqiy fayl/papka BO'LMASA runner yo'l(lar)iga
# almashtiriladi. Standart `pytest <path>` / `-k` / `-m` / bayroqlar buzilmaydi.
_SETUP      = "tests/test_setup/test_all_setup.py"
_GROUP_A    = "tests/test_group_a/test_all_group_a.py"
_REGRESSION = "tests/test_regression/test_all_regression.py"
_MAIN       = "tests/test_main/test_all_main.py"
_DOCUMENT   = "tests/test_document/test_all_document_runner.py"
_VISIT = [
    "tests/test_document/test_visit.py",
    "tests/test_document/test_Plan_visit_recurrence.py",
    "tests/test_document/test_agent_visit_tracking.py",
    "tests/test_document/test_route_analysis.py",
]
# Bitta narsa = bitta nom (chalkashmasin): 5 bo'lim aniq nomi + visit.
GROUP_ALIASES = {
    "setup":       [_SETUP],
    "group_a":     [_GROUP_A],
    "regression":  [_REGRESSION],
    "main":        [_MAIN],
    "document":    [_DOCUMENT],
    "visit":       list(_VISIT),
}


def _expand_group_aliases(items):
    """Ro'yxatdagi tanish guruh nomlarini runner yo'llariga yoyadi (tartib saqlanadi)."""
    out = []
    for arg in items:
        mapped = GROUP_ALIASES.get(str(arg).lower())
        if mapped and not os.path.exists(arg):
            out.extend(mapped)
        else:
            out.append(arg)
    return out


# ----------------------------------------------------------------------------------------------------------------------
# CLI BAYROQLAR — brauzer ko'rinishi va report ochilishi (CLI > .env > default)
# ----------------------------------------------------------------------------------------------------------------------
def pytest_addoption(parser):
    """Terminaldan boshqarish uchun tugma-bayroqlar. Tri-holat (True/False/None):
    berilmasa None qoladi va .env/default ga o'tiladi (qarang _headless_for/_open_report_for).

        pytest setup --show-browser        # brauzerni ko'rsat (env HEADLESS=1 ni ham bosadi)
        pytest setup --hide-browser        # brauzerni yashir (fon/CI)
        pytest setup --open-report         # yakunда Allure'ni brauzerda och
        pytest setup --no-open-report      # report yaratiladi, brauzer ochilmaydi
    """
    g = parser.getgroup("smartup24", "Smartup24 E2E tugmalari")
    g.addoption("--show-browser", dest="show_browser", action="store_const", const=True,
                default=None, help="Brauzerni ko'rsat (headless=False). .env HEADLESS'ni bosadi.")
    g.addoption("--hide-browser", dest="show_browser", action="store_const", const=False,
                help="Brauzerni yashir (headless).")
    g.addoption("--open-report", dest="open_report", action="store_const", const=True,
                default=None, help="Yakunда Allure hisobotini brauzerda och.")
    g.addoption("--no-open-report", dest="open_report", action="store_const", const=False,
                help="Hisobot yaratiladi, lekin brauzer ochilmaydi.")


# ----------------------------------------------------------------------------------------------------------------------

def pytest_configure(config):
    """Allure hisoboti uchun environment, categories, executor va history tayyorlaydi."""
    # Qisqa guruh nomlarini (`pytest setup`) collection'dan OLDIN runner yo'liga
    # almashtiramiz — positional argumentlar `config.args` va `option.file_or_dir`
    # da turadi (versiyaga qarab biri ishlatiladi, ikkalasini ham yangilaymiz).
    try:
        if getattr(config.option, "file_or_dir", None):
            config.option.file_or_dir = _expand_group_aliases(config.option.file_or_dir)
        if getattr(config, "args", None):
            config.args = _expand_group_aliases(list(config.args))
    except Exception as e:
        print(f"[group-aliases] almashtirishда xato (davom etadi): {e}")
    # Windows konsol/redirekt stdout default cp1252 — yiqilган testning Cyrillic
    # sabab matni (grid_row/save/select diagnostikasi, «Ошибка»/«Нет результатов»)
    # yoki "•" pytest traceback'ida yozilganда UnicodeEncodeError berib BUTUN
    # chiqishni buzmasligi uchun stdout/stderr'ni utf-8'ga o'tkazamiz (o'tmasa jim).
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass
    expect.set_options(timeout=DEFAULT_TIMEOUT)
    os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)

    # Trend uchun: oldingi hisobotdan history ko'chirish
    history_src = os.path.join(ALLURE_REPORT_DIR, "history")
    history_dst = os.path.join(ALLURE_RESULTS_DIR, "history")
    if os.path.exists(history_src):
        if os.path.exists(history_dst):
            shutil.rmtree(history_dst)
        shutil.copytree(history_src, history_dst)

    # Environment
    env_path = os.path.join(ALLURE_RESULTS_DIR, "environment.properties")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("Browser=Chromium\n")
        f.write("Browser.Headless=False\n")
        f.write("Framework=Playwright\n")
        f.write("Language=Python 3.11\n")
        f.write("Environment=Staging\n")
        f.write(f"Host={HOST_LABEL}\n")

    # Categories
    categories_src = "allure/categories.json"
    categories_dst = os.path.join(ALLURE_RESULTS_DIR, "categories.json")
    if os.path.exists(categories_src):
        shutil.copy(categories_src, categories_dst)

    # Executor
    executor_path = os.path.join(ALLURE_RESULTS_DIR, "executor.json")
    executor_data = {
        "name": HOST_LABEL,
        "type": "local",
        "buildName": "Smoke Tests",
        "reportName": "Allure Report"
    }
    with open(executor_path, "w", encoding="utf-8") as f:
        json.dump(executor_data, f, indent=2)

# ----------------------------------------------------------------------------------------------------------------------

def pytest_sessionstart(session):
    """GLOBAL RUN-LOCK: boshqa test run allaqachon ishlab tursa — SESSIYANI DARHOL
    to'xtatadi (parallel run ulashilgan akkauntда ikkalasini yiqitadi). Terminal,
    bot, CI — hammasi shu conftest'ni yuklaydi, universal himoya. xdist worker
    EMAS, --collect-only da o'tkazamiz (haqiqiy run emas)."""
    if getattr(session.config, "workerinput", None) is not None:
        return
    if session.config.option.collectonly:
        return
    try:
        os.makedirs(os.path.dirname(_RUN_LOCK), exist_ok=True)
    except Exception:
        pass
    # ATOMIK qulf (os.O_EXCL) — faqat BITTA jarayon qulf faylini yarata oladi.
    # Oldingi "os.path.exists() TEKSHIR, keyin YOZ" ketma-ketligi NOATOMIK edi:
    # bir vaqtda (~1s ichida) boshlangan ikki run ikkovi ham "qulf yo'q" deb ko'rib
    # PARALLEL ketardi (2026-09-08: ikki test_manufacturer runi birga yurgan bug).
    # O_EXCL bu poyga oynasini yopadi: yaratishning o'zi atomik qulflash.
    other = None
    payload = json.dumps({"pid": os.getpid(), "ts": time.time(), "host": HOST_LABEL}).encode("utf-8")
    for _attempt in range(5):
        try:
            fd = os.open(_RUN_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, payload)              # PID'ni DARHOL yozamiz (bo'sh oynani qisqartirish)
            finally:
                os.close(fd)
            other = None
            break                                  # qulf BIZDA — davom etamiz
        except FileExistsError:
            # Kimdir ushlab turibdi. DIQQAT: yaratuvchi faylni yaratib, PID'ni yozguncha
            # (mikrosoniya) fayl BO'SH bo'lishi mumkin — bo'shni ko'rib darrov "eskirgan"
            # deb O'CHIRMAYMIZ, aks holda yutqazgan run qulfni o'g'irlab parallel ketadi
            # (2026-09-08 poygasi shu edi). PID paydo bo'lguncha ~1s qayta o'qiymiz.
            d = {}
            for _r in range(40):                   # ~1s: 40 x 25ms
                try:
                    with open(_RUN_LOCK, encoding="utf-8-sig") as f:
                        d = json.load(f)
                except FileNotFoundError:
                    d = {}
                    break                          # yaratuvchi o'zi olib tashladi — qayta urinamiz
                except Exception:
                    d = {}                         # hali bo'sh / yozilyapti
                if d.get("pid"):
                    break
                time.sleep(0.025)
            o = d.get("pid")
            if o and o != os.getpid() and _lock_pid_alive(o):
                other = (o, d.get("host", "?"))    # TIRIK run bor — rad etamiz
                break
            # PID yo'q yoki O'LIK — eskirgan/buzuq qulf; olib tashlab qayta urinamiz
            # (O_EXCL keyingi urinishда yana kim yutsa — o'sha egallaydi).
            try:
                os.remove(_RUN_LOCK)
            except FileNotFoundError:
                pass                               # kimdir ulgurdi — keyingi urinishda ko'ramiz
            except Exception as e:
                print(f"[run-lock] eski qulfni olib tashlashda xato: {e}")
                break
        except Exception as e:
            print(f"[run-lock] yozishda xato (davom etadi): {e}")
            break
    if other:
        pid, host = other
        msg = (f"Boshqa test run allaqachon ishlayapti (PID {pid}, {host}) — "
               "ulashilgan akkaunt, parallel run mumkin emas. Avval uni tugating (yoki /stop).")
        _send_telegram(f"\U0001F6AB <b>Run rad etildi</b>\n{msg}")
        pytest.exit(msg, returncode=2)   # sessiyani darhol to'xtatadi (try'дан TASHQARIDA)


def _release_run_lock() -> None:
    """Run tugagach global qulfni bo'shatadi (agar bizniki bo'lsa)."""
    try:
        if os.path.exists(_RUN_LOCK):
            with open(_RUN_LOCK, encoding="utf-8-sig") as f:
                d = json.load(f)
            if d.get("pid") == os.getpid():
                os.remove(_RUN_LOCK)
    except Exception as e:
        print(f"[run-lock] bo'shatishda xato: {e}")


# ----------------------------------------------------------------------------------------------------------------------

def _auto_continue_session(page_obj: Page, password: str | None = None) -> None:
    """``app-session-lock`` overlay'ini avtomatik yopadi.

    Parol ``TEST_PASSWORD`` environment variable'dan olinadi (berilmasa
    default login paroli ishlatiladi).

    Sessiya ochilganidan ~30 daqiqa o'tgach app to'liq ekranli overlay
    chiqaradi va BARCHA kliklarni to'sib qo'yadi. Ikki holati bor:
    1) "Закрытие сессии" countdown dialogi (~20 sek) — TEZ YO'L: chapdagi
       "Блокировка экрана" tugmasi bosiladi va countdown KUTILMASDAN darhol
       parol qulfiga o'tiladi (foydalanuvchi kuzatuvi 2026-07-10; "Продолжить"
       countdown paytida bosilsa ham ish bermaydi — 15:40 trace);
    2) "Блокировка экрана" parol qulfi (input#password + "Войти") — parol
       kiritib "Войти" bosiladi.
    Shu tartibda qulf ~2-3 soniyada yechiladi — handler vaqti amal timeout'iga
    kirgani uchun bu muhim. Handler ichidagi xato yutiladi — trigger ko'rinib
    tursa keyingi amalda qayta uriniladi (regression 2026-07-08)."""
    password = password or os.environ.get("TEST_PASSWORD", "greenwhite")
    # Trigger ikkala holatni ham qamraydi: countdown backdrop YOKI parol input
    lock = page_obj.locator(
        "app-session-lock button[aria-label='Продолжить'], app-session-lock form input"
    )

    def _unlock(_) -> None:
        # MUHIM 1: qulfning IKKALA bosqich elementlari DOMda bir vaqtda turadi
        # (biri yashirin) — shuning uchun KO'RINADIGAN holatga qarab
        # tarmoqlanadi, parol bosqichi (terminal holat) birinchi (12:11 trace).
        # MUHIM 2: handler bir MARTA chaqiriladi, keyin Playwright qulf
        # yo'qolishini kutadi xolos — bitta urinish animatsiya/o'tish payti
        # hech narsa qilmay qolsa deadlock (14:56 trace: handler no-op bo'lib,
        # 30s davomida hech kim qulfni bosmagan). Shuning uchun qulf
        # YOPILGUNCHA sikl qilamiz.
        # MUHIM 3: ichki amallarga QISQA timeout va har urinish alohida
        # himoyalanadi — is_visible() dan dispatch_event gacha bo'lgan orada
        # element yo'qolsa (countdown -> parol o'tishi), default 60s bilan
        # dispatch_event yo'q tugmani kutib handlerni O'ZINI qotirar edi
        # (11:57 run: "Продолжить" dispatch_event 60000ms timeout).
        # force=True: qulf bilan birga boshqa overlay (masalan Ошибка dialogi)
        # ochiq bo'lsa ham fill "intercepts pointer events" bilan to'silmasin.
        # dispatch_event — DOM darajasidagi klik: backdrop hit-testini chetlab
        # tugmaning o'z handleriga boradi.
        root = page_obj.locator("app-session-lock")
        # 60→20s: qulf normalда ~2-3s da yechiladi; yechilmasa (uzoq run'da seans
        # SERVER'да expire bo'lgan — 2026-08-11 test_641 4.4 SOAT osilishi) tez
        # qaytamiz, add_locator_handler(no_wait_after) amalни o'z timeoutida davom
        # ettiradi, cheksiz qayta-o'q YO'Q.
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                # DIQQAT: app-session-lock elementi O'ZI o'lchamsiz konteyner
                # (bolalari fixed) — is_visible() unda har doim False. Shuning
                # uchun yopilganini ichki ko'rinadigan elementlar orqali bilamiz.
                if not root.count() or not lock.filter(visible=True).count():
                    return  # qulf yopildi
                # 1) Parol qulfi: forma ichida bitta input (placeholder "Пароль")
                pwd = root.locator("form input")
                if pwd.count() and pwd.first.is_visible():
                    pwd.first.fill(password, timeout=3_000, force=True)
                    root.locator("button", has_text="Войти").first.dispatch_event(
                        "click", timeout=2_000
                    )
                    page_obj.wait_for_timeout(700)
                    continue
                # 2) TEZ YO'L: countdown dialogidagi chap tugma "Блокировка
                # экрана" — countdown (~30s) KUTILMASDAN darhol parol qulfiga
                # o'tkazadi (foydalanuvchi kuzatuvi 2026-07-10).
                lock_btn = root.locator("button", has_text="Блокировка экрана")
                if lock_btn.count() and lock_btn.first.is_visible():
                    lock_btn.first.dispatch_event("click", timeout=2_000)
                    page_obj.wait_for_timeout(300)
                    continue
                # 3) Fallback: "Продолжить" (countdown paytida ko'pincha ish
                # bermaydi — 15:40 trace, lekin dialog varianti uchun qoladi)
                cont = root.locator("button", has_text="Продолжить")
                if cont.count() and cont.first.is_visible():
                    cont.first.dispatch_event("click", timeout=2_000)
                    page_obj.wait_for_timeout(700)
                    continue
                page_obj.wait_for_timeout(300)  # o'tish/animatsiya payti
            except Exception as exc:  # o'tish payti elementi yo'qolgan bo'lishi mumkin
                print(f"[session-lock] urinish xatosi (davom etadi): {exc}")
                try:
                    page_obj.wait_for_timeout(300)
                except Exception:
                    return  # page yopilgan — handlerdan chiqamiz
        print("[session-lock] 20s ichida qulf yechilmadi — amal o'z timeout'ida davom etadi")

    # no_wait_after=True: handler ishlagach Playwright qulf YO'QOLISHINI KUTMAYDI —
    # seans o'lib qulf yopilmasa ham handler cheksiz qayta-o'q UZMAYDI (default
    # no_wait_after=False shu sabab 2026-08-11 da test_641'ni 4.4 SOAT osdirgan:
    # qulf yechilmay Playwright handlerni ~260 marta qayta chaqirib sahifani
    # crash'gacha olib borgan). times=40: qo'shimcha qattiq cheklov (uzoq run'da
    # legit qulf ~30 daqiqada bir marta chiqadi — 40 martaga yetadi).
    page_obj.add_locator_handler(lock, _unlock, no_wait_after=True, times=40)


# ----------------------------------------------------------------------------------------------------------------------

def _auto_recover_chunk_error(page_obj: Page) -> None:
    """Vite/Angular lazy-chunk yuklash xatosini avtomatik tiklaydi (reload bilan).

    Uzoq run paytida dev-server (app3) QAYTA DEPLOY qilinsa, brauzerdagi eski
    ``index.html`` endi mavjud bo'lmagan chunk hash'iga murojaat qiladi va
    lazy-route (asosiy kontent) moduli yuklanmaydi — app "Ошибка" dialogini
    ko'rsatadi: ``Failed to fetch dynamically imported module: .../chunk-XXXX.js``.
    Bu ENVIRONMENTAL flaky (klik tezligi EMAS): navigatsiya bo'lgan, sarlavha
    router-outlet yuklangan, biroq kontent moduli chunk'i 404 (2026-07-27 runner,
    product_view: chunk-KUHAWWPQ.js). Bir marta reload YANGI manifestli
    ``index.html`` ni oladi va joriy deep-URL'ga qayta yo'naltiradi — chunk'lar
    to'g'ri hash bilan yuklanadi, kutilayotgan maydon paydo bo'ladi.

    Handler amal timeout'i ICHIDA ishga tushadi (add_locator_handler
    xatti-harakati), shuning uchun DEFAULT_TIMEOUT 60s reload + re-render'ni
    qamrab oladi. ``times=5`` bilan cheklaymiz — server HAQIQATAN buzuq bo'lsa
    cheksiz reload sikliga tushmasdan, amal timeout bilan haqiqiy xatoni qayd
    etsin. Handler xatosi yutiladi — dialog ko'rinib tursa keyingi amalda
    (yoki qayta polling'da) yana uriniladi."""
    error_dialog = page_obj.get_by_role("dialog").filter(
        has_text="Failed to fetch dynamically imported module"
    )

    def _reload(_) -> None:
        try:
            page_obj.reload(wait_until="domcontentloaded")
        except Exception as exc:  # reload navigatsiyasi uzilsa — keyingi amal qayta uriниadi
            print(f"[chunk-recover] reload xatosi (davom etadi): {exc}")

    # times=15: uzoq runner (setup+group_a+regression) davomida dev bir necha marta
    # deploy bo'lishi mumkin — 5 marta yetmay qolar edi (2026-07-30 runner, currency+add
    # chunk 404). Cheksiz emas, shuning uchun HAQIQATAN buzuq serverда amal timeout bilan
    # to'xtaydi.
    page_obj.add_locator_handler(error_dialog, _reload, times=15)


# ----------------------------------------------------------------------------------------------------------------------

# Brauzer ko'rinishi va report ochilishi — TUGMA (maxfiy emas). Boshqaruv tartibi:
# Brauzer ko'rinishi va report ochilishi — bitta manba (HEADLESS) + CLI override.
# Boshqaruv tartibi: CLI bayroq > .env HEADLESS > default.
#   • Odam uchun (intuitiv):  pytest ... --show-browser / --hide-browser / --open-report / --no-open-report
#   • CI/bot uchun (standart):  HEADLESS=1  (brauzerni yashiradi; report ham ochilmaydi)
# Default: brauzer KO'RINADI, report OCHILADI. Report ko'rinishga bog'liq —
# yashirin (CI/bot) rejimда report popup ochilmaydi, alohida NO_ALLURE_SERVE kerak emas.
def _headless_for(config) -> bool:
    """Brauzer yashirin (headless) ishlasinmi? CLI > HEADLESS > default(False=ko'rinadi)."""
    show = config.getoption("show_browser", None)   # True/False/None (berilmagan)
    if show is not None:
        return not show                              # --show-browser -> ko'rsat, --hide-browser -> yashir
    return os.getenv("HEADLESS") == "1"              # HEADLESS=1 -> yashir; aks holda ko'rinadi


def _open_report_for(config) -> bool:
    """Allure brauzerда ochilsinmi? CLI > (brauzer ko'rinishiga bog'liq) > default(ochiladi)."""
    val = config.getoption("open_report", None)     # True/False/None
    if val is not None:
        return val
    return not _headless_for(config)                 # yashirin (CI/bot) -> ochma; ko'rinsa -> och


@pytest.fixture
def browser(request):
    """Bitta browser instance, to'liq ekranda ochiladi.

    ``--window-size=1920,1080`` — MUHIM: ``--start-maximized`` Playwright
    headless=False'da KO'PINCHA ishlamaydi (oyna ~800x600 default holicha
    qoladi). Past viewport'da uzun formalarning (masalan Продукт) OXIRIDAGI
    maydon ekran chetiga tushadi va uning dropdown varianti viewport'dan
    chiqib ketadi — Playwright uni bosolmay 60s timeout beradi (prod run
    2026-07-23, Отрасль select "outside of the viewport"; 470px'da takrorlandi,
    1080px'da yo'qoladi — MCP o'lchab tasdiqlangan). Qat'iy o'lcham buni
    deterministik hal qiladi."""
    with sync_playwright() as p:
        browser_obj = p.chromium.launch(
            headless=_headless_for(request.config),
            args=["--start-maximized", "--window-size=1920,1080"],
        )
        yield browser_obj
        browser_obj.close()

# ----------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="session")
def session_browser(request):
    """Butun sessiya uchun bitta browser (test_smoke_runner uchun).

    ``--window-size=1920,1080`` sababi uchun ``browser`` fixture izohiga qarang
    (past viewport'da dropdown varianti ekrandan chiqib ketadi)."""
    with sync_playwright() as p:
        browser_obj = p.chromium.launch(
            headless=_headless_for(request.config),
            args=["--start-maximized", "--window-size=1920,1080"],
        )
        yield browser_obj
        browser_obj.close()

# ----------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="session")
def session_context(session_browser):
    """Barcha smoke testlar uchun yagona context. Bitta trace yoziladi."""
    context = session_browser.new_context(no_viewport=True)
    context.set_default_timeout(DEFAULT_TIMEOUT)
    context.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield context
    os.makedirs(TRACE_DIR, exist_ok=True)
    context.tracing.stop(path=os.path.join(TRACE_DIR, "smoke_trace.zip"))
    context.close()

# ----------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="session")
def session_page(session_context) -> Generator[Page, Any, None]:
    """Barcha smoke testlar uchun yagona sahifa — holat saqlanadi."""
    page_obj = session_context.new_page()
    _auto_continue_session(page_obj)
    _auto_recover_chunk_error(page_obj)
    yield page_obj
    logout(page_obj)  # seansni yopamiz — parallel seans limiti to'lib qolmasligi uchun
    page_obj.close()

# ----------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def page(browser: Browser, request) -> Generator[Page, Any, None]:
    """Har bir test uchun yangi sahifa, to'liq ekran (no_viewport + --start-maximized). Trace yoziladi."""
    context = browser.new_context(no_viewport=True)
    context.set_default_timeout(DEFAULT_TIMEOUT)
    context.set_default_navigation_timeout(NAVIGATION_TIMEOUT)

    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page_obj = context.new_page()
    _auto_continue_session(page_obj)
    _auto_recover_chunk_error(page_obj)

    yield page_obj

    logout(page_obj)  # seansni yopamiz — parallel seans limiti to'lib qolmasligi uchun
    os.makedirs(TRACE_DIR, exist_ok=True)
    safe_name = request.node.nodeid.replace("/", "_").replace("::", "__")
    context.tracing.stop(path=os.path.join(TRACE_DIR, f"{safe_name}.zip"))
    page_obj.close()
    context.close()

# ----------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="session")
def code():
    """Test sessiyasi uchun yagona cod qiymati.

    Vaqtga asoslangan (epoch sekundlarining oxirgi 7 raqami): vaqt orqaga
    qaytmagani uchun oldingi runlar yaratgan yozuvlar bilan HECH QACHON
    to'qnashmaydi — random 4 xonali kod baza to'lgan sari dublikat
    (dup_val_on_index) xatolarini chiqarayotgan edi."""
    return str(int(time.time()))[-7:]


# ----------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="session")
def runner_state():
    """Bo'lim-runner (test_all_*) testlari ORASIDA runtime qiymatlarni uzatish
    uchun umumiy lug'at (session scope).

    Aggregator mega-test bo'lganda bu qiymatlar oddiy lokal o'zgaruvchilar edi
    (masalan group_a'da yaratilgan ``product_name`` → linking → order). Endi har
    qadam ALOHIDA test bo'lganligi uchun ular orasida ma'lumot shu lug'at orqali
    uzatiladi: ``runner_state["ga_product_name"]``, ``runner_state["konkurs_region"]``."""
    return {}


# ----------------------------------------------------------------------------------------------------------------------

def _send_telegram(text: str) -> int | None:
    """Telegram Bot API orqali ``text`` xabarini yuboradi.

    Token yoki chat_id ``.env`` da bo'lmasa jim o'tadi (masalan lokal ishlab
    chiqishda). Tarmoq/API xatosi butun sessiyani yiqitmasligi uchun yutiladi.
    Muvaffaqiyatli bo'lsa yuborilgan xabarning ``message_id`` sini qaytaradi —
    keyinchalik uni ``_edit_telegram`` bilan yangilash (progress bar) uchun."""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return None
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(
            url,
            data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        if resp.status_code != 200:
            print(f"[Telegram] yuborilmadi (HTTP {resp.status_code}): {resp.text[:200]}")
            return None
        return resp.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"[Telegram] yuborishda xato: {e}")
        return None


def _edit_telegram(message_id: int, text: str, sync: bool = False) -> None:
    """Oldin yuborilgan Telegram xabarini (``message_id``) yangilaydi.

    Oddiy (oraliq) tahrirlar NON-BLOKING: tarmoq chaqiruvi FON thread'ida — test
    jarayoni Telegram javobini KUTMAYDI (aks holda har tahrir ~300ms test vaqtini
    yerdi). LEKIN ``sync=True`` — SINXRON (bloklaydi): YAKUNIY tahrir va OXIRGI test
    uchun SHART, chunki pytest jarayoni sessionfinish'дан keyin DARHOL chiqadi va
    daemon thread'даги tugamаган so'rov O'LADI (bag: yakuniy 'test yakunlandi'
    xabari kelmasdi, progress muzlab qolardi — 2026-08-27). Matn o'zgarmasa
    "message is not modified" (400) — xato emas. Tarmoq/API xatosi runni yiqitmaydi."""
    if not TG_BOT_TOKEN or not TG_CHAT_ID or not message_id:
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/editMessageText"

    def _do():
        try:
            requests.post(
                url,
                data={"chat_id": TG_CHAT_ID, "message_id": message_id,
                      "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
        except Exception as e:
            print(f"[Telegram] tahrirlashda xato: {e}")

    if sync:
        _do()  # jarayon chiqishдан oldin so'rov TUGAsin
    else:
        threading.Thread(target=_do, daemon=True).start()


def _send_telegram_photo(png_bytes: bytes, caption: str) -> None:
    """Telegram'ga rasm (screenshot) yuboradi. Yiqilgan testlar oxirida
    xatoning ekran holatini ko'rsatish uchun."""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
    try:
        requests.post(
            url,
            data={"chat_id": TG_CHAT_ID, "caption": caption[:1024], "parse_mode": "HTML"},
            files={"photo": ("failure.png", png_bytes, "image/png")},
            timeout=30,
        )
    except Exception as e:
        print(f"[Telegram] rasm yuborishda xato: {e}")




# Progress xabarining msg_id + joriy matnini shu faylga yozamiz — Telegram bot
# (ALOHIDA jarayon) uni o'qib, test ishlab turganда yangi start bosilса o'sha
# xabarning O'ZIGA vaqtincha "band" ogohlantirishini chaqillatadi (yangi xabar
# yubormasdan). Fayl bo'lmasa (run yo'q) bot fallback qiladi.
TG_PROGRESS_FILE = os.path.join("test-results", "tg_progress.json")


def _persist_progress(text: str | None) -> None:
    """Progress xabar msg_id + matnini faylga yozadi (bot o'qishi uchun).
    ``text=None`` — faylni o'chiradi (run tugadi/progress yo'q)."""
    try:
        if text is None or not _progress.get("msg_id"):
            if os.path.exists(TG_PROGRESS_FILE):
                os.remove(TG_PROGRESS_FILE)
            return
        os.makedirs(os.path.dirname(TG_PROGRESS_FILE), exist_ok=True)
        # Atomik yozuv: temp faylga yozib, keyin rename — bot (boshqa jarayon)
        # yarim yozilgan faylni o'qib qolmasin (Windows'da os.replace atomik).
        tmp = TG_PROGRESS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"msg_id": _progress["msg_id"], "text": text}, f, ensure_ascii=False)
        # RETRY: Windows'да os.replace destination fayl OCHIQ bo'lsa (bot /status
        # uchun o'qiyotган payt) PermissionError beradi -> fayl yangilanmasdan qolib,
        # /status eskirar edi (2026-08-27: 14% da 11% ko'rsatgan). Bot o'qishni
        # yopgach (bir necha ms) qayta urinamiz.
        for _ in range(10):
            try:
                os.replace(tmp, TG_PROGRESS_FILE)
                break
            except PermissionError:
                time.sleep(0.03)
    except Exception as e:
        print(f"[progress-file] xato: {e}")


# Yiqilgan testlarning screenshotlari (nom, png) — sessiya oxirida Telegram'ga
# yuboriladi. Spam bo'lmasligi uchun birinchi bir nechtasi bilan cheklanadi.
_failure_shots: list[tuple[str, bytes]] = []
_MAX_FAILURE_SHOTS = 5

# Yiqilgan test → BIZNES tilida kontekst: {nodeid: {"step": tavsif, "reason": sabab}}
# (qa_step context manager to'ldiradi; yakuniy Telegram xabarига chiqadi)
_failure_ctx: dict[str, dict] = {}


# ----------------------------------------------------------------------------------------------------------------------

# Jonli progress bar holati (faqat master jarayon, session davomida saqlanadi).
#   msg_id — tahrirlanadigan Telegram xabarining ID'si (None bo'lsa progress o'chiq)
#   total  — yig'ilgan testlar soni
#   done   — tugagan testlar soni
#   passed/failed — natija hisoblagichlari (jonli ko'rsatish uchun)
#   last_edit — oxirgi tahrir vaqti (throttle uchun, monotonic sekund)
_progress = {
    "msg_id": None,
    "total": 0,
    "done": 0,
    "passed": 0,
    "failed": 0,
    "last_edit": 0.0,
    "suite": "",   # qaysi bo'lim(lar) ishlayapti — Telegram xabarlarida ko'rsatiladi
    "current": "", # joriy ishlab turgan test nomi (jonli, /status uchun)
    "start_ts": 0.0,  # run boshlangan vaqt (o'tган vaqt/ETA uchun)
}


# Progress barni JUDA tez-tez tahrirlamaslik uchun minimal interval (sekund).
# editMessageText'ni har testda chaqirish (~2×test soni) test oqimini
# sekinlashtiradi va Telegram rate-limit xavfini tug'diradi — shu interval
# throttle qiladi. Oxirgi test bundan MUSTASNO: yakuniy holat DOIM ko'rsatiladi.
_PROGRESS_MIN_INTERVAL = 3.0


# Bo'lim-runner fayllari → ko'rsatiladigan nom. Aynan shu fayllar yig'ilsa,
# Telegram xabarida "Setup", "Group A", "Setup + Group A", "HAMMASI" ko'rinadi.
_RUNNER_LABELS = {
    "test_all_setup.py":            "Setup",
    "test_all_group_a.py":          "Group A",
    "test_all_regression.py":       "Regression",
    "test_all_main.py":             "Main",
    "test_all_document_runner.py":  "Document",
}


def _suite_label(items) -> str:
    """Yig'ilgan testlarning fayllaridan qaysi bo'lim(lar) ishlayotganini aniqlaydi.

    setup+group_a → "Setup + Group A"; faqat regression → "Regression"; beshtasi
    birga → "HAMMASI (5 bo'lim)". Runner bo'lmagan (individual debug) fayllar
    yig'ilsa — fayl nomi(lari) ko'rsatiladi. Fayl tartibi buyruq qatoridan
    saqlanadi, shuning uchun 'Setup + Group A' to'g'ri tartibda chiqadi."""
    files = []
    for it in items:
        base = it.nodeid.split("::")[0].rsplit("/", 1)[-1]
        if base not in files:
            files.append(base)
    known = [_RUNNER_LABELS[f] for f in files if f in _RUNNER_LABELS]
    if len(known) == len(files) and known:  # hammasi tanilgan runner fayllar
        if len(known) == len(_RUNNER_LABELS):
            return "All test"
        return " + ".join(f"{k} section" for k in known)
    # aralash yoki individual debug fayllar
    if len(files) == 1:
        return files[0]
    return f"{len(files)} fayl (debug)"


def _progress_bar(pct: int, width: int = 14) -> str:
    """``██████████░░░░  62%`` ko'rinishidagi toza progress bar qaytaradi."""
    filled = round(width * pct / 100)
    return f"{'█' * filled}{'░' * (width - filled)}  {pct}%"


def _decode_escapes(s: str) -> str:
    """pytest parametrli test ID'sidagi ASCII-escape (``\\u041e``) ni haqiqiy
    belgига o'giradi — Telegram xabarida kirillcha O'QISHLI chiqsin.

    pytest parametrli ID'larда (masalan ``test_023[Отчёт по торговым точкам]``)
    lotin bo'lmagan belgilarni default holда ``\\uXXXX`` ga escape qiladi — xabar
    ``test_023[\\u041e\\u0442...]`` ko'rinishida uzun va tushunarsiz bo'lardi.
    Faqat ``\\uXXXX`` naqshini almashtiramiz (butun stringni ``unicode_escape``
    bilan dekod qilish boshqa ``\\`` larni buzishi mumkin)."""
    if "\\u" not in s:
        return s
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)


def _short_nodeid(nodeid: str) -> str:
    """``tests/x.py::test_010_region`` → ``test_010_region`` (test nomi).
    Kirillcha parametrli ID escape qilinган bo'lsa o'qishli belgiга qaytaradi."""
    return _decode_escapes(nodeid.split("::")[-1]) if nodeid else nodeid


def _render_progress(current_name: str | None = None) -> str:
    """Progress xabari matnini yig'adi (bar + hisoblagichlar + joriy test).
    ``current_name=None`` bo'lsa saqlangan ``_progress['current']`` ishlatiladi —
    shunda logreport ham joriy test nomini yo'qotmaydi."""
    if current_name is None:
        current_name = _progress.get("current", "")
    total = _progress["total"] or 1
    done = _progress["done"]
    pct = int(done * 100 / total)
    env_emoji = "\U0001F534" if TEST_ENV == "prod" else "\U0001F7E2"  # 🔴 prod / 🟢 dev
    lines = [
        "\U0001F504 <b>Smartup24 — Test bajarilmoqda</b>",
        "━━━━━━━━━━━━━",
        f"{env_emoji} {TEST_ENV.upper()} ({COMPANY_CODE})   "
        f"\U0001F4E6 <b>{_progress['suite'] or '—'}</b>",
        _progress_bar(pct),
        f"✅ {_progress['passed']}   ❌ {_progress['failed']}   ⏳ {done}/{_progress['total']}",
    ]
    # Jonli progressда vaqt KO'RSATILMAYDI (marginal + chalkash edi) — jami ishlash
    # vaqti faqat YAKUNIY xabarда beriladi (standart, qadrli). start_ts shu uchun.
    if current_name:
        lines.append(f"▶️ <code>{current_name}</code>")
    return "\n".join(lines)


# ----------------------------------------------------------------------------------------------------------------------

def pytest_collection_finish(session):
    """Testlar yig'ilib bo'lgach jonli progress xabarini yaratadi.

    ``pytest_sessionstart`` payti testlar hali yig'ilmagani uchun JAMI son
    NOMA'LUM — shuning uchun progress xabarini aynan shu yerda (collection
    tugagach) yaratamiz. Xabar ID'sini ``_progress`` da saqlaymiz; keyingi
    ``pytest_runtest_*`` hooklari uni tahrirlab (editMessageText) barni jonli
    yangilaydi. xdist worker EMAS, faqat master; ``--collect-only`` da o'tamiz."""
    if getattr(session.config, "workerinput", None) is not None:
        return
    if session.config.option.collectonly or not session.items:
        return
    _progress["total"] = len(session.items)
    _progress["done"] = 0
    _progress["passed"] = 0
    _progress["failed"] = 0
    _progress["suite"] = _suite_label(session.items)
    _progress["current"] = ""
    _progress["start_ts"] = time.time()
    # BITTA xabar oqimi (foydalanuvchi so'rovi 2026-09-04): "Test boshlandi"
    # xabarini yuboramiz va uning O'ZINI keyinchalik progress bar → yakuniy
    # natijага TAHRIRLAYMIZ (uch alohida xabar EMAS — chat shovqini kamayadi).
    # msg_id shu banner'niki; birinchi test boshlanganда (logstart) u progress
    # barга, sessiya oxirida esa yakuniy holatга tahrirlanadi.
    env_emoji = "\U0001F534" if TEST_ENV == "prod" else "\U0001F7E2"  # 🔴 prod / 🟢 dev
    start_text = (
        "\U0001F680 <b>Test boshlandi</b>\n"
        f"{env_emoji} {TEST_ENV.upper()} ({COMPANY_CODE})   "
        f"\U0001F4E6 <b>{_progress['suite']}</b>\n"
        f"\U0001F4CA {_progress['total']} test   \U0001F5A5 {HOST_LABEL}"
    )
    _progress["msg_id"] = _send_telegram(start_text)
    _persist_progress(start_text)  # bot o'qishi uchun (band-flash)
    # Pin QILMAYMIZ (senior): o'tkinchi progress'ни qadash professional emas —
    # pin/unpin tizim shovqini + bezovta. Xabar shunchaki oxirgi bo'lib turadi.


def pytest_runtest_logstart(nodeid, location):
    """Har test boshlanganда joriy test nomini yangilaydi. Progress FAYLini DOIM
    yozamiz (/status har doim yangi bo'lsin), faqat Telegram tahririni throttle
    qilamiz (``_PROGRESS_MIN_INTERVAL`` — rate-limit va tezlik uchun)."""
    if not _progress["msg_id"]:
        return
    _progress["current"] = _short_nodeid(nodeid)
    text = _render_progress()
    _persist_progress(text)   # DOIM — bot /status uchun yangi holat
    now = time.monotonic()
    if now - _progress["last_edit"] < _PROGRESS_MIN_INTERVAL:
        return
    _progress["last_edit"] = now
    _edit_telegram(_progress["msg_id"], text)


def pytest_runtest_logreport(report):
    """Har test tugaganda (call fazasi) done/passed/failed hisoblagichini oshiradi
    va progress barni yangilaydi.

    ``call`` fazasini sanaymiz — bitta test uchun setup/call/teardown uchta report
    beradi, biz mantiqiy testni bir marta (call) hisoblaymiz. Test call fazasigacha
    yetmay setup'da yiqilsa (error), uni ham bir marta sanash uchun setup xatosini
    alohida qamraymiz."""
    if not _progress["msg_id"]:
        return
    counted = report.when == "call" or (report.when == "setup" and report.failed)
    if not counted:
        return
    _progress["done"] += 1
    if report.passed:
        _progress["passed"] += 1
    elif report.failed:
        _progress["failed"] += 1
    # skipped/xfailed ni alohida sanamaymiz (done'ga kiradi, natijada ko'rinmaydi)
    text = _render_progress()
    _persist_progress(text)   # DOIM — bot /status uchun yangi holat (throttle'siz)
    now = time.monotonic()
    is_last = _progress["done"] >= _progress["total"]
    if not is_last and now - _progress["last_edit"] < _PROGRESS_MIN_INTERVAL:
        return
    _progress["last_edit"] = now
    # Oxirgi test — SINXRON (jarayon chiqishдан oldin so'rov tugasin)
    _edit_telegram(_progress["msg_id"], text, sync=is_last)


# ----------------------------------------------------------------------------------------------------------------------

def pytest_sessionfinish(session, exitstatus):
    """Testlar tugagach Telegram bildirishnoma yuboradi va Allure hisobot yaratadi."""
    # xdist worker jarayoni: bildirishnomani FAQAT master jo'natadi (aks holda har
    # worker o'z qismini yuborib, ko'p dublikat xabar chiqadi)
    if getattr(session.config, "workerinput", None) is not None:
        return

    # --collect-only da session.items to'ladi, lekin test ishlamaydi — xabar yubormaymiz
    if session.items and not session.config.option.collectonly:
        # terminalreporter.stats — passed/failed/error/xfailed ro'yxatlari shu yerda
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        stats = getattr(reporter, "stats", {}) if reporter else {}
        passed  = len(stats.get("passed", []))
        failed  = len(stats.get("failed", []))
        errors  = len(stats.get("error", []))
        skipped = len(stats.get("skipped", []))
        xfailed = len(stats.get("xfailed", []))
        xpassed = len(stats.get("xpassed", []))
        total   = passed + failed + errors + skipped + xfailed + xpassed

        status_emoji = "✅" if (failed == 0 and errors == 0) else "❌"
        env_emoji = "\U0001F534" if TEST_ENV == "prod" else "\U0001F7E2"  # 🔴 prod / 🟢 dev
        lines = [
            f"{status_emoji} <b>Smartup24 — Test yakunlandi</b>",
            "━━━━━━━━━━━━━",
            f"{env_emoji} {TEST_ENV.upper()} ({COMPANY_CODE})   "
            f"\U0001F4E6 <b>{_progress['suite'] or '—'}</b>",
            f"\U0001F5A5 {HOST_LABEL}",
            "",
            f"✅ Passed: <b>{passed}</b>",
            f"❌ Failed: <b>{failed}</b>",
            f"\U0001F6A8 Error: <b>{errors}</b>",
        ]
        if xfailed:
            lines.append(f"\U0001F536 Xfail (kutilgan): {xfailed}")
        if xpassed:
            lines.append(f"\U0001F536 Xpass: {xpassed}")
        if skipped:
            lines.append(f"⏭ Skipped: {skipped}")

        # Xato QAYERDA — yiqilgan/error test NOMLARINI ro'yxatlaymiz (foydalanuvchi
        # so'rovi: "3 failed bo'lsa qaysi testlar" — masalan client_view, supplier).
        fail_reports = list(stats.get("failed", [])) + list(stats.get("error", []))
        if fail_reports:
            lines.append("")
            lines.append("<b>Yiqilgan joylar:</b>")
            for rep in fail_reports[:10]:
                lines.append(f"  ❌ <code>{_short_nodeid(rep.nodeid)}</code>")
                # BIZNES tilida kontekst (qa_step bo'lса) — tushunarsiz stack o'rniga
                ctx = _failure_ctx.get(rep.nodeid)
                if ctx and ctx.get("step"):
                    lines.append(f"     ↳ {ctx['step']} — <b>{ctx['reason']}</b>")
                elif ctx and ctx.get("reason"):
                    lines.append(f"     ↳ {ctx['reason']}")
            if len(fail_reports) > 10:
                lines.append(f"  … va yana {len(fail_reports) - 10} ta")

        lines += ["━━━━━━━━━━━━━"]
        if _progress["start_ts"]:  # jami ishlash vaqti — eng qadrli vaqt ma'lumoti
            dur = int(time.time() - _progress["start_ts"])
            lines.append(f"⏱ Jami vaqt: <b>{dur // 60} daq {dur % 60} son</b>")
        lines.append(f"\U0001F4CA Jami: <b>{total}</b>   ·   exit: {exitstatus}")
        final_text = "\n".join(lines)
        # BITTA xabar oqimi (foydalanuvchi so'rovi): progress xabari bo'lsa uni
        # YAKUNIY holatga TAHRIRLAYMIZ — yangi xabar yubormaymiz. Progress
        # bo'lmasa (Telegram o'chiq/xato) yangi xabar sifatida yuboramiz.
        if _progress["msg_id"]:
            # SINXRON: jarayon shu funksiyadan keyin DARHOL chiqadi — daemon
            # thread'да bo'lsa yakuniy xabar yuborilmay qolardi (2026-08-27 bug).
            _edit_telegram(_progress["msg_id"], final_text, sync=True)
        else:
            _send_telegram("\n".join(lines))

        # Yiqilgan testlarning screenshotlarini oxirida yuboramiz — caption'да
        # allaqachon BIZNES tilida tavsif (qa_step) bor.
        for caption, png in _failure_shots:
            _send_telegram_photo(png, caption)

    # Progress faylini o'chiramiz — run tugadi, bot endi "band-flash" qilmasin.
    _persist_progress(None)
    _release_run_lock()   # global qulfni bo'shatamiz — keyingi run boshlanishi mumkin

    _finish_allure_report(session)


def _find_chrome():
    """Google Chrome bajariladigan faylini topadi (topilmasa None)."""
    candidates = [
        shutil.which("chrome"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def _open_report_in_browser(allure_bin):
    """Hisobotni brauzerda ochadi.

    `allure open` OS STANDART brauzerini ochadi — bu mashinada u Edge bo'lib qolgan
    (Windows default reg = Chrome bo'lsa-da, allure ichidagi node `open` Edge'ni ochyapti).
    Shuning uchun statik report'ni O'ZIMIZ bo'sh portda uzatib, aniq CHROME'da ochamiz.
    Chrome topilmasa `allure open`ga (standart brauzer) qaytamiz.
    """
    import subprocess
    import socket
    chrome = _find_chrome()
    if not chrome:
        subprocess.Popen([allure_bin, "open", ALLURE_REPORT_DIR])   # fallback: standart brauzer
        return
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)            # bo'sh port olamiz
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--directory", ALLURE_REPORT_DIR],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(1)                                                   # server ko'tarilishini kutamiz
    subprocess.Popen([chrome, f"http://127.0.0.1:{port}/"])
    print(f"\n[Allure] Hisobot Chrome'da ochildi: http://127.0.0.1:{port}/")


def _finish_allure_report(session):
    """Allure hisobot papkasini yaratadi; interaktiv (lokal) runda brauzerda ham ochadi.

    Bot/CI (HEADLESS=1) da hisobot GENERATSIYA qilinaveradi (statik
    `test-results/allure-report/` — keyin qo'lda `allure open` bilan ko'riladi),
    faqat `allure open` web-serveri OCHILMAYDI — u fon/CI jarayonini tugamay osib
    qo'yardi. Shunday qilib Telegram/bot runidan keyin ham tayyor hisobot qoladi.
    """
    # --collect-only da session.items TO'LADI, lekin test ishlamaydi — hisobot
    # yaratmaymiz (aks holda collection ham allure generate qilib yuboradi)
    if not session.items or session.config.option.collectonly:
        return
    import subprocess
    import shutil
    allure_bin = shutil.which("allure") or shutil.which("allure.cmd")
    if not allure_bin:
        # CI'da (ubuntu) allure CLI o'rnatilmagan bo'lishi mumkin — normal, eslatib o'tamiz.
        print(f"\n[Allure] CLI topilmadi. Qo'lda ishlatish: allure serve {ALLURE_RESULTS_DIR}")
        return
    # Brauzer ochish: CLI (--open-report/--no-open-report) > brauzer ko'rinishi
    # (HEADLESS) > default(ochiladi). Ochilmasa ham hisobot generatsiya qilinadi.
    open_browser = _open_report_for(session.config)
    try:
        # Allure 3 (npm) CLI: `--clean` flagi YO'Q, `-o` o'rniga `--output`.
        # Eski Allure 2 `--clean` report papkasini oldin tozalardi — endi shuni
        # o'zimiz qilamiz (aks holda eski report fayllari aralashib qoladi).
        if os.path.exists(ALLURE_REPORT_DIR):
            shutil.rmtree(ALLURE_REPORT_DIR)
        subprocess.run(
            [allure_bin, "generate", ALLURE_RESULTS_DIR, "--output", ALLURE_REPORT_DIR],
            check=True,
            timeout=120,
        )
        if open_browser:
            _open_report_in_browser(allure_bin)
        else:
            print(f"\n[Allure] Hisobot tayyor: {ALLURE_REPORT_DIR}\n"
                  f"          Ko'rish: allure open {ALLURE_REPORT_DIR}")
    except Exception as e:
        print(f"\n[Allure] Hisobot yaratishda xato: {e}")


# ----------------------------------------------------------------------------------------------------------------------

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Test xato bo'lganда screenshot + BIZNES tilida sabab (qa_step) qayd etadi."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        # BIZNES tilида kontekst: ayni ishlaган qa_step tavsifi + qisqa sabab
        # (tushunarsiz lokator/stack o'rniga). Telegram yakuniy xabarига chiqadi.
        exc = call.excinfo.value if call.excinfo else None
        page = item.funcargs.get("session_page") or item.funcargs.get("page")
        _failure_ctx[item.nodeid] = {
            "step": current_step_desc(),          # masalan "…'category-12343' ni tanlash"
            # page berilса — ko'rinib turган backend «Ошибка» dialogi ASL sabab
            # sifatida raw timeout/detach o'rniga ustun qo'yiladi.
            "reason": friendly_reason(exc, page),
        }
        # Page/browser allaqachon yopilgan bo'lishi mumkin (masalan, test browser
        # crash bilan yiqilsa) — bunda hook xatosi INTERNALERROR bo'lib butun
        # sessiyani to'xtatib qo'yadi. Shu sabab himoya bilan o'raymiz.
        if page:
            try:
                page.evaluate("""
                    const el = document.activeElement;
                    if (el && el !== document.body) {
                        el.style.outline = '3px solid red';
                        el.style.outlineOffset = '2px';
                        el.style.boxShadow = '0 0 0 4px rgba(255,0,0,0.3)';
                        const dot = document.createElement('div');
                        const rect = el.getBoundingClientRect();
                        dot.style.cssText = `
                            position: fixed;
                            left: ${rect.left + rect.width / 2 - 8}px;
                            top: ${rect.top + rect.height / 2 - 8}px;
                            width: 16px; height: 16px;
                            background: red; border-radius: 50%;
                            z-index: 999999; pointer-events: none;
                            box-shadow: 0 0 0 3px white;
                        `;
                        document.body.appendChild(dot);
                    }
                """)
                # QISQA timeout (8s): buzuq/muzlagan brauzerда screenshot default
                # 60s osilib, makereport'ni (asosiy thread) bloklab, progress'ni
                # muzlatardi (2026-08-27: ketma-ket FAILED testlarда progress qotib
                # qolgan edi). Osilsa — screenshot'siz o'tamiz.
                screenshot = page.screenshot(full_page=True, timeout=8000)
                allure.attach(
                    screenshot,
                    name="screenshot",
                    attachment_type=allure.attachment_type.PNG,
                )
                # Telegram uchun ALOHIDA viewport screenshot to'playmiz (sessiya
                # oxirida yuboriladi) — full_page juda baland bo'lib Telegram rasm
                # nisbat cheklovidan o'tmasligi mumkin, viewport toza ko'rinadi.
                if len(_failure_shots) < _MAX_FAILURE_SHOTS:
                    try:
                        # Caption'ga BIZNES tilida tavsif (qa_step) — skrinshot bilan
                        # birga: "❌ test — ↳ '…' ni tanlash — element topilmadi"
                        ctx = _failure_ctx.get(item.nodeid, {})
                        cap = f"❌ <code>{_short_nodeid(item.nodeid)}</code>"
                        if ctx.get("step"):
                            cap += f"\n↳ {ctx['step']} — <b>{ctx['reason']}</b>"
                        elif ctx.get("reason"):
                            cap += f"\n↳ {ctx['reason']}"
                        _failure_shots.append((cap, page.screenshot(timeout=8000)))
                    except Exception:
                        pass
            except Exception:
                pass


# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
