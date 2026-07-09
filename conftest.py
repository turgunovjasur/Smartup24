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
DATA_DIR = "test-results/data"
ALLURE_RESULTS_DIR = "test-results/allure-results"
ALLURE_REPORT_DIR = "test-results/allure-report"

# Timeout konstantalari — bitta joyda, butun loyiha bo'ylab ishlatiladi
DEFAULT_TIMEOUT    = 10_000    # click, fill, expect va boshqa locator amallari (ms)
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

def _auto_continue_session(page_obj: Page, password: str = "greenwhite") -> None:
    """``app-session-lock`` overlay'ini avtomatik yopadi.

    Sessiya ochilganidan ~30 daqiqa o'tgach app to'liq ekranli overlay
    chiqaradi va BARCHA kliklarni to'sib qo'yadi. Ikki holati bor:
    1) "Закрытие сессии" countdown dialogi (~20 sek) — "Продолжить" bosiladi;
    2) countdown o'tib ketgan bo'lsa "Блокировка экрана" parol qulfi
       (input#password + "Войти") — parol kiritib "Войти" bosiladi.
    Handler ichidagi xato yutiladi — trigger ko'rinib tursa keyingi amalda
    qayta uriniladi (regression 2026-07-08)."""
    # Trigger ikkala holatni ham qamraydi: countdown backdrop YOKI parol input
    lock = page_obj.locator(
        "app-session-lock button[aria-label='Продолжить'], app-session-lock form input"
    )

    def _unlock(_) -> None:
        # MUHIM: qulfning IKKALA bosqich elementlari DOMda bir vaqtda turadi
        # (biri yashirin) — count() bilan tarmoqlash parol bosqichida ham
        # yashirin "Продолжить"ni bosishga urinib, parol tarmog'iga hech
        # yetmay abadiy timeout bo'lar edi (runner 2026-07-09 12:11 trace).
        # Shuning uchun KO'RINADIGAN holatga qarab tarmoqlanadi, parol
        # bosqichi (terminal holat) birinchi tekshiriladi.
        # force=True: qulf bilan birga boshqa overlay (masalan Ошибка dialogi)
        # ochiq bo'lsa ham klik "intercepts pointer events" bilan to'silmasin.
        root = page_obj.locator("app-session-lock")
        try:
            # Parol qulfi: forma ichida bitta input (id yo'q, placeholder "Пароль")
            pwd = root.locator("form input")
            if pwd.count() and pwd.first.is_visible():
                pwd.first.fill(password, timeout=3_000, force=True)
                root.locator("button", has_text="Войти").first.click(timeout=3_000, force=True)
                return
            cont = root.locator("button", has_text="Продолжить")
            if cont.count() and cont.first.is_visible():
                cont.first.click(timeout=3_000, force=True)
        except Exception as exc:  # countdown -> qulf o'tish payti bo'lishi mumkin
            print(f"[session-lock] handler xatosi (qayta urinadi): {exc}")

    page_obj.add_locator_handler(lock, _unlock)


# ----------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def browser():
    """Bitta browser instance, to'liq ekranda ochiladi."""
    with sync_playwright() as p:
        browser_obj = p.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        yield browser_obj
        browser_obj.close()

# ----------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="session")
def session_browser():
    """Butun sessiya uchun bitta browser (test_smoke_runner uchun)."""
    with sync_playwright() as p:
        browser_obj = p.chromium.launch(
            headless=False,
            args=["--start-maximized"],
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
def save_data():
    """JSON faylga ma'lumot saqlash."""
    os.makedirs(DATA_DIR, exist_ok=True)

    def _save(key, value, file_name="data_store"):
        path = os.path.join(DATA_DIR, f"{file_name}.json")
        data = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        data[key] = value
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    return _save

# ----------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="session")
def load_data():
    """JSON fayldan ma'lumot o'qish."""
    def _load(key, file_name="data_store"):
        path = os.path.join(DATA_DIR, f"{file_name}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f).get(key)
                except json.JSONDecodeError:
                    return None
        return None

    return _load

# ----------------------------------------------------------------------------------------------------------------------



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
