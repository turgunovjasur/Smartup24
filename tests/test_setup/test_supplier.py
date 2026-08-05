import random

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_setup.test_category import run_category
from tests.test_setup.test_form_of_ownership import run_form_of_ownership
from tests.test_setup.test_industry import run_industry
from tests.test_setup.test_region import run_region
from utils.base_page import BasePage


def run_supplier(page: Page, code, name=None, status=None) -> dict:
    """Yangi Поставщик (Тип=Поставщик) yaratadi. ``name`` berilmasa
    Supplier-{code}; ``status`` berilsa shu status radiosi tanlanadi (masalan
    "Пассивный"/"Приостановлено" — bunda passiv yozuv default ro'yxatda
    ko'rinmagani uchun tekshiruv "Показать все" bilan bajariladi). Yaratilgan
    qiymatlarni qaytaradi (regression CRUD testlari view/duplicate uchun
    Краткое = name va ``tin``/``form``/``region`` ga tayanadi — run_client
    bilan bir xil naqsh, ikkalasi ham umumiy person moduli)."""
    m = BasePage(page)
    if name is None:
        name = f"Supplier-{code}"
    tin = random.randint(100000000, 999999999)
    form = f"MCHJ-{code}"
    region = f"Region-{code}"

    with allure.step("Навигация: Модератор → Поставщики"):
        flow_navigate(page, tab="Модератор", name="Поставщики")
        m.expect_heading("Поставщики")

    with allure.step("Создать: yangi Поставщик formasi ochish"):
        m.open_create()
        m.expect_heading("Юр. Лицо (Создания)")

    with allure.step(f"Форма asosiy: Юр. лица название = {name}, ИНН = {tin}"):
        m.input(label="Юр. лица название", value=name)
        m.input(label="Краткое название", value=name)
        m.input(label="ИНН", value=tin)

    with allure.step(f"Форма: Форма собственности = {form}, Тип = Поставщик, Регион = {region}"):
        m.select(option_text=form, label="Форма собственности")
        m.radio("Поставщик", label="Тип Юр. лица")
        if status is not None:
            m.radio(status, label="Статус")
        m.select(option_text=region, label="Регион")

    with allure.step(f"Характеристика товаров: Отрасль = Industry-{code}"):
        m.click_button("Характеристика товаров")
        m.select(f"Industry-{code}", label="Отрасль")

    with allure.step("Сохранить"):
        # Saqlangach redirect barqaror emas (seansdagi keyingi create-savelarda
        # ilova dashboard'ga qaytarib yuboradi) — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        flow_navigate(page, tab="Модератор", name="Поставщики")
        m.expect_heading("Поставщики")
        m.search(name)
        if status in (None, "Активный"):
            m.grid_row(name)
        else:
            m.show_all()
            m.grid_row(name, status)

    return {"name": name, "tin": str(tin), "form": form, "region": region}


@allure.epic("Модератор")
@allure.feature("Поставщики")
@allure.story("Создание поставщика")
@allure.title("Yangi Поставщик (Юр. лицо) yaratish")
def test_supplier(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_supplier(page, code)


#---------------------------------------------------------------------------------------------------


# Supplier testlari uchun ma'lumotnomalar seansda BIR MARTA yaratiladi —
# testlar muhitda oldindan bor narsaga tayanmaydi (boshqa URL/muhitda ham
# yiqilmaydi). code session-scoped bo'lgani uchun oddiy set yetadi.
_refs_created = set()


def ensure_refs(page: Page, code) -> None:
    """Supplier testlari uchun kerakli ma'lumotnomalarni — Region-{code},
    MCHJ-{code}, Industry-{code}, Category-{code} — seansda BIR MARTA yaratadi;
    keyingi chaqiruvlar no-op.

    DIQQAT: tests/test_setup/test_all.py zanjiri ham xuddi shu nomlarni
    yaratadi — bitta seansda ikkalasini aralashtirib ishlatmang (dublikat
    nomlar paydo bo'ladi)."""
    if code in _refs_created:
        return
    with allure.step(f"Ma'lumotnomalar (seansda bir marta): Region/MCHJ/Industry/Category-{code}"):
        run_region(page, code)
        run_form_of_ownership(page, code)
        run_industry(page, code)
        run_category(page, code)
    _refs_created.add(code)


# CRUD testlari (full/edit/view/delete/status/duplicate) ko'chirilgan:
# tests/test_regression/test_supplier.py — bu yerda faqat basic create qoladi.
