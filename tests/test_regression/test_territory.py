"""Tерритория — to'liq CRUD regression testlari.

Basic create (run_territory/test_territory) tests/test_setup/test_territory.py
da turadi — bu yerda faqat CRUD ssenariylari: edit, view, delete, status.
Dublikat testi YO'Q: ilova bir xil nomli territoriyalarni yaratishga RUXSAT
beradi (unikal cheklov yo'q, MCP tasdiqlangan 2026-07-05).
Kod test_setup dan ko'chirilgan ishlaydigan nusxa.
"""

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_setup.test_territory import run_territory
from utils.base_page import BasePage


def run_territory_edit(page: Page, code) -> None:
    """Yangi territoriya yaratib, Изменить orqali nomini o'zgartiradi va
    o'zgarish ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"territory-edit-{code}"
    new_name = f"territory-upd-{code}"

    run_territory(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Tерритория (Редактирования)")

    with allure.step(f"Tahrirlash: nom {old_name} → {new_name}"):
        m.input(label="Название", value=new_name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        # Edit'dan keyin ham redirect barqaror emas (dashboard'ga tushadi) —
        # ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Tерритории")
        m.expect_heading("Tерритории")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        expect(page.locator(".smt-data-row").filter(has_text=old_name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Tерритории")
@allure.story("Редактирование территории")
@allure.title("Tерриторияни tahrirlash va o'zgarishni tekshirish")
def test_territory_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_territory_edit(page, code)


#---------------------------------------------------------------------------------------------------


def run_territory_view(page: Page, code) -> None:
    """Yangi territoriya yaratib, saqlangan qiymatlar to'g'riligini tekshiradi.

    Tерритория qatorida "Просмотреть" tugmasi YO'Q (Прикрепления/Изменить/
    Удалить/Неактивный, MCP tasdiqlangan 2026-07-05) — qiymatlar Изменить
    formasida (saqlamasdan) tekshiriladi."""
    m = BasePage(page)
    name = f"territory-view-{code}"

    run_territory(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.expect_heading("Tерритория (Редактирования)")

    with allure.step("Qiymatlar: Название va Статус to'g'ri to'ldirilgan"):
        m.input(label="Название", expect_value=name)
        m.checkbox(label="Статус", expect_checked=True)

    with allure.step("Saqlamasdan ro'yxatga qaytish"):
        flow_navigate(page, tab="Модератор", name="Tерритории")
        m.expect_heading("Tерритории")


@allure.epic("Модератор")
@allure.feature("Tерритории")
@allure.story("Просмотр территории")
@allure.title("Tерритория ma'lumotlari to'g'ri saqlanganini tekshirish")
def test_territory_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_territory_view(page, code)


#---------------------------------------------------------------------------------------------------


def run_territory_delete(page: Page, code) -> None:
    """Yangi territoriya yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi."""
    m = BasePage(page)
    name = f"territory-del-{code}"

    run_territory(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Tерритории")
@allure.story("Удаление территории")
@allure.title("Tерриторияни o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_territory_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_territory_delete(page, code)


#---------------------------------------------------------------------------------------------------


def run_territory_status(page: Page, code) -> None:
    """Status ikki yo'nalishda tekshiriladi. Tерриторияда status qator action
    paneldagi MAQSAD status nomidagi toggle tugma bilan almashtiriladi
    ("Изменить статус" menyusi YO'Q); tasdiqlash: "да". Tugma va grid badge
    nomlari INGLIZCHA "passive"/"active" (Валюта kabi; regression 2026-07-08,
    2026-07-05 da ruscha edi).

    1) Aktiv yaratilgan territoriya passive qilinadi — default ro'yxatdan
       yo'qoladi, "Показать все"da "passive" ko'rinadi.
    2) Passiv yaratilgan territoriya active qilinadi — ro'yxatda "active"."""
    m = BasePage(page)
    active_name = f"territory-stat-a-{code}"
    passive_name = f"territory-stat-p-{code}"

    run_territory(page, code, name=active_name)

    with allure.step(f"1) '{active_name}' ni passive qilish"):
        m.click_grid_row(active_name)
        m.click_button("passive")
        m.confirm("да")

    with allure.step("1) Default ro'yxatda ko'rinmasligini tekshirish"):
        m.search(active_name)
        expect(page.locator(".smt-data-row").filter(has_text=active_name)).to_have_count(0)

    with allure.step("1) Показать все filtrida 'passive' bo'lib ko'rinishi"):
        m.show_all()
        m.grid_row(active_name, "passive")

    run_territory(page, code, name=passive_name, active=False)

    with allure.step(f"2) Passiv yaratilgan '{passive_name}' ni active qilish"):
        m.click_grid_row(passive_name)
        m.click_button("active")
        m.confirm("да")

    with allure.step("2) Ro'yxatda 'active' bo'lib ko'rinishini tekshirish"):
        m.search(passive_name)
        m.grid_row(passive_name, "active")


@allure.epic("Модератор")
@allure.feature("Tерритории")
@allure.story("Статус территории")
@allure.title("Tерритория statusini Неактивный/Активный qilish va tekshirish")
def test_territory_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_territory_status(page, code)
