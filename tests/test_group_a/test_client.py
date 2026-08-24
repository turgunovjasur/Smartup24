import random

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_group_a.test_supplier import pick_region
from tests.test_setup.test_supplier import ensure_refs
from utils.base_page import BasePage


def run_client(page: Page, code, region=None, ownership=None, industry=None) -> None:
    """Group A: yangi Клиент yaratadi — supplier bilan bir xil region/otрасль
    bo'lgani uchun hamkorlikda 'Рекомендованные клиенты' ro'yxatiga tushadi.

    ``region``/``ownership``/``industry`` berilmasa bazadagi mavjud yozuvlar
    (birinchi Region-*, MCHJ-1, birinchi Industry-*) olinadi; 0 bazada
    test_all ularni avval o'zi yaratib, aniq nomlarini uzatadi."""
    m = BasePage(page)
    name = f"client-{code}"
    tin = random.randint(100000000, 999999999)
    if region is None:
        region = pick_region(page)

    with allure.step("Навигация: Модератор → Клиенты"):
        flow_navigate(page, tab="Модератор", name="Клиенты")
        m.expect_heading("Клиенты")

    with allure.step("Создать: yangi Клиент formasi ochish"):
        m.open_create()
        m.expect_heading("Юр. Лицо (Создания)")

    with allure.step(f"Форма asosiy: Юр. лица название = {name}, ИНН = {tin}"):
        m.input(label="Юр. лица название", value=name)
        m.input(label="Краткое название", value=name)
        m.input(label="ИНН", value=tin)

    with allure.step(f"Форма: Форма собственности = {ownership or 'MCHJ-1'}, Тип = Клиент, Регион = {region}"):
        m.select(ownership or "MCHJ-1", label="Форма собственности")
        m.radio("Клиент", label="Тип Юр. лица")
        m.select(region, label="Регион")

    with allure.step(f"Характеристика товаров: Отрасль = {industry or 'birinchi Industry-*'}"):
        m.click_button("Характеристика товаров")
        if industry:
            m.select(industry, label="Отрасль")
        else:
            # Muhitda barqaror nomli otрасль yo'q — birinchi Industry-* tanlanadi
            m.select("Industry-", label="Отрасль", exact=False)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Клиенты")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Group A")
@allure.story("Создание клиента")
@allure.title("Group A: yangi Клиент yaratish")
def test_client(page: Page, code) -> None:
    """Standalone: kerakli ma'lumotnomalarni (Region/MCHJ/Industry/Category) O'ZI
    yaratib, aniq nom bilan klient ochadi — istalgan TOZA serverda ishlaydi
    (pick_region/"MCHJ-1" fallback'lariga tayanmaydi). Alohida ``{code}gc`` kodi
    setup (``code``) va runner ({code}2/{code}3) nomlari bilan to'qnashmaydi."""
    with allure.step("Tizimga kirish"):
        authorization(page)
    code = f"{code}gc"
    with allure.step("Ma'lumotnomalar: Region/MCHJ/Industry/Category yaratish"):
        ensure_refs(page, code)
    run_client(
        page, code,
        region=f"Region-{code}", ownership=f"MCHJ-{code}", industry=f"Industry-{code}",
    )
