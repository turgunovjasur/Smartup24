"""OrderScreen validatsiyasi — sanobar (mavjud Sanobar Distir / Saber tovarlari)
uzra to'liq zakaz oqimini yugurtirib tekshiradi (test EMAS, debug uchun).

Har qadam alohida bosiladi; xato chiqса o'sha ekran DUMP qilinadi (aniq nima
buzilganini ko'rish uchun). Ishlatish (project root, venv):
    .venv\\Scripts\\python -m tests_mobile.validate_order
"""
import os
import sys
import time
import xml.etree.ElementTree as ET

from appium import webdriver
from appium.options.android import UiAutomator2Options

from tests_mobile.config import APP_ACTIVITY, APP_PACKAGE, APPIUM_SERVER, DEVICE_UDID
from tests_mobile.pages.login_screen import LoginScreen
from tests_mobile.pages.order_screen import OrderScreen

LOGIN = os.getenv("MOBILE_LOGIN", "sanobar@sm24")
PASSWORD = os.getenv("MOBILE_PASSWORD", "1")

# sanobarда mavjud ma'lumot
SUPPLIER = "Sanobar Distir"
CATEGORY = "Oziq-ovqat"
PRODUCT = "Saber Energy Drink Maximum Power"


def _opts() -> UiAutomator2Options:
    o = UiAutomator2Options()
    o.platform_name = "Android"
    o.automation_name = "UiAutomator2"
    o.app_package = APP_PACKAGE
    o.app_activity = APP_ACTIVITY
    o.no_reset = True
    o.new_command_timeout = 300
    o.set_capability("appium:ignoreHiddenApiPolicyError", True)
    if DEVICE_UDID:
        o.set_capability("appium:udid", DEVICE_UDID)
    return o


def dump(drv):
    root = ET.fromstring(drv.page_source)
    print("\n----- EKRAN (xato paytидаgi) -----")
    for el in root.iter():
        cd = el.get("content-desc") or ""
        cls = (el.get("class") or "").split(".")[-1]
        if cd or "EditText" in cls or "Button" in cls:
            print(f"  desc={cd!r} <{cls}>")
    print("----------------------------------\n")


def main():
    drv = webdriver.Remote(APPIUM_SERVER, options=_opts())
    drv.implicitly_wait(5)
    try:
        drv.activate_app(APP_PACKAGE)
        ls = LoginScreen(drv)
        if not ls.is_logged_in():
            print(">>> login kerak")
            ls.ensure_logged_out()
            ls.open_login_form()
            ls.submit_login(LOGIN, PASSWORD)
            time.sleep(3)
        print(f">>> is_logged_in = {ls.is_logged_in()}")

        order = OrderScreen(drv)
        steps = [
            ("open_supplier_catalog", lambda: order.open_supplier_catalog(SUPPLIER)),
            ("open_category", lambda: order.open_category(CATEGORY)),
            ("add_to_cart", lambda: order.add_to_cart(PRODUCT, qty=1)),
            ("open_cart", lambda: order.open_cart()),
            ("choose_payment", lambda: order.choose_payment("Наличные")),
            ("choose_delivery_date", lambda: order.choose_delivery_date(1)),
            ("place_order", lambda: order.place_order(SUPPLIER)),
            ("open_last_order", lambda: order.open_last_order()),
            ("verify_order", lambda: order.verify_order(SUPPLIER, PRODUCT, "Наличные")),
        ]
        for name, fn in steps:
            print(f">>> {name} ...")
            try:
                fn()
            except Exception as e:
                print(f"!!! XATO {name}: {type(e).__name__}: {str(e)[:200]}")
                dump(drv)
                sys.exit(1)
        print(">>> HAMMA QADAM O'TDI — zakaz yaratildi va detali tekshirildi ✅")
        sys.exit(0)
    finally:
        drv.quit()


if __name__ == "__main__":
    main()
