"""Appium driver yaratish — YAGONA joy (conftest ham, tools ham shuni ishlatadi)."""
import time

from appium import webdriver
from appium.options.android import UiAutomator2Options

from tests_mobile.config import APP_ACTIVITY, APP_PACKAGE, APPIUM_SERVER, DEVICE_UDID


def build_options() -> UiAutomator2Options:
    opts = UiAutomator2Options()
    opts.platform_name = "Android"
    opts.automation_name = "UiAutomator2"
    opts.app_package = APP_PACKAGE
    opts.app_activity = APP_ACTIVITY
    opts.no_reset = True                # login saqlanadi (har test qayta login qilmaydi)
    opts.new_command_timeout = 300
    opts.set_capability("appium:ignoreHiddenApiPolicyError", True)   # MIUI
    if DEVICE_UDID:
        opts.set_capability("appium:udid", DEVICE_UDID)
    return opts


def restart_app(drv) -> None:
    """Ilovani yopib qayta ochadi — oldingi testdan qolgan ekran/dialog ketadi."""
    try:
        drv.terminate_app(APP_PACKAGE)
    except Exception:
        pass
    drv.activate_app(APP_PACKAGE)
    time.sleep(2)   # Flutter birinchi kadrni chizguncha


def create_driver(*, restart_app_first: bool = True):
    """Yangi sessiya. implicit wait ATAYIN yo'q — hamma kutish explicit
    (BaseScreen). restart_app_first=False — joriy ekranni buzmaslik uchun (tools)."""
    drv = webdriver.Remote(APPIUM_SERVER, options=build_options())
    if restart_app_first:
        restart_app(drv)
    else:
        drv.activate_app(APP_PACKAGE)
    return drv
