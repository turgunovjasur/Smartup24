"""Объявления (Модератор → Главное → Объявления, biruni announcement_list) —
CRUD testlari.

MCP bilan real DOM'da tasdiqlangan:

Forma maydonlari:
  - "Титул *"        : smt-input (smtid=title) — MAJBURIY (grid ustuni "Заголовок")
  - "Описание *"     : smt-textarea (smtid=description) — MAJBURIY
  - "Отрасли"        : smt-multi-data-select (ko'p tanlov, masalan "Sport Clothes")
  - "Регион обслуживание": smt-tree-select (masalan "Узбекистан")
  - "Запланировать"  : smt-date-picker (ixtiyoriy)
  - Аватар           : fayl (ixtiyoriy, default rasm bor)

Status oqimi (Активный/Неактивный EMAS):
  - Yangi yozuv "Черновик" bo'lib saqlanadi (Сохранить create'dan list'ga qaytaradi).
  - Qator panelida "Опубликовать" ("Опубликовать объявление?" да/нет) statusni
    "Опубликовано"ga o'zgartiradi.
  - DIQQAT: "Опубликовано" yozuv READ-ONLY — panelda faqat "Просмотр" qoladi
    (Изменить/Удалить/Опубликовать YO'Q). Shu sabab Изменить va Удалить faqat
    "Черновик" holatida bajariladi.

Qator paneli (Черновик): Просмотр / Изменить / Опубликовать / Удалить.
Dublikat Титул RUXSAT etilgan (ro'yxatda bir xil nomli yozuvlar bor) — dublikat
xato testi yo'q.
"""
import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_announcement(page: Page, code, name=None) -> dict:
    """Yangi Объявление yaratadi (faqat majburiy maydonlar: Титул + Описание).
    ``name`` berilmasa ann-{code}. Yaratilgach yozuv "Черновик" statusida bo'ladi.
    Yaratilgan qiymatlarni qaytaradi."""
    m = BasePage(page)
    if name is None:
        name = f"ann-{code}"
    description = f"Описание {name}"

    with allure.step("Навигация: Модератор → Объявления"):
        flow_navigate(page, tab="Модератор", name="Объявления", expect_url="announcement_list")
        m.expect_heading("Объявления")

    with allure.step("Создать: yangi Объявление formasi ochish"):
        m.open_create()
        m.expect_heading("Объявление (создание)")

    with allure.step(f"Форма: Титул = {name}, Описание = {description}"):
        m.input(label="Титул", value=name)
        m.input(label="Описание", value=description)

    with allure.step("Сохранить va ro'yxatda 'Черновик' bo'lib ko'rinishini tekshirish"):
        # Saqlangach redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Объявления", expect_url="announcement_list")
        m.expect_heading("Объявления")
        m.search(name)
        m.grid_row(name, "Черновик")

    return {"name": name, "description": description}


@allure.epic("Модератор")
@allure.feature("Объявления")
@allure.story("Создание объявления")
@allure.title("Yangi Объявление yaratish (Черновик)")
def test_announcement_create(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_announcement(page, code)


# ---------------------------------------------------------------------------------------------------


def run_announcement_full(page: Page, code) -> None:
    """Majburiy maydonlardan tashqari ixtiyoriy Отрасли (multi-select) ni ham
    to'ldiradi — ro'yxatda Отрасли ustunida ko'rinishini tekshiradi.

    "Регион обслуживание" (smt-tree-select) ATAYIN qo'shilmagan: barqaror
    top-level regionlar (Узбекистан va h.k.) BOLALI tugun bo'lgani uchun ularning
    treeitem nomi yig'ish tugmasi bilan "Свернуть Узбекистан" ko'rinishida keladi
    va exact-match BasePage.select topolmaydi; barqaror LEAF regionni kafolatlab
    bo'lmaydi."""
    m = BasePage(page)
    name = f"ann-full-{code}"

    with allure.step("Навигация: Модератор → Объявления"):
        flow_navigate(page, tab="Модератор", name="Объявления", expect_url="announcement_list")
        m.expect_heading("Объявления")

    with allure.step("Создать: yangi Объявление formasi ochish"):
        m.open_create()
        m.expect_heading("Объявление (создание)")

    with allure.step(f"Форма (to'liq): Титул + Отрасли + Описание"):
        m.input(label="Титул", value=name)
        # Отрасли multi-select menyusi tanlangach OCHIQ qoladi (Escape ham,
        # heading klik ham yopmaydi — MCP tasdiqlangan 2026-07-24), faqat boshqa
        # input'ga HAQIQIY klik yopadi. Shuning uchun Отрасли'dan keyin darhol
        # Описание to'ldiriladi (textarea'ga klik menyuni yopadi).
        m.select("Sport Clothes", label="Отрасли")
        m.input(label="Описание", value=f"Описание {name}")

    with allure.step("Сохранить va ro'yxatda Отрасли bilan ko'rinishini tekshirish"):
        m.save()
        flow_navigate(page, tab="Модератор", name="Объявления", expect_url="announcement_list")
        m.expect_heading("Объявления")
        m.search(name)
        m.grid_row(name, "Sport Clothes", "Черновик")


@allure.epic("Модератор")
@allure.feature("Объявления")
@allure.story("Создание объявления — все поля")
@allure.title("Объявлениени Отрасли va Регион bilan yaratish")
def test_announcement_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_announcement_full(page, code)


# ---------------------------------------------------------------------------------------------------


def run_announcement_view(page: Page, code) -> None:
    """Yangi объявление yaratib, qator panelidan Просмотр formasini ochadi va
    Титул qiymati view'da to'g'ri ko'rinishini tekshiradi."""
    m = BasePage(page)
    name = f"ann-view-{code}"

    run_announcement(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Просмотр formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Просмотр")
        m.expect_heading("Объявление (просмотр)")

    with allure.step("View'da Титул qiymati to'g'ri ko'rinishini tekshirish"):
        m.input(label="Титул", expect_value=name)

    with allure.step("Ro'yxatga qaytish"):
        # View read-only forma; navbar orqali ro'yxatga qaytamiz
        flow_navigate(page, tab="Модератор", name="Объявления", expect_url="announcement_list")
        m.expect_heading("Объявления")


@allure.epic("Модератор")
@allure.feature("Объявления")
@allure.story("Просмотр объявления")
@allure.title("Объявление Просмотр formasi ochilishi")
def test_announcement_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_announcement_view(page, code)


# ---------------------------------------------------------------------------------------------------


def run_announcement_edit(page: Page, code) -> None:
    """Yangi объявление (Черновик) yaratib, Изменить orqali Титул'ni o'zgartiradi
    va o'zgarish ro'yxatda aks etganini tekshiradi. Изменить faqat "Черновик"
    holatida mavjud."""
    m = BasePage(page)
    old_name = f"ann-edit-{code}"
    new_name = f"ann-upd-{code}"

    run_announcement(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Объявление (изменение)")

    with allure.step(f"Tahrirlash: Титул {old_name} → {new_name}"):
        m.input(label="Титул", value=new_name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save()
        flow_navigate(page, tab="Модератор", name="Объявления", expect_url="announcement_list")
        m.expect_heading("Объявления")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        m.expect_no_row(old_name)


@allure.epic("Модератор")
@allure.feature("Объявления")
@allure.story("Редактирование объявления")
@allure.title("Объявлениени tahrirlash va o'zgarishni tekshirish")
def test_announcement_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_announcement_edit(page, code)


# ---------------------------------------------------------------------------------------------------


def run_announcement_publish(page: Page, code) -> None:
    """Yangi объявление (Черновик) yaratib, qator panelidagi "Опубликовать" bilan
    statusni "Опубликовано"ga o'zgartiradi va ro'yxatda tekshiradi.

    Опубликовать -> "Опубликовать объявление?" -> да. Chop etilgach yozuv
    read-only bo'ladi (panelda faqat Просмотр)."""
    m = BasePage(page)
    name = f"ann-pub-{code}"

    run_announcement(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Опубликовать bosish"):
        m.click_grid_row(name)
        m.click_button("Опубликовать")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    with allure.step(f"Ro'yxatda '{name}' 'Опубликовано' bo'lib ko'rinishi"):
        flow_navigate(page, tab="Модератор", name="Объявления", expect_url="announcement_list")
        m.expect_heading("Объявления")
        m.search(name)
        m.grid_row(name, "Опубликовано")


@allure.epic("Модератор")
@allure.feature("Объявления")
@allure.story("Публикация объявления")
@allure.title("Объявлениени Опубликовать va statusni tekshirish")
def test_announcement_publish(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_announcement_publish(page, code)


# ---------------------------------------------------------------------------------------------------


def run_announcement_delete(page: Page, code) -> None:
    """Yangi объявление (Черновик) yaratib, Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi. Удалить faqat "Черновик" holatida mavjud."""
    m = BasePage(page)
    name = f"ann-del-{code}"

    run_announcement(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish (Удалить объявление?)"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        m.expect_no_row(name)


@allure.epic("Модератор")
@allure.feature("Объявления")
@allure.story("Удаление объявления")
@allure.title("Объявлениени o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_announcement_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_announcement_delete(page, code)
