"""Mobil pilot testi — Smartup24 ilovaga LOGIN (takrorlanadigan).

Har test TOZA holatdan boshlanadi (`ensure_logged_out`) — shuning uchun ketma-ket
va qayta-qayta ishlaydi. Login ma'lumotlari env orqali (koda yozilmaydi):
    $env:MOBILE_LOGIN="<login>"; $env:MOBILE_PASSWORD="<parol>"
    .venv\\Scripts\\python -m pytest tests_mobile/test_login.py -v -s
Appium server ishlab turishi + telefon ulangan/qulfi ochiq bo'lishi shart.
"""
import pytest

from tests_mobile.config import MOBILE_LOGIN, MOBILE_PASSWORD
from tests_mobile.pages.login_screen import LoginScreen


@pytest.mark.mobile
def test_login_valid(driver):
    """To'g'ri login/parol bilan tizimga kirish muvaffaqiyatli bo'ladi."""
    if not MOBILE_LOGIN or not MOBILE_PASSWORD:
        pytest.skip("MOBILE_LOGIN / MOBILE_PASSWORD env berilmagan")

    screen = LoginScreen(driver)
    screen.ensure_logged_out()                       # toza holat
    screen.open_login_form()
    screen.submit_login(MOBILE_LOGIN, MOBILE_PASSWORD)

    assert screen.is_logged_in(), "Login muvaffaqiyatsiz: 'Вход' hali ko'rinmoqda"


@pytest.mark.mobile
def test_login_wrong_password(driver):
    """Noto'g'ri parol bilan kirish RAD etiladi (negativ)."""
    if not MOBILE_LOGIN:
        pytest.skip("MOBILE_LOGIN env berilmagan")

    screen = LoginScreen(driver)
    screen.ensure_logged_out()                       # toza holat
    screen.open_login_form()
    screen.submit_login(MOBILE_LOGIN, "wrong_password_000")

    # Login RAD etilishi kerak — ilova hali login FORMASIDA qoladi (kirmaydi)
    assert screen.on_login_form(timeout=6), "Noto'g'ri parol bilan kirib ketdi (kutilmagan)"


@pytest.mark.mobile
def test_logout(driver):
    """Login qilingach tizimdan chiqish ishlaydi."""
    if not MOBILE_LOGIN or not MOBILE_PASSWORD:
        pytest.skip("MOBILE_LOGIN / MOBILE_PASSWORD env berilmagan")

    screen = LoginScreen(driver)
    screen.ensure_logged_out()
    screen.open_login_form()
    screen.submit_login(MOBILE_LOGIN, MOBILE_PASSWORD)
    assert screen.is_logged_in(), "Login bo'lmadi — logout testi uchun shart"

    screen.logout()
    assert screen.is_logged_out(), "Logout muvaffaqiyatsiz: 'Вход' qaytmadi"
