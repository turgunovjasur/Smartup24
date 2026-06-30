import random
import re

from playwright.sync_api import Page, expect
from flow_authorization import authorization


# ─── Helper funksiyalar ───────────────────────────────────────────────────────

REGION_URL = "https://app3.greenwhite.uz/x24/a2/sb/sbr/moderator/region_list"


def _navigate_to_regions(page: Page) -> None:
    # To'g'ridan-to'g'ri URL bilan o'tamiz (sidebar menyu strukturasi o'zgaruvchan)
    page.goto(REGION_URL)
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name="Создать").wait_for(state="visible", timeout=15000)


def _open_create_form(page: Page) -> None:
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").click()


def _search_and_open(page: Page, name: str) -> None:
    """Nom bo'yicha qidirib, kartani ochadi."""
    searchbox = page.get_by_role("searchbox", name="Поиск")
    searchbox.click()
    searchbox.clear()
    searchbox.press_sequentially(name, delay=150)
    target_element = page.get_by_text(name, exact=True).first
    target_element.wait_for(state="attached", timeout=15000)
    page.wait_for_timeout(300)
    target_element.click()
    page.wait_for_load_state("networkidle")



def _delete_region(page: Page, name: str) -> None:
    _search_and_open(page, name)
    page.get_by_role("button", name="Удалить", exact=True).click()
    page.get_by_role("button", name="Да").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name)).to_have_count(0)

# ─── Testlar ──────────────────────────────────────────────────────────────────

def test_region_create(page: Page, code) -> None:
    """Aktiv holda yangi region yaratish."""
    a = random.randint(1000, 9999)
    name = f"6test_region{a}"
    authorization(page)
    _navigate_to_regions(page)
    _open_create_form(page)

    page.locator("smt-input input").first.wait_for(state="visible")
    page.locator("smt-input input").first.fill(name)
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    # Tekshiruv
    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_region(page, name)


def test_region_create_inactive(page: Page, code) -> None:
    """Passiv holda region yaratish."""
    a = random.randint(100, 999)
    name = f"5test_region{a}"
    authorization(page)
    _navigate_to_regions(page)
    _open_create_form(page)

    page.locator("smt-input input").first.wait_for(state="visible")
    page.locator("smt-input input").first.fill(name)
    page.get_by_role("switch").click()  # Статус: Активный → Неактивный (passiv)
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    # Tekshiruv: passiv holda yaratildi
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.locator(".gap-2.inline-flex").click()
    page.get_by_role("button", name="Показать все").click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name, exact=True).first).to_be_visible()


def test_region_edit(page: Page, code) -> None:
    """Regionni tahrirlash."""
    a = random.randint(1000, 9999)
    name = f"4tashkent{a}"
    edited_name = f"4tashkent{a}edit"
    authorization(page)
    _navigate_to_regions(page)

    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").first.wait_for(state="visible", timeout=15000)
    page.locator(".bg-white.box-border.duration-100").click()
    page.locator("smt-input input").first.wait_for(state="visible")
    page.locator("smt-input input").first.fill(name)
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)

    page.get_by_role("button", name="Изменить").click()
    page.locator(".bg-white.box-border.duration-100").click()
    page.locator("smt-input input").first.clear()
    page.locator("smt-input input").first.wait_for(state="visible")
    page.locator("smt-input input").first.fill(edited_name)
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    # Tekshiruv: yangi nom bilan topiladi
    _search_and_open(page, edited_name)
    expect(page.get_by_text(edited_name).first).to_be_visible()


def test_region_oblast_create(page: Page, code) -> None:
    """Region ichida oblast yaratish."""
    a = random.randint(100, 999)
    region_name = f"3tashkent{a}"
    oblast_name = f"3olmazor{a}"
    authorization(page)
    _navigate_to_regions(page)

    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").first.wait_for(state="visible", timeout=15000)
    page.locator(".bg-white.box-border.duration-100").click()
    page.locator("smt-input input").first.wait_for(state="visible")
    page.locator("smt-input input").first.fill(region_name)
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, region_name)

    # Oblast yaratish
    page.get_by_role("button", name="Области").click()
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").click()
    page.locator("smt-input input").first.wait_for(state="visible")
    page.locator("smt-input input").first.fill(oblast_name)
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, region_name)

    page.get_by_role("button", name="Области").click()
    page.get_by_role("searchbox", name="Поиск").click()
    page.get_by_role("searchbox", name="Поиск").fill(oblast_name)
    expect(page.get_by_text(oblast_name).first).to_be_visible()



def test_region_delete(page: Page, code) -> None:
    """Regionni o'chirish va yo'qligi tasdiqlash."""
    a = random.randint(100, 999)
    name = f"2tashkent{a}"
    authorization(page)
    _navigate_to_regions(page)

    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").first.wait_for(state="visible", timeout=15000)
    page.locator(".bg-white.box-border.duration-100").click()
    page.locator("smt-input input").first.wait_for(state="visible")
    page.locator("smt-input input").first.fill(name)
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)

    page.get_by_role("button", name="Удалить", exact=True).click()
    confirm = page.get_by_role("button", name="да", exact=True)
    confirm.wait_for(state="visible", timeout=5000)
    confirm.click()
    page.wait_for_load_state("networkidle")

    # Tekshiruv: o'chirilgan yozuv topilmasin
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name)).to_have_count(0)


def test_region_duplicate_error(page: Page, code) -> None:
    """Mavjud nom bilan yaratishda xato chiqishi kerak."""
    authorization(page)
    _navigate_to_regions(page)

    page.get_by_role("searchbox", name="Поиск").click()
    page.get_by_role("searchbox", name="Поиск").fill("Узбекистан")

    _open_create_form(page)
    page.locator("smt-input input").first.wait_for(state="visible")
    page.locator("smt-input input").first.fill("Узбекистан")
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    # Tekshiruv: xato dialog ko'rinadi
    close_btn = page.locator(".cdk-overlay-container button").filter(has_text="Закрыть")
    expect(close_btn.first).to_be_visible(timeout=5000)
    close_btn.first.click()


def test_region_trim(page: Page, code) -> None:
    """Bo'shliqli nom bilan yaratish — tizim trim qilishi kerak."""
    a = random.randint(100, 999)
    name = f"11tashkent{a}"
    authorization(page)
    _navigate_to_regions(page)

    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").first.wait_for(state="visible", timeout=15000)
    page.locator(".bg-white.box-border.duration-100").click()
    page.locator("smt-input input").first.wait_for(state="visible")
    page.locator("smt-input input").first.fill(f"   {name}   ")
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    # Tekshiruv: trim qilingan nom bilan topiladi
    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_region(page, name)



def test_region_all_runner(page: Page, code) -> None:
    test_region_create(page, code)
    test_region_create_inactive(page, code)
    test_region_edit(page, code)
    test_region_oblast_create(page, code)
    test_region_delete(page, code)
    test_region_duplicate_error(page, code)
    test_region_trim(page, code)