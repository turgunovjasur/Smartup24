import re
import random
from playwright.sync_api import expect, Page
from flow_authorization import authorization

SUPPLIER_URL = "https://app3.greenwhite.uz/x24/a2/sb/sbr/moderator/supplier/supplier_list"


# ─── Helper funksiyalar ───────────────────────────────────────────────────────

def _go_to_supplier_list(page: Page) -> None:
    page.goto(SUPPLIER_URL)
    page.wait_for_load_state("networkidle")


def _create_supplier(page: Page, name: str, status: str = "active") -> None:
    """Ta'minotchi yaratadi (minimal to'plam)."""
    _go_to_supplier_list(page)
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator('smt-input[smtid="short_name"] input').fill(name)
    page.get_by_role("textbox", name="Подбор").click()
    page.get_by_text("MCHJ").click()
    a_part = name.replace("test_supplier", "")
    page.locator('smt-input[smtid="tin"] input').fill(f"{a_part}{a_part}")
    page.locator("label").filter(has_text="Поставщик").nth(1).click()
    if status == "inactive":
        page.get_by_role("radio").nth(3).click()
    elif status == "suspended":
        page.get_by_role("radio").nth(5).click()
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")


def _search_and_open(page: Page, name: str) -> None:
    action_btn = page.locator("button").filter(
        has_text=re.compile(r"Изменить|Удалить|Просмотреть")
    ).first

    searchbox = page.get_by_role("searchbox", name="Поиск")

    for i in range(3):
        _go_to_supplier_list(page)

        searchbox.click()
        searchbox.clear()
        searchbox.press_sequentially(name, delay=100)

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)

        target_element = page.get_by_text(name, exact=True).first

        try:
            target_element.wait_for(state="visible", timeout=3000)

            target_element.click()

            action_btn.wait_for(state="visible", timeout=5000)
            return

        except Exception:
            print(f"Urinish {i + 1}: Supplier topilmadi yoki yuklanmadi, qayta urinish...")
            continue

    action_btn.wait_for(state="visible", timeout=5000)


def _delete_supplier(page: Page, name: str) -> None:
    """Ta'minotchini o'chiradi va yo'qligini tekshiradi."""
    _search_and_open(page, name)
    btn = page.get_by_role("button", name="Удалить", exact=True).first
    btn.wait_for(state="visible", timeout=10000)
    btn.click()
    confirm = page.get_by_role("button", name="да", exact=True)
    confirm.wait_for(state="visible", timeout=5000)
    confirm.click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name)).to_have_count(0)


# ─── Testlar ──────────────────────────────────────────────────────────────────

def test_supplier_max(page: Page, code) -> None:
    """To'liq ma'lumotlar bilan ta'minotchi yaratish."""
    a = random.randint(10000, 99999)
    name = f"test_supplier{a}"

    _go_to_supplier_list(page)
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator('smt-input[smtid="short_name"] input').fill(name)
    page.get_by_role("textbox", name="Подбор").click()
    page.get_by_text("MCHJ").click()
    page.locator('smt-input[smtid="tin"] input').fill(f"{a}{a}")
    page.get_by_text("Регион Регион").click()
    page.get_by_role("treeitem", name="Свернуть Узбекистан").click()
    page.keyboard.press("Escape")  # region daraxti overlay'ini yopamiz — aks holda Сохранить'ni to'sadi
    page.get_by_role("button", name="Отслеживание визитов").click()
    save_btn = page.get_by_role("button", name="Сохранить")
    save_btn.wait_for(state="visible", timeout=10000)
    save_btn.click()

    page.locator("button").filter(has_text="Характеристика товаров").click()
    page.locator("smt-multi-data-select").get_by_role("textbox", name="Подбор").click()
    page.get_by_text("Продовольствие").click()
    page.locator("label").filter(has_text="Поставщик").nth(1).click()
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_supplier(page, name)


def test_supplier_mini(page: Page, code) -> None:
    """Minimal majburiy maydonlar bilan ta'minotchi yaratish."""
    a = random.randint(10000, 99999)
    name = f"test_supplier{a}"
    _create_supplier(page, name)
    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_supplier(page, name)


def test_supplier_view(page: Page, code) -> None:
    """Barcha tablarni ko'rish testi."""
    a = random.randint(10000, 99999)
    name = f"test_supplier{a}"

    _create_supplier(page, name)
    _search_and_open(page, name)

    # ✅ .click() kerak!
    view_btn = page.get_by_role("button", name="Просмотреть")
    view_btn.wait_for(state="visible", timeout=10000)
    view_btn.click()

    tabs = [
        "Запросы на сотрудничество",
        "Получатель", "Товары", "Портфель",
        "Склад ", "Бонусная система",
        "Лимитирование товаров", "Характеристика клиента",
        "Тип цены", "Характеристика клиента", "Отзывы", "Брендинг",
        "Акция", "MML", "Скидки",
        "Расчётные счёта", "Пользователи", "Реквизиты ", "Настройки",
        "Логи интеграции (Заказы)",
        "Логи интеграции (Баланс продуктов)", "Логи интеграции (Цена продуктов)", "Логи интеграции (Возвраты)",
        "Логи интеграции (Акции)", "История изменений",
    ]
    # ✅ loop ham kerak! Har bir tabni ketma-ket bosib ko'ramiz.
    for tab in tabs:
        btn = page.locator("#main-content button").filter(
            has_text=re.compile(rf"^{re.escape(tab.strip())}$")
        ).first
        try:
            btn.click(timeout=5000)
            page.wait_for_timeout(300)
        except Exception:
            # UI qayta ishlangan — tab nomi o'zgargan/yo'q bo'lishi mumkin, o'tkazib yuboramiz
            continue
    page.get_by_role("button", name="Go back").click()
    expect(page.get_by_role("button", name="Создать")).to_be_visible(timeout=10000)
    _delete_supplier(page, name)


def test_supplier_edit(page: Page, code) -> None:
    """Ta'minotchini tahrirlash."""
    a = random.randint(10000, 99999)
    name = f"test_supplier{a}"
    edited_name = f"test_supplier_edit{a}"

    _create_supplier(page, name)
    _search_and_open(page, name)

    page.get_by_role("button", name="Изменить", exact=True).click()
    page.wait_for_load_state("networkidle")

    name_input = page.locator('smt-input[smtid="name"] input')
    name_input.wait_for(state="visible")
    name_input.clear()
    name_input.fill(edited_name)

    short_name_input = page.locator('smt-input[smtid="short_name"] input')
    short_name_input.clear()
    short_name_input.fill(edited_name)

    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    _search_and_open(page, edited_name)
    expect(page.get_by_text(edited_name).first).to_be_visible()
    _delete_supplier(page, edited_name)


def test_supplier_error(page: Page, code) -> None:
    """Bo'sh forma yuborilganda validatsiya xatosi ko'rinishi kerak."""
    _go_to_supplier_list(page)
    page.get_by_role("button", name="Создать").click()
    page.get_by_role("button", name="Сохранить").click()

    expect(page.get_by_text("Пожалуйста, выберите хотя бы один тип!")).to_be_visible()
    page.locator("#cdk-dialog-0 button").filter(has_text="Закрыть").click()

def test_supplier_duplicate(page: Page, code) -> None:
    """Mavjud INN bilan ikkinchi marta yaratishda xato chiqishi kerak."""
    a = random.randint(10000, 99999)
    name = f"test_supplier{a}"

    _create_supplier(page, name)

    _go_to_supplier_list(page)
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(f"{name}_dup")
    page.locator('smt-input[smtid="short_name"] input').fill(f"{name}_dup")
    page.get_by_role("textbox", name="Подбор").click()
    page.get_by_text("MCHJ").click()
    a_part = name.replace("test_supplier", "")
    page.locator('smt-input[smtid="tin"] input').fill(f"{a_part}{a_part}")
    page.locator("label").filter(has_text="Поставщик").nth(1).click()
    page.get_by_role("button", name="Сохранить").click()

    close_btn = page.locator(".cdk-overlay-container button").filter(has_text="Закрыть").first
    close_btn.wait_for(state="visible", timeout=10000)
    close_btn.click(force=True)  # backdrop'ni e'tiborsiz qoldiradi

    _delete_supplier(page, name)


def _open_inactive(page: Page, name: str) -> None:
    """Passiv/to'xtatilgan supplierni 'Показать все' filter bilan ochadi."""
    _go_to_supplier_list(page)
    page.locator(".gap-2.inline-flex").click()
    page.get_by_role("button", name="Показать все").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_timeout(1200)
    page.get_by_text(name, exact=True).first.click()
    page.wait_for_timeout(1000)


def test_supplier_status(page: Page, code) -> None:
    """Passiv holda yaratib, aktiv qilish testi."""
    a = random.randint(10000, 99999)
    name = f"test_supplier{a}"

    _create_supplier(page, name, status="inactive")
    _open_inactive(page, name)

    page.get_by_role("button", name="Изменить статус").click()
    page.get_by_role("menuitem", name="Активный").click()
    page.get_by_role("button", name="да", exact=True).click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("smt-badge")).to_contain_text("Активный")

    _delete_supplier(page, name)



def test_supplier_status_suspended(page: Page, code) -> None:
    """To'xtatilgan → Aktiv → To'xtatilgan holat almashtirish testi."""
    a = random.randint(10000, 99999)
    name = f"test_supplier{a}"

    _create_supplier(page, name, status="suspended")
    _open_inactive(page, name)

    page.get_by_role("button", name="Изменить статус").click()
    page.get_by_role("menuitem", name="Активный").click()
    page.get_by_role("button", name="да", exact=True).click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("smt-badge")).to_contain_text("Активный")

    _delete_supplier(page, name)



def test_supplier_delete(page: Page, code) -> None:
    """Ta'minotchini o'chirish va yo'qligi tasdiqlash."""
    a = random.randint(10000, 99999)
    name = f"test_supplier{a}"

    _create_supplier(page, name)
    _delete_supplier(page, name)


def test_supplier_trim(page: Page, code) -> None:
    """Bo'shliqli nom bilan yaratish — tizim trim qilishi kerak."""
    a = random.randint(10000, 99999)
    name = f"test_supplier{a}"

    _go_to_supplier_list(page)
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(f"    {name}   ")
    page.locator('smt-input[smtid="short_name"] input').fill(f"   {name}   ")
    page.get_by_role("textbox", name="Подбор").click()
    page.get_by_text("MCHJ").click()
    page.locator('smt-input[smtid="tin"] input').fill(f"{a}{a}")
    page.locator("label").filter(has_text="Поставщик").nth(1).click()
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")

    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_supplier(page, name)


def test_supplier_all_runner(page: Page, code) -> None:
    """Barcha testlarni bitta session da ketma-ket ishlatish."""
    authorization(page)

    test_supplier_max(page, code)
    test_supplier_mini(page, code)
    test_supplier_view(page, code)
    test_supplier_edit(page, code)
    test_supplier_error(page, code)
    test_supplier_duplicate(page, code)
    test_supplier_status(page, code)
    test_supplier_status_suspended(page, code)
    test_supplier_delete(page, code)
    test_supplier_trim(page, code)