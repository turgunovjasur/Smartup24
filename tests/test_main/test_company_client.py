"""Клиенты OAuth2 сервера для компании (Модератор → Главное, biruni
company_client_list) — CRUD testlari.

MCP bilan real DOM'da tasdiqlangan (2026-07-24, dev/sm24):

Forma maydonlari:
  - "Тип разрешения" : smt-radio-group (label[smt-radio], value C/A) —
    "Учетные данные клиента" (C, default) / "Код авторизации" (A). DIQQAT:
    "Код авторизации"ga o'tilsa forma maydonlari o'zgaradi (Название/Организация/
    Роли yo'qoladi) — shuning uchun grant-type DEFAULT (C) da qoldiriladi.
  - "Название *"     : smt-input — MAJBURIY
  - "Организация"    : smt-data-select — MAJBURIY (yulduzchasiz bo'lsa ham,
    tanlanmasa Сохранить jim ishlamaydi; testda barqaror seed org "FMCG")
  - "Роли"           : smt-multi-data-select — ixtiyoriy (barqaror rol nomi
    kafolatlanmagani uchun test'ga qo'shilmagan)
  - "Доступы"        : IKKI mustaqil checkbox (Чтение / Запись) — nostandart
    span[role=checkbox] (smt-checkbox EMAS, BasePage.checkbox topolmaydi),
    label matnini bosib yoqiladi. KAMIDA BITTA majburiy ("Хотя бы один доступ
    должен быть выбран!"). Grid'da Чтение→"Read", Запись→"Write", ikkalasi→"Read/Write".

Grid ustunlari: Название / Ид клиента / Client Secret / Тип разрешения / Доступы /
Дата создания. Ид клиента va Client Secret avtomatik generatsiya qilinadi. Статус YO'Q.

Heading'lar: list "Клиенты OAuth2 сервера для компании", create "...(создание)".
DIQQAT: EDIT heading TARJIMA QILINMAGAN — xom route "/biruni/kauth/company_client+edit"
ko'rsatadi, shuning uchun edit'da expect_heading ISHLATILMAYDI; forma yuklangani
Название maydonining joriy qiymati orqali tekshiriladi.

Qator paneli: Изменить / Удалить (Просмотр va status YO'Q). Удалить NATIVE brauzer
confirm() dialogini ochadi ("Удалить $1 клиента?") — cdk-overlay да/нет EMAS;
`page.once("dialog", accept)` bilan qabul qilinadi (conftest'da handler yo'q, default
rad etiladi). Dublikat Название testi yo'q (xatti-harakat tekshirilmagan).
"""
import time

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage

MENU = "Клиенты OAuth2 сервера для компании"
# Barqaror seed organizatsiya (org-* lar test'da yaratiladi/o'chiriladi, FMCG doim bor)
ORG = "FMCG"


def _set_access(page: Page, label: str) -> None:
    """Доступы checkbox'ini (Чтение/Запись) yoqadi. Ular nostandart
    span[role=checkbox] (smt-checkbox EMAS) — BasePage.checkbox topolmaydi,
    shuning uchun ko'rinadigan label matni bosiladi (yangi formada boshlang'ich
    holat o'chiq, bir marta bosish yoqadi). MCP tasdiqlangan 2026-07-24."""
    page.get_by_text(label, exact=True).click()


def run_company_client(page: Page, code, name=None) -> dict:
    """Yangi OAuth2 mijoz yaratadi (majburiy: Название + Организация + Доступы).
    Тип разрешения default "Учетные данные клиента" (Client credentials) da qoladi.
    ``name`` berilmasa oauth-{code}."""
    m = BasePage(page)
    if name is None:
        name = f"oauth-{code}"

    with allure.step(f"Навигация: Модератор → {MENU}"):
        flow_navigate(page, tab="Модератор", name=MENU, expect_url="company_client_list")
        m.expect_heading(MENU)

    with allure.step("Создать: yangi mijoz formasi ochish"):
        m.open_create()
        m.expect_heading(f"{MENU} (создание)")

    with allure.step(f"Форма: Название = {name}, Организация = {ORG}, Доступы = Чтение"):
        m.input(label="Название", value=name)
        m.select(ORG, label="Организация")
        _set_access(page, "Чтение")

    with allure.step("Сохранить va ro'yxatda tekshirish (Client credentials, Read)"):
        m.save()
        flow_navigate(page, tab="Модератор", name=MENU, expect_url="company_client_list")
        m.expect_heading(MENU)
        m.search(name)
        m.grid_row(name, "Client credentials", "Read")

    return {"name": name}


@allure.epic("Модератор")
@allure.feature("Клиенты OAuth2")
@allure.story("Создание клиента")
@allure.title("Yangi OAuth2 mijoz yaratish")
def test_company_client_create(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_company_client(page, code)


# ---------------------------------------------------------------------------------------------------


def run_company_client_full(page: Page, code) -> None:
    """Ikkala Доступы (Чтение + Запись) bilan yaratadi — ro'yxatda "Read/Write"
    bo'lib ko'rinishini tekshiradi."""
    m = BasePage(page)
    name = f"oauth-full-{code}"

    with allure.step(f"Навигация: Модератор → {MENU}"):
        flow_navigate(page, tab="Модератор", name=MENU, expect_url="company_client_list")
        m.expect_heading(MENU)

    with allure.step("Создать: yangi mijoz formasi ochish"):
        m.open_create()
        m.expect_heading(f"{MENU} (создание)")

    with allure.step(f"Форма: Название = {name}, Организация = {ORG}, Доступы = Чтение + Запись"):
        m.input(label="Название", value=name)
        m.select(ORG, label="Организация")
        _set_access(page, "Чтение")
        _set_access(page, "Запись")

    with allure.step("Сохранить va ro'yxatda 'Read/Write' bo'lib ko'rinishi"):
        m.save()
        flow_navigate(page, tab="Модератор", name=MENU, expect_url="company_client_list")
        m.expect_heading(MENU)
        m.search(name)
        m.grid_row(name, "Client credentials", "Read/Write")


@allure.epic("Модератор")
@allure.feature("Клиенты OAuth2")
@allure.story("Создание клиента — оба доступа")
@allure.title("OAuth2 mijozni Чтение+Запись bilan yaratish")
def test_company_client_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_company_client_full(page, code)


# ---------------------------------------------------------------------------------------------------


def run_company_client_edit(page: Page, code) -> None:
    """Yangi mijoz yaratib, Изменить orqali Название'ni o'zgartiradi va o'zgarish
    ro'yxatda aks etganini tekshiradi.

    Edit heading tarjimasiz (xom route) — forma yuklangani Название maydonining
    joriy qiymati orqali tasdiqlanadi (expect_heading ishlatilmaydi)."""
    m = BasePage(page)
    old_name = f"oauth-edit-{code}"
    new_name = f"oauth-upd-{code}"

    run_company_client(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        # Edit heading tarjimasiz — forma yuklanganini Название qiymatidan bilamiz
        m.input(label="Название", expect_value=old_name)

    with allure.step(f"Tahrirlash: Название {old_name} → {new_name}"):
        m.input(label="Название", value=new_name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save()
        flow_navigate(page, tab="Модератор", name=MENU, expect_url="company_client_list")
        m.expect_heading(MENU)

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        expect(page.locator(".smt-data-row").filter(has_text=old_name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Клиенты OAuth2")
@allure.story("Редактирование клиента")
@allure.title("OAuth2 mijozni tahrirlash va o'zgarishni tekshirish")
def test_company_client_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_company_client_edit(page, code)


# ---------------------------------------------------------------------------------------------------


def run_company_client_delete(page: Page, code) -> None:
    """Yangi mijoz yaratib, Удалить orqali o'chiradi. Удалить NATIVE brauzer
    confirm() dialogini ochadi — `page.once("dialog", accept)` bilan qabul
    qilinadi (cdk-overlay да/нет EMAS)."""
    m = BasePage(page)
    name = f"oauth-del-{code}"

    run_company_client(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish (native confirm)"):
        m.click_grid_row(name)
        # Удалить window.confirm() ochadi; handler tayinlanmasa Playwright uni
        # RAD etadi (o'chirilmaydi) — klikdan OLDIN qabul qiluvchi handler qo'yamiz.
        page.once("dialog", lambda dialog: dialog.accept())
        m.click_button("Удалить")
        m.wait_for_loader()

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Клиенты OAuth2")
@allure.story("Удаление клиента")
@allure.title("OAuth2 mijozni o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_company_client_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_company_client_delete(page, code)


# ---------------------------------------------------------------------------------------------------


@allure.epic("Модератор")
@allure.feature("Клиенты OAuth2")
@allure.story("Полный CRUD цикл")
@allure.title("Клиенты OAuth2: barcha CRUD testlari — bitta seansda zanjir")
def test_company_client_all(page: Page, code) -> None:
    """Barcha OAuth2 mijoz testlarini bitta login bilan ketma-ket ishga tushiradi
    (test_announcement_all patterni). Har run o'z unikal nomlari bilan ishlaydi."""
    code = str(int(time.time()))[-7:]
    with allure.step("Tizimga kirish"):
        authorization(page)

    with allure.step("1. Создание"):
        run_company_client(page, code)

    with allure.step("2. Создание — оба доступа (Read/Write)"):
        run_company_client_full(page, code)

    with allure.step("3. Редактирование"):
        run_company_client_edit(page, code)

    with allure.step("4. Удаление"):
        run_company_client_delete(page, code)
