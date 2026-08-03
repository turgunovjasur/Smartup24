import os
import json
import time
import shutil
import socket
import random
import allure
import pytest
from typing import Any, Generator
from playwright.sync_api import sync_playwright, Browser, Page, expect

from flows.flow_authorization import logout

TRACE_DIR = "test-results/traces"
ALLURE_RESULTS_DIR = "test-results/allure-results"
ALLURE_REPORT_DIR = "test-results/allure-report"

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

def pytest_configure(config):
    """Allure hisoboti uchun environment, categories, executor va history tayyorlaydi."""
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
        f.write(f"Host={socket.gethostname()}\n")

    # Categories
    categories_src = "allure/categories.json"
    categories_dst = os.path.join(ALLURE_RESULTS_DIR, "categories.json")
    if os.path.exists(categories_src):
        shutil.copy(categories_src, categories_dst)

    # Executor
    executor_path = os.path.join(ALLURE_RESULTS_DIR, "executor.json")
    executor_data = {
        "name": socket.gethostname(),
        "type": "local",
        "buildName": "Smoke Tests",
        "reportName": "Allure Report"
    }
    with open(executor_path, "w", encoding="utf-8") as f:
        json.dump(executor_data, f, indent=2)

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
        deadline = time.monotonic() + 60
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
        print("[session-lock] 60s ichida qulf yechilmadi")

    page_obj.add_locator_handler(lock, _unlock)


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

# CI/headless: HEADLESS=1 env var bilan brauzer ko'rinmasdan ishlaydi
# (default — ko'rinadigan brauzer, lokal xatti-harakat o'zgarmaydi).
_HEADLESS = os.getenv("HEADLESS") == "1"


@pytest.fixture
def browser():
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
            headless=_HEADLESS,
            args=["--start-maximized", "--window-size=1920,1080"],
        )
        yield browser_obj
        browser_obj.close()

# ----------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="session")
def session_browser():
    """Butun sessiya uchun bitta browser (test_smoke_runner uchun).

    ``--window-size=1920,1080`` sababi uchun ``browser`` fixture izohiga qarang
    (past viewport'da dropdown varianti ekrandan chiqib ketadi)."""
    with sync_playwright() as p:
        browser_obj = p.chromium.launch(
            headless=_HEADLESS,
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
    """test_all_runner testlari ORASIDA runtime qiymatlarni uzatish uchun umumiy
    lug'at (session scope).

    Aggregator mega-test bo'lganda bu qiymatlar oddiy lokal o'zgaruvchilar edi
    (masalan group_a'da yaratilgan ``product_name`` → linking → zakaz). Endi har
    qadam ALOHIDA test bo'lganligi uchun ular orasida ma'lumot shu lug'at orqali
    uzatiladi: ``runner_state["ga_product_name"]``, ``runner_state["konkurs_region"]``."""
    return {}


# ----------------------------------------------------------------------------------------------------------------------

def pytest_sessionfinish(session, exitstatus):
    """Testlar tugagach Allure hisobot yaratadi va brauzerda ochadi."""
    # --collect-only da session.items TO'LADI, lekin test ishlamaydi — hisobot
    # yaratmaymiz (aks holda collection ham allure generate/open qilib yuboradi)
    if not session.items or session.config.option.collectonly:
        return
    import subprocess
    import shutil
    allure_bin = shutil.which("allure") or shutil.which("allure.cmd")
    if not allure_bin:
        print(f"\n[Allure] CLI topilmadi. Qo'lda ishlatish: allure serve {ALLURE_RESULTS_DIR}")
        return
    try:
        subprocess.run(
            [allure_bin, "generate", "--clean", ALLURE_RESULTS_DIR, "-o", ALLURE_REPORT_DIR],
            check=True,
            timeout=120,
        )
        subprocess.Popen([allure_bin, "open", ALLURE_REPORT_DIR])
    except Exception as e:
        print(f"\n[Allure] Hisobot yaratishda xato: {e}")


# ----------------------------------------------------------------------------------------------------------------------

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Test xato bo'lganda screenshot olib Allure ga qo'shadi."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        page = item.funcargs.get("session_page") or item.funcargs.get("page")
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
                screenshot = page.screenshot(full_page=True)
                allure.attach(
                    screenshot,
                    name="screenshot",
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception:
                pass


# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
