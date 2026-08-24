import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_setup.test_industry import run_industry
from tests.test_setup.test_manufacturer import run_manufacturer
from utils.base_page import BasePage


def run_product(page: Page, code, name=None, status=None) -> dict:
    """Yangi Продукт yaratadi. ``name`` berilmasa product-{code}; ``status``
    berilsa shu status radiosi tanlanadi. Yaratilgan qiymatlarni qaytaradi.

    Manufacturer-{code} va Industry-{code} oldindan mavjud bo'lishi kerak
    (test_all zanjiri yoki regression'dagi ensure_product_refs yaratadi)."""
    m = BasePage(page)
    if name is None:
        name = f"product-{code}"
    kod = f"code-{name}"

    with allure.step("Навигация: Модератор → Товары"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")

    with allure.step("Создать: yangi Продукт formasi ochish"):
        m.open_create()
        m.expect_heading("Продукт (создание)")

    with allure.step("Форма asosiy: Название, Краткое название, Код"):
        m.input(label="Название", value=name)
        m.input(label="Краткое название", value=name)
        # "Код" maydoni smtid orqali: ikkinchi ketma-ket create formada yonidagi
        # label "Код сервера" ga aralashib, `label="Код"` regex mos kelmay
        # topolmaydi.
        m.input(smtid="code", value=kod)

    with allure.step(f"Форма: Производитель = Manufacturer-{code}, measure = кг"):
        m.select(f"Manufacturer-{code}", label="Производитель")
        m.select("кг", label="measure")
        if status is not None:
            m.radio(status, label="Статус")

    with allure.step(f"Характеристика: Отрасль = Industry-{code}"):
        m.click_button("Характеристика")
        m.select(f"Industry-{code}", label="Отрасль")

    with allure.step("Сохранить"):
        # Saqlangach redirect barqaror emas (seansdagi keyingi create-savelarda
        # ilova dashboard'ga qaytarib yuboradi) — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")
        m.search(name)
        if status in (None, "Активный"):
            m.grid_row(name)
        else:
            m.show_all()
            m.grid_row(name, status)

    return {"name": name, "kod": kod}


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Создание продукта")
@allure.title("Yangi Продукт yaratish")
def test_product(page: Page, code) -> None:
    """Standalone: kerakli ma'lumotnomalarni (Manufacturer/Industry) O'ZI yaratib,
    keyin tovar ochadi — istalgan TOZA serverda ishlaydi (oldindan mavjud refga
    tayanmaydi; "кг" measure tizimda global). Alohida ``{code}p`` kodi setup'dagi
    test_manufacturer/test_industry ({code}) va runner ({code}2/{code}3) nomlari
    bilan to'qnashmaydi. ``run_product`` (runner import qiladi) O'ZGARMAYDI."""
    with allure.step("Tizimga kirish"):
        authorization(page)
    code = f"{code}p"
    with allure.step("Ma'lumotnomalar: Manufacturer/Industry yaratish"):
        run_manufacturer(page, code)
        run_industry(page, code)
    run_product(page, code)


# CRUD testlari ko'chirilgan: tests/test_regression/ — bu yerda faqat basic create qoladi.
