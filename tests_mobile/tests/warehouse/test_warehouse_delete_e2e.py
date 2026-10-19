"""S-05.1.2 Ombor o'chirish — tovarlar va regionlar cascade (WEB + MOBIL), 4 bosqich ketma-ket:
1 web seed → 2 mobil katalog (oldin) → 3 web o'chirish → 4 mobil katalog (keyin).
Oldingi bosqich yiqilsa keyingisi skip. Kod varianti {code}9.

Katalog MOBILDA tekshiriladi (web zakaz katalogi ombor regionini filtrlamaydi). DEV'da
Toshkent/Samarqand yo'q — test Region-{c}t (Gamma, TSH) va Region-{c}s (Epsilon, SAM)
yaratadi. Avtomatlashtirilmagan: DW qayta qurilmasligi, Dalion bind (UI'dan ko'rinmaydi),
tovar so'rovi → ORA-02292 (SMAR24-1059, UI'da so'rov yaratish yo'li yo'q).
Test-case: docs/qa/test-cases/sbr/supplier/warehouse.md.
"""
import re

import allure
import pytest
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from tests.sbr.supplier.warehouse.warehouse_helpers import (
    DEFAULT_WAREHOUSE, GRID_ROW, SAM_CODE, SAM_NAME, TSH_CODE, TSH_NAME,
    attach_product, confirm_dialog, create_warehouse, detach_product, login_supplier_user,
    open_warehouse_products, open_warehouses, row_panel, toggle_in_stock,
)
from tests.test_group_a.test_client import run_client
from tests.test_group_a.test_client_user import run_client_user
from tests.test_group_a.test_cooperation import run_cooperation
from tests.test_group_a.test_product import run_product
from tests.test_group_a.test_product_linking import run_product_linking
from tests.test_group_a.test_supplier import run_supplier
from tests.test_group_a.test_supplier_user import run_supplier_user
from tests.test_setup.test_manufacturer import run_manufacturer
from tests.test_setup.test_region import run_region
from tests.test_setup.test_supplier import ensure_refs
from tests_mobile.tests.warehouse.catalog_helpers import catalog_view, expect_in_view

pytestmark = [pytest.mark.mobile, allure.epic("Supplier"), allure.feature("S-05 Склады"),
              allure.id("S-05.1.2"), allure.story("O'chirish — cascade"),
              allure.tag("crud", "effect", "bug-candidate")]


@pytest.fixture
def n(code) -> dict:
    c = f"{code}9"
    return {"c": c, "supplier": f"supplier-{c}", "gamma": f"{c}g", "epsilon": f"{c}e",
            "region_t": f"Region-{c}t", "region_s": f"Region-{c}s", "category": f"Category-{c}",
            "sut": f"Sut 1L-{c}", "qatiq": f"Qatiq-{c}"}


def _view(driver, n, client_code) -> dict:
    return catalog_view(driver, client_code, n["supplier"], n["category"], (n["sut"], n["qatiq"]))


@allure.title("S-05.1.2 (1/4) — Web: supplier, Gamma/Epsilon, tovarlar, omborlar tayyorlanadi")
def test_delete_e2e_1_setup_web(session_page: Page, n, runner_state) -> None:
    """Shart: «Samarqand ombori»da Sut va Qatiq (Y), Qatiq boshqa omborda yo'q; Sut Toshkentda ham."""
    page, c = session_page, n["c"]
    authorization(page)
    with allure.step(f"Ma'lumotnomalar, {n['region_t']}, {n['region_s']}, Manufacturer"):
        ensure_refs(page, c)
        run_region(page, f"{c}t")
        run_region(page, f"{c}s")
        run_manufacturer(page, c)
    common = dict(ownership=f"MCHJ-{c}", industry=f"Industry-{c}")
    with allure.step(f"Alfa {n['supplier']} (2 region) + user; Gamma va Epsilon + userlar; hamkorlik"):
        run_supplier(page, c, region=n["region_t"], extra_regions=(n["region_s"],), **common)
        run_supplier_user(page, c)
        run_client(page, n["gamma"], region=n["region_t"], **common)
        run_client_user(page, n["gamma"])
        run_client(page, n["epsilon"], region=n["region_s"], **common)
        run_client_user(page, n["epsilon"])
        for client_code in (n["gamma"], n["epsilon"]):
            run_cooperation(page, c, supplier_name=n["supplier"], client_name=f"client-{client_code}")
    with allure.step(f"Tovarlar «{n['sut']}» va «{n['qatiq']}» — biriktirish + narx"):
        for name in (n["sut"], n["qatiq"]):
            run_product(page, c, manufacturer=f"Manufacturer-{c}", industry=f"Industry-{c}",
                        category=n["category"], name=name)
            run_product_linking(page, c, product_name=name)
    with allure.step(f"Omborlar: «{TSH_NAME}» ({n['region_t']}), «{SAM_NAME}» ({n['region_s']})"):
        login_supplier_user(page, c)
        create_warehouse(page, TSH_NAME, TSH_CODE, n["region_t"])
        create_warehouse(page, SAM_NAME, SAM_CODE, n["region_s"])
    with allure.step(f"Bog'lanishlar: Sut → TSH+SAM, Qatiq → faqat SAM; standart ombordan Открепить; В наличие"):
        attach_product(page, TSH_NAME, n["sut"])
        attach_product(page, SAM_NAME, n["sut"])
        attach_product(page, SAM_NAME, n["qatiq"])
        detach_product(page, DEFAULT_WAREHOUSE, n["sut"])
        detach_product(page, DEFAULT_WAREHOUSE, n["qatiq"])
        toggle_in_stock(page, n["sut"])
        toggle_in_stock(page, n["qatiq"])
    with allure.step(f"Setup tekshiruvi: {SAM_NAME} da ikkala tovar «Да», {TSH_NAME} da faqat Sut"):
        m = open_warehouse_products(page, SAM_NAME)
        m.grid_row(n["sut"], "Да")
        m.grid_row(n["qatiq"], "Да")
        m = open_warehouse_products(page, TSH_NAME)
        m.grid_row(n["sut"], "Да")
        m.expect_no_row(n["qatiq"])
    runner_state["s0512_seed_ok"] = True


@allure.title("S-05.1.2 (2/4) — Mobil: o'chirishdan OLDIN Epsilon katalogida Sut va Qatiq bor")
def test_delete_e2e_2_catalog_before_mobile(driver, n, runner_state) -> None:
    """Shart nazorati: Epsilon (Samarqand) katalogda Sut va Qatiq'ni ko'radi."""
    if not runner_state.get("s0512_seed_ok"):
        pytest.skip("1-bosqich (web seed) o'tmadi")
    expect_in_view(_view(driver, n, n["epsilon"]), n["epsilon"], present=(n["sut"], n["qatiq"]))
    runner_state["s0512_before_ok"] = True


@allure.title("S-05.1.2 (3/4) — Web: Alfa-admin «Samarqand ombori»ni o'chiradi")
def test_delete_e2e_3_delete_warehouse_web(session_page: Page, n, runner_state) -> None:
    """«Samarqand ombori» → Удалить → «Вы действительно хотите удалить Samarqand ombori?» → Да.
    Kutilgan: ombor ro'yxatdan o'chadi."""
    if not runner_state.get("s0512_before_ok"):
        pytest.skip("2-bosqich (mobil shart nazorati) o'tmadi")
    page = session_page
    delete_msg = f"Вы действительно хотите удалить {SAM_NAME}?"
    login_supplier_user(page, n["c"])
    with allure.step(f"Склады → «{SAM_NAME}» → Удалить → «{delete_msg}» → Да"):
        m = open_warehouses(page)
        row_panel(m.click_grid_row(SAM_NAME)).get_by_role("button", name="Удалить", exact=True).click()
        dialog = confirm_dialog(page)
        expect(dialog).to_contain_text("Подтвердить")
        expect(dialog.get_by_text(delete_msg, exact=True)).to_be_visible()
        m.confirm("Да")
    with allure.step(f"Ombor o'chdi: ro'yxatda «{SAM_NAME}» 0"):
        m = open_warehouses(page)
        m.grid_row(TSH_NAME)          # ro'yxat yuklandi (premature 0 emas)
        expect(page.locator(GRID_ROW).filter(has_text=re.compile(re.escape(SAM_NAME)))).to_have_count(0)
    runner_state["s0512_deleted"] = True


@allure.title("S-05.1.2 (4/4) — Mobil: Epsilon Qatiq va Sut'ni ko'rmaydi, Gamma Qatiq'ni ko'rmaydi")
def test_delete_e2e_4_catalog_after_mobile(driver, n, runner_state) -> None:
    """Kutilgan: Qatiq katalogdan yo'qoladi (hech qayerda Y yo'q); Epsilon Sut'ni ko'rmaydi
    (regionida ombor yo'q)."""
    if not runner_state.get("s0512_deleted"):
        pytest.skip("3-bosqich (web o'chirish) o'tmadi")
    with allure.step(f"Epsilon (client-{n['epsilon']}): {n['qatiq']} va {n['sut']} YO'Q"):
        expect_in_view(_view(driver, n, n["epsilon"]), n["epsilon"], absent=(n["qatiq"], n["sut"]))
    with allure.step(f"Gamma (client-{n['gamma']}): {n['qatiq']} YO'Q"):
        expect_in_view(_view(driver, n, n["gamma"]), n["gamma"], absent=(n["qatiq"],))
