import random
import re

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_setup.test_supplier import ensure_refs
from utils.base_page import BasePage


def pick_region(page: Page) -> str:
    """Регионы ro'yxatidagi birinchi Region-* nomini qaytaradi.

    Muhitda barqaror nomli region yo'q (hammasi test yaratgan Region-XXXX),
    shuning uchun nom qattiq kodlanmaydi — ro'yxat alifbo tartibida bo'lgani
    uchun supplier va client bir xil regionni oladi (hamkorlik tavsiyasi
    'Рекомендованные клиенты' region/otрасль mosligiga tayanadi)."""
    m = BasePage(page)
    flow_navigate(page, tab="Модератор", name="Регионы")
    m.expect_heading("Регионы")
    m.search("Region-")
    row = m.grid_row("Region-")
    return re.search(r"Region-\S+", row.inner_text()).group(0)


def run_supplier(page: Page, code, region=None, ownership=None, industry=None) -> None:
    """Group A: yangi Поставщик yaratadi — keyingi group A testlari shunga tayanadi.

    ``region``/``ownership``/``industry`` berilmasa bazadagi mavjud yozuvlar
    (birinchi Region-*, MCHJ-1, birinchi Industry-*) olinadi; 0 bazada
    test_all ularni avval o'zi yaratib, aniq nomlarini uzatadi."""
    m = BasePage(page)
    name = f"supplier-{code}"
    tin = random.randint(100000000, 999999999)
    if region is None:
        region = pick_region(page)

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

    with allure.step(f"Форма: Форма собственности = {ownership or 'MCHJ-1'}, Тип = Поставщик, Регион = {region}"):
        m.select(ownership or "MCHJ-1", label="Форма собственности")
        m.radio("Поставщик", label="Тип Юр. лица")
        m.select(region, label="Регион")

    with allure.step(f"Характеристика товаров: Отрасль = {industry or 'birinchi Industry-*'}"):
        m.click_button("Характеристика товаров")
        if industry:
            m.select(industry, label="Отрасль")
        else:
            # Muhitda barqaror nomli otрасль yo'q — birinchi Industry-* tanlanadi
            m.select("Industry-", label="Отрасль", exact=False)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Поставщики")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Group A")
@allure.story("Создание поставщика")
@allure.title("Group A: yangi Поставщик yaratish")
def test_supplier(page: Page, code) -> None:
    """Standalone: kerakli ma'lumotnomalarni (Region/MCHJ/Industry/Category) O'ZI
    yaratib, aniq nom bilan supplier ochadi — istalgan TOZA serverda ishlaydi
    (pick_region/"MCHJ-1" fallback'lariga tayanmaydi). Alohida ``{code}gs`` kodi
    setup (``code``) va runner ({code}2/{code}3) nomlari bilan to'qnashmaydi."""
    with allure.step("Tizimga kirish"):
        authorization(page)
    code = f"{code}gs"
    with allure.step("Ma'lumotnomalar: Region/MCHJ/Industry/Category yaratish"):
        ensure_refs(page, code)
    run_supplier(
        page, code,
        region=f"Region-{code}", ownership=f"MCHJ-{code}", industry=f"Industry-{code}",
    )


#---------------------------------------------------------------------------------------------------
