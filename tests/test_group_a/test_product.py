import re

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_setup.test_manufacturer import run_manufacturer
from tests.test_setup.test_supplier import ensure_refs
from utils.base_page import BasePage


def pick_manufacturer(page: Page) -> str:
    """Производители ro'yxatidagi birinchi Manufacturer-* nomini qaytaradi.

    Muhitda barqaror nomli ishlab chiqaruvchi yo'q (hammasi test yaratgan
    Manufacturer-XXXX) — nom qattiq kodlanmaydi, ro'yxatdan aniq nom olinib
    select'da exact tanlanadi (prefix bilan contains-tanlash dropdown'dagi
    "Добавить" harakat elementiga urilib ketgan edi, 2026-07-05)."""
    m = BasePage(page)
    flow_navigate(page, tab="Модератор", name="Товары")
    m.expect_heading("Товары")
    m.click_link("Производители")
    m.expect_heading("Производители")
    m.search("Manufacturer-")
    row = m.grid_row("Manufacturer-")
    return re.search(r"Manufacturer-\S+", row.inner_text()).group(0)


def run_product(page: Page, code, manufacturer=None, industry=None, category=None) -> str:
    """Group A: yangi Продукт yaratadi — run_product_linking shu tovarni
    supplier'ga biriktira oladi. Yaratilgan tovar nomini qaytaradi.

    ``manufacturer``/``industry``/``category`` berilmasa bazadagi birinchi
    Manufacturer-*/Industry-*/Category-* olinadi; 0 bazada test_all ularni
    avval o'zi yaratib, aniq nomlarini uzatadi."""
    m = BasePage(page)
    name = f"product-{code}"
    if manufacturer is None:
        manufacturer = pick_manufacturer(page)

    with allure.step("Навигация: Модератор → Товары"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")

    with allure.step("Создать: yangi Продукт formasi ochish"):
        m.open_create()
        m.expect_heading("Продукт (создание)")

    with allure.step(f"Форма asosiy: Название = {name}, measure = кг, Производитель = {manufacturer}"):
        m.input(label="Название", value=name)
        m.input(label="Краткое название", value=name)
        m.select("кг", label="measure")
        m.select(manufacturer, label="Производитель")

    with allure.step(f"Характеристика: Отрасль = {industry or 'birinchi Industry-*'}, Категории = {category or 'birinchi Category-*'}"):
        m.click_button("Характеристика")
        if industry:
            m.select(industry, label="Отрасль")
        else:
            m.select("Industry-", label="Отрасль", exact=False)
        if category:
            m.select(category, label="Категории")
        else:
            m.select("Category-", label="Категории", exact=False)

    with allure.step("Сохранить"):
        # Saqlangach redirect barqaror emas (seansdagi keyingi create-savelarda
        # ilova dashboard'ga qaytarib yuboradi) — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")
        m.search(name)
        m.grid_row(name)

    return name


@allure.epic("Модератор")
@allure.feature("Group A")
@allure.story("Создание продукта")
@allure.title("Group A: yangi Продукт yaratish")
def test_product(page: Page, code) -> None:
    """Standalone: kerakli ma'lumotnomalarni (Manufacturer/Industry/Category) O'ZI
    yaratib, aniq nom bilan tovar ochadi — istalgan TOZA serverda ishlaydi
    (pick_manufacturer/"Industry-"/"Category-" fallback'lariga tayanmaydi).
    ``ensure_refs`` Industry/Category ni beradi (+ ishlatilmaydigan Region/MCHJ),
    ``run_manufacturer`` Manufacturer ni. Alohida ``{code}gp`` kodi to'qnashmaydi."""
    with allure.step("Tizimga kirish"):
        authorization(page)
    code = f"{code}gp"
    with allure.step("Ma'lumotnomalar: Industry/Category (+ Manufacturer) yaratish"):
        ensure_refs(page, code)
        run_manufacturer(page, code)
    run_product(
        page, code,
        manufacturer=f"Manufacturer-{code}", industry=f"Industry-{code}",
        category=f"Category-{code}",
    )
