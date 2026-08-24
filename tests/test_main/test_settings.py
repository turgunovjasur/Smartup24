"""Настройка (Модератор → Главное → Настройка, biruni moderator/setting) —
kompaniya sozlamalari sahifasi smoke testi.

Loyiha-playwright bilan tasdiqlangan:
- URL .../sb/sbr/moderator/setting, heading "Настройка".
- Yagona sozlamalar formasi: ~11 textbox + 3 switch + "Сохранить".
- Bu KOMPANIYA darajasidagi GLOBAL sozlamalar (CRUD EMAS). PROD config'ni
  O'ZGARTIRISH butun kompaniyaga ta'sir qiladi — shuning uchun test NON-DESTRUCTIVE:
  sahifa ochilishi + forma elementlari (Сохранить/input/switch) render bo'lishini
  tekshiradi, HECH NARSA SAQLAMAYDI.

DIQQAT: bu "Настройки шаблонов" (report_template formasi, URL ker/setting) EMAS —
"Главное"даги alohida yakka "Настройка" (URL moderator/setting) sahifasi.
"""
import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage

MENU = "Настройка"


def run_settings(page: Page, code=None) -> None:
    """Настройка sahifasi ochilishi va sozlamalar formasi elementlari (Сохранить +
    input + switch) render bo'lishini tekshiradi. PROD config O'ZGARTIRILMAYDI."""
    m = BasePage(page)

    with allure.step("Навигация: Модератор → Настройка"):
        flow_navigate(page, tab="Модератор", name=MENU)
        m.expect_heading(MENU)

    with allure.step("Sozlamalar formasi elementlari (Сохранить + input + switch) mavjudligi"):
        # PROD sozlamasini o'zgartirmaymiz — faqat forma render bo'lganini tasdiqlaymiz
        expect(page.get_by_role("button", name="Сохранить").first).to_be_visible()
        expect(page.get_by_role("textbox").first).to_be_visible()
        assert page.get_by_role("switch").count() >= 1, "Sozlama switch'lari topilmadi"


@allure.epic("Модератор")
@allure.feature("Настройка")
@allure.story("Настройки компании")
@allure.title("Настройка sahifasi va sozlamalar formasi ochilishi (non-destructive)")
def test_settings(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_settings(page, code)
