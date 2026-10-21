"""Mobil (Appium) fixtures: preflight, driver, yiqilganda artefaktlar, INFRA-RETRY
(faqat core/infra.py dagi infra sabablar, BIR marta; Allure'da tag "infra-retry").

Web conftest'dan alohida; root conftest'ning `code` / `runner_state` /
`session_page` fixture'lari bu yerda ham ko'rinadi (E2E test shundan foydalanadi).
"""
import subprocess
import time
import traceback
import urllib.request
from pathlib import Path

import allure
import pytest

from tests_mobile.config import APP_PACKAGE, APPIUM_SERVER, DEVICE_UDID, INSTALL_APP
from tests_mobile.core.app_installer import app_version, reinstall_from_play
from tests_mobile.core.driver_factory import create_driver, restart_app
from tests_mobile.core.infra import MobileInfraError, infra_reason, instrumentation_crashed

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


def _prepare_driver(holder, *, recreate: bool = False):
    """Tirik sessiyada ilovani qayta ochadi; o'lgan bo'lsa (yoki ``recreate``) yangi sessiya."""
    drv = holder["drv"]
    if drv is not None and not recreate and _alive(drv):
        restart_app(drv)
        return drv
    if drv is not None:
        try:
            drv.quit()
        except Exception:
            pass
    holder["drv"] = None
    # avval holder'ga yoziladi — restart_app yiqilsa ham sessiya keyin quit qilinadi (oqmaydi)
    drv = holder["drv"] = create_driver(restart_app_first=False)
    restart_app(drv)
    return drv


def _attach_phone(drv, prefix: str) -> None:
    try:
        allure.attach(drv.get_screenshot_as_png(), name=f"{prefix}: telefon ekrani",
                      attachment_type=allure.attachment_type.PNG)
    except Exception:
        pass


def _mark_infra_retry(where: str, reason: str) -> None:
    allure.dynamic.tag("infra-retry")
    print(f"\n[INFRA-RETRY] {where}: {reason}", flush=True)


@pytest.fixture
def driver(_appium_session, _install_app):
    try:
        drv = _prepare_driver(_appium_session)
    except Exception as exc:
        # (a) splash/root node, (c) instrumentation crash — sessiya qayta yaratiladi, 1 marta
        reason = infra_reason(exc)
        if reason is None:
            raise
        _mark_infra_retry("driver setup", reason)
        with allure.step(f"INFRA-RETRY (1/1): Appium sessiyasi qayta yaratiladi — {reason}"):
            drv = _prepare_driver(_appium_session, recreate=True)
    yield drv


# ── INFRA-RETRY (test tanasi): faqat infra sabab, BIR marta ─────────────────────────────
# Test funksiyasi o'ralib, infra xatoda (core/infra.py) driver/ilova tiklanadi va funksiya
# yana bir marta chaqiriladi. Fixture'lar (session seed, runner_state) QAYTA yaratilmaydi;
# delete_e2e bosqichlari runner_state bayrog'ini faqat oxirida qo'yadi — bitta bosqichni
# qayta yurgizish keyingilarini buzmaydi. Tekshiruv xatolari o'zgarmasdan yuqoriga ketadi.
def _with_infra_retry(item, func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            drv = kwargs.get("driver", item.funcargs.get("driver"))
            reason = infra_reason(exc, drv)
            if reason is None:
                raise
            first_error = exc
        _mark_infra_retry(item.nodeid, reason)
        if drv is not None:
            _attach_phone(drv, "INFRA-RETRY 1-urinish")
        allure.attach("".join(traceback.format_exception(first_error)),
                      name="INFRA-RETRY 1-urinish xatosi", attachment_type=allure.attachment_type.TEXT)
        with allure.step(f"INFRA-RETRY (1/1) — 2-urinish. 1-urinish sababi: {reason}"):
            holder = item._request.getfixturevalue("_appium_session")
            new_drv = _prepare_driver(holder, recreate=instrumentation_crashed(first_error))
            item.funcargs["driver"] = new_drv
            if "driver" in kwargs:
                kwargs["driver"] = new_drv
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                again = infra_reason(exc, new_drv)
                if again and not isinstance(exc, MobileInfraError):
                    raise MobileInfraError(f"2-urinishda ham infra xato — {again}") from exc
                raise
    return wrapper


@pytest.hookimpl(hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    if "driver" not in pyfuncitem.fixturenames:      # faqat web bosqichlar — retry yo'q
        yield
        return
    original = pyfuncitem.obj
    pyfuncitem.obj = _with_infra_retry(pyfuncitem, original)
    try:
        yield
    finally:
        pyfuncitem.obj = original


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
