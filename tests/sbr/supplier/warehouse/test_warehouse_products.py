"""S-05 §3 Ombor tovarlari (warehouse_product_bind_list): 3.1 Прикрепленные / Доступные (web qismi).
Katalog (mobil) qismi — tests_mobile/tests/warehouse/test_warehouse_catalog.py.
Test-case: docs/qa/test-cases/sbr/supplier/warehouse.md."""
import allure
from playwright.sync_api import Page, expect

from tests.sbr.supplier.warehouse.warehouse_helpers import (
    GRID_HEADER_CELL, TSH_NAME,
    bind_tab, confirm_dialog, detach_product, login_supplier_user, open_warehouse_products, row_panel,
)


@allure.id("S-05.3.1")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Прикрепленные / Доступные")
@allure.title("S-05.3.1 (web) — Omborga tovar biriktirish va olib tashlash")
@allure.tag("crud", "effect")
def test_warehouse_product_attach_detach(session_page: Page, alfa_seed) -> None:
    """«Toshkent ombori» → Товары → Доступные → Qatiq → Прикрепить → Да; keyin Non → Открепить.
    Kutilgan: Доступные = shu omborda yo'q tovarlar; Qatiq «В наличие» = Нет; ustunlar 4 ta
    (miqdor yo'q); Non ro'yxatdan yo'qoladi."""
    page, d = session_page, alfa_seed
    login_supplier_user(page, d["c"])
    with allure.step(f"«{TSH_NAME}» → Товары → Доступные"):
        m = open_warehouse_products(page, TSH_NAME)
        bind_tab(page, m, "Доступные")
    with allure.step(f"Доступные — shu omborda bo'lmaganlar: {d['qatiq']} (hech qayerda) va {d['sut']} "
                     f"(boshqa omborda) BOR, {d['non']} (shu omborda) YO'Q"):
        m.grid_row(d["qatiq"])
        m.grid_row(d["sut"])
        m.expect_no_row(d["non"])
    with allure.step(f"{d['qatiq']} → Прикрепить → «Хотите прикрепить {d['qatiq']}?» → Да"):
        m.search(d["qatiq"])
        row = m.click_grid_row(d["qatiq"])
        row_panel(row, "Прикрепить").get_by_role("button", name="Прикрепить", exact=True).click()
        expect(confirm_dialog(page).get_by_text(f"Хотите прикрепить {d['qatiq']}?", exact=True)).to_be_visible()
        m.confirm("да")
    with allure.step(f"Прикрепленные: {d['qatiq']} «В наличие» = Нет"):
        bind_tab(page, m, "Прикрепленные")
        m.grid_row(d["qatiq"], "Нет")
    with allure.step("Ustunlar: Штрих-коды, Название, Статус, В наличие — miqdor ustuni yo'q"):
        headers = {t.strip() for t in page.locator(GRID_HEADER_CELL).all_inner_texts() if t.strip()}
        assert headers == {"Штрих-коды", "Название", "Статус", "В наличие"}, f"Ustunlar: {sorted(headers)}"
    with allure.step(f"Прикрепленные → {d['non']} → Открепить → Да → ro'yxatdan yo'qoladi"):
        detach_product(page, TSH_NAME, d["non"])
