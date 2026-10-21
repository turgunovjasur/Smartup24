"""Appium driver yaratish — YAGONA joy (conftest ham, tools ham shuni ishlatadi)."""
import time

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from tests_mobile.config import APP_ACTIVITY, APP_PACKAGE, APPIUM_SERVER, DEVICE_UDID
from tests_mobile.core.infra import MobileInfraError

# Flutter ilova (splash/animatsiya) UI thread'ni band qiladi — UiAutomator2 har amaldan
# oldin "idle"ni kutadi va sekin emulyatorda "Timed out ... waiting for the root
# AccessibilityNodeInfo" beradi. UiAutomator2 Settings API: waitForIdleTimeout = 0
# (idle kutilmaydi) — Flutter/animatsiyali ilovalar uchun tavsiya etilgan sozlama.
DRIVER_SETTINGS = {"waitForIdleTimeout": 0}
# sekund: qayta ochilgan ilova splash'dan chiqib, element berguncha. Sekin emulyatorda
# o'lchangan: 50.2 / 51.2 / 54.5 s (2026-10-15) — 60 s chegara juda tor, shuning uchun 120.
APP_READY_TIMEOUT = 120
# Splash (oq fon + logo) da content-desc'li element yo'q; ilova tayyor bo'lgach
# tab/tugmalar ("Главная", "Профиль", ...) content-desc bilan chiqadi.
_ANY_DESC = (AppiumBy.XPATH, "//*[string-length(@content-desc) > 0]")


def build_options() -> UiAutomator2Options:
    opts = UiAutomator2Options()
    opts.platform_name = "Android"
    opts.automation_name = "UiAutomator2"
    opts.app_package = APP_PACKAGE
    opts.app_activity = APP_ACTIVITY
    opts.no_reset = True                # login saqlanadi (har test qayta login qilmaydi)
    # Web+mobil testlarda bitta test ichida web qadamlar (holat o'zgartirish) bir necha
    # daqiqa davom etadi — sessiya shu paytda o'lmasin (S-05 katalog guruhi, 2026-10-16).
    opts.new_command_timeout = 1800
    opts.set_capability("appium:ignoreHiddenApiPolicyError", True)   # MIUI
    # Sekin emulyatorda UiAutomator2 instrumentation 30s (default) ichida ko'tarilmaydi
    # ("instrumentation process cannot be initialized within 30000ms", 2026-10-15).
    opts.set_capability("appium:uiautomator2ServerLaunchTimeout", 90_000)
    if DEVICE_UDID:
        opts.set_capability("appium:udid", DEVICE_UDID)
    return opts


def wait_app_ready(drv, timeout: float = APP_READY_TIMEOUT) -> None:
    """Ilova birinchi interaktiv ekranini chizguncha kutadi. Splash paytida UiAutomator2
    root node'ni ololmay WebDriverException beradi — bu xato e'tiborsiz qoldirilib,
    1s oraliqda qayta so'raladi (explicit polling, time.sleep emas)."""
    try:
        WebDriverWait(drv, timeout, poll_frequency=1,
                      ignored_exceptions=(WebDriverException,)).until(
            lambda d: d.find_elements(*_ANY_DESC))
    except TimeoutException:
        raise MobileInfraError(
            f"Ilova {timeout}s ichida tayyor bo'lmadi (splash'da qoldi yoki UiAutomator2 "
            f"root AccessibilityNodeInfo'ni ololmadi)") from None


def restart_app(drv) -> None:
    """Ilovani yopib qayta ochadi — oldingi testdan qolgan ekran/dialog ketadi."""
    try:
        drv.terminate_app(APP_PACKAGE)
    except Exception:
        pass
    drv.activate_app(APP_PACKAGE)
    time.sleep(2)   # Flutter birinchi kadrni chizguncha
    wait_app_ready(drv)


def create_driver(*, restart_app_first: bool = True):
    """Yangi sessiya. implicit wait ATAYIN yo'q — hamma kutish explicit
    (BaseScreen). restart_app_first=False — joriy ekranni buzmaslik uchun (tools)."""
    drv = webdriver.Remote(APPIUM_SERVER, options=build_options())
    drv.update_settings(DRIVER_SETTINGS)
    if restart_app_first:
        restart_app(drv)
    else:
        drv.activate_app(APP_PACKAGE)
    return drv
