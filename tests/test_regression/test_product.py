"""Продукт — to'liq CRUD regression testlari.

Basic create (run_product/test_product) tests/test_setup/test_product.py da
turadi — bu yerda faqat CRUD ssenariylari: full create, edit, view, delete,
status. Dublikat testi YO'Q: ilova bir xil nom va Код bilan produkt
yaratishga RUXSAT beradi (unikal cheklov yo'q, MCP tasdiqlangan 2026-07-05).
Kod test_setup dan ko'chirilgan ishlaydigan nusxa.
"""
import random

import allure
import pytest
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_setup.test_manufacturer import run_manufacturer
from tests.test_setup.test_product import run_product
from tests.test_setup.test_supplier import ensure_refs
from utils.base_page import BasePage

# Manufacturer seansda BIR MARTA yaratiladi (supplier ensure_refs'iga kirmaydi)
_manufacturer_ready = set()


def ensure_product_refs(page: Page, code) -> None:
    """Product testlari uchun ma'lumotnomalarni seansda bir marta yaratadi:
    ensure_refs (Region/MCHJ/Industry/Category-{code}) + Manufacturer-{code}.
    O'lchov birligi ("кг") tizimda global mavjud (кг/уп/шт — MCP 2026-07-05)."""
    ensure_refs(page, code)
    if code not in _manufacturer_ready:
        run_manufacturer(page, code)
        _manufacturer_ready.add(code)


def run_product_basic(page: Page, code, name=None, status=None) -> dict:
    """CRUD testlari uchun tayyorlov: kerakli ma'lumotnomalarni
    (ensure_product_refs) yaratib, ``run_product`` ni chaqiradi — alohida
    seansda ham ishlaydi."""
    ensure_product_refs(page, code)
    return run_product(page, code, name=name, status=status)


def run_product_full(page: Page, code) -> None:
    """Продукт formasining BARCHA to'ldiriladigan maydonlari bilan yaratish:
    Основное (Название, Краткое название, Код, Производитель, Регион
    производство, Статус, measure, Тип упаковки, Кол-во в упаковке, Артикул,
    Штрих-код, ИКПУ, ГТИН), Вес tab (нетто/брутто, Литр), Характеристика tab
    (Категории, Отрасль). "Бренд" selecti to'ldirilmaydi — muhitdagi alohida
    lug'atga bog'liq (MCP tasdiqlangan 2026-07-05)."""
    ensure_product_refs(page, code)
    m = BasePage(page)
    name = f"product-full-{code}"

    with allure.step("Навигация: Модератор → Товары"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")

    with allure.step("Создать: yangi Продукт formasi ochish"):
        m.open_create()
        m.expect_heading("Продукт (создание)")

    with allure.step(f"Основное: matn maydonlari ({name})"):
        m.input(label="Название", value=name)
        m.input(label="Краткое название", value=name)
        # "Код" smtid orqali (ikkinchi create formada label "Код сервера" ga aralashadi)
        m.input(smtid="code", value=f"code-{name}")
        m.input(label="Артикул код", value=f"art-{code}")
        m.input(label="Штрих-код", value=f"{random.randint(10**12, 10**13 - 1)}")
        m.input(label="ИКПУ", value=f"{random.randint(10**10, 10**11 - 1)}")
        m.input(label="ГТИН", value=f"{random.randint(10**12, 10**13 - 1)}")

    with allure.step(f"Основное: Производитель, Регион, Статус, measure, Тип упаковки"):
        m.select(f"Manufacturer-{code}", label="Производитель")
        m.select(f"Region-{code}", label="Регион производство")
        m.radio("Активный", label="Статус")
        m.select("кг", label="measure")
        m.select("Коробка", label="Тип упаковки")
        # Кол-во в упаковке "Тип упаковки" tanlanmaguncha disabled turadi
        m.input(label="Кол-во в упаковке", value="12")

    with allure.step("Вес tab: Вес нетто/брутто, Литр"):
        m.input(label="Вес нетто", value="1.5")
        m.input(label="Вес брутто", value="1.7")
        m.input(label="Литр", value="1")

    with allure.step(f"Характеристика tab: Категории = Category-{code}, Отрасль = Industry-{code}"):
        m.click_button("Характеристика")
        m.select(f"Category-{code}", label="Категории")
        m.select(f"Industry-{code}", label="Отрасль")

    with allure.step("Сохранить"):
        # Redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Создание продукта — все поля")
@allure.title("Продуктни BARCHA maydonlar bilan yaratish")
def test_product_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_product_full(page, code)


#---------------------------------------------------------------------------------------------------


def run_product_edit(page: Page, code) -> None:
    """Yangi produkt yaratib, Изменить orqali tahrirlaydi va o'zgarish
    ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"product-edit-{code}"
    new_name = f"product-upd-{code}"

    run_product_basic(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Товары (Редактирования)")

    with allure.step(f"Tahrirlash: nom {old_name} → {new_name}"):
        m.input(label="Название", value=new_name)
        m.input(label="Краткое название", value=new_name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        # Edit'dan keyin ham redirect barqaror emas (dashboard'ga tushadi) —
        # ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        expect(page.locator(".smt-data-row").filter(has_text=old_name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Редактирование продукта")
@allure.title("Продуктни tahrirlash va o'zgarishni tekshirish")
def test_product_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_product_edit(page, code)


#---------------------------------------------------------------------------------------------------


def run_product_view(page: Page, code) -> None:
    """Yangi produkt yaratib, Просмотреть formasida qiymatlar to'g'ri
    ko'rsatilishini tekshiradi (heading "Продукт (Просмотр)", readonly
    pv_main_* inputlar; MCP tasdiqlangan 2026-07-05)."""
    m = BasePage(page)
    name = f"product-view-{code}"

    data = run_product_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Просмотр formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Просмотреть")
        m.expect_heading("Продукт (Просмотр)")

    with allure.step("Qiymatlar: Название, Статус, Производитель, Код, measure"):
        m.input(smtid="pv_main_name", expect_value=data["name"])
        m.input(smtid="pv_main_state_name", expect_value="Активный")
        m.input(smtid="pv_main_producer_name", expect_value=f"Manufacturer-{code}")
        m.input(smtid="pv_main_code", expect_value=data["kod"])
        m.input(smtid="pv_main_measure_name", expect_value="кг")


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Просмотр продукта")
@allure.title("Продукт ma'lumotlari Просмотр formasida to'g'ri ko'rinishi")
def test_product_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_product_view(page, code)


#---------------------------------------------------------------------------------------------------


def run_product_delete(page: Page, code) -> None:
    """Yangi produkt yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi."""
    m = BasePage(page)
    name = f"product-del-{code}"

    run_product_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Удаление продукта")
@allure.title("Продуктни o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_product_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_product_delete(page, code)


#---------------------------------------------------------------------------------------------------


def run_product_status(page: Page, code) -> None:
    """Status ikki yo'nalishda tekshiriladi ("Изменить статус" menyusi —
    supplier'dagi kabi, variantlar Пассивный/Приостоновлено):

    1) Aktiv yaratilgan produkt Пассивный qilinadi — default ro'yxatdan
       yo'qoladi, "Показать все"da "Пассивный" ko'rinadi.
    2) Пассивный holatda yaratilgan produkt Активный qilinadi."""
    m = BasePage(page)
    active_name = f"product-stat-a-{code}"
    passive_name = f"product-stat-p-{code}"

    run_product_basic(page, code, name=active_name)

    with allure.step(f"1) '{active_name}' ni Пассивный qilish"):
        m.click_grid_row(active_name)
        m.change_status("Пассивный")

    with allure.step("1) Default ro'yxatda ko'rinmasligini tekshirish"):
        m.search(active_name)
        expect(page.locator(".smt-data-row").filter(has_text=active_name)).to_have_count(0)

    with allure.step("1) Показать все filtrida 'Пассивный' bo'lib ko'rinishi"):
        m.show_all()
        m.grid_row(active_name, "Пассивный")

    run_product_basic(page, code, name=passive_name, status="Пассивный")

    with allure.step(f"2) Passiv yaratilgan '{passive_name}' ni Активный qilish"):
        m.click_grid_row(passive_name)
        m.change_status("Активный")

    with allure.step("2) Ro'yxatda 'Активный' bo'lib ko'rinishini tekshirish"):
        m.search(passive_name)
        m.grid_row(passive_name, "Активный")


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Статус продукта")
@allure.title("Продукт statusini Пассивный/Активный qilish va tekshirish")
def test_product_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_product_status(page, code)


# ======================================================================================
# Справочник → Товар sub-modullari (Товары sahifasi sub-nav linklari) — CRUD.
# Barchasi bir xil pattern: qator paneli Изменить / Неактивный / Удалить (toggle
# status, confirm "да"), status badge "Активный"/"Неактивный". Passiv qatorni
# ko'rish uchun "Показать все". (MCP tasdiqlangan 2026-08-21)
# ======================================================================================

def _product_subsection_crud(page: Page, code, *, link: str, heading: str,
                             create_heading: str, name_prefix: str,
                             extra_fields: dict | None = None) -> None:
    """Товар sub-moduli (Типы упаковок / Единицы измерения / Услуги) umumiy CRUD:
    create → edit → status (deactivate/reactivate) → delete. Forma odatda Код /
    Название* (+ ixtiyoriy maydonlar). Edit forma sarlavhasi assert QILINMAYDI
    (modullararo casing farq qiladi) — natija ro'yxat orqali tekshiriladi."""
    m = BasePage(page)
    name = f"{name_prefix}-{code}"
    edited = f"{name}-edit"

    with allure.step(f"Навигация: Модератор → Товары → {link}"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")
        m.click_link(link)
        m.expect_heading(heading)

    with allure.step(f"Создать: '{name}'"):
        m.open_create()
        m.expect_heading(create_heading)
        m.input(label="Код", value=code)
        m.input(label="Название", value=name)
        for field_label, value in (extra_fields or {}).items():
            m.input(label=field_label, value=value)
        m.save_and_expect_heading(heading)

    with allure.step(f"Ro'yxatda '{name}' Активный ko'rinishini tekshirish"):
        m.search(name)
        m.grid_row(name, "Активный")

    with allure.step(f"Изменить: nomni '{edited}' ga o'zgartirish"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.input(label="Название", value=edited)
        m.save_and_expect_heading(heading)
        m.search(edited)
        m.grid_row(edited, "Активный")

    with allure.step(f"Статус: '{edited}' ni Неактивный qilib, qayta Активный qilish"):
        m.click_grid_row(edited)
        m.click_button("Неактивный")
        m.confirm("да")
        m.show_all()
        m.search(edited)
        m.grid_row(edited, "Неактивный")
        m.click_grid_row(edited)
        m.click_button("Активный")
        m.confirm("да")
        m.search(edited)
        m.grid_row(edited, "Активный")

    with allure.step(f"Удалить: '{edited}' ni o'chirib, ro'yxatdan yo'qolganini tekshirish"):
        m.click_grid_row(edited)
        m.click_button("Удалить")
        m.confirm("да")
        m.search(edited)
        expect(page.locator(".smt-data-row").filter(has_text=edited)).to_have_count(0)


def run_package_types(page: Page, code) -> None:
    """Типы упаковок (box_type_list) CRUD — Код / Название* / Краткое название."""
    _product_subsection_crud(
        page, code, link="Типы упаковок", heading="Типы упаковок",
        create_heading="Типы упаковок (создание)", name_prefix="box",
        extra_fields={"Краткое название": f"b{code[-4:]}"},
    )


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Типы упаковок")
@allure.title("Типы упаковок — to'liq CRUD (create/edit/status/delete)")
def test_package_types(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_package_types(page, code)


def run_measure_units(page: Page, code) -> None:
    """Единицы измерения (measure_list) CRUD — Код / Название* / Краткое название
    (+ 'Знаков после запятой' default 0 — majburiy, lekin oldindan to'lган)."""
    _product_subsection_crud(
        page, code, link="Единицы измерения", heading="Единицы измерения",
        create_heading="Единица измерения (Создания)", name_prefix="measure",
        extra_fields={"Краткое название": f"m{code[-4:]}"},
    )


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Единицы измерения")
@allure.title("Единицы измерения — to'liq CRUD (create/edit/status/delete)")
def test_measure_units(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_measure_units(page, code)


def run_services(page: Page, code) -> None:
    """Услуги (service_list) CRUD. Продукт'ga o'xshash to'liqroq forma: Название* /
    Краткое название* / Код / Ед. изм.* (select) / Статус radio (Активный/Пассивный/
    Приостоновлено). Qator paneli: Просмотр / Изменить / Изменить статус / Удалить —
    status TOGGLE emas, "Изменить статус" MENYU orqali (m.change_status). Passiv
    qator default yashirin (Показать все kerak). (MCP tasdiqlangan 2026-08-21)"""
    m = BasePage(page)
    name = f"service-{code}"
    edited = f"{name}-edit"

    with allure.step("Навигация: Модератор → Товары → Услуги"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")
        m.click_link("Услуги")
        m.expect_heading("Услуги")

    with allure.step(f"Создать: '{name}' (Название/Краткое/Код/Ед. изм.)"):
        m.open_create()
        m.expect_heading("Услуга (Создание)")
        m.input(label="Название", value=name)
        m.input(label="Краткое название", value=f"s{code[-4:]}")
        m.input(label="Код", value=code)
        m.select("кг", label="Ед. изм.")
        m.save_and_expect_heading("Услуги")

    with allure.step(f"Ro'yxatda '{name}' Активный ko'rinishini tekshirish"):
        m.search(name)
        m.grid_row(name, "Активный")

    with allure.step(f"Изменить: nomni '{edited}' ga o'zgartirish"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.input(label="Название", value=edited)
        m.save_and_expect_heading("Услуги")
        m.search(edited)
        m.grid_row(edited, "Активный")

    with allure.step(f"Статус: '{edited}' ni Пассивный, keyin qayta Активный qilish"):
        m.click_grid_row(edited)
        m.change_status("Пассивный")
        m.search(edited)
        m.show_all()
        m.grid_row(edited, "Пассивный")
        m.click_grid_row(edited)
        m.change_status("Активный")
        m.search(edited)
        m.grid_row(edited, "Активный")

    with allure.step(f"Удалить: '{edited}' ni o'chirib, ro'yxatdan yo'qolganini tekshirish"):
        m.click_grid_row(edited)
        m.click_button("Удалить")
        m.confirm("да")
        m.search(edited)
        expect(page.locator(".smt-data-row").filter(has_text=edited)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Услуги")
@allure.title("Услуги — to'liq CRUD (create/edit/status/delete)")
def test_services(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_services(page, code)
