"""Mobil pilot testi — Smartup24 ilovaga LOGIN.

Ishga tushirish (Appium server ishlab turishi + telefon ulangan/ochiq):
    $env:MOBILE_LOGIN="<login>"; $env:MOBILE_PASSWORD="<parol>"
    .venv\\Scripts\\python -m pytest tests_mobile/test_login.py -v -s

Login ma'lumotlari env orqali beriladi (koda yozilmaydi). Berilmasa test skip.
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

    # 1. Профиль -> Вход -> login formasi
    screen.open_login_form()

    # 2. Login/parolni kiritib Войти
    screen.submit_login(MOBILE_LOGIN, MOBILE_PASSWORD)

    # 3. Kirish muvaffaqiyatli — Профиль ekranida "Вход" endi yo'q
    assert screen.is_logged_in(), "Login muvaffaqiyatsiz: 'Вход' tugmasi hali ham ko'rinmoqda"


@pytest.mark.mobile
def test_login_wrong_password(driver):
    """Noto'g'ri parol bilan kirish RAD etiladi (negativ)."""
    if not MOBILE_LOGIN:
        pytest.skip("MOBILE_LOGIN env berilmagan")

    screen = LoginScreen(driver)
    screen.open_login_form()
    screen.submit_login(MOBILE_LOGIN, "wrong_password_000")

    # Login qilinmagan holatda qolishi kerak (forma yopilmaydi / xato chiqadi)
    assert screen.is_logged_out(), "Noto'g'ri parol bilan ham kirib ketdi (kutilmagan)"
