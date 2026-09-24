"""Mobil testlar uchun pytest fixtures (Appium).

Web `conftest.py` (Playwright) dan ALOHIDA — bu yerda `driver` (Appium
WebDriver) beriladi, `page` emas. Web testlarga umuman aralashmaydi.

SHART: Appium server ishlab turishi kerak (alohida terminalda):
    appium --address 127.0.0.1 --port 4723
Qurilma USB bilan ulangan + qulfi ochiq + "USB debugging (Security settings)"
yoqilgan bo'lishi kerak (Xiaomi/MIUI uchun). `_preflight` buni test boshida
tekshiradi va yo'q bo'lsa TUSHUNARLI xabar bilan to'xtatadi.
"""
import subprocess
import time
import urllib.request
from pathlib import Path

import allure
import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options

from tests_mobile.config import (
    APP_ACTIVITY, APP_PACKAGE, APPIUM_SERVER, DEVICE_UDID,
)

_SCREENSHOT_DIR = Path(__file__).parent / "screenshots"


def build_options() -> UiAutomator2Options:
    """Appium sessiya sozlamalari — YAGONA manba (debug skriptlar ham shuni oladi)."""
    opts = UiAutomator2Options()
    opts.platform_name = "Android"
    opts.automation_name = "UiAutomator2"
    opts.app_package = APP_PACKAGE
    opts.app_activity = APP_ACTIVITY
    opts.no_reset = True                # ilova ma'lumotini (login) tozalamaydi
    opts.new_command_timeout = 300
    # MIUI maxfiy sozlamaga tegishli xatoni e'tiborsiz qoldir
    opts.set_capability("appium:ignoreHiddenApiPolicyError", True)
    if DEVICE_UDID:
        opts.set_capability("appium:udid", DEVICE_UDID)
    return opts


# ── 3. PREFLIGHT: Appium + telefon bormi — yo'q bo'lsa aniq xabar ────────────
def _appium_ready() -> bool:
    try:
        with urllib.request.urlopen(f"{APPIUM_SERVER}/status", timeout=3) as r:
            return b'"ready":true' in r.read()
    except Exception:
        return False


def _connected_devices() -> list[str]:
    try:
        out = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return []
    return [ln.split()[0] for ln in out.splitlines()[1:] if ln.strip().endswith("device")]


@pytest.fixture(scope="session", autouse=True)
def _preflight():
    """Test boshlanishidan OLDIN: Appium server yoniqmi, telefon ulanganmi.
    Aks holda tushunarsiz ConnectionRefused o'rniga ANIQ sabab bilan to'xtaydi."""
    problems = []
    if not _appium_ready():
        problems.append(
            f"Appium server ishlamayapti ({APPIUM_SERVER}). Yoqing:\n"
            f"    appium --address 127.0.0.1 --port 4723"
        )
    devices = _connected_devices()
    if not devices:
        problems.append(
            "Telefon ulanmagan (`adb devices` bo'sh). Tekshiring: USB kabel (ma'lumot "
            "uzatadigan), telefonda 'Fayl uzatish' rejimi, USB debugging ruxsati."
        )
    elif DEVICE_UDID and DEVICE_UDID not in devices:
        problems.append(f"ANDROID_UDID={DEVICE_UDID} ulanmagan. Ulanganlar: {devices}")
    if problems:
        pytest.exit("MOBIL PREFLIGHT XATO:\n  - " + "\n  - ".join(problems), returncode=3)


# ── 2. DRIVER: implicit wait YO'Q + har test ilovani qayta ochadi ────────────
@pytest.fixture
def driver():
    """Har test uchun yangi Appium sessiyasi.

    - implicit wait ATAYIN yo'q: u explicit WebDriverWait bilan aralashsa har
      `timeout=1` tekshiruv amalda 5+ sek kutadi (sekin va beqaror). Hamma kutish
      BaseScreen'dagi explicit wait orqali.
    - Ilova YOPIB qayta ochiladi: oldingi testdan qolgan ochiq ekran/dialog
      yangi testga o'tmaydi (login `no_reset` tufayli saqlanadi)."""
    drv = webdriver.Remote(APPIUM_SERVER, options=build_options())
    try:
        try:
            drv.terminate_app(APP_PACKAGE)
        except Exception:
            pass
        drv.activate_app(APP_PACKAGE)
        time.sleep(2)   # Flutter birinchi kadrni chizguncha (ilova sovuq start)
        yield drv
    finally:
        drv.quit()


# ── 1. YIQILGANDA ARTEFAKT: screenshot + ekran tuzilmasi → Allure ────────────
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    drv = item.funcargs.get("driver")
    if drv is None:
        return
    try:
        png = drv.get_screenshot_as_png()
        allure.attach(png, name="telefon ekrani", attachment_type=allure.attachment_type.PNG)
        _SCREENSHOT_DIR.mkdir(exist_ok=True)
        (_SCREENSHOT_DIR / f"{item.name}_{time.strftime('%Y%m%d_%H%M%S')}.png").write_bytes(png)
    except Exception:
        pass
    try:
        allure.attach(drv.page_source, name="ekran tuzilmasi (XML)",
                      attachment_type=allure.attachment_type.XML)
    except Exception:
        pass
