"""Регион — to'liq CRUD regression testlari.

Basic create (run_region/test_region) tests/test_setup/test_region.py da
turadi — bu yerda faqat CRUD ssenariylari: edit, view, delete, status,
duplicate. Region hech qanday tashqi ma'lumotnomaga bog'liq emas.
Kod test_setup dan ko'chirilgan ishlaydigan nusxa.
"""
import random

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_setup.test_region import run_region
from utils.base_page import BasePage


def run_region_full(page: Page, code) -> None:
    """Регион formasining BARCHA to'ldiriladigan maydonlari bilan yaratish.

    Regionda supplier'dagidek qo'shimcha tab/bo'lim YO'Q — forma bor-yo'g'i
    ikki maydondan iborat: Название (majburiy, smt-input[smtid=region-name])
    va Статус (smt-switch), yagona tugma Сохранить (MCP tasdiqlangan
    2026-07-06). Ikkalasi ham yaqqol (explicit) to'ldiriladi, saqlangach
    qiymatlar Изменить formasida qayta ochib tekshiriladi — Regionда
    "Просмотреть" tugmasi yo'q."""
    m = BasePage(page)
    name = f"Region-full-{code}"

    with allure.step("Навигация: Модератор → Регионы"):
        flow_navigate(page, tab="Модератор", name="Регионы")
        m.expect_heading("Регионы")

    with allure.step("Создать: yangi Регион formasi ochish"):
        m.open_create()
        m.expect_heading("Регион (Создания)")

    kod = str(random.randint(10**8, 10**9 - 1))  # Код GLOBAL unikal bo'lishi kerak

    with allure.step(f"Форма (barcha maydonlar): Код = {kod}, Название = {name}, Статус = Активный"):
        # "Код *" MAJBURIY. smtid ISHLATILADI: ikkinchi create formada
        # yonidagi label "Код сервера *" ga aralashadi → `label="Код"` topolmaydi.
        m.input(smtid="region-code", value=kod)
        m.input(smtid="region-name", value=name)
        m.checkbox(label="Статус", checked=True)

    with allure.step("Сохранить"):
        # Saqlangach redirect barqaror emas (seansdagi keyingi saqlashlarda
        # ilova dashboard'ga qaytarib yuboradi) — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Ro'yxatda '{name}' 'Активный' bo'lib ko'rinishi"):
        flow_navigate(page, tab="Модератор", name="Регионы")
        m.expect_heading("Регионы")
        m.search(name)
        m.grid_row(name, "Активный")

    with allure.step("Изменить formasida saqlangan qiymatlar to'g'riligi"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.expect_heading("Регионы (Редактирования)")
        m.input(smtid="region-name", expect_value=name)
        m.checkbox(label="Статус", expect_checked=True)

    with allure.step("Saqlamasdan ro'yxatga qaytish"):
        flow_navigate(page, tab="Модератор", name="Регионы")
        m.expect_heading("Регионы")


@allure.epic("Модератор")
@allure.feature("Регионы")
@allure.story("Создание региона — все поля")
@allure.title("Регионни BARCHA maydonlar bilan yaratish")
def test_region_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_region_full(page, code)


#---------------------------------------------------------------------------------------------------


def run_region_edit(page: Page, code) -> None:
    """Yangi region yaratib, Изменить orqali nomini o'zgartiradi va o'zgarish
    ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"Region-edit-{code}"
    new_name = f"Region-upd-{code}"

    run_region(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Регионы (Редактирования)")

    with allure.step(f"Tahrirlash: nom {old_name} → {new_name}"):
        m.input(smtid="region-name", value=new_name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        # Edit'dan keyin ham redirect barqaror emas (dashboard'ga tushadi) —
        # ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Регионы")
        m.expect_heading("Регионы")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        m.expect_no_row(old_name)


@allure.epic("Модератор")
@allure.feature("Регионы")
@allure.story("Редактирование региона")
@allure.title("Регионни tahrirlash va o'zgarishni tekshirish")
def test_region_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_region_edit(page, code)


#---------------------------------------------------------------------------------------------------


def run_region_view(page: Page, code) -> None:
    """Yangi region yaratib, saqlangan qiymatlar to'g'ri ekanini tekshiradi.

    Регион qatorida "Просмотреть" tugmasi YO'Q (faqat Изменить/Области/Удалить,
    MCP tasdiqlangan 2026-07-05) — shuning uchun qiymatlar Изменить formasida
    (saqlamasdan) tekshiriladi."""
    m = BasePage(page)
    name = f"Region-view-{code}"

    run_region(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.expect_heading("Регионы (Редактирования)")

    with allure.step("Qiymatlar: Название va Статус to'g'ri to'ldirilgan"):
        m.input(smtid="region-name", expect_value=name)
        m.checkbox(label="Статус", expect_checked=True)

    with allure.step("Saqlamasdan ro'yxatga qaytish"):
        flow_navigate(page, tab="Модератор", name="Регионы")
        m.expect_heading("Регионы")


@allure.epic("Модератор")
@allure.feature("Регионы")
@allure.story("Просмотр региона")
@allure.title("Регион ma'lumotlari to'g'ri saqlanganini tekshirish")
def test_region_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_region_view(page, code)


#---------------------------------------------------------------------------------------------------


def run_region_delete(page: Page, code) -> None:
    """Yangi region yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi."""
    m = BasePage(page)
    name = f"Region-del-{code}"

    run_region(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        m.expect_no_row(name)


@allure.epic("Модератор")
@allure.feature("Регионы")
@allure.story("Удаление региона")
@allure.title("Регионни o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_region_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_region_delete(page, code)


#---------------------------------------------------------------------------------------------------


def run_region_status(page: Page, code) -> None:
    """Status ikki yo'nalishda tekshiriladi (Регионда "Изменить статус" tugmasi
    yo'q — status Изменить formasidagi Статус switch orqali o'zgartiriladi):

    1) Aktiv yaratilgan region passiv qilinadi — default ro'yxatdan yo'qoladi,
       "Показать все"da "Неактивный" bo'lib ko'rinadi.
    2) Passiv yaratilgan region aktiv qilinadi — ro'yxatda "Активный" ko'rinadi."""
    m = BasePage(page)
    active_name = f"Region-stat-a-{code}"
    passive_name = f"Region-stat-p-{code}"

    run_region(page, code, name=active_name)

    with allure.step(f"1) '{active_name}' ni Изменить formasida passiv qilish"):
        m.click_grid_row(active_name)
        m.click_button("Изменить")
        m.expect_heading("Регионы (Редактирования)")
        m.checkbox(label="Статус", checked=False)
        # Edit'dan keyin ham redirect barqaror emas (dashboard'ga tushadi) —
        # ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Регионы")
        m.expect_heading("Регионы")

    with allure.step("1) Default ro'yxatda ko'rinmasligini tekshirish"):
        m.search(active_name)
        m.expect_no_row(active_name)

    with allure.step("1) Показать все filtrida 'Неактивный' bo'lib ko'rinishi"):
        m.show_all()
        m.grid_row(active_name, "Неактивный")

    run_region(page, code, name=passive_name, active=False)

    with allure.step(f"2) Passiv yaratilgan '{passive_name}' ni aktiv qilish"):
        m.click_grid_row(passive_name)
        m.click_button("Изменить")
        m.expect_heading("Регионы (Редактирования)")
        m.checkbox(label="Статус", checked=True)
        # Edit'dan keyin ham redirect barqaror emas (dashboard'ga tushadi) —
        # ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Регионы")
        m.expect_heading("Регионы")

    with allure.step("2) Ro'yxatda 'Активный' bo'lib ko'rinishini tekshirish"):
        m.search(passive_name)
        m.grid_row(passive_name, "Активный")


@allure.epic("Модератор")
@allure.feature("Регионы")
@allure.story("Статус региона")
@allure.title("Регион statusini Неактивный/Активный qilish va tekshirish")
def test_region_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_region_status(page, code)


#---------------------------------------------------------------------------------------------------


def run_region_duplicate(page: Page, code) -> None:
    """Bir xil nom bilan qayta yaratishga urinish xatolik berishini tekshiradi.

    Region nomi unikal: saqlashda "Ошибка" dialogi chiqadi — matni
    "Название региона уже существует"."""
    m = BasePage(page)
    name = f"Region-dup-{code}"

    run_region(page, code, name=name)

    with allure.step(f"Xuddi shu nom '{name}' bilan qayta yaratishga urinish"):
        m.open_create()
        m.expect_heading("Регион (Создания)")
        # "Код *" majburiy — UNIKAL boshqa qiymat beramiz (faqat Название to'qnashsin →
        # "Название региона уже существует", Код to'qnashuvi emas). smtid ishlatiladi.
        m.input(smtid="region-code", value=str(random.randint(10**8, 10**9 - 1)))
        m.input(smtid="region-name", value=name)
        m.click_button("Сохранить")

    with allure.step("Ошибка dialogi chiqishini tekshirish (nom dublikat)"):
        # "Ошибка" dialogi = validatsiya ishga tushdi, save bloklandi. Aniq jumla
        # ("Название региона уже существует") server i18n'iga qarab ru↔en almashishi
        # mumkin (CLAUDE.md: status/xabar tili barqaror emas) — shuning uchun tekshiruv
        # til-mustaqil: dialog chiqdi + quyida dublikat YARATILMAGANI (count==1).
        m.expect_error_dialog("Ошибка")

    with allure.step("Dialogni yopish — forma ochiq qoladi, yozuv saqlanmagan"):
        m.expect_heading("Регион (Создания)")

    with allure.step(f"Ro'yxatda '{name}' faqat BITTA ekanini tekshirish"):
        flow_navigate(page, tab="Модератор", name="Регионы")
        m.expect_heading("Регионы")
        m.search(name)
        m.expect_row_count(name, 1)


@allure.epic("Модератор")
@allure.feature("Регионы")
@allure.story("Дубликат региона")
@allure.title("Bir xil nom bilan Регион qayta yaratishda xatolik chiqishi")
def test_region_duplicate(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_region_duplicate(page, code)
