import re
import random
from playwright.sync_api import Page, expect
from flow_authorization import authorization

SHABLON_URL = "https://app3.greenwhite.uz/x24/a2/sb/sbv/quiz/template_list"


# ─── Helper funksiyalar ───────────────────────────────────────────────────────

def _navigate_to_shablon(page: Page) -> None:
    page.goto(SHABLON_URL)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_role("heading")).to_contain_text("Шаблоны отчетов по опросам")


def _open_create_form(page: Page) -> None:
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").click()


def _search_and_open(page: Page, name: str, status: str = "active") -> None:
    page.goto(SHABLON_URL)
    page.wait_for_load_state("networkidle")
    # Passiv shablon default listda ko'rinmaydi — "Показать все" filter kerak
    if status == "inactive":
        page.locator(".gap-2.inline-flex").click()
        page.get_by_role("button", name="Показать все").click()
        page.wait_for_load_state("networkidle")
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_timeout(900)  # Angular debounce va qidiruv natijasini kutish
    page.get_by_text(name, exact=True).first.click()
    page.wait_for_timeout(800)  # Panel ochilish animatsiyasini kutish


def _create_shablon(page: Page, name: str) -> None:
    _navigate_to_shablon(page)
    _open_create_form(page)
    page.locator('input[id="null"]:not([type="checkbox"]):not([type="search"])').fill(name)
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")


# ─── Testlar ──────────────────────────────────────────────────────────────────

def test_shablon_creat_full(page: Page, code) -> None:
    a = random.randint(1000, 9999)
    name = f"test_shablon{a}"
    authorization(page)
    _navigate_to_shablon(page)
    _open_create_form(page)
    page.locator('input[id="null"]:not([type="checkbox"]):not([type="search"])').fill(name)
    page.get_by_role("button", name="+").click()
    page.get_by_role("textbox", name="Выбрать").click()
    page.get_by_role("textbox", name="Выбрать").fill("test_vaprost")
    page.wait_for_timeout(1500)
    # Dropdown'dagi birinchi mavjud test_vaprost variantini tanlaymiz
    option = page.locator(".cdk-overlay-container").get_by_text(
        re.compile(r"test_vaprost\d+")
    ).first
    option.wait_for(state="visible", timeout=10000)
    option.click()
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()


def test_shablon_creat_mini(page: Page, code) -> None:
    a = random.randint(1000, 9999)
    name = f"test_shablon{a}"
    authorization(page)
    _create_shablon(page, name)
    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()


def test_shablon_edit(page: Page, code) -> None:
    a = random.randint(1000, 9999)
    name = f"test_shablon{a}"
    edited_name = f"test_shablon{a}edit"
    authorization(page)
    _create_shablon(page, name )
    _search_and_open(page, name)

    edit_btn = page.get_by_role("button", name="Изменить", exact=True)
    edit_btn.wait_for(state="visible", timeout=10000)
    edit_btn.click()
    page.locator(".bg-white.box-border.duration-100").wait_for(state="visible")
    page.locator(".bg-white.box-border.duration-100").click()
    page.locator('input[id="null"]:not([type="checkbox"]):not([type="search"])').fill(edited_name)
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, edited_name)
    expect(page.get_by_text(edited_name).first).to_be_visible()


def test_shablon_creat_neaktive(page: Page, code) -> None:
    a = random.randint(1000, 9999)
    name = f"test_shablon{a}"
    authorization(page)
    _create_shablon(page, name)
    _search_and_open(page, name)

    neaktiv_btn = page.get_by_role("button", name="Неактивный")
    neaktiv_btn.wait_for(state="visible", timeout=5000)
    neaktiv_btn.click()
    confirm = page.get_by_role("button", name="да", exact=True)
    confirm.wait_for(state="visible", timeout=5000)
    confirm.click()
    page.wait_for_load_state("networkidle")

    # Status passiv bo'ldi — "Показать все" filter bilan qayta topiladi
    _search_and_open(page, name, status="inactive")
    expect(page.get_by_text(name).first).to_be_visible()


def test_shablon_creat_neaktive2(page: Page, code) -> None:
    a = random.randint(1000, 9999)
    name = f"test_shablon{a}"
    authorization(page)
    _navigate_to_shablon(page)
    _open_create_form(page)
    page.locator('input[id="null"]:not([type="checkbox"]):not([type="search"])').fill(name)
    page.get_by_role("switch").click()
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name,"inactive")
    expect(page.get_by_text(name).first).to_be_visible()


def test_shablon_creat_delet(page: Page, code) -> None:
    a = random.randint(1000, 9999)
    name = f"test_shablon{a}"
    authorization(page)
    _create_shablon(page, name)
    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()


def test_shablon_creat_view(page: Page, code) -> None:
    a = random.randint(1000, 9999)
    name = f"test_shablon{a}"
    authorization(page)
    _create_shablon(page, name)
    _search_and_open(page, name)



def test_shablon_creat_error(page: Page, code) -> None:
    authorization(page)
    _navigate_to_shablon(page)
    page.get_by_role("button", name="Создать").click()
    page.get_by_role("button", name="Сохранить").click()
    page.locator("button").filter(has_text="Закрыть").wait_for(state="visible")
    page.locator("button").filter(has_text="Закрыть").click()
    page.wait_for_load_state("networkidle")


def test_shablon_creat_trim(page: Page, code) -> None:
    a = random.randint(1000, 9999)
    name = f"test_shablon{a}"
    authorization(page)
    _navigate_to_shablon(page)
    _open_create_form(page)
    page.locator('input[id="null"]:not([type="checkbox"]):not([type="search"])').fill(f"    {name}    ")
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()


def test_shablon_all_runner(page: Page, code) -> None:
    authorization(page)
    test_shablon_creat_full(page, code)
    test_shablon_creat_mini(page, code)
    test_shablon_edit(page, code)
    test_shablon_creat_neaktive(page, code)
    test_shablon_creat_neaktive2(page, code)
    test_shablon_creat_delet(page, code)
    test_shablon_creat_view(page, code)
    test_shablon_creat_error(page, code)
    test_shablon_creat_trim(page, code)
