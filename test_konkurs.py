import re
import random
from playwright.sync_api import Page, expect
from flow_authorization import authorization


# ─── Helper funksiyalar ───────────────────────────────────────────────────────

RANK_LOCATOR = (
    "smt-control:nth-child(2) > .flex.flex-col.gap-0\\.75 > div > "
    "smt-input > .flex.flex-col > div > .bg-white"
)


KONKURS_URL = "https://app3.greenwhite.uz/x24/a2/sb/sbg/moderator/contest_list"


def _navigate_to_konkurs(page: Page) -> None:
    # To'g'ridan-to'g'ri URL bilan o'tamiz (sidebar menyu strukturasi o'zgaruvchan)
    page.goto(KONKURS_URL)
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name="Создать").wait_for(state="visible", timeout=15000)


def _open_create_form(page: Page) -> None:
    page.get_by_role("button", name="Создать").click()
    page.locator("input[name='ng.form1.name']").wait_for(state="visible", timeout=15000)
    page.locator(".bg-white.box-border.duration-100").first.click()


def _fill_base(page: Page, name: str, rank: str = "2") -> None:
    """Nom va rank to'ldiradi."""
    page.locator("input[name='ng.form1.name']").fill(name)
    page.locator(RANK_LOCATOR).click()
    page.locator("input[name='ng.form1.rank_count']").fill(rank)


def _search_and_open(page: Page, name: str) -> None:
    """Qidirib kartani ochadi (panel ochilguncha qayta urinish)."""
    action_btn = page.locator("button").filter(
        has_text=re.compile(r"Просмотр|Изменить|Удалить")
    ).first

    for _ in range(3):
        page.get_by_role("searchbox", name="Поиск").fill(name)
        page.wait_for_timeout(1200)
        page.get_by_text(name).first.click()
        page.wait_for_timeout(1000)
        try:
            action_btn.wait_for(state="visible", timeout=5000)
            return
        except Exception:
            _navigate_to_konkurs(page)
            continue

    action_btn.wait_for(state="visible", timeout=5000)



# ─── Testlar ──────────────────────────────────────────────────────────────────

def test_konkurs_create_full(page: Page, code) -> None:
    """To'liq ma'lumotlar bilan konkurs yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_konkurs{a}"
    authorization(page)
    _navigate_to_konkurs(page)
    _open_create_form(page)
    _fill_base(page, name)

    page.locator("smt-tree-select").get_by_text("Регион").click()
    page.get_by_role("textbox", name="Поиск").fill("у")
    page.get_by_text("Узбекистан").click()
    page.get_by_role("textbox", name="Характеристики", exact=True).click()
    page.get_by_text("test", exact=True).click()
    page.get_by_role("textbox", name="Характеристики клиента").click()
    page.locator("div").filter(has_text="Full nam").nth(5).click()
    page.get_by_role("radio").nth(3).click()

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()


def test_konkurs_create2(page: Page, code) -> None:
    """Ikkinchi tur varianti bilan konkurs yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_konkurs{a}"
    authorization(page)
    _navigate_to_konkurs(page)
    _open_create_form(page)
    _fill_base(page, name)

    page.locator("smt-tree-select").get_by_text("Регион").click()
    page.get_by_role("textbox", name="Поиск").fill("у")
    page.get_by_text("Узбекистан").click()
    page.get_by_role("textbox", name="Характеристики", exact=True).click()
    page.get_by_text("test", exact=True).click()
    page.get_by_role("textbox", name="Характеристики клиента").click()
    page.locator("div").filter(has_text="Full nam").nth(5).click()
    page.get_by_role("radio").nth(3).click()

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name, exact=True).first).to_be_visible()



def test_konkurs_create_mini(page: Page, code) -> None:
    """Minimal maydonlar bilan konkurs yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_konkurs{a}"
    authorization(page)
    _navigate_to_konkurs(page)
    _open_create_form(page)
    _fill_base(page, name)

    page.get_by_role("radio").nth(3).click()
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()



def test_konkurs_view(page: Page, code) -> None:
    """Konkursni ko'rish va tablarni ochish testi."""
    a = random.randint(1000, 9999)
    name = f"test_konkurs{a}"
    authorization(page)
    _navigate_to_konkurs(page)
    _open_create_form(page)
    _fill_base(page, name)

    page.get_by_role("radio").nth(3).click()
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)

    view_btn = page.get_by_role("button", name="Просмотр")
    view_btn.wait_for(state="visible", timeout=5000)
    view_btn.click()
    page.locator("button").filter(has_text="Результаты").first.wait_for(state="visible", timeout=15000)

    for tab in ["Результаты", "История изменений"]:
        page.locator("button").filter(has_text=tab).click()
        expect(page.locator("button").filter(has_text=tab)).to_be_visible()

    page.get_by_role("button", name="Go back").click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_role("button", name="Создать")).to_be_visible()


def test_konkurs_edit(page: Page, code) -> None:
    """Konkursni tahrirlash."""
    a = random.randint(1000, 9999)
    name = f"test_konkurs{a}"
    edited_name = f"test_konkurs{a}edit"
    authorization(page)
    _navigate_to_konkurs(page)
    _open_create_form(page)
    _fill_base(page, name)

    page.get_by_role("radio").nth(3).click()
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)

    edit_btn = page.get_by_role("button", name="Изменить", exact=True)
    edit_btn.wait_for(state="visible", timeout=5000)
    edit_btn.click()
    page.locator(".bg-white.box-border.duration-100").first.click()
    name_input = page.locator("smt-input[smtid='name'] input")
    name_input.wait_for(state="visible")
    name_input.clear()
    name_input.fill(edited_name)
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, edited_name)
    expect(page.get_by_text(edited_name).first).to_be_visible()


def test_konkurs_create_draft(page: Page, code) -> None:
    """Qoralama (chernovik) holatida konkurs yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_konkurs{a}"
    authorization(page)
    _navigate_to_konkurs(page)
    _open_create_form(page)
    _fill_base(page, name)

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()


def test_konkurs_create_finished(page: Page, code) -> None:
    """'Завершён' holatida konkurs yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_konkurs{a}"
    authorization(page)
    _navigate_to_konkurs(page)
    _open_create_form(page)
    _fill_base(page, name)

    page.get_by_role("radio").nth(5).click()
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()


def test_konkurs_delete(page: Page, code) -> None:
    """Konkursni o'chirish va yo'qligi tasdiqlash."""
    a = random.randint(1000, 9999)
    name = f"test_konkurs{a}"
    authorization(page)
    _navigate_to_konkurs(page)
    _open_create_form(page)
    _fill_base(page, name)

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)

    delete_btn = page.get_by_role("button", name="Удалить", exact=True)
    delete_btn.wait_for(state="visible", timeout=5000)
    delete_btn.click()
    confirm_btn = page.get_by_role("button", name="да", exact=True)
    confirm_btn.wait_for(state="visible", timeout=5000)
    confirm_btn.click()
    page.wait_for_load_state("networkidle")

    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name)).to_have_count(0)


def test_konkurs_create_error(page: Page, code) -> None:
    """Nom bo'sh qolganda xato chiqishi kerak."""
    authorization(page)
    _navigate_to_konkurs(page)
    _open_create_form(page)

    page.locator(RANK_LOCATOR).click()
    page.locator("input[name='ng.form1.rank_count']").fill("2")
    page.get_by_role("radio").nth(3).click()
    page.get_by_role("button", name="Сохранить").click()

    # Nom bo'sh bo'lgani uchun forma yuborilmaydi — create formada qolamiz
    expect(page.locator("input[name='ng.form1.name']")).to_be_visible()
    expect(page.get_by_role("button", name="Сохранить")).to_be_visible()


def test_konkurs_create_trim(page: Page, code) -> None:
    """Bo'shliqli nom bilan yaratish — tizim trim qilishi kerak."""
    a = random.randint(1000, 9999)
    name = f"test_konkurs{a}"
    authorization(page)
    _navigate_to_konkurs(page)
    _open_create_form(page)

    page.locator("input[name='ng.form1.name']").fill(f"    {name}   ")
    page.locator(RANK_LOCATOR).click()
    page.locator("input[name='ng.form1.rank_count']").fill("2")
    page.get_by_role("radio").nth(3).click()

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()


def test_konkurs_all_runner(page: Page, code) -> None:
    authorization(page)
    test_konkurs_create_full(page, code)
    test_konkurs_create2(page, code)
    test_konkurs_create_mini(page, code)
    test_konkurs_view(page, code)
    test_konkurs_edit(page, code)
    test_konkurs_create_draft(page, code)
    test_konkurs_create_finished(page, code)
    test_konkurs_create_error(page, code)
    test_konkurs_create_trim(page, code)
