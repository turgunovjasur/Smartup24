import os
import json
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
    """Test sessiyasi uchun yagona cod qiymati"""
    return str(random.randint(1000, 9999))


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
