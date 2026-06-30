import re
import random
from playwright.sync_api import expect, Page
from flow_authorization import authorization

CLIENT_URL = "https://app3.greenwhite.uz/x24/a2/sb/sbr/moderator/client/client_list"


# ─── Helper funksiyalar ───────────────────────────────────────────────────────

def _go_to_client_list(page: Page) -> None:
    """Klientlar ro'yxatiga o'tish."""
    page.goto(CLIENT_URL)
    page.wait_for_load_state("networkidle")


def _dismiss_overlay(page: Page) -> None:
    """Ochiq qolgan cdk overlay backdrop'ini yopadi (keyingi click'ni to'smasligi uchun)."""
    if page.locator(".cdk-overlay-backdrop.cdk-overlay-backdrop-showing").count() > 0:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)


def _select_field(page: Page, label: str, option: str, exact: bool = True) -> None:
    """smt-control dropdownidan variant tanlaydi (eski 'Выбрать' textbox o'rniga).

    Yangi UI'da dropdown — smt-select-trigger; eski 'Выбрать' nomli textbox yo'q.
    """
    _dismiss_overlay(page)
    ctl = page.locator("smt-control").filter(has_text=label)
    trg = ctl.locator("smt-select-trigger")
    if trg.count() > 0:
        trg.first.click()
    else:
        ph = ctl.get_by_placeholder("Выбрать")
        if ph.count() > 0:
            ph.first.click()
        else:
            ctl.get_by_text("Выбрать", exact=True).first.click()
    page.wait_for_timeout(800)
    page.locator(".cdk-overlay-container").get_by_text(option, exact=exact).first.click()
    page.wait_for_timeout(700)
    _dismiss_overlay(page)


def _save_person(page: Page) -> None:
    """'Сохранить' ni bosib, saqlash so'rovi ($save) ketib ro'yxatga qaytguncha
    qayta urinadi. Forma asinxron yuklanadi — erta bosilsa so'rov ketmaydi."""
    for _ in range(4):
        if "client_list" in page.url:
            return
        try:
            with page.expect_response(
                lambda r: r.request.method == "POST"
                and "$save" in r.url and "person" in r.url.lower(),
                timeout=6000,
            ):
                page.get_by_role("button", name="Сохранить").click()
            for _ in range(20):
                if "client_list" in page.url:
                    return
                page.wait_for_timeout(500)
            return
        except Exception:
            page.wait_for_timeout(800)


def _create_client(page: Page, name: str, status: str = "active") -> None:
    """Klient yaratadi (minimal to'plam)."""
    _go_to_client_list(page)
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator('smt-input[smtid="short_name"] input').fill(name)
    _select_field(page, "Форма собственности", "MCHJ", exact=False)
    a_part = name.replace("test_client", "")
    page.locator('smt-input[smtid="tin"] input').fill(f"2{a_part}{a_part}")
    page.locator("label").filter(has_text="Клиент").nth(1).click()
    if status == "inactive":
        page.get_by_role("radio").nth(3).click()
        expect(page.get_by_role("heading")).to_contain_text("Клиенты")

    elif status == "suspended":
        page.get_by_role("radio").nth(5).click()
    _save_person(page)


def _search_and_open(page: Page, name: str) -> None:
    """Ro'yxatda qidirib, kartani ochadi.

    Angular qatorni qayta render qilgani uchun bitta click ba'zan "tegmaydi" —
    action tugmalari (Изменить/Удалить/Просмотреть) paydo bo'lguncha qayta urinamiz.
    """
    action_btn = page.locator("button").filter(
        has_text=re.compile(r"Изменить|Удалить|Просмотреть")
    ).first

    for _ in range(4):
        _go_to_client_list(page)
        page.get_by_role("searchbox", name="Поиск").fill(name)
        try:
            target = page.get_by_text(name, exact=True).first
            target.wait_for(state="visible", timeout=6000)
            target.click()
            action_btn.wait_for(state="visible", timeout=5000)
            return
        except Exception:
            page.wait_for_timeout(1500)

    target = page.get_by_text(name, exact=True).first
    target.wait_for(state="visible", timeout=8000)
    target.click()
    action_btn.wait_for(state="visible", timeout=5000)


def _click_action(page: Page, label: str, exact: bool = True) -> None:
    """Ochilgan klient panelidagi action tugmasini ishonchli bosadi.

    Panel qayta render bo'lib tugma vaqtincha DOM'dan uziladi — qayta urinamiz.
    """
    btn = page.get_by_role("button", name=label, exact=exact)
    for _ in range(6):
        try:
            btn.first.click(timeout=4000)
            return
        except Exception:
            page.wait_for_timeout(800)
    btn.first.click(timeout=5000)

def _click_and_confirm(page: Page, action_label: str, confirm_label: str = "да") -> None:
    """Action tugmasini bosib, tasdiq dialogi chiqishini kutadi.

    Panel re-render paytida click "tegmasligi" (dialog ochilmasligi) mumkin —
    tasdiq tugmasi ko'rinmaguncha action'ni qayta bosamiz, so'ng tasdiqlaymiz.
    """
    confirm = page.get_by_role("button", name=confirm_label, exact=True)
    for _ in range(6):
        try:
            page.get_by_role("button", name=action_label, exact=True).first.click(timeout=4000)
            confirm.wait_for(state="visible", timeout=4000)
            break
        except Exception:
            page.wait_for_timeout(800)
    confirm.wait_for(state="visible", timeout=5000)
    confirm.click()
    page.wait_for_load_state("networkidle")


def _delete_client(page: Page, name: str) -> None:
    _search_and_open(page, name)
    page.wait_for_timeout(500)  # sahifa render bo'lishini kutish
    _click_and_confirm(page, "Удалить")
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name)).to_have_count(0)

# ─── Testlar ──────────────────────────────────────────────────────────────────

def test_client_full_create(page: Page, code) -> None:
    """To'liq ma'lumotlar bilan klient yaratish."""
    a = random.randint(10000, 99999)
    name = f"test_client{a}"

    _go_to_client_list(page)
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator('smt-input[smtid="short_name"] input').fill(name)
    _select_field(page, "Форма собственности", "MCHJ", exact=False)
    page.locator('smt-input[smtid="tin"] input').fill(f"2{a}{a}")
    page.locator("label").filter(has_text="Клиент").nth(1).click()
    # Регион (ixtiyoriy) — bo'lsa Узбекистан ni tanlab, overlay'ni Escape bilan yopamiz
    try:
        page.locator("smt-select-trigger").filter(has_text="Регион").click(timeout=4000)
        page.get_by_role("textbox", name="Поиск").fill("у")
        page.get_by_role("treeitem", name=re.compile("Узбекистан")).first.click(timeout=4000)
        page.wait_for_timeout(400)
        page.keyboard.press("Escape")
    except Exception:
        _dismiss_overlay(page)
    # Характеристика товаров -> Отрасль = Продовольствие (smt-multi-data-select)
    page.locator("button").filter(has_text="Характеристика товаров").click()
    page.wait_for_timeout(800)
    page.locator("smt-multi-data-select input").first.click()
    page.wait_for_timeout(800)
    page.locator(".cdk-overlay-container").get_by_text("Продовольствие", exact=False).first.click()
    page.wait_for_timeout(400)
    page.keyboard.press("Escape")
    grafik = page.get_by_role("textbox", name="График работы")
    if grafik.count():
        grafik.fill("dushanba juma 19.00-9.00")
    _save_person(page)

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_client(page, name)


def test_client_minimal_create(page: Page, code) -> None:
    """Minimal majburiy maydonlar bilan klient yaratish."""
    a = random.randint(10000, 99999)
    name = f"test_client{a}"
    _create_client(page, name)

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_client(page, name)



def test_client_create_and_view(page: Page, code) -> None:
    """Barcha tablarni ko'rish testi."""
    a = random.randint(10000, 99999)
    name = f"test_client{a}"

    _create_client(page, name)
    _search_and_open(page, name)
    _click_action(page, "Просмотреть", exact=False)
    page.wait_for_load_state("networkidle")

    tabs = [
        "Запросы на сотрудничество",
        "Торговые точки",
        "Поставщики",
        "Пользователи",
        "Расчётные счёта",
        "Шаблон документооборота",
        "Реквизиты",
        "Настройки",
        "Начисления бонусов",
        "Бонусный кошелек",
        "История изменений",
    ]
    for tab in tabs:
        page.locator("button").filter(has_text=tab).first.click()
        expect(page.locator("button").filter(has_text=tab).first).to_be_visible()

    page.get_by_role("button", name="Go back").click()
    _delete_client(page, name)









def test_client_create_and_edit(page: Page, code) -> None:
    """Klientni tahrirlash."""
    a = random.randint(10000, 99999)
    name = f"test_client{a}"
    edited_name = f"client_edit{a}"

    _create_client(page, name)
    _search_and_open(page, name)

    _click_action(page, "Изменить")
    page.wait_for_load_state("networkidle")
    page.locator(".bg-white.box-border.duration-100").first.click()

    name_input = page.locator('smt-input[smtid="name"] input').first
    name_input.wait_for(state="visible")
    name_input.clear()
    name_input.fill(edited_name)

    short_name_input = page.locator('smt-input[smtid="short_name"] input').first
    short_name_input.clear()
    short_name_input.fill(edited_name)

    _save_person(page)

    _search_and_open(page, edited_name)
    expect(page.get_by_text(edited_name).first).to_be_visible()

    # TUZATISH: edited_name bilan o'chirish



def test_client_error_create(page: Page, code) -> None:
    """Bo'sh forma yuborilganda validatsiya xatosi ko'rinishi kerak."""
    _go_to_client_list(page)
    page.get_by_role("button", name="Создать").click()
    page.get_by_role("button", name="Сохранить").click()


    expect(page.get_by_text("Пожалуйста, выберите хотя бы один тип!")).to_be_visible()


def test_client_duplicate_error(page: Page, code) -> None:
    """Mavjud INN bilan ikkinchi marta yaratishda xato chiqishi kerak."""
    a = random.randint(10000, 99999)
    name = f"test_client{a}"

    # Avval yaratib saqlaymiz
    _create_client(page, name)

    # Xuddi shu TIN bilan yana yaratamiz
    _go_to_client_list(page)
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(f"{name}_dup")
    page.locator('smt-input[smtid="short_name"] input').fill(f"{name}_dup")
    _select_field(page, "Форма собственности", "MCHJ", exact=False)
    a_part = name.replace("test_client", "")
    page.locator('smt-input[smtid="tin"] input').fill(f"2{a_part}{a_part}")
    page.locator("label").filter(has_text="Клиент").nth(1).click()
    page.get_by_role("button", name="Сохранить").click()

    # Xato dialogi (cdk-overlay) ichidagi "Закрыть" — sahifadagi yashirin tugmadan farqlash
    close_btn = page.locator(".cdk-overlay-container button").filter(has_text="Закрыть").first
    close_btn.wait_for(state="visible", timeout=5000)
    close_btn.click()



def test_client_inactive_create(page: Page, code) -> None:
    """Passiv holda yaratilgan klient 'Показать все' da ko'rinishi."""
    a = random.randint(10000, 99999)
    name = f"test_client{a}"

    _go_to_client_list(page)
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator('smt-input[smtid="short_name"] input').fill(name)
    _select_field(page, "Форма собственности", "MCHJ", exact=False)
    a_part = name.replace("test_client", "")
    page.locator('smt-input[smtid="tin"] input').fill(f"2{a_part}{a_part}")
    page.locator("label").filter(has_text="Клиент").nth(1).click()
    page.get_by_role("radio").nth(3).click()
    page.get_by_role("button", name="Сохранить").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Клиенты")



    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.locator(".focus-visible\\:z-10").first.click()
    page.get_by_role("button", name="Показать все").click()

    page.get_by_text(name).first.click()

    expect(page.get_by_text("Пассивный").first).to_be_visible(timeout=5000)



def test_client_suspended_create(page: Page, code) -> None:
    """To'xtatilgan holda yaratilgan klient ko'rinishi."""
    a = random.randint(10000, 99999)
    name = f"test_client{a}"

    _create_client(page, name, status="suspended")

    _go_to_client_list(page)
    page.locator(".gap-2.inline-flex").click()
    page.get_by_role("button", name="Показать все").click()
    page.wait_for_load_state("networkidle")

    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    page.get_by_text(name).first.click()
    page.wait_for_load_state("networkidle")

    expect(page.get_by_text("Приостановлен").first).to_be_visible(timeout=5000)

    # Tozalash


def test_client_status_change(page: Page, code) -> None:
    """Aktiv klientni passiv qilish testi."""
    a = random.randint(10000, 99999)
    name = f"test_client{a}"

    _create_client(page, name)
    # Ro'yxatda qolamiz — checkbox bilan tanlash uchun sahifadan chiqmaslik kerak
    _go_to_client_list(page)
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")

    page.get_by_role("checkbox").nth(3).click()
    page.get_by_role("button", name="Изменить статус").first.click()
    page.get_by_role("menuitem", name="Пассивный").click()
    page.get_by_role("button", name="Да").click()

    _go_to_client_list(page)
    page.locator(".gap-2.inline-flex").click()
    page.get_by_role("button", name="Показать все").click()
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text("Пассивный").first).to_be_visible(timeout=5000)

    # Tozalash


def test_client_delete(page: Page, code) -> None:
    """Klientni o'chirish va yo'qligi tasdiqlash."""
    a = random.randint(10000, 99999)
    name = f"test_client{a}"

    _create_client(page, name)
    _delete_client(page, name)



def test_client_trim(page: Page, code) -> None:
    """Bo'shliqli nom bilan yaratish — tizim trim qilishi kerak."""
    a = random.randint(10000, 99999)
    name = f"test_client{a}"

    _go_to_client_list(page)
    page.get_by_role("button", name="Создать").click()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(f"    {name}    ")
    page.locator('smt-input[smtid="short_name"] input').fill(f"    {name}    ")
    _select_field(page, "Форма собственности", "MCHJ", exact=False)
    page.locator('smt-input[smtid="tin"] input').fill(f"2{a}{a}")
    page.locator("label").filter(has_text="Клиент").nth(1).click()
    _save_person(page)

    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_client(page, name)




def test_client_all_runner(page: Page, code) -> None:
    """Barcha testlarni bitta session da ketma-ket ishlatish."""
    authorization(page)

    test_client_full_create(page, code)
    test_client_minimal_create(page, code)
    test_client_create_and_view(page, code)
    test_client_create_and_edit(page, code)
    test_client_error_create(page, code)
    test_client_duplicate_error(page, code)
    test_client_inactive_create(page, code)
    test_client_suspended_create(page, code)
    test_client_status_change(page, code)
    test_client_delete(page, code)
    test_client_trim(page, code)