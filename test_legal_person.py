import re
import random
from playwright.sync_api import expect, Page
from flow_authorization import authorization

legal_person_URL = "https://app3.greenwhite.uz/x24/a2/sb/sbr/moderator/person/person_list"

# ─── Helper funksiyalar ───────────────────────────────────────────────────────

def _go_to_legal_person_list(page: Page) -> None:
    page.goto(legal_person_URL)
    page.wait_for_load_state("networkidle")
    # Angular SPA routing tugashini kutish
    page.wait_for_timeout(500)

def _create_legal_person(page: Page, name: str, status: str = "active") -> None:
    """Yuridik shaxs yaratadi (minimal to'plam)."""
    _go_to_legal_person_list(page)
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator('smt-input[smtid="short_name"] input').fill(name)
    page.get_by_role("textbox", name="Подбор").click()
    page.get_by_text("MCHJ").click()
    a_part = name.replace("test_legalperson", "")
    page.locator('smt-input[smtid="tin"] input').fill(f"2{a_part}{a_part}")
    page.locator("label").filter(has_text="Клиент").nth(1).click()
    if status == "inactive":
        page.get_by_role("radio").nth(3).click()
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")


def _search(page: Page, name: str) -> None:
    """Ro'yxatda qidiruvni bajaradi va natija paydo bo'lishini kutadi."""
    _go_to_legal_person_list(page)
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    # Angular jadvalni qayta render qilguncha kut — networkidle yetarli emas
    page.get_by_text(name).first.wait_for(state="visible", timeout=15000)


def _search_and_open(page: Page, name: str) -> None:
    """Ro'yxatda qidirib, kartani ochadi va karta yuklanishini kutadi.

    Karta ochilganda URL o'zgarmaydi (panel/modal). Angular qatorni qayta render
    qilishi sababli bitta click ba'zan "tegmaydi" — karta ochilganini "Изменить"
    tugmasi orqali tekshiramiz, ochilmasa qaytadan qidirib bosamiz.
    """
    edit_btn = page.get_by_role("button", name="Изменить", exact=True)

    for _ in range(3):
        _search(page, name)  # qaytadan qidirib, eng yangi qatorni olamiz
        page.get_by_text(name).first.click()
        page.wait_for_load_state("networkidle")
        try:
            edit_btn.wait_for(state="visible", timeout=10000)
            page.wait_for_timeout(300)  # action panel barqarorlashishi uchun
            return
        except Exception:
            continue  # click karta ochmadi — qayta urinamiz

    # so'nggi urinish — bu yerda ham chiqmasa, haqiqiy xato ko'rinadi
    edit_btn.wait_for(state="visible", timeout=10000)
    page.wait_for_timeout(300)

def _delete_legal_person(page: Page, name: str) -> None:
    _search_and_open(page, name)
    page.get_by_role("button", name="Удалить", exact=True).click()
    page.get_by_role("button", name="Да").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.locator("smt-table")).to_contain_text("Нет результатов")


# ─── Testlar ──────────────────────────────────────────────────────────────────

def test_legal_person_full_create(page: Page) -> None:
    """To'liq ma'lumotlar bilan yuridik shaxs yaratish."""
    a = random.randint(10000, 99999)
    name = f"test_legalperson{a}"

    _go_to_legal_person_list(page)
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator('smt-input[smtid="short_name"] input').fill(name)
    page.get_by_role("textbox", name="Подбор").click()
    page.get_by_text("MCHJ").click()
    page.locator('smt-input[smtid="tin"] input').fill(f"2{a}{a}")
    page.locator('smt-input[smtid="code"] input').fill(f"uzb{a}")
    page.locator("div").filter(has_text=re.compile(r"^Регион$")).nth(2).click()
    page.get_by_role("textbox", name="Поиск").fill("у")
    page.get_by_text("Узбекистан").click()
    page.get_by_role("button", name="Отслеживание визитов").click()
    page.get_by_role("button", name="Сохранить").click()
    page.locator("button").filter(has_text="Характеристика товаров").click()
    page.locator(".cdk-menu-trigger.smt-data-select").click()
    page.get_by_text("Продовольствие").click()
    page.locator("label").filter(has_text="Клиент").nth(1).click()
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()



def test_legal_person_minimal_create(page: Page) -> None:
    """Minimal majburiy maydonlar bilan yaratish."""
    a = random.randint(10000, 99999)
    name = f"test_legalperson{a}"

    _create_legal_person(page, name)
    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_legal_person(page, name)




def test_legal_person_edit(page: Page) -> None:
    """Mavjud yuridik shaxsni tahrirlash."""
    a = random.randint(10000, 99999)
    name = f"test_legalperson{a}"
    edited_short_name = f"legal_person_edit{a}"

    _create_legal_person(page, name)
    _search_and_open(page, name)

    # _search_and_open ichida "Изменить" allaqachon kutilgan
    page.get_by_role("button", name="Изменить", exact=True).click()
    page.wait_for_load_state("networkidle")

    short_name_input = page.locator('smt-input[smtid="short_name"] input')
    short_name_input.wait_for(state="visible", timeout=15000)
    short_name_input.clear()
    short_name_input.fill(edited_short_name)
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")



def test_legal_person_error_create(page: Page) -> None:
    """Bo'sh forma yuborilganda validatsiya xatosi ko'rinishi kerak."""
    _go_to_legal_person_list(page)
    page.get_by_role("button", name="Создать").click()
    page.get_by_role("button", name="Сохранить").click()
    expect(page.get_by_text("Пожалуйста, выберите хотя бы один тип!")).to_be_visible()
    page.get_by_role("button", name="Закрыть")



def test_legal_person_change_status(page: Page) -> None:
    """Aktiv ↔ Passiv holat almashtirish testi."""
    a = random.randint(10000, 99999)
    name = f"test_legalperson{a}"

    _create_legal_person(page, name, status="inactive")

    # Passiv filtr ochib qidirish (row bosmaslik — faqat checkbox kerak)
    _go_to_legal_person_list(page)
    page.locator(".gap-2.inline-flex").click()
    page.get_by_role("button", name="Показать все").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    page.get_by_text(name).first.wait_for(state="visible", timeout=15000)

    # Passiv → Aktiv
    page.get_by_text(f"test_legalperson{a}").click()
    page.get_by_role("button", name="Изменить статус").click()
    page.get_by_role("menuitem", name="Активный").click()
    page.get_by_role("button", name="Да").click()
    page.get_by_text(f"test_legalperson{a}").click()



def test_legal_person_inactive_create(page: Page) -> None:
    """Nofaol holda yaratilgan shaxs ro'yxatda ko'rinishi."""
    a = random.randint(10000, 99999)
    name = f"test_legalperson{a}"

    _create_legal_person(page, name, status="inactive")

    _go_to_legal_person_list(page)
    page.locator(".gap-2.inline-flex").click()
    page.get_by_role("button", name="Показать все").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    row = page.get_by_text(name).first
    row.wait_for(state="visible", timeout=15000)
    row.click()
    page.wait_for_load_state("networkidle")

    expect(page.get_by_text("Пассивный").first).to_be_visible(timeout=5000)

    # Tozalash


def test_legal_person_delete(page: Page) -> None:
    """Yuridik shaxsni o'chirish va yo'qligi tasdiqlash."""
    a = random.randint(10000, 99999)
    name = f"test_legalperson{a}"

    _create_legal_person(page, name)
    _delete_legal_person(page, name)



def test_legal_person_whitespace_create(page: Page) -> None:
    """Bo'shliqli nom bilan yaratish — tizim trim qilishi kerak."""
    a = random.randint(10000, 99999)
    name = f"test_legalperson{a}"

    _go_to_legal_person_list(page)
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(f"    {name}   ")
    page.locator('smt-input[smtid="short_name"] input').fill(f"   {name}   ")
    page.get_by_role("textbox", name="Подбор").click()
    page.get_by_text("MCHJ").click()
    page.locator('smt-input[smtid="tin"] input').fill(f"2{a}{a}")
    page.locator("label").filter(has_text="Клиент").nth(1).click()
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_legal_person(page, name)




def test_legal_person_runner(page: Page) -> None:
    """Barcha testlarni bitta session da ketma-ket ishlatish."""
    authorization(page)

    test_legal_person_full_create(page)
    test_legal_person_minimal_create(page)
    test_legal_person_edit(page)
    test_legal_person_error_create(page)
    test_legal_person_change_status(page)
    test_legal_person_inactive_create(page)
    test_legal_person_delete(page)
    test_legal_person_whitespace_create(page)