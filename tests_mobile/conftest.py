"""Mobil (Appium) fixtures: preflight, driver, yiqilganda artefaktlar.

Web conftest'dan alohida; root conftest'ning `code` / `runner_state` /
`session_page` fixture'lari bu yerda ham ko'rinadi (E2E test shundan foydalanadi).
"""
import subprocess
import time
import urllib.request
from pathlib import Path

import allure
import pytest

from tests_mobile.config import APPIUM_SERVER, DEVICE_UDID
from tests_mobile.core.driver_factory import create_driver

_SCREENSHOT_DIR = Path(__file__).parent / "screenshots"


# ── Preflight: Appium va telefon bo'lmasa tushunarli xabar bilan to'xtaydi ──
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
    problems = []
    if not _appium_ready():
        problems.append(f"Appium server ishlamayapti ({APPIUM_SERVER}). Yoqing:\n"
                        f"    appium --address 127.0.0.1 --port 4723")
    devices = _connected_devices()
    if not devices:
        problems.append("Telefon ulanmagan (`adb devices` bo'sh). Tekshiring: ma'lumot "
                        "uzatadigan USB kabel, 'Fayl uzatish' rejimi, USB debugging ruxsati.")
    elif DEVICE_UDID and DEVICE_UDID not in devices:
        problems.append(f"ANDROID_UDID={DEVICE_UDID} ulanmagan. Ulanganlar: {devices}")
    if problems:
        pytest.exit("MOBIL PREFLIGHT XATO:\n  - " + "\n  - ".join(problems), returncode=3)


# ── Driver: har test uchun yangi sessiya, ilova qayta ochiladi ──────────────
@pytest.fixture
def driver():
    drv = create_driver()
    try:
        yield drv
    finally:
        drv.quit()


# ── Yiqilganda: telefon ekrani + ekran tuzilmasi -> Allure (+ screenshots/) ──
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    drv = item.funcargs.get("driver")
    if report.when != "call" or not report.failed or drv is None:
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
