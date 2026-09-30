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

from tests_mobile.config import APP_PACKAGE, APPIUM_SERVER, DEVICE_UDID, INSTALL_APP
from tests_mobile.core.app_installer import app_version, reinstall_from_play
from tests_mobile.core.driver_factory import create_driver, restart_app

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


# ── INSTALL_APP: 1 -> Play Market'dan (qayta) o'rnatish; 0 -> ilovaga tegmaslik ──
@pytest.fixture(scope="session", autouse=True)
def _install_app(_preflight, request):
    if INSTALL_APP:
        print(f"\n[INSTALL_APP=1] {APP_PACKAGE}: Play Market'dan o'rnatilmoqda "
              f"(hozirgi: {app_version()})...", flush=True)
        try:
            version = reinstall_from_play()
        except Exception as e:
            pytest.exit(f"ILOVANI O'RNATIB BO'LMADI: {type(e).__name__}: {str(e).splitlines()[0][:300]}", returncode=3)
        source = "Play Market (qayta o'rnatildi)"
    else:
        version = app_version()
        if version == "o'rnatilmagan":
            pytest.exit(f"{APP_PACKAGE} telefonda o'rnatilmagan. INSTALL_APP=1 bilan ishga "
                        f"tushiring (Play Market'dan o'rnatadi).", returncode=3)
        source = "telefondagi (INSTALL_APP=0)"
    print(f"[ilova] {APP_PACKAGE} {version} — {source}", flush=True)
    alluredir = request.config.getoption("allure_report_dir", None)
    if alluredir:
        try:
            with open(Path(alluredir) / "environment.properties", "a", encoding="utf-8") as f:
                f.write(f"Mobile.App={APP_PACKAGE} {version}\nMobile.App.Source={source}\n")
        except OSError:
            pass


# ── Driver: BITTA Appium sessiyasi, lekin har test oldidan ilova qayta ochiladi ──
# Sessiya yaratish ~10-15s — har testda qayta yaratmaymiz. Izolyatsiya ilovani
# yopib-ochish bilan saqlanadi. Sessiya o'lgan bo'lsa (masalan E2E web seed
# paytida new_command_timeout o'tib ketsa) — yangisi yaratiladi.
def _alive(drv) -> bool:
    try:
        drv.current_package
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def _appium_session():
    holder = {"drv": None}
    yield holder
    if holder["drv"] is not None:
        try:
            holder["drv"].quit()
        except Exception:
            pass


@pytest.fixture
def driver(_appium_session, _install_app):
    drv = _appium_session["drv"]
    if drv is not None and _alive(drv):
        restart_app(drv)
    else:
        if drv is not None:
            try:
                drv.quit()
            except Exception:
                pass
        drv = _appium_session["drv"] = create_driver()
    yield drv


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
