"""Locator KASHFIYOTI uchun yordamchi skript (test EMAS).

Mobil ekranning UI daraxtini o'qib, foydali elementlarni (content-desc / matn /
EditText / tugma + bosiladimi) ro'yxat qilib chiqaradi. Shu ro'yxatdan
`pages/order_screen.py` locatorlari aniqlanadi.

ISHLATISH (project root'dan, venv python bilan):
    # 1) Hozirgi ekranни o'qish (hech narsaga tegmaydi — READ-ONLY):
    .venv\\Scripts\\python -m tests_mobile.explore
    # 2) sanobar bilan login qilib, so'ng ekранни o'qish:
    .venv\\Scripts\\python -m tests_mobile.explore login
    # 3) login qilib, keyin ketma-ket content-desc'larни bosib, oxirida o'qish:
    .venv\\Scripts\\python -m tests_mobile.explore login "Профиль" "Заказы"

DIQQAT: no_reset=True — ilova holati sessiyalar orasида saqlanadi (login qilingan
bo'lsa qolaveradi). Appium server ishlab turishi + telefon ulangan bo'lishi shart.
"""
import sys
import time
import xml.etree.ElementTree as ET

from appium import webdriver
from appium.options.android import UiAutomator2Options

from tests_mobile.config import (
    APP_ACTIVITY, APP_PACKAGE, APPIUM_SERVER, DEVICE_UDID,
)
from tests_mobile.pages.login_screen import LoginScreen

# Kashfiyot uchun demo klient (hamkorlik + tovarlari bor) — env bilan almashtirsa bo'ladi
import os
EXPLORE_LOGIN = os.getenv("MOBILE_LOGIN", "sanobar@sm24")
EXPLORE_PASSWORD = os.getenv("MOBILE_PASSWORD", "1")


def _build_options() -> UiAutomator2Options:
    opts = UiAutomator2Options()
    opts.platform_name = "Android"
    opts.automation_name = "UiAutomator2"
    opts.app_package = APP_PACKAGE
    opts.app_activity = APP_ACTIVITY
    opts.no_reset = True
    opts.new_command_timeout = 300
    opts.set_capability("appium:ignoreHiddenApiPolicyError", True)
    if DEVICE_UDID:
        opts.set_capability("appium:udid", DEVICE_UDID)
    return opts


def dump(driver) -> None:
    """Joriy ekранning foydali elementlarини chiqaradi."""
    root = ET.fromstring(driver.page_source)
    print("\n" + "=" * 70)
    print("EKRAN ELEMENTLARI  [bosiladimi] desc / text / klass")
    print("=" * 70)
    seen = 0
    for el in root.iter():
        cd = el.get("content-desc") or ""
        txt = el.get("text") or ""
        cls = el.get("class") or ""
        clk = el.get("clickable") or ""
        short = cls.split(".")[-1]
        if cd or txt or "EditText" in cls or "Button" in cls:
            mark = "TAP" if clk == "true" else "   "
            print(f"[{mark}] desc={cd!r}  text={txt!r}  <{short}>")
            seen += 1
    if not seen:
        print("(foydali element topilmadi — ehtimol yuklanmoqda yoki boshqa ekran)")
    print("=" * 70 + "\n")


def tree(driver) -> None:
    """Joriy ekranni INDENT bilan daraxt ko'rinishida chiqaradi (parent/child
    munosabatini ko'rish uchun — XPath tuzishда kerak)."""
    root = ET.fromstring(driver.page_source)
    print("\n" + "=" * 70)
    print("EKRAN DARAXTI (indent = ichkarilagan)")
    print("=" * 70)

    def walk(el, depth):
        cd = el.get("content-desc") or ""
        cls = (el.get("class") or "").split(".")[-1]
        rid = el.get("resource-id") or ""
        label = cd[:40].replace("\n", "|") if cd else ""
        extra = f" desc={label!r}" if label else ""
        if rid:
            extra += f" id={rid}"
        print("  " * depth + f"<{cls}>{extra}")
        for ch in el:
            walk(ch, depth + 1)

    walk(root, 0)
    print("=" * 70 + "\n")


def main() -> None:
    args = sys.argv[1:]
    show_tree = args and args[0] == "tree"
    if show_tree:
        args = args[1:]
    do_login = args and args[0] == "login"
    taps = args[1:] if do_login else args

    drv = webdriver.Remote(APPIUM_SERVER, options=_build_options())
    drv.implicitly_wait(5)
    try:
        drv.activate_app(APP_PACKAGE)
        ls = LoginScreen(drv)

        if do_login:
            print(f">>> ensure_logged_out + open_login_form + login: {EXPLORE_LOGIN}")
            ls.ensure_logged_out()
            ls.open_login_form()
            ls.submit_login(EXPLORE_LOGIN, EXPLORE_PASSWORD)
            time.sleep(3)
            print(f">>> is_logged_in = {ls.is_logged_in()}")

        for t in taps:
            if t.startswith("t:"):
                text = t[2:]
                print(f">>> type (1-EditText): {text!r}")
                from appium.webdriver.common.appiumby import AppiumBy
                ed = drv.find_element(AppiumBy.CLASS_NAME, "android.widget.EditText")
                ed.click()
                ed.clear()
                ed.send_keys(text)
                time.sleep(2)  # filtrlash uchun kutamiz (live search)
            elif t.startswith("x:"):
                xp = t[2:]
                print(f">>> tap (xpath): {xp!r}")
                from appium.webdriver.common.appiumby import AppiumBy
                drv.find_element(AppiumBy.XPATH, xp).click()
            elif t.startswith("c:"):
                needle = t[2:]
                print(f">>> tap (contains): {needle!r}")
                from appium.webdriver.common.appiumby import AppiumBy
                el = drv.find_element(
                    AppiumBy.XPATH, f'//*[contains(@content-desc, "{needle}")]'
                )
                el.click()
            else:
                print(f">>> tap: {t!r}")
                ls.tap(t)
            time.sleep(1.5)

        if show_tree:
            tree(drv)
        else:
            dump(drv)
    finally:
        drv.quit()


if __name__ == "__main__":
    main()
