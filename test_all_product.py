import re
import random
from playwright.sync_api import expect, Page
from flow_authorization import authorization

PRODUCT_URL = "https://app3.greenwhite.uz/x24/a2/sb/sbr/moderator/product/product_list"

ARTICLE_FILTER = (
    "Название * Краткое название * Код Производитель * "
    "Регион производство Выбрать Ст"
)


# ─── Helper funksiyalar ───────────────────────────────────────────────────────

def _go_to_product_list(page: Page) -> None:
    """Mahsulotlar ro'yxatiga o'tish."""
    page.goto(PRODUCT_URL)
    page.wait_for_load_state("networkidle")


def _pick_option(page: Page, text: str) -> None:
    opt = page.locator(".cdk-overlay-container").get_by_text(text, exact=False).first
    opt.wait_for(state="visible", timeout=6000)
    opt.click()
    page.wait_for_timeout(300)




def _click_action(page: Page, label: str, exact: bool = True) -> None:
    btn = page.get_by_role("button", name=label, exact=exact)
    for _ in range(6):
        try:
            btn.first.click(timeout=4000)
            return
        except Exception:
            page.wait_for_timeout(800)
    btn.first.click(timeout=5000)


def _click_and_confirm(page: Page, action_label: str, confirm_label: str = "да") -> None:
    """Action tugmasini bosib, tasdiq dialogi chiqishini kutadi; chiqmasa qayta
    bosadi, so'ng tasdiqlaydi."""
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


def _create_product(page: Page, name: str, status: str = "active") -> None:
    for attempt in range(3):
        try:
            _go_to_product_list(page)
            page.get_by_role("button", name="Создать").click()
            expect(page.get_by_text("Продукт (создание)").first).to_be_visible()
            page.locator(".bg-white.box-border.duration-100").first.click()
            page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
            page.locator('smt-input[smtid="name"] input').fill(name)
            page.locator('smt-input[smtid="short_name"] input').fill(name)
            page.locator("smt-control").filter(has_text="measure *").get_by_placeholder("Подбор").click()
            page.get_by_text("бл").click()
            page.get_by_role("article").filter(has_text="Название * Краткое название * Код Производитель * Регион производство Подбор Ста").get_by_placeholder("Подбор").click()
            _pick_option(page, "Energy Drink")
            page.get_by_role("button", name="Сохранить").click()

            if status == "inactive":
                page.get_by_role("radio").nth(3).click()
                page.get_by_role("button", name="Сохранить").click()

            return
        except Exception:
            if attempt == 2:
                raise
            page.wait_for_timeout(1000)


def _search_and_open(page: Page, name: str, status: str = "active") -> None:
    """Ro'yxatda qidirib kartani ochadi — natija/click flaky bo'lgani uchun retry."""
    action_btn = page.locator("button").filter(
        has_text=re.compile(r"Изменить|Удалить|Просмотреть")
    ).first
    for _ in range(4):
        _go_to_product_list(page)
        if status == "inactive":
            try:
                page.locator(".gap-2.inline-flex").first.click()
                page.get_by_role("button", name="Показать все").click()
                page.wait_for_load_state("networkidle")
            except Exception:
                pass
        page.get_by_role("searchbox", name="Поиск").fill(name)
        page.wait_for_timeout(1200)
        try:
            page.get_by_text(name).first.click(timeout=6000)
            action_btn.wait_for(state="visible", timeout=5000)
            return
        except Exception:
            page.wait_for_timeout(1000)
    page.get_by_text(name).first.click(timeout=8000)
    action_btn.wait_for(state="visible", timeout=5000)


def _delete_product(page: Page, name: str) -> None:
    _search_and_open(page, name)
    page.wait_for_timeout(500)  # sahifa render bo'lishini kutish
    _click_and_confirm(page, "Удалить")
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name)).to_have_count(0)




# ─── Testlar ──────────────────────────────────────────────────────────────────

def test_product_full_create(page: Page, code) -> None:
    """To'liq ma'lumotlar bilan mahsulot yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_tavar{a}"

    _go_to_product_list(page)
    page.get_by_role("button", name="Создать").click()
    expect(page.get_by_text("Продукт (создание)").first).to_be_visible()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator('smt-input[smtid="short_name"] input').fill(name)
    page.locator("smt-control").filter(has_text="measure *").get_by_placeholder("Подбор").click()
    page.get_by_text("бл").click()
    page.get_by_role("article").filter(has_text="Название * Краткое название * Код Производитель * Регион производство Подбор Ста").get_by_placeholder("Подбор").click()
    _pick_option(page, "Energy Drink")
    page.locator("smt-control").filter(has_text="Тип упаковки").get_by_placeholder("Подбор").click()
    _pick_option(page, "Блок")
    page.locator("smt-select-trigger").filter(has_text="Подбор").click()
    page.get_by_role("textbox", name="Поиск").fill("у")
    _pick_option(page, "Узбекистан")
    page.get_by_role("button", name="Сохранить").click()


    # Tekshiruv
    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_product(page, name)



def test_product_minimal_create(page: Page, code) -> None:
    """Minimal majburiy maydonlar bilan mahsulot yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_tavar{a}"

    _create_product(page, name)

    # Tekshiruv
    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_product(page, name)




def test_product_create_and_view(page: Page, code) -> None:
    """Yaratib, 'Просмотреть' ochish testi."""
    a = random.randint(1000, 9999)
    name = f"test_tavar{a}"

    _create_product(page, name)
    _search_and_open(page, name)

    _click_action(page, "Просмотреть", exact=False)
    expect(page.get_by_text("Продукт (Просмотр)").first).to_be_visible(timeout=10000)
    page.wait_for_load_state("networkidle")


    page.get_by_role("button", name="Go back").click()
    page.wait_for_load_state("networkidle")

    # Tekshiruv: ro'yxatga qaytdi
    expect(page.get_by_role("button", name="Создать")).to_be_visible()
    _delete_product(page, name)




def test_product_create_and_edit(page: Page, code) -> None:
    """Mahsulotni tahrirlash testi."""
    a = random.randint(1000, 9999)
    name = f"test_tavar{a}"
    edited_name = f"test_tavar{a}edit"

    _create_product(page, name)
    _search_and_open(page, name)

    _click_action(page, "Изменить")
    page.wait_for_load_state("networkidle")
    page.locator(".bg-white.box-border.duration-100").first.click()

    name_input = page.locator('smt-input[smtid="name"] input')
    name_input.wait_for(state="visible")
    name_input.clear()
    name_input.fill(edited_name)

    short_name_input = page.locator('smt-input[smtid="short_name"] input')
    short_name_input.clear()
    short_name_input.fill(edited_name)

    page.get_by_role("button", name="Сохранить").click()

    # Tekshiruv: yangi nom bilan topiladi
    _search_and_open(page, edited_name)
    expect(page.get_by_text(edited_name).first).to_be_visible()
    _delete_product(page, name)




def test_product_duplicate_error(page: Page, code) -> None:
    """Mavjud nom bilan ikkinchi marta yaratishda xato chiqishi kerak."""
    a = random.randint(1000, 9999)
    name = f"test_tavar{a}"

    # Avval yaratib saqlaymiz
    _create_product(page, name)

    # Xuddi shu nom bilan yana yaratamiz
    _go_to_product_list(page)
    page.get_by_role("button", name="Создать").click()
    expect(page.get_by_text("Продукт (создание)").first).to_be_visible()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator('smt-input[smtid="short_name"] input').fill(name)
    page.locator("smt-control").filter(has_text="measure *").get_by_placeholder("Подбор").click()
    page.get_by_text("бл").click()
    page.keyboard.press("Escape")
    page.get_by_role("article").filter(
        has_text="Название * Краткое название * Код Производитель * Регион производство Подбор Ста").get_by_placeholder(
        "Подбор").click()
    _pick_option(page, "Energy Drink")
    page.get_by_role("button", name="Сохранить").click()

    # Tekshiruv: xato dialog ko'rinadi
    close_btn = page.locator("button").filter(has_text="Закрыть")
    expect(close_btn.first).to_be_visible(timeout=5000)
    close_btn.first.dispatch_event("click")


def test_product_inactive_create(page: Page, code) -> None:
    """Passiv holda yaratilgan mahsulot kartasida 'Пассивный' ko'rinishi."""
    a = random.randint(1000, 9999)
    name = f"test_tavar{a}"

    _go_to_product_list(page)
    page.get_by_role("button", name="Создать").click()
    expect(page.get_by_text("Продукт (создание)").first).to_be_visible()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator('smt-input[smtid="short_name"] input').fill(name)
    page.locator("smt-control").filter(has_text="measure *").get_by_placeholder("Подбор").click()
    page.get_by_text("бл").click()
    page.keyboard.press("Escape")
    page.get_by_role("article").filter(
        has_text="Название * Краткое название * Код Производитель * Регион производство Подбор Ста").get_by_placeholder(
        "Подбор").click()
    _pick_option(page, "Energy Drink")
    page.get_by_role("radio").nth(3).click()
    page.get_by_role("button", name="Сохранить").click()
    _search_and_open(page, name, status="inactive")
    expect(page.get_by_text("Пассивный").first).to_be_visible(timeout=5000)



def test_product_status_change(page: Page, code) -> None:
    """Passiv mahsulotni aktiv qilish testi."""
    a = random.randint(1000, 9999)
    name = f"test_tavar{a}"

    _go_to_product_list(page)
    page.get_by_role("button", name="Создать").click()
    expect(page.get_by_text("Продукт (создание)").first).to_be_visible()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(name)
    page.locator('smt-input[smtid="short_name"] input').fill(name)
    page.locator("smt-control").filter(has_text="measure *").get_by_placeholder("Подбор").click()
    page.get_by_text("бл").click()
    page.keyboard.press("Escape")
    page.get_by_role("article").filter(
        has_text="Название * Краткое название * Код Производитель * Регион производство Подбор Ста").get_by_placeholder(
        "Подбор").click()
    _pick_option(page, "Energy Drink")
    page.get_by_role("radio").nth(3).click()
    page.get_by_role("button", name="Сохранить").click()
    _search_and_open(page, name, status="inactive")
    expect(page.get_by_text("Пассивный").first).to_be_visible(timeout=5000)
    _click_action(page, "Изменить")
    page.wait_for_load_state("networkidle")
    page.get_by_role("radio").nth(1).click()
    page.get_by_role("button", name="Сохранить").click()

    # Tekshiruv: aktiv holat ko'rinadi
    expect(page.get_by_text("Активный").first).to_be_visible(timeout=5000)

    # Tozalash
    _delete_product(page, name)


def test_product_delete(page: Page, code) -> None:
    """Mahsulotni checkbox orqali o'chirish."""
    a = random.randint(1000, 9999)
    name = f"test_tavar{a}"

    _create_product(page, name)
    _go_to_product_list(page)

    # Qidirib checkbox bilan tanlash
    page.get_by_role("searchbox", name="Поиск").fill(f"test_tavar{a}")
    page.wait_for_selector(f"text={name}", timeout=10000)
    page.get_by_role("checkbox").nth(3).click()
    _click_and_confirm(page, "Удалить", confirm_label="Да")

    # Tekshiruv
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name)).to_have_count(0)


def test_product_trim(page: Page, code) -> None:
    """Bo'shliqli nom bilan yaratish — tizim trim qilishi kerak."""
    a = random.randint(1000, 9999)
    name = f"test_tavar{a}"

    _go_to_product_list(page)
    page.get_by_role("button", name="Создать").click()
    expect(page.get_by_text("Продукт (создание)").first).to_be_visible()
    page.locator(".bg-white.box-border.duration-100").first.click()
    page.locator('smt-input[smtid="name"] input').wait_for(state="visible")
    page.locator('smt-input[smtid="name"] input').fill(f"    {name}    ")
    page.locator('smt-input[smtid="short_name"] input').fill(f"    {name}    ")
    page.locator("smt-control").filter(has_text="measure *").get_by_placeholder("Подбор").click()
    page.get_by_text("бл").click()
    page.keyboard.press("Escape")
    page.get_by_role("article").filter(
        has_text="Название * Краткое название * Код Производитель * Регион производство Подбор Ста").get_by_placeholder(
        "Подбор").click()
    _pick_option(page, "Energy Drink")
    page.get_by_role("button", name="Сохранить").click()

    _search_and_open(page, name)  # ✅ status="active" default
    expect(page.get_by_text(name).first).to_be_visible()
    _delete_product(page, name)





def test_all_product(page: Page, code) -> None:
    """Barcha testlarni bitta session da ketma-ket ishlatish."""
    authorization(page)

    test_product_full_create(page, code)
    test_product_minimal_create(page, code)
    test_product_create_and_view(page, code)
    test_product_create_and_edit(page, code)
    test_product_duplicate_error(page, code)
    test_product_inactive_create(page, code)
    test_product_status_change(page, code)
    test_product_trim(page, code)