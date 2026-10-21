"""S-05 Склады — umumiy web yordamchilar (test emas). Barcha ombor testlari
(web: tests/sbr/supplier/warehouse/, mobil: tests_mobile/tests/warehouse/) shularni ishlatadi.

UI (MCP tasdiqlangan, DEV): Поставщик → Склады, sarlavha «Склады»; grid kataklari
``[data-smt-col-key]`` (name/code/region_names/count_child); create «Склад (Добавить)»,
edit «Склад (Редактирование)»; «Регион» — multi ``smt-tree-select`` (2+ tanlovda
«N выбрано», tanlanganini qayta bosish olib tashlaydi). Standart ombor panelida «Удалить» yo'q.
"""
import random
import re
from contextlib import contextmanager

import pytest
from playwright.sync_api import Page, expect

from flows.flow_authorization import COMPANY_CODE, authorization, logout
from flows.flow_navbar import flow_navigate
from tests.test_group_a.test_client import run_client
from tests.test_group_a.test_client_user import run_client_user
from tests.test_group_a.test_cooperation import run_cooperation
from tests.test_group_a.test_product import run_product
from tests.test_group_a.test_product_linking import run_product_linking
from utils.base_page import BasePage

DEFAULT_WAREHOUSE = "Склад по умолчанию"
TSH_NAME, TSH_CODE = "Toshkent ombori", "TSH"
# Mobil testlar (tests_mobile/tests/warehouse/) o'zi yaratgan «...sam» region bilan ishlatadi.
SAM_NAME, SAM_CODE = "Samarqand ombori", "SAM"
# Web testlar: DEV'da "Toshkent"/"Samarqand" nomli region yo'q — mavjud seed regionlar ishlatiladi.
BUX_NAME, BUX_CODE = "Buxoro ombori", "BUX"
TSH_REGION = "Ташкент"
BUX_REGION = "Бухара"

GRID_ROW = ".smt-data-row"
GRID_HEADER_CELL = ".smt-grid-header smt-cell-header"
CREATE_HEADING = "Склад (Добавить)"
EDIT_HEADING = "Склад (Редактирование)"
# Xato matnidagi xom texnik belgilar — «tushunarli xato» emasligi (web dialog va API javobi)
RAW_ERROR_MARKERS = ("dup_val_on_index", "ORA-", "Z:#z:")


# ── ma'lum bag (xfail) ─────────────────────────────────────────────────────────────
@contextmanager
def known_bug(reason):
    """Faqat SHU blokdagi bag assertion'i yiqilsa — xfail (reason Allure'da ko'rinadi);
    o'tsa — XPASS sifatida FAIL (strict). ``@pytest.mark.xfail`` setup/navigatsiya
    xatolarini ham xfail deb yashirardi (2026-10-16) — shuning uchun marker emas."""
    try:
        yield
    except AssertionError as exc:
        pytest.xfail(f"{reason} | {str(exc).splitlines()[0][:300]}")
    pytest.fail(f"XPASS: {reason} — bag tuzatilgan ko'rinadi, known_bug blokini olib tashlang")


# ── kichik locator yordamchilari ────────────────────────────────────────────────────
def cell(row, key):
    """Grid qatoridagi ustun katagi (key: name / code / region_names / count_child)."""
    return row.locator(f'[data-smt-col-key="{key}"]')


def row_panel(row, has_button="Изменить"):
    """Tanlangan qator ostidagi action panel (``has_button`` tugmasi bor sibling)."""
    btn = row.page.get_by_role("button", name=has_button, exact=True)
    return row.locator("xpath=following-sibling::*[position()<=2]").filter(has=btn).first


def confirm_dialog(page: Page):
    """Ochiq tasdiqlash dialogi («Подтвердить …»)."""
    return page.locator(".cdk-overlay-container [role=dialog]").last


def name_input(page: Page):
    """Ombor formasidagi «Название» input."""
    return BasePage(page).input_control(label="Название").locator("input").first


# ── login ─────────────────────────────────────────────────────────────────────────
def login_supplier_user(page: Page, supplier_code) -> None:
    """supplier_user-{supplier_code} (Alfa-admin) sifatida toza seans."""
    logout(page)
    authorization(page, email=f"supplier_user-{supplier_code}@{COMPANY_CODE}", password="1")


def login_admin(page: Page) -> None:
    logout(page)
    authorization(page)


# ── ombor ro'yxati va formasi ───────────────────────────────────────────────────────
def open_warehouses(page: Page) -> BasePage:
    """Поставщик → Склады."""
    m = BasePage(page)
    flow_navigate(page, tab="Поставщик", name="Склады")
    m.expect_heading("Склады")
    return m


def open_create_form(page: Page) -> BasePage:
    """Склады → Создать → «Склад (Добавить)»."""
    m = open_warehouses(page)
    m.open_create()
    m.expect_heading(CREATE_HEADING)
    return m


def open_edit_form(page: Page, warehouse) -> BasePage:
    """Склады → qator → Изменить → «Склад (Редактирование)»."""
    m = open_warehouses(page)
    row = m.click_grid_row(warehouse)
    row_panel(row).get_by_role("button", name="Изменить", exact=True).click()
    m.expect_heading(EDIT_HEADING)
    m.settle()
    return m


def create_warehouse(page: Page, name, code, region) -> None:
    """Ombor yaratadi va ro'yxatda tekshiradi. Save'dan keyingi redirect barqaror emas
    (modul menyusi qayta bosilgach dashboard'ga uloqtiradi — ilova bag'i), shuning uchun
    ro'yxatga o'zimiz kiramiz."""
    m = open_create_form(page)
    m.input(label="Название", value=name)
    m.input(label="Код", value=code)
    m.select(region, label="Регион")
    m.save()
    m = open_warehouses(page)
    m.grid_row(name, code)


def create_tsh_sam_warehouses(page: Page, tsh_region, sam_region) -> None:
    """«Toshkent ombori» (TSH, ``tsh_region``) va «Samarqand ombori» (SAM, ``sam_region``)."""
    create_warehouse(page, TSH_NAME, TSH_CODE, tsh_region)
    create_warehouse(page, SAM_NAME, SAM_CODE, sam_region)


# ── seed: tovarlar va mijozlar (admin) ──────────────────────────────────────────────
def create_products(page: Page, c, category, names) -> None:
    """Har ``names`` tovari: run_product (Manufacturer-/Industry-{c}, ``category``) + linking."""
    for name in names:
        run_product(page, c, manufacturer=f"Manufacturer-{c}", industry=f"Industry-{c}",
                    category=category, name=name)
        run_product_linking(page, c, product_name=name)


def create_clients(page: Page, c, supplier, clients, *, ownership, industry) -> None:
    """``clients`` — ((client_code, region), ...): har biri client + client_user, so'ng
    hammasi ``supplier`` bilan hamkorlik (run_cooperation)."""
    for client_code, region in clients:
        run_client(page, client_code, region=region, ownership=ownership, industry=industry)
        run_client_user(page, client_code)
    for client_code, _ in clients:
        run_cooperation(page, c, supplier_name=supplier, client_name=f"client-{client_code}")


# ── ombor tovarlari (Прикрепленные / Доступные) ─────────────────────────────────────
def open_warehouse_products(page: Page, warehouse) -> BasePage:
    """Склады → qator → «Товары» («Прикрепленные» tab)."""
    m = open_warehouses(page)
    row = m.click_grid_row(warehouse)
    row_panel(row).get_by_role("button", name="Товары", exact=True).click()
    m.expect_heading("Прикрепленные товары")
    m.settle()
    return m


def bind_tab(page: Page, m: BasePage, tab) -> None:
    """«Прикрепленные»/«Доступные» tabi (get_by_role 2 element beradi — ichki button olinadi)."""
    page.locator("button").filter(has_text=re.compile(rf"^\s*{tab}\s*$")).first.click()
    m.expect_heading(f"{tab} товары")
    m.settle()


def attach_product(page: Page, warehouse, product) -> None:
    """Доступные → tovar → Прикрепить → да; yangi bog'lanish «В наличие» = Нет."""
    m = open_warehouse_products(page, warehouse)
    bind_tab(page, m, "Доступные")
    m.search(product)
    row = m.click_grid_row(product)
    row_panel(row, "Прикрепить").get_by_role("button", name="Прикрепить", exact=True).click()
    m.confirm("да")   # "Хотите прикрепить <tovar>?"
    bind_tab(page, m, "Прикрепленные")
    m.grid_row(product)


def detach_product(page: Page, warehouse, product) -> None:
    """Прикрепленные → tovar → Открепить → да → ro'yxatdan yo'qoladi."""
    m = open_warehouse_products(page, warehouse)
    row = m.click_grid_row(product)
    row_panel(row, "Открепить").get_by_role("button", name="Открепить", exact=True).click()
    m.confirm("да")   # "Хотите открепить <tovar>?"
    page.reload()
    m.expect_heading("Прикрепленные товары")
    m.settle()
    m.expect_no_row(product)


def attached_products(page: Page, warehouse, products) -> set:
    """``warehouse`` ning «Прикрепленные» ro'yxatida ``products`` dan qaysilari bor."""
    open_warehouse_products(page, warehouse)
    rows = page.locator(GRID_ROW)
    # grid chizilguncha kut (qator yoki bo'sh holat) — aks holda count() erta 0 qaytaradi
    expect(rows.first.or_(page.get_by_text("Нет результатов"))).to_be_visible()
    return {p for p in products if rows.filter(has_text=p).count()}


def set_binds(page: Page, binds: dict, products) -> None:
    """Har ombor bog'lanishlarini ``binds[warehouse]`` ga keltiradi (ortiqchasi Открепить,
    yetishmagani Прикрепить). Yangi bog'lanish Нет — kerak bo'lsa keyin set_in_stock."""
    for warehouse, want in binds.items():
        have = attached_products(page, warehouse, products)
        for product in sorted(have - set(want)):
            detach_product(page, warehouse, product)
        for product in sorted(set(want) - have):
            attach_product(page, warehouse, product)


# ── «Изменить наличие» (Поставщик → Товары) ─────────────────────────────────────────
def _stock_panel(page: Page, m: BasePage, product):
    m.search(product)
    row = m.click_grid_row(product)
    panel = row_panel(row, "Настройка")
    expect(panel.get_by_role("button", name="Настройка", exact=True)).to_be_visible()
    return panel


def _ensure_not_in_stock(page: Page, product):
    """Поставщик → Товары → tovar paneli; «Не в наличие» tugmasi bo'lsa bosadi + да + reload.
    Qaytaradi (m, panel) — bosilgan bo'lsa panel None (reload'dan keyin eskirgan)."""
    m = BasePage(page)
    flow_navigate(page, tab="Поставщик", name="Товары")
    m.expect_heading("Товары")
    panel = _stock_panel(page, m, product)
    off_btn = panel.get_by_role("button", name="Не в наличие", exact=True)
    if off_btn.count():
        off_btn.click()
        m.confirm("да")
        page.reload()
        m.settle()
        return m, None
    return m, panel


def toggle_in_stock(page: Page, product) -> None:
    """Tovarni «В наличие» (Y) qiladi — BARCHA ombor bog'lanishlari «Да». Panel faqat
    maqsad tugmani ko'rsatadi: «Да» bo'lsa avval «Не в наличие», keyin «В наличие»
    (yangi bog'lanishlar ham Y bo'lsin). Grid o'zi yangilanmaydi — reload."""
    m, panel = _ensure_not_in_stock(page, product)
    if panel is None:
        panel = _stock_panel(page, m, product)
    on_btn = panel.get_by_role("button", name="В наличие", exact=True)
    expect(on_btn).to_be_visible()
    on_btn.click()
    m.confirm("да")
    page.reload()
    m.settle()
    m.search(product)
    m.grid_row(product, "Да")


def set_in_stock(page: Page, product, want: bool) -> None:
    """Y — toggle_in_stock; N — «Не в наличие» (allaqachon Нет bo'lsa tegilmaydi)."""
    if want:
        toggle_in_stock(page, product)
        return
    m, _ = _ensure_not_in_stock(page, product)
    m.search(product)
    m.grid_row(product, "Нет")


# ── regionlar ───────────────────────────────────────────────────────────────────────
def set_warehouse_regions(page: Page, warehouse, regions, universe) -> None:
    """Ombor regionlarini aynan ``regions`` ga keltiradi. ``universe`` — testdagi barcha
    region nomlari (bir-birining qismi bo'lmasligi shart); joriy holat «Регионы»
    katagidan o'qiladi, farqlilari daraxtda toggle qilinadi, keyin ro'yxatda tekshiriladi."""
    want = set(regions)
    m = open_warehouses(page)
    text = cell(m.grid_row(warehouse), "region_names").inner_text()
    have = {r for r in universe if r in text}
    if have == want:
        return
    m = open_edit_form(page, warehouse)
    for region in sorted(have ^ want):
        m.select(region, label="Регион", expect_selected=False)
    m.save()
    m = open_warehouses(page)
    region_cell = cell(m.grid_row(warehouse), "region_names")
    for region in universe:
        if region in want:
            expect(region_cell).to_contain_text(region)
        else:
            expect(region_cell).not_to_contain_text(region)


def create_child_region(page: Page, parent, name) -> None:
    """Регионы → ``parent`` → «Области» → Создать: bola region (Регион formasida ota
    maydoni yo'q). «Области» ro'yxatida qidiruvda ota nomi qoladi — bola nomi bilan qidiriladi."""
    m = BasePage(page)

    def _open_children() -> None:
        flow_navigate(page, tab="Модератор", name="Регионы")
        m.expect_heading("Регионы")
        m.search(parent)
        row = m.click_grid_row(parent)
        row_panel(row, "Области").get_by_role("button", name="Области", exact=True).click()
        m.expect_heading(parent)
        m.settle()

    _open_children()
    m.open_create()
    m.expect_heading("Регион (Создания)")
    m.input(smtid="region-code", value=str(random.randint(10**8, 10**9 - 1)))
    m.input(smtid="region-name", value=name)
    m.save()
    _open_children()
    m.search(name)
    m.grid_row(name)
