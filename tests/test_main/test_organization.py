"""Организации (Модератор → Организации, biruni filial_list) — CRUD testlari.

Codegen'da yozilgan testlar BasePage uslubiga o'tkazildi (2026-07-20):
hardcoded login o'rniga authorization(), dinamik ng.formN / #cdk-drop-list-N
selektorlar o'rniga label orqali BasePage, hardcoded nom o'rniga unikal
f"org-...-{code}".

Biruni farqlar (MCP 2026-07-15): komponentlar smtid EMAS oddiy id
(filial-state, filial-timezone) — maydonlar faqat LABEL orqali topiladi;
"Часовой пояс" placeholder "select_timezone" (Подбор fallback ishlaydi);
view bo'limlari LINK emas BUTTON. 2026-07-15 da create/edit formada
"Сохранить" tugmasi YO'Q edi (xfail); 2026-07-19 codegen yozuvida tugma
QAYTGAN — testlar oddiy (xfail'siz) yozildi.
"""
import time

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_organization(page: Page, code, name=None) -> dict:
    """Yangi Организация yaratadi. ``name`` berilmasa org-{code}.
    Yaratilgan qiymatlarni qaytaradi."""
    m = BasePage(page)
    if name is None:
        name = f"org-{code}"
    # Порядковый номер maydoni maksimal 6 belgi qabul qiladi ("N/6" hisoblagich,
    # ortiqcha belgilar jim kesiladi) — zanjir code'i 7 xonali bo'lishi mumkin
    order_no = str(code)[-6:]

    with allure.step("Навигация: Модератор → Организации"):
        flow_navigate(page, tab="Модератор", name="Организации")
        m.expect_heading("Организации")

    with allure.step("Создать: yangi Организация formasi ochish"):
        m.open_create()
        m.expect_heading("Организация (создание)")

    with allure.step(f"Форма: Название = {name}, Часовой пояс = Ташкент, Порядковый номер = {order_no}"):
        m.input(label="Название", value=name)
        m.select("(+05:00) Ташкент", label="Часовой пояс")
        m.input(label="Порядковый номер", value=order_no)

    with allure.step("Сохранить va ro'yxatda tekshirish"):
        # Saqlangach redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Организации")
        m.expect_heading("Организации")
        m.search(name)
        m.grid_row(name)

    return {"name": name, "order_no": order_no}


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.story("Создание организации")
@allure.title("Yangi Организация yaratish")
def test_organization_create(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_organization(page, code)


# ---------------------------------------------------------------------------------------------------


def run_organization_minimal(page: Page, code) -> None:
    """Faqat majburiy maydonlar (Название + Порядковый номер) bilan yaratish —
    Часовой пояс tanlanmaydi."""
    m = BasePage(page)
    name = f"org-min-{code}"

    with allure.step("Навигация: Модератор → Организации"):
        flow_navigate(page, tab="Модератор", name="Организации")
        m.expect_heading("Организации")

    with allure.step("Создать: yangi Организация formasi ochish"):
        m.open_create()
        m.expect_heading("Организация (создание)")

    with allure.step(f"Форма (minimal): Название = {name}, Порядковый номер = {str(code)[-6:]}"):
        m.input(label="Название", value=name)
        # Порядковый номер maksimal 6 belgi ("N/6" hisoblagich)
        m.input(label="Порядковый номер", value=str(code)[-6:])

    with allure.step("Сохранить va ro'yxatda tekshirish"):
        m.save()
        flow_navigate(page, tab="Модератор", name="Организации")
        m.expect_heading("Организации")
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.story("Создание организации — минимальные поля")
@allure.title("Организацияни minimal maydonlar bilan yaratish")
def test_organization_minimal(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_organization_minimal(page, code)


# ---------------------------------------------------------------------------------------------------


def run_organization_view(page: Page, code) -> None:
    """Yangi организация yaratib, Просмотреть formasini ochadi va view
    bo'limlarini (BUTTON: Пользователи, История пользователя, Системные
    ошибки) aylanib chiqadi."""
    m = BasePage(page)
    name = f"org-view-{code}"

    run_organization(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Просмотреть formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Просмотреть")
        m.expect_heading("Организация (просмотр)")

    with allure.step("View bo'limlari: Пользователи → История пользователя → Системные ошибки"):
        m.click_button("Пользователи")
        m.click_button("История пользователя")
        m.click_button("Системные ошибки")

    with allure.step("Ro'yxatga qaytish"):
        # "Go back" tugmasi view bo'limlari almashganda sarlavhadan YO'QOLADI
        # (Системные ошибки bo'limida yo'q edi, 2026-07-20) — unga tayanmay
        # navbar orqali qaytamiz
        flow_navigate(page, tab="Модератор", name="Организации")
        m.expect_heading("Организации")


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.story("Просмотр организации")
@allure.title("Организация Просмотр formasi va bo'limlari ochilishi")
def test_organization_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_organization_view(page, code)


# ---------------------------------------------------------------------------------------------------


def run_organization_edit(page: Page, code) -> None:
    """Yangi организация yaratib, Изменить orqali nomini o'zgartiradi va
    o'zgarish ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"org-edit-{code}"
    new_name = f"org-upd-{code}"

    run_organization(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Организация (изменение)")

    with allure.step(f"Tahrirlash: nom {old_name} → {new_name}"):
        m.input(label="Название", value=new_name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save()
        flow_navigate(page, tab="Модератор", name="Организации")
        m.expect_heading("Организации")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        expect(page.locator(".smt-data-row").filter(has_text=old_name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.story("Редактирование организации")
@allure.title("Организацияни tahrirlash va o'zgarishni tekshirish")
def test_organization_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_organization_edit(page, code)


# ---------------------------------------------------------------------------------------------------


def run_organization_status(page: Page, code) -> None:
    """Status ikki yo'nalishda tekshiriladi — Изменить formasidagi Статус
    switch orqali (codegen'dagi ikkala status testi birlashtirilgan):

    1) Aktiv организация Неактивный qilinadi — default ro'yxatdan yo'qoladi,
       "Показать все"da Неактивный badge bilan ko'rinadi.
    2) Qayta Активный qilinadi — ro'yxatda Активный badge bilan ko'rinadi.

    Grid badge tili barqaror emas (ruscha/inglizcha almashib turadi) —
    BasePage _STATUS_SYNONYMS ikkala tilni ham qabul qiladi."""
    m = BasePage(page)
    name = f"org-stat-{code}"

    run_organization(page, code, name=name)

    with allure.step(f"1) '{name}' ni Изменить orqali Неактивный qilish"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.expect_heading("Организация (изменение)")
        m.checkbox(label="Статус", checked=False)
        m.save()

    with allure.step("1) Default ro'yxatda ko'rinmasligini tekshirish"):
        flow_navigate(page, tab="Модератор", name="Организации")
        m.expect_heading("Организации")
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(0)

    with allure.step("1) Показать все filtrida Неактивный bo'lib ko'rinishi"):
        m.show_all()
        m.grid_row(name, "Неактивный")

    with allure.step(f"2) '{name}' ni qayta Активный qilish"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.expect_heading("Организация (изменение)")
        m.checkbox(label="Статус", checked=True)
        m.save()

    with allure.step("2) Ro'yxatda Активный bo'lib ko'rinishini tekshirish"):
        flow_navigate(page, tab="Модератор", name="Организации")
        m.expect_heading("Организации")
        m.search(name)
        m.grid_row(name, "Активный")


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.story("Статус организации")
@allure.title("Организация statusini Неактивный/Активный qilish va tekshirish")
def test_organization_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_organization_status(page, code)


# ---------------------------------------------------------------------------------------------------


def run_organization_delete(page: Page, code) -> None:
    """Yangi организация yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi."""
    m = BasePage(page)
    name = f"org-del-{code}"

    run_organization(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.story("Удаление организации")
@allure.title("Организацияни o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_organization_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_organization_delete(page, code)


# ---------------------------------------------------------------------------------------------------


def run_organization_duplicate(page: Page, code) -> None:
    """Bir xil Название bilan qayta yaratishga urinish xatolik berishini
    tekshiradi — server "dup_val_on_index" (md_filials) xato dialogini
    qaytaradi (codegen 2026-07-19)."""
    m = BasePage(page)
    name = f"org-dup-{code}"

    run_organization(page, code, name=name)

    with allure.step(f"Xuddi shu nom '{name}' bilan qayta yaratishga urinish"):
        m.open_create()
        m.expect_heading("Организация (создание)")
        m.input(label="Название", value=name)
        # Порядковый номер maksimal 6 belgi ("N/6" hisoblagich)
        m.input(label="Порядковый номер", value=str(code)[-6:])
        m.click_button("Сохранить")

    with allure.step("Ошибка dialogi chiqishini tekshirish (dup_val_on_index)"):
        dialog = page.locator(".cdk-overlay-container")
        expect(dialog).to_contain_text("dup_val_on_index")

    with allure.step("Dialogni yopish — ochiq dialog navbar'ni to'sib qo'yadi"):
        dialog.get_by_role("button", name="Закрыть").first.click()
        m.expect_heading("Организация (создание)")

    with allure.step(f"Ro'yxatda '{name}' faqat BITTA ekanini tekshirish"):
        flow_navigate(page, tab="Модератор", name="Организации")
        m.expect_heading("Организации")
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(1)


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.story("Дубликат организации")
@allure.title("Bir xil nom bilan Организация qayta yaratishda xatolik chiqishi")
def test_organization_duplicate(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_organization_duplicate(page, code)


# ---------------------------------------------------------------------------------------------------


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.story("Полный CRUD цикл")
@allure.title("Организация: barcha CRUD testlari — bitta seansda zanjir")
def test_organization_all(page: Page, code) -> None:
        """Barcha Организация testlarini bitta login bilan ketma-ket ishga
        tushiradi (test_client_all / test_valyuta_all patterni). Har run o'z
        unikal nomlari bilan ishlaydi (org-*, org-min-*, ...)."""
        # Bir sessiyada individual testlar bilan nom to'qnashmasligi uchun zanjir
        # o'z code'i bilan ishlaydi
        code = str(int(time.time()))[-7:]
        with allure.step("Tizimga kirish"):
            authorization(page)

        with allure.step("1. Создание"):
            run_organization(page, code)

        with allure.step("2. Создание — minimal maydonlar"):
            run_organization_minimal(page, code)

        with allure.step("3. Просмотр"):
            run_organization_view(page, code)

        with allure.step("4. Редактирование"):
            run_organization_edit(page, code)

        with allure.step("5. Статус — Неактивный/Активный"):
            run_organization_status(page, code)

        with allure.step("6. Удаление"):
            run_organization_delete(page, code)

        with allure.step("7. Дубликат — nom bilan xatolik"):
            run_organization_duplicate(page, code)
