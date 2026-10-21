"""S-05 §1 Ro'yxat (warehouse_list): 1.1 tarkib, 1.4 bitta omborni o'chirish, 1.6 moderator.
Test-case: docs/qa/test-cases/sbr/supplier/warehouse.md."""
import re

import allure
from playwright.sync_api import Page, expect

from flows.flow_navbar import flow_navigate
from tests.sbr.supplier.warehouse.warehouse_helpers import (
    BUX_CODE, BUX_NAME, BUX_REGION, DEFAULT_WAREHOUSE, GRID_HEADER_CELL, GRID_ROW,
    TSH_CODE, TSH_NAME, TSH_REGION,
    cell, create_warehouse, login_admin, login_supplier_user, open_warehouses, row_panel,
)
from tests.test_group_a.test_supplier import run_supplier
from tests.test_group_a.test_supplier_user import run_supplier_user
from tests.test_setup.test_supplier import ensure_refs
from utils.base_page import BasePage
from utils.qa_report import visible_error_dialog_text


def run_warehouse_list(page: Page, code) -> None:
    """S-05.1.1 — admin bilan login qilingan deb hisoblaydi. O'z ma'lumoti ({code}6):
    Alfa (TSH, SAM) va Beta (Beta ombori) supplier'lari."""
    code6 = f"{code}6"
    alfa, beta = f"{code6}a", f"{code6}b"
    beta_warehouse = f"Beta ombori-{code6}"

    with allure.step(f"Setup (admin): ma'lumotnomalar, Alfa supplier-{alfa} va Beta supplier-{beta} + userlar"):
        ensure_refs(page, code6)
        refs = dict(region=f"Region-{code6}", ownership=f"MCHJ-{code6}", industry=f"Industry-{code6}")
        for sup in (alfa, beta):
            run_supplier(page, sup, **refs)
            run_supplier_user(page, sup)
    with allure.step(f"Setup: Alfa — «{TSH_NAME}», «{BUX_NAME}»; Beta — «{beta_warehouse}»"):
        login_supplier_user(page, alfa)
        create_warehouse(page, TSH_NAME, TSH_CODE, TSH_REGION)
        create_warehouse(page, BUX_NAME, BUX_CODE, BUX_REGION)
        login_supplier_user(page, beta)
        create_warehouse(page, beta_warehouse, "BET", TSH_REGION)
    with allure.step("(a) Alfa-admin → Поставщик → Склады: ro'yxat ochildi"):
        login_supplier_user(page, alfa)
        m = open_warehouses(page)
        m.settle()

    rows = page.locator(GRID_ROW)
    with allure.step(f"(b) Aniq 3 qator: {DEFAULT_WAREHOUSE}, {TSH_NAME}, {BUX_NAME}"):
        expect(rows).to_have_count(3)
        names = {t.strip() for t in rows.locator('[data-smt-col-key="name"]').all_inner_texts()}
        assert names == {DEFAULT_WAREHOUSE, TSH_NAME, BUX_NAME}, f"Ro'yxatdagi omborlar: {sorted(names)}"
    with allure.step(f"(b) {DEFAULT_WAREHOUSE}: Код va Регионы kataklari BO'SH"):
        row = m.grid_row(DEFAULT_WAREHOUSE)
        expect(cell(row, "code")).to_have_text(re.compile(r"^\s*$"))
        expect(cell(row, "region_names")).to_have_text(re.compile(r"^\s*$"))
    for name, code, region in ((TSH_NAME, TSH_CODE, TSH_REGION), (BUX_NAME, BUX_CODE, BUX_REGION)):
        with allure.step(f"(b) {name}: Код={code}, Регионы={region}"):
            row = m.grid_row(name)
            expect(cell(row, "code")).to_have_text(code)
            expect(cell(row, "region_names")).to_have_text(region)

    headers = page.locator(GRID_HEADER_CELL)
    with allure.step("(c) Ko'rinadigan ustunlar aynan: Название, Код, Регионы, Количество товаров "
                     "(ИД склада, Создал … yashirin)"):
        for column in ("Название", "Код", "Регионы", "Количество товаров"):
            expect(headers.filter(has_text=re.compile(rf"^\s*{column}\s*$"))).to_have_count(1)
        visible = {t.strip() for t in headers.all_inner_texts() if t.strip()}   # checkbox ustuni matnsiz
        assert visible == {"Название", "Код", "Регионы", "Количество товаров"}, f"Ustunlar: {sorted(visible)}"
    with allure.step("(d) «Статус» ustuni YO'Q"):
        expect(headers.filter(has_text=re.compile(r"Статус"))).to_have_count(0)
    with allure.step(f"(e) «{DEFAULT_WAREHOUSE}» tanlanganda «Удалить» o'chiq/yo'q (bosilmaydi)"):
        panel = row_panel(m.click_grid_row(DEFAULT_WAREHOUSE))
        expect(panel.get_by_role("button", name="Изменить", exact=True)).to_be_visible()
        delete_btn = panel.get_by_role("button", name="Удалить", exact=True)
        if delete_btn.count():
            expect(delete_btn.first).to_be_disabled()
    with allure.step(f"(e) Taqqoslash: «{TSH_NAME}» tanlanganda «Удалить» yoqiq (bosilmaydi)"):
        delete_btn = row_panel(m.click_grid_row(TSH_NAME)).get_by_role("button", name="Удалить", exact=True)
        expect(delete_btn).to_be_visible()
        expect(delete_btn).to_be_enabled()
    with allure.step(f"(f) Beta ombori «{beta_warehouse}» Alfa ro'yxatida yo'q"):
        expect(rows.filter(has_text=beta_warehouse)).to_have_count(0)
        m.search(beta_warehouse)
        expect(rows.filter(has_text=beta_warehouse)).to_have_count(0)
        expect(rows).to_have_count(0)
    with allure.step(f"(f) Nazorat: qidiruv ishlaydi — «{TSH_NAME}» topiladi"):
        m.search(TSH_NAME)
        expect(rows).to_have_count(1)
        expect(cell(rows.first, "name")).to_have_text(TSH_NAME)


@allure.id("S-05.1.1")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Ro'yxat tarkibi")
@allure.title("S-05.1.1 — Ombor ro'yxati: 3 qator, ustunlar, Статус yo'q, Beta omborlari yo'q")
@allure.tag("crud")
def test_warehouse_list_shows_columns(session_page: Page, code) -> None:
    """Alfa-admin → Склады. Kutilgan: 3 qator (standart, TSH, SAM), ustunlar Название/Код/
    Регионы/Количество товаров, «Статус» yo'q, standartda «Удалить» o'chiq, Beta omborlari yo'q.
    session_page ishlatiladi: papkadagi boshqa testlar ham session_page'da — bitta pytest
    jarayonida ikkinchi sync_playwright (function ``page``) «Sync API inside the asyncio loop»
    xatosini beradi (2026-10-16)."""
    with allure.step("Tizimga kirish (admin)"):
        login_admin(session_page)
    run_warehouse_list(session_page, code)


@allure.id("S-05.1.4")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Bitta qatorni o'chirish")
@allure.title("S-05.1.4 — Bitta omborni qator menyusidan o'chirish")
@allure.tag("crud", "bug-candidate")
def test_warehouse_delete(session_page: Page, alfa_seed) -> None:
    """Alohida ombor yaratiladi → qator menyusidan «Удалить» → Да.
    Kutilgan: ombor o'chadi (xato yo'q)."""
    page, c = session_page, alfa_seed["c"]
    name = f"Del ombori-{c}"
    with allure.step(f"Alfa-admin: alohida ombor «{name}» yaratish"):
        login_supplier_user(page, c)
        create_warehouse(page, name, "DEL", TSH_REGION)
    with allure.step("Qator menyusidan «Удалить» → Да"):
        m = open_warehouses(page)
        row_panel(m.click_grid_row(name)).get_by_role("button", name="Удалить", exact=True).click()
        m.confirm("Да")
    with allure.step("Kutilgan: ombor o'chadi (xato dialogi yo'q)"):
        err = visible_error_dialog_text(page)
        assert err is None, f"O'chirishda xato: {err}"
        m = open_warehouses(page)
        m.grid_row(TSH_NAME)                          # ro'yxat yuklandi
        m.expect_no_row(name)


@allure.id("S-05.1.6")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Moderator kirishi")
@allure.title("S-05.1.6 — Moderator supplier ko'rinishida omborlarni ochadi")
@allure.tag("access", "bug-candidate")
def test_warehouse_moderator_can_open(session_page: Page, alfa_seed) -> None:
    """Moderator → Поставщики → Alfa → Просмотр → Склады.
    Kutilgan: ro'yxat; «Создать», «Изменить», «Товары» bor."""
    page, d = session_page, alfa_seed
    m = BasePage(page)
    with allure.step(f"Moderator (admin) → Модератор → Поставщики → {d['supplier']} → Просмотр"):
        login_admin(page)
        flow_navigate(page, tab="Модератор", name="Поставщики")
        m.expect_heading("Поставщики")
        m.search(d["supplier"])
        m.click_grid_row(d["supplier"])
        m.click_button("Просмотреть", expect_heading="Поставщик (Просмотр)")
    with allure.step("Просмотр → «Склады»: ro'yxat"):
        m.click_button("Склады")
        m.settle()
        m.grid_row(TSH_NAME)
    with allure.step("Kutilgan: «Создать» bor"):
        expect(page.locator("#main-content").get_by_role("button", name="Создать", exact=True)).to_be_visible()
    with allure.step(f"Kutilgan: «{TSH_NAME}» qatorida «Изменить» va «Товары» bor"):
        panel = m.click_grid_row(TSH_NAME).locator("xpath=following-sibling::*[position()<=2]")
        expect(panel.get_by_role("button", name="Изменить", exact=True).first).to_be_visible()
        expect(panel.get_by_role("button", name="Товары", exact=True).first).to_be_visible()
