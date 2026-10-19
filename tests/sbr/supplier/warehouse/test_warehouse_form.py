"""S-05 §2 Forma (warehouse+add|+edit): 2.1 a–e maydon tekshiruvlari, 2.2 regionlar (web).
Test-case: docs/qa/test-cases/sbr/supplier/warehouse.md."""
import re

import allure
from playwright.sync_api import Page, expect

from tests.sbr.supplier.warehouse.warehouse_helpers import (
    CREATE_HEADING, GRID_ROW, RAW_ERROR_MARKERS, SAM_REGION, TSH_NAME, TSH_REGION,
    cell, known_bug, login_supplier_user, name_input, open_create_form, open_edit_form, open_warehouses,
)
from utils.base_page import BasePage

REASON_DUP_CODE = "SMAR24-1060: dublikat kod — xom texnik xato (dup_val_on_index), tushunarli xabar yo'q"
REASON_DUP_NAME = ("S-05.2.1(e) test-case [taxmin]: ilova nomni unikal qiladi («Этот название уже используется»), "
                   "test-case «ruxsat» kutadi — Team Lead qarori kutilmoqda")
ERROR_BORDER = re.compile(r"\bborder-error-\d+")   # qizil maydon (MCP 2026-10-15)


def _input_box(m: BasePage, label):
    """Maydon chegarasi (`.smt-input-wrapper`) — qizil bo'lsa `border-error-*` klassi."""
    return (m.input_control(label=label).locator("input").first
            .locator("xpath=ancestor::*[contains(@class,'smt-input-wrapper')][1]"))


@allure.id("S-05.2.1")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Yaratish — maydonlar va tekshiruvlar")
@allure.title("S-05.2.1 (a) — Bo'sh Название bilan saqlab bo'lmaydi")
@allure.tag("crud", "negative")
def test_warehouse_create_empty_name_blocked(session_page: Page, alfa_seed) -> None:
    """Код to'ldiriladi, Название bo'sh → Сохранить.
    Kutilgan: maydon qizil, xato matni yo'q, saqlanmaydi."""
    page, c = session_page, alfa_seed["c"]
    login_supplier_user(page, c)
    m = open_create_form(page)
    with allure.step("Код to'ldiriladi, Название bo'sh → Сохранить"):
        m.input(label="Код", value=f"A{c}")
        page.get_by_role("button", name="Сохранить", exact=True).first.click()
    with allure.step("Kutilgan: forma ochiq qoladi, Название qizil (Код emas), xato matni yo'q"):
        m.expect_heading(CREATE_HEADING)
        expect(_input_box(m, "Название")).to_have_class(ERROR_BORDER)
        expect(_input_box(m, "Код")).not_to_have_class(ERROR_BORDER)
        expect(m.field_wrapper("Название")).to_have_text(re.compile(r"^\s*Название\s*\*?\s*$"))


@allure.id("S-05.2.1")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Yaratish — maydonlar va tekshiruvlar")
@allure.title("S-05.2.1 (b) — Takroriy kod «tsh»: tushunarli «bunday kod bor» xato")
@allure.tag("crud", "negative", "bug-candidate")
def test_warehouse_create_duplicate_code_error(session_page: Page, alfa_seed) -> None:
    """Код «tsh» (TSH allaqachon bor) bilan yangi ombor → Сохранить.
    Kutilgan: «bunday kod bor» — xato dialogida xom texnik matn yo'q."""
    page, c = session_page, alfa_seed["c"]
    login_supplier_user(page, c)
    m = open_create_form(page)
    with allure.step("Название + Код «tsh» → Сохранить"):
        m.input(label="Название", value=f"Dup kod-{c}")
        m.input(label="Код", value="tsh")
        page.get_by_role("button", name="Сохранить", exact=True).first.click()
    with allure.step("Kutilgan: «bunday kod bor» — xato dialogi, xom texnik matnsiz"):
        dialog = page.get_by_role("dialog").filter(has_text="Ошибка").first
        expect(dialog).to_be_visible()
        text = " ".join(dialog.inner_text().split())
        allure.attach(text, name="xato matni", attachment_type=allure.attachment_type.TEXT)
        raw_markers = [mk for mk in RAW_ERROR_MARKERS if mk in text]
        with known_bug(REASON_DUP_CODE):
            assert not raw_markers, f"Xom texnik xato ({', '.join(raw_markers)}): {text}"


@allure.id("S-05.2.1")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Yaratish — maydonlar va tekshiruvlar")
@allure.title("S-05.2.1 (c) — Koddagi chetki bo'shliqlar kesiladi")
@allure.tag("crud", "negative")
def test_warehouse_create_code_trimmed(session_page: Page, alfa_seed) -> None:
    """Код «  Z…  » (chetida bo'shliq) bilan ombor saqlanadi.
    Kutilgan: ro'yxatda kod bo'shliqsiz."""
    page, c = session_page, alfa_seed["c"]
    name, code = f"Trim ombori-{c}", f"Z{c}"
    login_supplier_user(page, c)
    m = open_create_form(page)
    with allure.step(f"Название + Код «  {code}  » → Сохранить"):
        m.input(label="Название", value=name)
        m.input(label="Код", value=f"  {code}  ")
        m.save()
    with allure.step(f"Kutilgan: ro'yxatda Код = «{code}» (bo'shliqsiz)"):
        raw = cell(open_warehouses(page).grid_row(name), "code").text_content()
        allure.attach(repr(raw), name="Код katagi (xom)", attachment_type=allure.attachment_type.TEXT)
        assert raw == code, f"Kod bo'shliq bilan saqlangan: {raw!r}"


@allure.id("S-05.2.1")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Yaratish — maydonlar va tekshiruvlar")
@allure.title("S-05.2.1 (d) — Название 500 belgidan oshmaydi")
@allure.tag("crud", "boundary")
def test_warehouse_create_name_max_500(session_page: Page, alfa_seed) -> None:
    """Название ga 501 belgi yoziladi. Kutilgan: UI 500 da cheklaydi."""
    page, c = session_page, alfa_seed["c"]
    login_supplier_user(page, c)
    open_create_form(page)
    with allure.step("Название ga 501 belgi yoziladi"):
        field = name_input(page)
        field.fill("N" * 501)
    with allure.step("Kutilgan: qiymat uzunligi 500"):
        assert len(field.input_value()) == 500, f"Uzunlik: {len(field.input_value())}"


@allure.id("S-05.2.1")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Yaratish — maydonlar va tekshiruvlar")
@allure.title("S-05.2.1 (e) — Bir xil nomli ikki ombor (ruxsat kutiladi)")
@allure.tag("crud")
def test_warehouse_create_duplicate_name_allowed(session_page: Page, alfa_seed) -> None:
    """Bir xil nomli, har xil kodli ikki ombor yaratiladi.
    Kutilgan: ruxsat — ro'yxatda ikkalasi (test-case [taxmin])."""
    page, c = session_page, alfa_seed["c"]
    name = f"Bir nom-{c}"
    login_supplier_user(page, c)
    with allure.step(f"1-ombor «{name}» (Код E1{c})"):
        m = open_create_form(page)
        m.input(label="Название", value=name)
        m.input(label="Код", value=f"E1{c}")
        m.save()
    save_error = None
    with allure.step(f"2-ombor «{name}» (Код E2{c})"):
        m = open_create_form(page)
        m.input(label="Название", value=name)
        m.input(label="Код", value=f"E2{c}")
        try:
            m.save()
        except AssertionError as exc:
            # Faqat ma'lum bag (nom band) — boshqa saqlash xatolari oddiy FAIL
            if "уже используется" not in str(exc):
                raise
            save_error = str(exc).splitlines()[0]
            m.expect_error_dialog("уже используется")      # dialog yopiladi (navbar'ni yashiradi)
    with allure.step(f"Kutilgan: ro'yxatda «{name}» nomli 2 ta ombor"):
        open_warehouses(page).grid_row(name)           # 1-ombor bor (ro'yxat yuklandi)
        with known_bug(REASON_DUP_NAME):
            assert save_error is None, f"2-ombor saqlanmadi: {save_error}"
            expect(page.locator(GRID_ROW).filter(has_text=name)).to_have_count(2)


@allure.id("S-05.2.2")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Regionlar — multiselect, daraxt")
@allure.title("S-05.2.2 (web) — Omborga 2 region; hammasi olib tashlansa regionsiz")
@allure.tag("crud", "effect")
def test_warehouse_edit_regions(session_page: Page, alfa_seed) -> None:
    """«Toshkent ombori» → Изменить → ikkinchi region → Сохранить → qayta ochish; keyin
    hamma region olib tashlanadi. Kutilgan: ikkalasi saqlanadi va ro'yxatda; oxirida regionsiz."""
    page, c = session_page, alfa_seed["c"]
    login_supplier_user(page, c)

    def _region_trigger(m: BasePage):
        return m.select_control(label="Регион")

    with allure.step(f"«{TSH_NAME}» → Изменить → Регион daraxtida {TSH_REGION} + {SAM_REGION} → Сохранить"):
        m = open_edit_form(page, TSH_NAME)
        expect(_region_trigger(m)).to_contain_text(TSH_REGION)
        # 2+ tanlovda trigger nom emas «N выбрано» ko'rsatadi
        m.select(SAM_REGION, label="Регион", expect_selected=False)
        expect(_region_trigger(m)).to_contain_text("2 выбрано")
        m.save()
    with allure.step("Qayta ochish: ikkala region tanlangan"):
        expect(_region_trigger(open_edit_form(page, TSH_NAME))).to_contain_text("2 выбрано")
    with allure.step("Ro'yxat «Регионы» ustunida ikkalasi"):
        region_cell = cell(open_warehouses(page).grid_row(TSH_NAME), "region_names")
        expect(region_cell).to_contain_text(TSH_REGION)
        expect(region_cell).to_contain_text(SAM_REGION)
    with allure.step("Hamma regionni olib tashlab (daraxtda qayta bosish) Сохранить → ombor regionsiz"):
        m = open_edit_form(page, TSH_NAME)
        for region in (TSH_REGION, SAM_REGION):
            m.select(region, label="Регион", expect_selected=False)
        expect(_region_trigger(m)).to_have_text(re.compile(r"^\s*Регион\s*$"))   # placeholder
        m.save()
        expect(cell(open_warehouses(page).grid_row(TSH_NAME), "region_names")).to_have_text(re.compile(r"^\s*$"))
