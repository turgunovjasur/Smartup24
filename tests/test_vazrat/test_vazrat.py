"""Возврат (qaytarish) — klient foydalanuvchisi ЗАВЕРШЕН bo'lgan zakazidan
возврат yaratadi, admin esa uni Модератор → Возвраты da tekshiradi.

Bu modul ``run_*`` biznes-funksiyalarni beradi; ular bo'lim runneri
(``test_all_vazrat.py``) tomonidan bitta seansда, order oqimining DAVOMI sifatida
chaqiriladi. Возврат faqat ЗАВЕРШЕН zakaz uchun yaratiladi.

OQIM
----
  1. Klient user bilan kirib "Возвраты" → Создать (3 qadamli wizard):
     - Основное: "Заказы *" selectдан завершен zakazni tanlash (торговая
       точка/поставщик avtomatik to'ladi, Время доставки oldindan to'lган);
     - Товары: jadval "Поиск" filtriga tovar nomini yozib, avtokomplitдан
       tovarni tanlash → "Кол-во" ga qaytariladigan miqdorni yozish;
     - Завершение: Статус=Новый, Тип оплаты=Наличные, Причины, Описание → Сохранить.
  2. Klient ro'yxatida возврат ko'rinishini tekshirish.
  3. Admin bilan kirib Модератор → Возвраты da o'sha возвратни tekshirish.

DOM (2026-09-21 MCP dev/sm24 + user bilan tasdiqlangan)
-------------------------------------------------------
- Klient nav: tab="Клиент", name="Возвраты" (KO'PLIK), heading "Возвраты".
- Wizard qadamlari: Основное/Товары/Завершение; pastda "Далее"/"Назад", tepada "Сохранить".
- "Заказы *" — smt-data-select (ichki input placeholder "Поиск"); dropdown завершен
  zakazlarni ko'rsatadi (option matnida supplier-{code}/client-{code}/zakaz raqami).
- **Товары (KALIT):** "Подбор" tugmasi ISHLATILMAYDI (bo'sh picker). Tovar jadval
  "Поиск" filtriga nom yozganда avtokomplit (smt-select-dropdown) da chiqadi;
  tanlanгач "Кол-во" (``quantity``) ustuniga miqdor yoziladi.
- Admin verify: tab="Модератор", name="Возвраты" (.../moderator/return/return_list);
  ustunlar: Поставщик, Клиент, Торговая точка, ..., Статус.

DIQQAT: возврат uchun zakaz TOVARLI (non-zero) bo'lishi shart — run_order
price 100000 × qty 2 beradi; 0-sum zakazda Товары qadamида tovar chiqmaydi.
"""
from datetime import datetime

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import COMPANY_CODE, authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def _fill_return_qty(page: Page, m: BasePage, product_name: str, value: str) -> None:
    """2-qadam Товары: jadval "Поиск" filtriga tovar nomini yozib, chiqadigan
    dropdownдан tovarni tanlaydi (u grid'ga tushadi), so'ng "Кол-во" ustuniga
    qaytariladigan miqdorni yozadi.

    DIQQAT (user + MCP tasdiqlangan 2026-09-21): tovar "Подбор" tugmasi bilan
    QO'SHILMAYDI (u bo'sh picker ochadi). Buning o'rniga jadval boshidagi "Поиск"
    filtriga (``input[type=text][placeholder="Поиск"]``) tovar nomi YOZILADI —
    shунда ``smt-select-dropdown`` avtokomplit ochilib tovar qatorini ko'rsatadi;
    u bosilгач tovar grid'ga qo'shiladi. Grid ustunlari: Название | Цена товара |
    sold_quant | Возвращенное количество | quantity_of_return | **Кол-во**
    (``quantity``) | quantity box — qaytariladigan miqdor "Кол-во" (``quantity``)
    input'iga yoziladi (Сумма shунда yangilanadi)."""
    search = page.locator('#main-content input[type="text"][placeholder="Поиск"]').first
    expect(search).to_be_visible(timeout=15_000)
    search.click()
    search.fill(product_name)

    # Avtokomplit dropdownдан tovarni tanlaymiz (smt-select-dropdown li — select
    # bilan bir xil struktura).
    option = (
        page.locator(".cdk-overlay-container smt-select-dropdown li")
        .filter(has_text=product_name)
        .first
    )
    expect(option).to_be_visible(timeout=30_000)
    option.click()
    m.settle()
    page.wait_for_timeout(1_000)  # tanlangan tovar grid'ga tushishini kutamiz

    # "Кол-во" (quantity) — tovar qatoridagi input (grid'da tovar qatori filtr
    # qatoridан oldin keladi → .first).
    qty_input = page.locator('#main-content [data-smt-col-key="quantity"] input').first
    qty_input.click()
    qty_input.fill(value)
    qty_input.press("Tab")
    expect(qty_input).to_have_value(value)


def run_vazrat(page: Page, code, product_name=None, return_qty: str = "1") -> None:
    """Klient foydalanuvchisi nomidan завершен zakazdan Возврат yaratadi.

    ``client_user-{code}`` bilan login qilingan bo'lishi kerak; "Заказы *"
    selectда faqat shu klientning ЗАВЕРШЕН zakazlari chiqadi — shuning uchun
    run_order + run_order_status_change (Завершен) oldindan bajarilган bo'lishi
    shart. ``product_name`` — zakazda biriktirilган tovar (run_order bilan bir xil).
    """
    m = BasePage(page)
    supplier_name = f"supplier-{code}"
    client_name = f"client-{code}"
    product_name = product_name or f"product-{code}"
    description = f"Возврат {product_name} {datetime.now():%d.%m.%Y}"

    with allure.step("Навигация: Клиент → Возвраты"):
        flow_navigate(page, tab="Клиент", name="Возвраты")
        m.expect_heading("Возвраты")

    with allure.step("Создать: yangi Возврат formasi ochish"):
        m.open_create()
        m.expect_heading("Возврат (создание)")

    with allure.step(f"1-qadam Основное: Заказы = {supplier_name} завершен zakaz"):
        # "Заказы *" dropdownда завершен zakazlar; option matnida supplier-{code}
        # bor — substring bilan tanlaymiz. Tanlangач торговая точка/поставщик
        # avtomatik to'ladi, Время доставки oldindan to'lган.
        m.select(supplier_name, label="Заказы", exact=False)
        m.click_button("Далее")
        m.settle()

    with allure.step(f"2-qadam Товары: {product_name} — Кол-во = {return_qty}"):
        _fill_return_qty(page, m, product_name, return_qty)
        m.click_button("Далее")
        m.settle()

    with allure.step("3-qadam Завершение: Статус=Новый, Тип оплаты=Наличные, Причины, Описание"):
        # "Статус *" — smt-select (qidiruvsiz), variantlar: Черновик/Новый/Отменён.
        m.select("Новый", label="Статус")
        # "Тип оплаты" — smt-data-select (Наличные/Перечисление/Платежная система).
        m.select("Наличные", label="Тип оплаты")
        # "Причины" — sabablar ro'yxati (MCP 2026-09-21). "Товар испорчен /
        # дефектный" — tovar nuqsonli sababi ("Другое" qo'lда matn talab qiladi).
        m.select("Товар испорчен / дефектный", label="Причины")
        m.input(label="Описание", value=description)
        # "Тип возврата *" radio default "E" bilan to'lган — tegilmaydi.

    with allure.step("Сохранить va Возвраты ro'yxatiga qaytish"):
        m.click_button("Сохранить")
        m.expect_heading("Возвраты")

    with allure.step(f"Ro'yxatда yangi возврат ({supplier_name} / {client_name}) tekshirish"):
        m.grid_row(supplier_name, client_name)


def run_vazrat_verify(page: Page, code) -> None:
    """Admin nomidan Модератор → Возвраты da yaratilган возвратни tekshiradi.

    ``admin@{COMPANY_CODE}`` bilan login qilinган bo'lishi kerak."""
    m = BasePage(page)
    supplier_name = f"supplier-{code}"
    client_name = f"client-{code}"

    with allure.step("Навигация: Модератор → Возвраты"):
        flow_navigate(page, tab="Модератор", name="Возвраты")
        m.expect_heading("Возвраты")

    with allure.step(f"Возврат ({supplier_name} / {client_name}) ro'yxатда bor va Новый statusда"):
        m.grid_row(supplier_name, client_name, "Новый")


@allure.epic("Возврат")
@allure.feature("Возврат")
@allure.story("Создание возврата")
@allure.title("Возврат: klient foydalanuvchisi nomidan завершен zakazdan qaytarish")
def test_vazrat(page: Page, code) -> None:
    """Alohida (debug) test — завершен zakaz OLDINDAN mavjud bo'lishi kutiladi
    (to'liq oqim uchun ``test_all_vazrat.py`` runnerini ishlating)."""
    with allure.step("Tizimga kirish (klient foydalanuvchisi)"):
        authorization(page, email=f"client_user-{code}@{COMPANY_CODE}", password="1")
    run_vazrat(page, code)
