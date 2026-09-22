"""Mobil testlar uchun pytest fixtures (Appium).

Web `conftest.py` (Playwright) dan ALOHIDA — bu yerda `driver` (Appium
WebDriver) beriladi, `page` emas. Web testlarga umuman aralashmaydi.

SHART: Appium server ishlab turishi kerak (alohida terminalda):
    appium --address 127.0.0.1 --port 4723
Qurilma USB bilan ulangan + qulfi ochiq + "USB debugging (Security settings)"
yoqilgan bo'lishi kerak (Xiaomi/MIUI uchun).
"""
import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options

from tests_mobile.config import (
    APP_ACTIVITY, APP_PACKAGE, APPIUM_SERVER, DEVICE_UDID,
)


def _build_options() -> UiAutomator2Options:
    opts = UiAutomator2Options()
    opts.platform_name = "Android"
    opts.automation_name = "UiAutomator2"
    opts.app_package = APP_PACKAGE
    opts.app_activity = APP_ACTIVITY
    opts.no_reset = True                # ilova ma'lumotini tozalamaydi
    opts.new_command_timeout = 300
    # MIUI maxfiy sozlamaga tegishli xatoni e'tiborsiz qoldir
    opts.set_capability("appium:ignoreHiddenApiPolicyError", True)
    if DEVICE_UDID:
        opts.set_capability("appium:udid", DEVICE_UDID)
    return opts


@pytest.fixture
def driver():
    """Har test uchun yangi Appium sessiyasi (ilova old planga chiqariladi)."""
    drv = webdriver.Remote(APPIUM_SERVER, options=_build_options())
    drv.implicitly_wait(5)
    try:
        drv.activate_app(APP_PACKAGE)   # ilovani old planga
        yield drv
    finally:
        drv.quit()
