"""Перевод строки таблицы (Модератор → Главное, biruni md/table_translate_list) —
jadval yozuvlari tarjimasi testi.

MCP bilan real DOM'da tasdiqlangan (2026-08-07, PROD/test):

Bu modul CREATE-CRUD EMAS — oldindan belgilangan tizim jadvallarining ustun/yozuv
nomlarini tillarga (uz/ru/en) tarjima qilish. "Создать" YO'Q.

Oqim:
  - table_translate_list (heading "Перевод строки таблицы"): 10 ta jadval
    (Товары, Виды оплаты, Валюты, Регионы, ...). Ustunlar: Название таблицы / Колонки /
    Названия колонок.
  - Qatorni tanlab qator panelidagi "Перевод строки таблицы" tugmasi bosiladi →
    record_translate_list?table_name=X (o'sha jadval yozuvlari).
  - record sahifasi: har yozuv (masalan "Наличные"/"Перечисление"/"Терминал") uchun
    `<textarea placeholder="uz|ru|en">` tarjima maydonlari + til chiplari
    (O'zbekcha/Русский/English) + "Сохранить" (joyida saqlaydi, redirect YO'Q).

Test — TARJIMA ROUND-TRIP (prod-xavfsiz): birinchi yozuvning uz maydoniga qiymat yozib
saqlaydi → reload qilib saqlanganini tasdiqlaydi → ASL qiymatga QAYTARADI (baseline
saqlab qo'yiladi, finally'da tiklanadi). Grid heading list va record sahifada BIR XIL
("Перевод строки таблицы") — record sahifa uz textarea mavjudligi bilan aniqlanadi.
"""
import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage

MENU = "Перевод строки таблицы"
TABLE = "Виды оплаты"   # kichik jadval (3 yozuv: Наличные/Перечисление/Терминал)


def _open_records(page: Page, m: BasePage) -> None:
    """table_translate_list → TABLE qatori → "Перевод строки таблицы" → record sahifa."""
    flow_navigate(page, tab="Модератор", name=MENU, expect_url="table_translate_list")
    m.expect_heading(MENU)
    m.click_grid_row(TABLE)
    # Qator panelidagi tugma matni sahifa heading'i bilan bir xil — role=button aniqlaydi
    m.click_button(MENU)
    m._settle()


def run_table_translate(page: Page, code) -> None:
    """Birinchi yozuvning uz tarjimasini yozib saqlaydi, reload'da tasdiqlaydi va
    ASL qiymatga qaytaradi (prod'ni o'zgartirmaydi)."""
    m = BasePage(page)
    value = f"Naqd-{code}"

    with allure.step(f"Навигация: {MENU} → '{TABLE}' → record sahifa"):
        _open_records(page, m)

    # uz/ru/en maydonlari oddiy input EMAS, <textarea placeholder="uz|ru|en"> —
    # BasePage label bilan topmaydi, raw locator (MCP tasdiqlangan 2026-08-07).
    uz = page.locator('textarea[placeholder="uz"]').first
    expect(uz).to_be_visible()
    original = uz.input_value()  # baseline — oxirida tiklanadi

    try:
        with allure.step(f"Birinchi yozuv uz = '{value}' → Сохранить"):
            uz.fill(value)
            m.click_button("Сохранить")
            m.wait_for_loader()

        with allure.step("Reload → uz tarjimasi saqlanganini tasdiqlash"):
            page.reload()
            m._settle()
            uz_after = page.locator('textarea[placeholder="uz"]').first
            expect(uz_after).to_have_value(value)
    finally:
        with allure.step(f"Asl qiymatga qaytarish (uz = '{original}')"):
            uz_restore = page.locator('textarea[placeholder="uz"]').first
            expect(uz_restore).to_be_visible()
            uz_restore.fill(original)
            m.click_button("Сохранить")
            m.wait_for_loader()


@allure.epic("Модератор")
@allure.feature("Перевод строки таблицы")
@allure.story("Перевод записей таблицы")
@allure.title("Jadval yozuvi uz tarjimasi: saqlash → tasdiqlash → tiklash")
def test_table_translate(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_table_translate(page, code)
