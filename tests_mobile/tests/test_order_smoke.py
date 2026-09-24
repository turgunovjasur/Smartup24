"""Mobil zakaz smoke — tayyor klient (sanobar) va uning mavjud ma'lumotlari bilan.
Web seed kerak emas (~2-3 min); mobil oqim buzilganini tez ko'rsatadi."""
import allure
import pytest

from tests_mobile.config import (
    MOBILE_LOGIN, MOBILE_PASSWORD, SMOKE_CATEGORY, SMOKE_PRODUCT, SMOKE_SUPPLIER,
)
from tests_mobile.flows import create_and_verify_order
from tests_mobile.screens.login_screen import LoginScreen

pytestmark = [pytest.mark.mobile, allure.epic("Mobil"), allure.feature("Zakaz")]


def test_order_smoke(driver):
    # Har doim qayta login: ilovada boshqa user (masalan E2E client_user) qolgan bo'lishi mumkin
    login = LoginScreen(driver)
    login.login(MOBILE_LOGIN, MOBILE_PASSWORD)
    assert login.is_logged_in(), f"Mobil login muvaffaqiyatsiz: {MOBILE_LOGIN}"

    create_and_verify_order(driver, SMOKE_SUPPLIER, SMOKE_CATEGORY, SMOKE_PRODUCT)
