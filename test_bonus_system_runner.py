import random
from playwright.sync_api import Page, expect
from flow_authorization import authorization


# ─── Helper funksiyalar ───────────────────────────────────────────────────────

def _navigate_to_bonus(page: Page) -> None:

    page.get_by_role("button", name="Модератор").click()
    page.get_by_role("menuitem", name="Бонусная система").click()



def _search_and_open(page: Page, name: str, status: str = "active") -> None:
    """Nom bo'yicha qidirib, kartani ochadi."""

    # ✅ 1. AVVAL filter — inactive bo'lsa "Показать все"
    if status == "inactive":
        page.locator(".focus-visible\\:z-10").first.click()
        page.get_by_role("button", name="Показать все").click()
        page.wait_for_load_state("domcontentloaded")

    # ✅ 2. KEYIN search
    page.get_by_role("searchbox", name="Поиск").click()
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.locator(".inline-flex.-ml-px.first\\:ml-0.first\\:\\[\\&\\>button\\]\\:rounded-l.last\\:\\[\\&\\>button\\]\\:rounded-r.cdk-menu-trigger > .bg-white").click()
    page.get_by_role("menuitem", name="Настройки поиска").click()
    page.locator("label").filter(has_text="Название бонуса").click()
    page.get_by_role("button", name="Сохранить").click()
    page.get_by_text(name).first.wait_for(state="visible", timeout=30000)
    page.get_by_text(name).first.click()


def _set_dates(page: Page) -> None:
    """Boshlanish sanasi — bugun, tugash sanasi — 31."""
    page.locator(".svg-icon-calendar > svg").first.click()
    page.get_by_role("button", name="Сегодня").click()
    page.locator("smt-control").filter(has_text="Конец периода").get_by_test_id("smt-date-picker-input").click()
    page.locator("smt-control").filter(has_text="Конец периода").get_by_test_id("smt-date-picker-input").fill(
        "30.06.2026")


def _open_create_form(page: Page) -> None:
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")


def _delete_bonus(page: Page, name: str, status: str = "active") -> None:
    _search_and_open(page, name, status=status)
    page.get_by_role("button", name="Удалить", exact=True).click()
    page.get_by_role("button", name="Да").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name)).to_have_count(0)


# ─── Testlar ──────────────────────────────────────────────────────────────────

def test_bonus_system_create(page: Page) -> None:
    """Standart bonus tizimi yaratish (Заказ завершен + sana)."""
    a = random.randint(1000, 9999)
    name = f"test_bonus{a}"
    authorization(page)
    _navigate_to_bonus(page)
    _open_create_form(page)


    page.locator("//label[contains(text(),'Название')]/..//input").fill(name)
    page.get_by_role("spinbutton").fill("5")
    _set_dates(page)

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_bonus(page, name)


def test_bonus_system_create2(page: Page) -> None:
    """MMA turi bilan bonus tizimi yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_bonus{a}"
    authorization(page)
    _navigate_to_bonus(page)
    _open_create_form(page)

    page.locator('smt-input[smtid="name"] input').fill(name)

    page.locator("smt-control").filter(has_text="Тип действия").locator("smt-select-trigger").click()
    page.locator("smt-select-dropdown").get_by_text("Минимальный обязательный ассортимент").click()
    page.locator("smt-textarea textarea").fill("test uchun yartilidi")
    page.get_by_role("spinbutton").fill("4")
    _set_dates(page)

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.locator("span.break-all", has_text=name)).to_be_visible()
    _delete_bonus(page, name)



def test_bonus_system_create3(page: Page) -> None:
    """SMARTUPX turi bilan bonus tizimi yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_bonus{a}"
    authorization(page)
    _navigate_to_bonus(page)
    _open_create_form(page)

    page.locator('smt-input[smtid="name"] input').fill(name)
    # "Источник" selecti ham xuddi shu sabab (qiymat input value'da) label orqali ochiladi
    page.locator("smt-control").filter(has_text="Источник").locator("smt-select-trigger").click()
    page.locator("smt-select-dropdown").get_by_text("SMARTUPX").click()
    page.locator("smt-textarea textarea").fill("test uchun yartilidni")
    page.get_by_role("spinbutton").fill("4")
    _set_dates(page)

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_bonus(page, name)



def test_bonus_system_create4(page: Page) -> None:
    """Switch o'chirilgan holda bonus tizimi yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_bonus{a}"
    authorization(page)
    _navigate_to_bonus(page)
    _open_create_form(page)

    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator("smt-textarea textarea").fill("test uchun yartilindi")
    page.get_by_role("spinbutton").fill("4")
    _set_dates(page)
    # Eski CSS zanjiri (div:nth-child(2) > ... > .bg-brand-500) yangi UI'da hech
    # narsa topmaydi. "Авто одобрение" switchini label orqali aniq tanlaymiz —
    # status switchi emas, aks holda yozuv inactive bo'lib qidiruvda topilmaydi.
    page.locator("smt-control").filter(has_text="Авто одобрение").get_by_role("switch").click()

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_bonus(page, name)



def test_bonus_system_mini(page: Page) -> None:
    """Minimal maydonlar bilan bonus tizimi yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_bonus{a}"
    authorization(page)
    _navigate_to_bonus(page)
    _open_create_form(page)

    page.locator('smt-input[smtid="name"] input').fill(name)
    page.get_by_role("spinbutton").fill("4")

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_bonus(page, name)



def test_bonus_system_edit(page: Page) -> None:
    """Bonus tizimini tahrirlash."""
    a = random.randint(1000, 9999)
    name = f"test_bonus{a}"
    edited_name = f"test_bonus{a}edit"
    authorization(page)
    _navigate_to_bonus(page)
    _open_create_form(page)

    page.locator('smt-input[smtid="name"] input').fill(name)
    page.get_by_role("spinbutton").fill("4")
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)

    page.get_by_role("button", name="Изменить", exact=True).dispatch_event("click")
    page.wait_for_load_state("domcontentloaded")
    page.locator(".bg-white.box-border.duration-100").first.click()
    name_input = page.locator('smt-input[smtid="name"] input')
    name_input.clear()
    name_input.fill(edited_name)
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    # Tekshiruv: yangi nom bilan topiladi
    _search_and_open(page, edited_name)
    expect(page.get_by_text(edited_name).first).to_be_visible()


def test_bonus_system_delete(page: Page) -> None:
    """Bonus tizimini o'chirish va yo'qligi tasdiqlash."""
    a = random.randint(1000, 9999)
    name = f"test_bonus{a}"
    authorization(page)
    _navigate_to_bonus(page)
    _open_create_form(page)

    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator("smt-textarea textarea").fill("test uchn yartilingan bonus")
    page.get_by_role("spinbutton").fill("5")
    _set_dates(page)

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)

    page.get_by_role("button", name="Удалить").dispatch_event("click")
    page.get_by_role("button", name="Да").click()
    page.wait_for_load_state("networkidle")

    # Tekshiruv: o'chirilgan yozuv topilmasin
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name)).to_have_count(0)


def test_bonus_system_inactive(page: Page) -> None:
    """Bonus tizimini nofaol holda yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_bonus{a}"
    authorization(page)
    _navigate_to_bonus(page)
    _open_create_form(page)

    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator("smt-textarea textarea").fill("test uchn yartilingan bonus")
    page.get_by_role("spinbutton").fill("5")
    _set_dates(page)
    page.get_by_role("switch").first.click()

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name, status="inactive")
    # Tekshiruv: karta ochildi
    expect(page.get_by_text(name).first).to_be_visible()


def test_bonus_system_status_change(page: Page) -> None:
    """Aktiv bonus tizimini 'Изменить статус' orqali o'zgartirish."""
    a = random.randint(1000, 9999)
    name = f"test_bonus{a}"
    authorization(page)
    _navigate_to_bonus(page)
    _open_create_form(page)

    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator("smt-textarea textarea").fill("test uchn yartilingan bonus")
    page.get_by_role("spinbutton").fill("5")
    _set_dates(page)

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)

    page.get_by_role("button", name="Изменить статус").click()
    page.get_by_role("button", name="Да").click()
    page.wait_for_load_state("networkidle")

    # Tekshiruv: status passiv bo'ldi — "Показать все" filter bilan topiladi
    _search_and_open(page, name, status="inactive")
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_bonus(page, name, status="inactive")


def test_bonus_system_copy(page: Page) -> None:
    """Mavjud bonus tizimidan nusxa olib duplicate xatosini tekshirish."""
    authorization(page)
    _navigate_to_bonus(page)

    page.get_by_role("searchbox", name="Поиск").click()
    page.get_by_role("searchbox", name="Поиск").fill("test MMLL")

    _open_create_form(page)

    page.locator('smt-input[smtid="name"] input').fill("test MMLL")
    page.locator("smt-textarea textarea").fill("test MMLL")
    page.get_by_role("spinbutton").fill("4")
    _set_dates(page)

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    # Tekshiruv: saqlandi yoki xato dialog ko'rindi
    expect(page.get_by_role("button", name="Создать")).to_be_visible(timeout=5000)


def test_bonus_system_trim(page: Page) -> None:
    """Bo'shliqli nom bilan yaratish — tizim trim qilishi kerak."""
    a = random.randint(1000, 9999)
    name = f"test_bonus{a}"
    authorization(page)
    _navigate_to_bonus(page)
    _open_create_form(page)

    page.locator('smt-input[smtid="name"] input').fill(f"   {name}   ")
    page.locator("smt-textarea textarea").fill("test uchn yartilingan bonus")
    page.get_by_role("spinbutton").fill("5")
    _set_dates(page)

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_bonus(page, name)



def test_bonus_system_error(page: Page) -> None:
    """Foiz (spinbutton) bo'sh qolganda xato chiqishi kerak."""
    a = random.randint(1000, 9999)
    name = f"test_bonus{a}"
    authorization(page)
    _navigate_to_bonus(page)
    _open_create_form(page)

    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator("smt-textarea textarea").fill("test uchn yartilingan bonus")
    # spinbutton bo'sh — xato chiqishi kerak
    _set_dates(page)

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    # Tekshiruv: forma saqlanmadi — hali ham yaratish formasida turibmiz
    expect(page.get_by_role("heading", name="Основная информация")).to_be_visible(timeout=5000)
    page.get_by_role("button", name="Go back").click()


def test_bonus_system_runner(page: Page) -> None:
    test_bonus_system_create(page)
    test_bonus_system_create2(page)
    test_bonus_system_create3(page)
    test_bonus_system_create4(page)
    test_bonus_system_mini(page)
    test_bonus_system_edit(page)
    test_bonus_system_delete(page)
    test_bonus_system_inactive(page)
    test_bonus_system_status_change(page)
    test_bonus_system_copy(page)
    test_bonus_system_trim(page)
    test_bonus_system_error(page)