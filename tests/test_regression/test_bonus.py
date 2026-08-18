"""Бонусная система — to'liq CRUD regression testlari.

Basic create (run_bonus/test_bonus) tests/test_setup/test_bonus.py da turadi —
bu yerda faqat CRUD ssenariylari: full create, edit, view, delete, status.
Dublikat testi YO'Q: ilova bir xil nomli bonus tizimlarini yaratishga RUXSAT
beradi (unikal cheklov yo'q, MCP tasdiqlangan 2026-07-05).
Kod test_setup dan ko'chirilgan ishlaydigan nusxa.
"""

import allure
from playwright.sync_api import Page, expect

from datetime import date, timedelta

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_setup.test_bonus import BONUS_END, BONUS_START, run_bonus
from utils.base_page import BasePage


def run_bonus_full(page: Page, code) -> None:
    """Бонусная система formasining BARCHA to'ldiriladigan maydonlari bilan
    yaratish: Название, Описание, Значение, Начало/Конец, Авто одобрение,
    Статус. "Валюта" maydoni readonly (default Узбекский сум), "Тип значения"
    switch default holatda qoldiriladi (MCP tasdiqlangan 2026-07-05)."""
    m = BasePage(page)
    name = f"bonus-full-{code}"

    with allure.step("Навигация: Модератор → Бонусная система"):
        flow_navigate(page, tab="Модератор", name="Бонусная система")
        m.expect_heading("Бонусная система")

    with allure.step("Создать: yangi Бонусная система formasi ochish"):
        m.open_create()
        m.expect_heading("Создать бонусную систему")

    with allure.step(f"Форма: barcha maydonlar ({name})"):
        m.input(label="Название", value=name)
        m.input(label="Описание", value=f"Avto-test bonus tavsifi {code}")
        m.input(label="Значение", value="10")
        # Lokal dinamik sanalar (bu testda tekshirilmaydi) — start bugun, end +180 kun
        m.input(label="Начало", value=BONUS_START)
        m.input(label="Конец", value=(date.today() + timedelta(days=180)).strftime("%d.%m.%Y"))
        m.checkbox(label="Авто одобрение", checked=True)
        m.checkbox(label="Статус", checked=True)

    with allure.step("Сохранить"):
        # Saqlangach redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        flow_navigate(page, tab="Модератор", name="Бонусная система")
        m.expect_heading("Бонусная система")
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Бонусная система")
@allure.story("Создание бонусной системы — все поля")
@allure.title("Бонусная системани BARCHA maydonlar bilan yaratish")
def test_bonus_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_bonus_full(page, code)


#---------------------------------------------------------------------------------------------------


def run_bonus_edit(page: Page, code) -> None:
    """Yangi bonus tizimi yaratib, Изменить orqali nomini o'zgartiradi va
    o'zgarish ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"bonus-edit-{code}"
    new_name = f"bonus-upd-{code}"

    run_bonus(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Редактировать бонусную систему")

    with allure.step(f"Tahrirlash: nom {old_name} → {new_name}, Значение = 7"):
        m.input(label="Название", value=new_name)
        m.input(label="Значение", value="7")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        # Edit'dan keyin ham redirect barqaror emas (dashboard'ga tushadi) —
        # ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Бонусная система")
        m.expect_heading("Бонусная система")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        expect(page.locator(".smt-data-row").filter(has_text=old_name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Бонусная система")
@allure.story("Редактирование бонусной системы")
@allure.title("Бонусная системани tahrirlash va o'zgarishni tekshirish")
def test_bonus_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_bonus_edit(page, code)


#---------------------------------------------------------------------------------------------------


def run_bonus_view(page: Page, code) -> None:
    """Yangi bonus tizimi yaratib, saqlangan qiymatlar to'g'riligini tekshiradi.

    Бонусная системада "Просмотреть" tugmasi YO'Q (Начисление бонусов/Изменить/
    Изменить статус/Удалить, MCP tasdiqlangan 2026-07-05) — qiymatlar Изменить
    formasida (saqlamasdan) tekshiriladi."""
    m = BasePage(page)
    name = f"bonus-view-{code}"

    run_bonus(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.expect_heading("Редактировать бонусную систему")

    with allure.step("Qiymatlar: Название, Значение, Начало, Конец to'g'ri"):
        m.input(label="Название", expect_value=name)
        m.input(label="Значение", expect_value="5")
        m.input(label="Начало", expect_value=BONUS_START)
        m.input(label="Конец", expect_value=BONUS_END)

    with allure.step("Saqlamasdan ro'yxatga qaytish"):
        flow_navigate(page, tab="Модератор", name="Бонусная система")
        m.expect_heading("Бонусная система")


@allure.epic("Модератор")
@allure.feature("Бонусная система")
@allure.story("Просмотр бонусной системы")
@allure.title("Бонусная система ma'lumotlari to'g'ri saqlanganini tekshirish")
def test_bonus_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_bonus_view(page, code)


#---------------------------------------------------------------------------------------------------


def run_bonus_delete(page: Page, code) -> None:
    """Yangi bonus tizimi yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi."""
    m = BasePage(page)
    name = f"bonus-del-{code}"

    run_bonus(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Бонусная система")
@allure.story("Удаление бонусной системы")
@allure.title("Бонусная системани o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_bonus_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_bonus_delete(page, code)


#---------------------------------------------------------------------------------------------------


def run_bonus_status(page: Page, code) -> None:
    """Status ikki yo'nalishda tekshiriladi. Бонусная системада status UI'si
    opros modullaridagidek: qator panelida "Изменить статус" tugmasi EMAS,
    MAQSAD status nomidagi TOGGLE tugma ("Неактивный"/"Активный") bosiladi va
    tasdiqlash dialogi ("да") chiqadi (UI 2026-08-18 da o'zgardi — avval
    "Изменить статус" edi, 2026-07-05).

    1) Aktiv yaratilgan bonus Неактивный qilinadi — default ro'yxatdan
       yo'qoladi, "Показать все"da "Неактивный" ko'rinadi.
    2) Passiv yaratilgan bonus Активный qilinadi — ro'yxatda "Активный"."""
    m = BasePage(page)
    active_name = f"bonus-stat-a-{code}"
    passive_name = f"bonus-stat-p-{code}"

    run_bonus(page, code, name=active_name)

    with allure.step(f"1) '{active_name}' ni Неактивный qilish"):
        m.click_grid_row(active_name)
        m.click_button("Неактивный")  # maqsad status toggle tugmasi (UI 2026-08-18)
        m.confirm("да")

    with allure.step("1) Default ro'yxatda ko'rinmasligini tekshirish"):
        m.search(active_name)
        expect(page.locator(".smt-data-row").filter(has_text=active_name)).to_have_count(0)

    with allure.step("1) Показать все filtrida 'Неактивный' bo'lib ko'rinishi"):
        m.show_all()
        m.grid_row(active_name, "Неактивный")

    run_bonus(page, code, name=passive_name, active=False)

    with allure.step(f"2) Passiv yaratilgan '{passive_name}' ni Активный qilish"):
        m.click_grid_row(passive_name)
        m.click_button("Активный")  # maqsad status toggle tugmasi (UI 2026-08-18)
        m.confirm("да")

    with allure.step("2) Ro'yxatda 'Активный' bo'lib ko'rinishini tekshirish"):
        m.search(passive_name)
        m.grid_row(passive_name, "Активный")


@allure.epic("Модератор")
@allure.feature("Бонусная система")
@allure.story("Статус бонусной системы")
@allure.title("Бонусная система statusini Неактивный/Активный qilish va tekshirish")
def test_bonus_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_bonus_status(page, code)
