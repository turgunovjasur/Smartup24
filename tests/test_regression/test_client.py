"""Клиент — to'liq CRUD regression testlari.

Basic create (run_client/test_client) tests/test_setup/test_client.py da,
ma'lumotnomalar tayyorlovi (ensure_refs) tests/test_setup/test_supplier.py da
turadi — bu yerda faqat CRUD ssenariylari: full create, edit, view, delete,
status, duplicate. Kod test_setup dan ko'chirilgan ishlaydigan nusxa
(MCP tasdiqlangan 2026-07-05).
"""
import random

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_setup.test_client import run_client
from tests.test_setup.test_supplier import ensure_refs
from utils.base_page import BasePage


def run_client_basic(page: Page, code, name=None, status=None) -> dict:
    """CRUD testlari uchun tayyorlov: kerakli ma'lumotnomalarni (ensure_refs)
    yaratib, ``run_client`` ni chaqiradi — alohida seansda ham ishlaydi."""
    ensure_refs(page, code)
    return run_client(page, code, name=name, status=status)


def run_client_full(page: Page, code) -> None:
    """Клиент formasining BARCHA to'ldiriladigan maydonlari bilan yaratish —
    Основное (Адрес va Характеристика товаров tablari bilan), Реквизиты va
    Расчётные счёта bo'limlari (forma supplier bilan bir xil person modul).
    Readonly maydonlar to'ldirilmaydi: Время создания, GPS координаты."""
    ensure_refs(page, code)
    m = BasePage(page)
    name = f"client-full-{code}"
    tin = random.randint(100000000, 999999999)
    gln = random.randint(10**12, 10**13 - 1)
    phone = f"+998(99)-{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}"
    region = f"Region-{code}"
    form = f"MCHJ-{code}"

    with allure.step("Навигация: Модератор → Клиенты"):
        flow_navigate(page, tab="Модератор", name="Клиенты")
        m.expect_heading("Клиенты")

    with allure.step("Создать: yangi Клиент formasi ochish"):
        # OAuth2 leak'ini tozalash (Юр.Лицо tab/label buzilmasin) — reload
        page.reload()
        m.settle()
        m.open_create()
        m.expect_heading("Юр. Лицо (Создания)")

    with allure.step(f"Основное: matn maydonlari ({name})"):
        # Юр.Лицо formasida label'lar ikkinchi create formada aralashadi — smtid orqali
        m.input(smtid="name", value=name)
        m.input(smtid="code", value=f"cl-code-{code}")
        m.input(smtid="tin", value=tin)
        m.input(smtid="note", value=f"Avto-test izohi {code}")
        m.input(smtid="short_name", value=name)
        m.input(smtid="gln", value=gln)
        m.input(smtid="working_hours", value="Пн-Пт 09:00-18:00")

    with allure.step(f"Основное: Форма собственности = {form}, Статус = Активный, Тип = Клиент"):
        m.select(form, label="Форма собственности")
        m.radio("Активный", label="Статус")
        m.radio("Клиент", label="Тип Юр. лица")

    with allure.step(f"Адрес tab: Регион = {region}, Номер телефона = {phone}, Адрес"):
        m.select(region, label="Регион")
        m.input(label="Номер телефона", value=phone)
        m.input(smtid="address", value=f"Toshkent sh., Avto-test ko'chasi {code}")

    with allure.step(f"Характеристика товаров tab: Отрасль = Industry-{code}"):
        m.click_button("Характеристика товаров")
        m.select(f"Industry-{code}", label="Отрасль")

    with allure.step("Реквизиты: barcha rekvizit maydonlari"):
        m.click_button("Реквизиты")
        m.input(label="Телефон", value="+998712005050")
        m.input(label="Дата регистрации", value="01.01.2020")
        m.input(label="Регистрирующий орган", value="Минюст")
        m.input(label="Состояние", value="Активное")
        m.input(label="Тип налогоплательщика", value="Юридическое лицо")
        m.input(label="Форма собственности КФС", value="144")
        m.input(label="СОАТО", value="1726273")
        m.input(label="СООГУ", value="07794")
        m.input(label="Категория предприятия", value="Малое предприятие")
        m.input(label="Размер уставного фонда", value="100000000")
        m.input(label="ОКПО", value=f"{random.randint(10000000, 99999999)}")
        m.input(label="ОКЭД", value="46901")
        m.input(label="Налоговый режим", value="Общеустановленный")
        m.input(label="Номер свидетельства НДС", value=f"НДС-{code}")
        m.input(label="Статус свидетельства НДС", value="Активный")
        m.input(label="Руководитель", value=f"Director-{code}")

    with allure.step("Расчётные счёта: hisob-raqam qatori"):
        m.click_button("Расчётные счёта")
        account_row = page.locator("#main-content .smt-data-row").first
        cells = account_row.locator("input[type=text]")
        cells.nth(0).fill(f"Account-{code}")
        cells.nth(1).fill("20208000900000000003")
        cells.nth(2).fill("Ipoteka Bank")
        cells.nth(3).fill("00425")
        m.checkbox(locator=account_row.locator("smt-switch").first, checked=True)

    with allure.step("Сохранить"):
        # Redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        flow_navigate(page, tab="Модератор", name="Клиенты")
        m.expect_heading("Клиенты")
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Клиенты")
@allure.story("Создание клиента — все поля")
@allure.title("Клиентни BARCHA maydonlar bilan yaratish")
def test_client_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_client_full(page, code)


#---------------------------------------------------------------------------------------------------


def run_client_edit(page: Page, code) -> None:
    """Yangi klient yaratib, Изменить orqali tahrirlaydi va o'zgarish
    ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"client-edit-{code}"
    new_name = f"client-upd-{code}"

    run_client_basic(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Юр. Лицо (Редактирования)")

    with allure.step(f"Tahrirlash: nom {old_name} → {new_name}, izoh yangilash"):
        # Edit forma ham leak'dan buziladi (Примечания→Примечание) — smtid orqali
        m.input(smtid="name", value=new_name)
        m.input(smtid="short_name", value=new_name)
        m.input(smtid="note", value=f"Tahrirlangan {code}")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        # Edit'dan keyin ham redirect barqaror emas (dashboard'ga tushadi) —
        # ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Клиенты")
        m.expect_heading("Клиенты")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        expect(page.locator(".smt-data-row").filter(has_text=old_name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Клиенты")
@allure.story("Редактирование клиента")
@allure.title("Клиентни tahrirlash va o'zgarishni tekshirish")
def test_client_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_client_edit(page, code)


#---------------------------------------------------------------------------------------------------


def run_client_view(page: Page, code) -> None:
    """Yangi klient yaratib, Просмотреть formasida qiymatlar to'g'ri
    ko'rsatilishini tekshiradi (heading "Клиент (Просмотр)", readonly
    cv_main_* inputlar; MCP tasdiqlangan 2026-07-05)."""
    m = BasePage(page)
    name = f"client-view-{code}"

    data = run_client_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Просмотр formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Просмотреть")
        m.expect_heading("Клиент (Просмотр)")

    with allure.step("Qiymatlar: Название, ИНН, Статус, Краткое название"):
        m.input(smtid="cv_main_name", expect_value=data["name"])
        m.input(smtid="cv_main_tin", expect_value=data["tin"])
        m.input(smtid="cv_main_status", expect_value="Активный")
        m.input(smtid="cv_main_short_name", expect_value=data["name"])

    with allure.step(f"Адрес: Регион ko'rsatilgan"):
        expect(page.locator("#main-content")).to_contain_text(f"Region-{code}")


@allure.epic("Модератор")
@allure.feature("Клиенты")
@allure.story("Просмотр клиента")
@allure.title("Клиент ma'lumotlari Просмотр formasida to'g'ri ko'rinishi")
def test_client_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_client_view(page, code)


#---------------------------------------------------------------------------------------------------


def run_client_delete(page: Page, code) -> None:
    """Yangi klient yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi ("Удалить" klient rolini o'chiradi; "Удалить с юр.
    лицом" ishlatilmaydi)."""
    m = BasePage(page)
    name = f"client-del-{code}"

    run_client_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Клиенты")
@allure.story("Удаление клиента")
@allure.title("Клиентни o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_client_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_client_delete(page, code)


#---------------------------------------------------------------------------------------------------


def run_client_status(page: Page, code) -> None:
    """Status ikki yo'nalishda tekshiriladi ("Изменить статус" menyusi —
    supplier'dagi kabi, variantlar Пассивный/Приостановлено):

    1) Aktiv yaratilgan klient Пассивный qilinadi — default ro'yxatdan
       yo'qoladi, "Показать все"da "Пассивный" ko'rinadi.
    2) Пассивный holatda yaratilgan klient Активный qilinadi."""
    m = BasePage(page)
    active_name = f"client-stat-a-{code}"
    passive_name = f"client-stat-p-{code}"

    run_client_basic(page, code, name=active_name)

    with allure.step(f"1) '{active_name}' ni Пассивный qilish"):
        m.click_grid_row(active_name)
        m.change_status("Пассивный")

    with allure.step("1) Default ro'yxatda ko'rinmasligini tekshirish"):
        m.search(active_name)
        expect(page.locator(".smt-data-row").filter(has_text=active_name)).to_have_count(0)

    with allure.step("1) Показать все filtrida 'Пассивный' bo'lib ko'rinishi"):
        m.show_all()
        m.grid_row(active_name, "Пассивный")

    run_client_basic(page, code, name=passive_name, status="Пассивный")

    with allure.step(f"2) Passiv yaratilgan '{passive_name}' ni Активный qilish"):
        m.click_grid_row(passive_name)
        m.change_status("Активный")

    with allure.step("2) Ro'yxatda 'Активный' bo'lib ko'rinishini tekshirish"):
        m.search(passive_name)
        m.grid_row(passive_name, "Активный")


@allure.epic("Модератор")
@allure.feature("Клиенты")
@allure.story("Статус клиента")
@allure.title("Клиент statusini Пассивный/Активный qilish va tekshirish")
def test_client_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_client_status(page, code)


#---------------------------------------------------------------------------------------------------


def run_client_duplicate(page: Page, code) -> None:
    """Bir xil nom va ИНН bilan qayta yaratishga urinish xatolik berishini
    tekshiradi (person modulda ИНН bo'yicha unikal indeks — "Ошибка" dialogi,
    matnida "dup_val_on_index" va tin)."""
    m = BasePage(page)
    name = f"client-dup-{code}"

    data = run_client_basic(page, code, name=name)

    with allure.step(f"Xuddi shu nom '{name}' va ИНН {data['tin']} bilan qayta yaratish"):
        flow_navigate(page, tab="Модератор", name="Клиенты")
        m.expect_heading("Клиенты")
        m.open_create()
        m.expect_heading("Юр. Лицо (Создания)")
        m.input(label="Юр. лица название", value=name)
        m.input(label="Краткое название", value=name)
        m.input(label="ИНН", value=data["tin"])
        m.select(data["form"], label="Форма собственности")
        m.radio("Клиент", label="Тип Юр. лица")
        m.click_button("Сохранить")

    with allure.step("Ошибка dialogi chiqishini tekshirish (ИНН dublikat)"):
        dialog = page.locator(".cdk-overlay-container")
        expect(dialog).to_contain_text("Ошибка")
        expect(dialog).to_contain_text("dup_val_on_index")
        expect(dialog).to_contain_text(data["tin"])

    with allure.step("Dialogni yopish — forma ochiq qoladi, yozuv saqlanmagan"):
        dialog.get_by_role("button", name="Закрыть").first.click()
        m.expect_heading("Юр. Лицо (Создания)")

    with allure.step(f"Ro'yxatda '{name}' faqat BITTA ekanini tekshirish"):
        flow_navigate(page, tab="Модератор", name="Клиенты")
        m.expect_heading("Клиенты")
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(1)


@allure.epic("Модератор")
@allure.feature("Клиенты")
@allure.story("Дубликат клиента")
@allure.title("Bir xil nom/ИНН bilan Клиент qayta yaratishда xatolik chiqishi")
def test_client_duplicate(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_client_duplicate(page, code)
