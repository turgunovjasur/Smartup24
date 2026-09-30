"""Ilovani Play Market'dan (qayta) o'rnatish va 1-ochilish ekranlarini o'tkazish.

conftest INSTALL_APP=1 bo'lganda test yugurishi boshida BIR MARTA chaqiradi.
Alohida qisqa Appium sessiyasi ishlatiladi (Play Market paketi, autoLaunch=False) —
ilova hali o'rnatilmagan bo'lsa ham sessiya ochiladi.

Play Market sahifasi (MCP/real qurilmada tasdiqlangan, 2026-09-30):
- UI o'zbek tilida, resource-id yashirilgan -> tugma content-desc bo'yicha;
  bir so'zda IKKI xil apostrof uchraydi ("O‘rnatish" / "Oʻrnatish").
- "Boshqa qurilmalar uchun ham mavjud" bo'limida BOSHQA telefonlarning
  "Oʻrnatish" tugmalari bor, yonida "Qurilmalarda oʻrnatish" menyusi —
  ularni bosmaslik uchun ekranda ENG TEPADAGI o'rnatish tugmasi olinadi.
1-ochilish: Android bildirishnoma ruxsati (permission_allow_button) -> "Til tanlang"
(Ru/Uz/En) -> Главная (mehmon).

Server: toza o'rnatilgan ilova PROD'ga ulanadi. Yashirin "Для разработчиков" menyusi:
login oynasidagi "ВЕРСИЯ ПРИЛОЖЕНИЯ : v X" raqamini ~400ms BOSIB TURIB ketma-ket
bosish (qisqa tegish SEZILMAYDI; 4-bosishda ochiladi) -> parol (sana DDMM -> D1 M1 D2 M2,
masalan 30.09 -> 3009) -> tasdiq tugmasi (nomi serverga qarab "Войти"/"Вход"; login
formasida ham "Войти" bor -> modal ichidan olinadi) -> "Изменить URL-адрес сервера" ->
maydonga host -> "Сохранить". Qiymat ilova qayta ochilganda saqlanib qoladi.
"""
from __future__ import annotations

import subprocess
import time
from datetime import date

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import StaleElementReferenceException

from tests_mobile.config import (
    APP_ACTIVITY, APP_LANGUAGE, APP_PACKAGE, APP_SERVER_HOST, APPIUM_SERVER, DEVICE_UDID,
    PLAY_INSTALL_TIMEOUT,
)
from tests_mobile.screens.base_screen import BaseScreen

PLAY_PACKAGE = "com.android.vending"
INSTALL_NAMES = ["O‘rnatish", "Oʻrnatish", "O'rnatish", "Установить", "Install"]
ALLOW_PERMISSION = (AppiumBy.XPATH, "//*[contains(@resource-id, 'permission_allow')]")
LANGUAGE_SCREEN = (AppiumBy.ACCESSIBILITY_ID, "Til tanlang")
HOME_TAB = (AppiumBy.ACCESSIBILITY_ID, "Главная")
PROFILE_TAB = (AppiumBy.ACCESSIBILITY_ID, "Профиль")
VERSION_LABEL = (AppiumBy.XPATH, "//*[contains(@content-desc, 'ВЕРСИЯ ПРИЛОЖЕНИЯ')]")
DEV_MODAL = (AppiumBy.ACCESSIBILITY_ID, "Для разработчиков")
DEV_PASSWORD = (AppiumBy.XPATH, "//*[@content-desc='введите пароль']/following::android.widget.EditText[1]")
DEV_SUBMIT = (AppiumBy.XPATH, "//*[@content-desc='введите пароль']"
                              "/following::*[@content-desc='Войти' or @content-desc='Вход'][1]")
URL_MENU_ITEM = (AppiumBy.ACCESSIBILITY_ID, "Изменить URL-адрес сервера")
URL_FIELD = (AppiumBy.XPATH, "//*[@content-desc='https://']/following::android.widget.EditText[1]")
URL_SAVE = (AppiumBy.ACCESSIBILITY_ID, "Сохранить")


def _adb(*args: str) -> str:
    cmd = ["adb"] + (["-s", DEVICE_UDID] if DEVICE_UDID else []) + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout


def app_version() -> str:
    """Telefondagi ilova versiyasi: "1.0.125 (158)" yoki "o'rnatilmagan"."""
    out = _adb("shell", "dumpsys", "package", APP_PACKAGE)
    name = next((ln.split("=", 1)[1].strip() for ln in out.splitlines() if "versionName=" in ln), None)
    code = next((ln.split("versionCode=", 1)[1].split()[0] for ln in out.splitlines() if "versionCode=" in ln), "?")
    return f"{name} ({code})" if name else "o'rnatilmagan"


def _play_session():
    o = UiAutomator2Options()
    o.platform_name = "Android"
    o.automation_name = "UiAutomator2"
    o.app_package = PLAY_PACKAGE
    o.app_activity = "com.google.android.finsky.activities.MainActivity"
    o.no_reset = True
    o.set_capability("appium:autoLaunch", False)
    o.set_capability("appium:ignoreHiddenApiPolicyError", True)
    if DEVICE_UDID:
        o.set_capability("appium:udid", DEVICE_UDID)
    return webdriver.Remote(APPIUM_SERVER, options=o)


def _tap_main_install_button(drv) -> None:
    """Play sahifasi yuklanishini kutib, ENG TEPADAGI o'rnatish tugmasini bosadi."""
    end = time.time() + 30
    while time.time() < end:
        try:
            buttons = [b for name in INSTALL_NAMES for b in drv.find_elements(AppiumBy.ACCESSIBILITY_ID, name)]
            if buttons:
                min(buttons, key=lambda b: b.rect["y"]).click()
                return
        except StaleElementReferenceException:
            pass                           # sahifa hali chizilyapti — qayta topamiz
        time.sleep(1)
    raise AssertionError(
        "Play Market'da 'O‘rnatish' tugmasi topilmadi (30s). Tekshiring: telefonda Google akkaunt "
        "kirganmi, internet bormi, bu akkaunt Smartup24 ichki sinovchilari ro'yxatidami"
    )


def _complete_first_launch(drv) -> None:
    """Ilovani ochib ruxsat va til ekranlarini o'tkazadi; Главная chiqquncha kutadi."""
    _adb("shell", "am", "start", "-n", f"{APP_PACKAGE}/{APP_ACTIVITY}")
    end = time.time() + 60
    while time.time() < end:
        allow = drv.find_elements(*ALLOW_PERMISSION)
        if allow:
            allow[0].click()
        elif drv.find_elements(*LANGUAGE_SCREEN):
            drv.find_element(AppiumBy.ACCESSIBILITY_ID, APP_LANGUAGE).click()
        elif drv.find_elements(*HOME_TAB):
            return
        time.sleep(1.5)
    raise AssertionError("Toza o'rnatishdan keyin ilova Главная ekraniga yetmadi (60s)")


def dev_menu_password(today: date | None = None) -> str:
    """Kun va oy raqamlari aralashtiriladi: DDMM -> D1 M1 D2 M2 (30.09 -> 3009, 24.06 -> 2046)."""
    t = today or date.today()
    dd, mm = f"{t.day:02d}", f"{t.month:02d}"
    return dd[0] + mm[0] + dd[1] + mm[1]


def _open_dev_menu(drv) -> None:
    s = BaseScreen(drv)
    for _ in range(3):                     # mehmon holatida "Профиль" login oynasini ochadi
        if s.exists(VERSION_LABEL, timeout=3):
            break
        if s.exists(PROFILE_TAB, timeout=15):
            s.tap(PROFILE_TAB)
    r = s.wait_for(VERSION_LABEL, error="Login oynasida 'ВЕРСИЯ ПРИЛОЖЕНИЯ' topilmadi").rect
    x, y = int(r["x"] + r["width"] * 0.9), int(r["y"] + r["height"] / 2)   # o'ng tomon = raqam
    for _ in range(8):
        drv.execute_script("mobile: longClickGesture", {"x": x, "y": y, "duration": 400})
        time.sleep(0.3)
        if s.exists(DEV_MODAL, timeout=0.5):
            return
    raise AssertionError("'Для разработчиков' oynasi ochilmadi (versiya raqami 8 marta bosildi)")


def set_server(drv, host: str = APP_SERVER_HOST) -> None:
    """Ilovani berilgan serverga o'tkazadi (allaqachon shu server bo'lsa saqlamaydi)."""
    s = BaseScreen(drv)
    _open_dev_menu(drv)
    s.type(DEV_PASSWORD, dev_menu_password())
    s.hide_keyboard()
    s.tap(DEV_SUBMIT)
    s.tap(URL_MENU_ITEM)
    field = s.wait_for(URL_FIELD, error="Server URL maydoni ochilmadi")
    if field.text.strip() != host:
        s.type(URL_FIELD, host)
        s.hide_keyboard()
        s.tap(URL_SAVE)
        time.sleep(2)
    drv.terminate_app(APP_PACKAGE)         # yangi server bilan toza ochilsin
    drv.activate_app(APP_PACKAGE)
    time.sleep(2)


def reinstall_from_play() -> str:
    """Bor bo'lsa o'chiradi, Play Market'dan o'rnatadi, 1-ochilishni o'tkazadi.
    O'rnatilgan versiyani qaytaradi."""
    drv = _play_session()
    try:
        if drv.is_app_installed(APP_PACKAGE):
            drv.remove_app(APP_PACKAGE)
        _adb("shell", "am", "start", "-a", "android.intent.action.VIEW",
             "-d", f"market://details?id={APP_PACKAGE}", "-p", PLAY_PACKAGE)
        _tap_main_install_button(drv)
        end = time.time() + PLAY_INSTALL_TIMEOUT
        while not drv.is_app_installed(APP_PACKAGE):
            if time.time() > end:
                raise AssertionError(f"Play Market'dan o'rnatish {PLAY_INSTALL_TIMEOUT}s ichida tugamadi")
            time.sleep(3)
        _complete_first_launch(drv)
        set_server(drv)                    # toza o'rnatish PROD'ga ulanadi -> TEST_ENV serveri
        return app_version()
    finally:
        drv.quit()
