"""Login / logout (tayyor klient, config.MOBILE_LOGIN). Har test toza holatdan boshlanadi."""
import allure
import pytest

from tests_mobile.config import MOBILE_LOGIN, MOBILE_PASSWORD
from tests_mobile.screens.login_screen import LoginScreen

pytestmark = [pytest.mark.mobile, allure.epic("Mobil"), allure.feature("Login")]


@pytest.fixture
def login_screen(driver) -> LoginScreen:
    return LoginScreen(driver)


def test_login_valid(login_screen):
    login_screen.login(MOBILE_LOGIN, MOBILE_PASSWORD)
    assert login_screen.is_logged_in(), "Login muvaffaqiyatsiz: 'Вход' hali ko'rinmoqda"


def test_login_wrong_password(login_screen):
    login_screen.login(MOBILE_LOGIN, "wrong_password_000")
    assert login_screen.on_login_form(timeout=6), "Noto'g'ri parol bilan kirib ketdi"


def test_logout(login_screen):
    login_screen.login(MOBILE_LOGIN, MOBILE_PASSWORD)
    assert login_screen.is_logged_in(), "Login bo'lmadi — logout tekshirib bo'lmaydi"
    login_screen.logout()
    assert login_screen.is_logged_out(), "Logout muvaffaqiyatsiz: 'Вход' qaytmadi"
