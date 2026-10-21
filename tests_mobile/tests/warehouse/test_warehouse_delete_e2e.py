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
from tests.sbr.supplier.warehouse.seed_api import (
    seed_binds, seed_clients, seed_products, seed_reference_data, seed_supplier, seed_warehouses,
)
from tests.sbr.supplier.warehouse.warehouse_helpers import (
    DEFAULT_WAREHOUSE, GRID_ROW, SAM_CODE, SAM_NAME, TSH_CODE, TSH_NAME,
    confirm_dialog, login_supplier_user, open_warehouse_products, open_warehouses, retry_seed,
    row_panel,
)
from tests_mobile.tests.warehouse.catalog_helpers import catalog_view, expect_in_view

pytestmark = [pytest.mark.mobile, allure.epic("Supplier"), allure.feature("S-05 Склады"),
              allure.id("S-05.1.2"), allure.story("O'chirish — cascade"),
              allure.tag("crud", "effect", "bug-candidate")]


def _seed_names(c) -> dict:
    return {"c": c, "supplier": f"supplier-{c}", "gamma": f"{c}g", "epsilon": f"{c}e",
            "region_t": f"Region-{c}t", "region_s": f"Region-{c}s", "category": f"Category-{c}",
            "sut": f"Sut 1L-{c}", "qatiq": f"Qatiq-{c}"}


@pytest.fixture
def seed(code, runner_state) -> dict:
    """1-bosqich retry bilan boshqa kodda (``r{code}9``) yaratgan bo'lsa — o'sha seed."""
    return runner_state.get("s0512_seed") or _seed_names(f"{code}9")


def _view(driver, seed, client_code) -> dict:
    return catalog_view(driver, client_code, seed["supplier"], seed["category"], (seed["sut"], seed["qatiq"]))


@allure.title("S-05.1.2 (1/4) — Web: supplier, Gamma/Epsilon, tovarlar, omborlar tayyorlanadi")
def test_delete_e2e_1_setup_web(session_page: Page, seed, runner_state) -> None:
    """Shart: «Samarqand ombori»da Sut va Qatiq (Y), Qatiq boshqa omborda yo'q; Sut Toshkentda ham.
    Yiqilsa ``retry_seed`` sahifani tiklab 1 marta ``r{code}9`` bilan noldan qayta yaratadi."""
    page = session_page
    d = retry_seed(page, lambda c: _create_seed(page, _seed_names(c)), seed["c"], "S-05.1.2 seed")
    runner_state["s0512_seed"] = d
    runner_state["s0512_seed_ok"] = True


def _create_seed(page: Page, seed) -> dict:
    c = seed["c"]
    authorization(page)
    with allure.step(f"Ma'lumotnomalar, {seed['region_t']}, {seed['region_s']}, Manufacturer"):
        seed_reference_data(page, c, regions=(f"{c}t", f"{c}s"))
    common = dict(ownership=f"MCHJ-{c}", industry=f"Industry-{c}")
    with allure.step(f"Alfa {seed['supplier']} (2 region) + user; Gamma va Epsilon + userlar; hamkorlik"):
        seed_supplier(page, c, region=seed["region_t"], extra_regions=(seed["region_s"],), **common)
        seed_clients(page, c, seed["supplier"], ((seed["gamma"], seed["region_t"]), (seed["epsilon"], seed["region_s"])),
                     **common)
    with allure.step(f"Tovarlar «{seed['sut']}» va «{seed['qatiq']}» — biriktirish + narx"):
        seed_products(page, c, seed["category"], (seed["sut"], seed["qatiq"]))
    with allure.step(f"Omborlar: «{TSH_NAME}» ({seed['region_t']}), «{SAM_NAME}» ({seed['region_s']})"):
        login_supplier_user(page, c)
        seed_warehouses(page, c, ((TSH_NAME, TSH_CODE, seed["region_t"]), (SAM_NAME, SAM_CODE, seed["region_s"])))
    with allure.step("Bog'lanishlar: Sut → TSH+SAM, Qatiq → faqat SAM; standart ombordan Открепить; В наличие"):
        seed_binds(page, c,
                   attach=((TSH_NAME, seed["sut"]), (SAM_NAME, seed["sut"]), (SAM_NAME, seed["qatiq"])),
                   detach=((DEFAULT_WAREHOUSE, seed["sut"]), (DEFAULT_WAREHOUSE, seed["qatiq"])),
                   in_stock=(seed["sut"], seed["qatiq"]))
    with allure.step(f"Setup tekshiruvi: {SAM_NAME} da ikkala tovar «Да», {TSH_NAME} da faqat Sut"):
        m = open_warehouse_products(page, SAM_NAME)
        m.grid_row(seed["sut"], "Да")
        m.grid_row(seed["qatiq"], "Да")
        m = open_warehouse_products(page, TSH_NAME)
        m.grid_row(seed["sut"], "Да")
        m.expect_no_row(seed["qatiq"])
    return seed


@allure.title("S-05.1.2 (2/4) — Mobil: o'chirishdan OLDIN Epsilon katalogida Sut va Qatiq bor")
def test_delete_e2e_2_mobile_catalog_before(driver, seed, runner_state) -> None:
    """Shart nazorati: Epsilon (Samarqand) katalogda Sut va Qatiq'ni ko'radi."""
    if not runner_state.get("s0512_seed_ok"):
        pytest.skip("1-bosqich (web seed) o'tmadi")
    expect_in_view(_view(driver, seed, seed["epsilon"]), seed["epsilon"], present=(seed["sut"], seed["qatiq"]))
    runner_state["s0512_before_ok"] = True


@allure.title("S-05.1.2 (3/4) — Web: Alfa-admin «Samarqand ombori»ni o'chiradi")
def test_delete_e2e_3_delete_warehouse_web(session_page: Page, seed, runner_state) -> None:
    """«Samarqand ombori» → Удалить → «Вы действительно хотите удалить Samarqand ombori?» → Да.
    Kutilgan: ombor ro'yxatdan o'chadi."""
    if not runner_state.get("s0512_before_ok"):
        pytest.skip("2-bosqich (mobil shart nazorati) o'tmadi")
    page = session_page
    delete_msg = f"Вы действительно хотите удалить {SAM_NAME}?"
    login_supplier_user(page, seed["c"])
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
def test_delete_e2e_4_mobile_catalog_after(driver, seed, runner_state) -> None:
    """Kutilgan: Qatiq katalogdan yo'qoladi (hech qayerda Y yo'q); Epsilon Sut'ni ko'rmaydi
    (regionida ombor yo'q)."""
    if not runner_state.get("s0512_deleted"):
        pytest.skip("3-bosqich (web o'chirish) o'tmadi")
    with allure.step(f"Epsilon (client-{seed['epsilon']}): {seed['qatiq']} va {seed['sut']} YO'Q"):
        expect_in_view(_view(driver, seed, seed["epsilon"]), seed["epsilon"], absent=(seed["qatiq"], seed["sut"]))
    with allure.step(f"Gamma (client-{seed['gamma']}): {seed['qatiq']} YO'Q"):
        expect_in_view(_view(driver, seed, seed["gamma"]), seed["gamma"], absent=(seed["qatiq"],))
