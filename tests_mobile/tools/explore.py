"""Locator kashfiyoti (test EMAS): joriy ekran elementlarini chiqaradi.

    python -m tests_mobile.tools.explore                    # joriy ekran (hech narsaga tegmaydi)
    python -m tests_mobile.tools.explore login              # config user bilan login, keyin ekran
    python -m tests_mobile.tools.explore tree               # daraxt ko'rinishi (XPath tuzish uchun)
    python -m tests_mobile.tools.explore login "Профиль" "c:Заказ" "x://..." "t:matn"

Bosish argumentlari: "<desc>" aniq | "c:<matn>" contains | "x:<xpath>" | "t:<matn>" 1-inputga yozish.
Appium Inspector (http://127.0.0.1:4723/inspector) qulayroq muqobil.
"""
import sys
import time
import xml.etree.ElementTree as ET

from appium.webdriver.common.appiumby import AppiumBy

from tests_mobile.config import MOBILE_LOGIN, MOBILE_PASSWORD
from tests_mobile.core.driver_factory import create_driver
from tests_mobile.screens.base_screen import BaseScreen, contains, desc, xpath
from tests_mobile.screens.login_screen import LoginScreen


def dump(driver) -> None:
    """Foydali elementlar: [TAP] = bosiladi."""
    print("\n" + "=" * 70)
    seen = 0
    for el in ET.fromstring(driver.page_source).iter():
        cd, txt, cls = el.get("content-desc") or "", el.get("text") or "", el.get("class") or ""
        if cd or txt or "EditText" in cls or "Button" in cls:
            mark = "TAP" if el.get("clickable") == "true" else "   "
            print(f"[{mark}] desc={cd!r}  text={txt!r}  <{cls.split('.')[-1]}>")
            seen += 1
    if not seen:
        print("(foydali element yo'q — ekran yuklanmoqda yoki bo'sh)")
    print("=" * 70 + "\n")


def tree(driver) -> None:
    """Ichma-ich daraxt (parent/child — XPath tuzish uchun)."""
    def walk(el, depth):
        cd = (el.get("content-desc") or "")[:40].replace("\n", "|")
        cls = (el.get("class") or "").split(".")[-1]
        print("  " * depth + f"<{cls}>" + (f" desc={cd!r}" if cd else ""))
        for ch in el:
            walk(ch, depth + 1)
    walk(ET.fromstring(driver.page_source), 0)


def main() -> None:
    args = sys.argv[1:]
    show_tree = bool(args) and args[0] == "tree"
    args = args[1:] if show_tree else args
    do_login = bool(args) and args[0] == "login"
    taps = args[1:] if do_login else args

    drv = create_driver(restart_app=False)   # joriy ekranni buzmaslik uchun
    try:
        screen = BaseScreen(drv)
        if do_login:
            print(f">>> login: {MOBILE_LOGIN}")
            LoginScreen(drv).login(MOBILE_LOGIN, MOBILE_PASSWORD)
        for t in taps:
            print(f">>> {t!r}")
            if t.startswith("t:"):
                screen.type((AppiumBy.CLASS_NAME, "android.widget.EditText"), t[2:])
            elif t.startswith("x:"):
                screen.tap(xpath(t[2:]))
            elif t.startswith("c:"):
                screen.tap(contains(t[2:]))
            else:
                screen.tap(desc(t))
            time.sleep(1.5)   # ekran almashsin (kashfiyot vositasi — test emas)
        tree(drv) if show_tree else dump(drv)
    finally:
        drv.quit()


if __name__ == "__main__":
    main()
