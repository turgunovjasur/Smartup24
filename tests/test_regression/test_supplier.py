"""Поставщик — to'liq CRUD regression testlari.

Basic create (run_supplier/test_supplier) va ma'lumotnomalar tayyorlovi
(ensure_refs) tests/test_setup/test_supplier.py da turadi — bu yerda faqat
CRUD ssenariylari: full create, edit, view, delete, status, duplicate.
Kod test_setup dan ko'chirilgan ishlaydigan nusxa (MCP tasdiqlangan 2026-07-05).
"""
import random

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_setup.test_supplier import ensure_refs, run_supplier
from utils.base_page import BasePage


def run_supplier_basic(page: Page, code, name=None, status=None) -> dict:
    """CRUD testlari (edit/view/delete/status/duplicate) uchun tayyorlov:
    kerakli ma'lumotnomalarni (``ensure_refs`` — Region-{code}, MCHJ-{code},
    Industry-{code}, Category-{code}) yaratib, ``run_supplier`` ni chaqiradi —
    alohida seansda ham ishlaydi (muhitda oldindan hech narsa bo'lishi shart
    emas). ``name`` berilmasa supplier-basic-{code} — setup_supplier'ning
    "Supplier-{code}" nomi bilan to'qnashmaslik uchun alohida.

    ``status``: "Пассивный"/"Приостановлено" berilsa shu statusda yaratiladi;
    run_supplier passiv yozuvni "Показать все" bilan tekshiradi. Yaratilgan
    qiymatlarni ({name, tin, form, region}) qaytaradi va ro'yxatni ``name``
    bo'yicha qidirilgan holda qoldiradi (client/legal_person bilan bir xil naqsh)."""
    ensure_refs(page, code)
    if name is None:
        name = f"supplier-basic-{code}"
    return run_supplier(page, code, name=name, status=status)


#---------------------------------------------------------------------------------------------------


def run_supplier_full(page: Page, code) -> None:
    """Поставщик formasining BARCHA to'ldiriladigan maydonlari bilan yaratish.

    Faqat majburiylar emas — Основное (Адрес va Характеристика товаров tablari
    bilan), Реквизиты va Расчётные счёта bo'limlari ham to'ldiriladi.
    Ma'lumotnomalar ``ensure_refs`` yaratganlaridan tanlanadi. Readonly
    maydonlar to'ldirilmaydi: Время создания, GPS координаты (faqat Карта
    dialogi orqali kiritiladi)."""
    ensure_refs(page, code)
    m = BasePage(page)
    name = f"supplier-full-{code}"
    tin = random.randint(100000000, 999999999)
    gln = random.randint(10**12, 10**13 - 1)
    phone = f"+998(99)-{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}"
    region = f"Region-{code}"
    form = f"MCHJ-{code}"

    with allure.step("Навигация: Модератор → Поставщики"):
        flow_navigate(page, tab="Модератор", name="Поставщики")
        m.expect_heading("Поставщики")

    with allure.step("Создать: yangi Поставщик formasi ochish"):
        # OAuth2 formasi (regression'da oldin ishlaydi) keyingi formalarga
        # "Главная/Детали/Код сервера" label'larini YUQTIRADI (i18n leak) — Юр.Лицо
        # tab'lari (Реквизиты→Детали) buziladi. Reload SPA'ni qayta yuklab tozalaydi
        # (MCP tasdiqlangan 2026-07-30).
        page.reload()
        m.settle()
        m.open_create()
        m.expect_heading("Юр. Лицо (Создания)")

    with allure.step(f"Основное: matn maydonlari ({name})"):
        # Юр.Лицо formasida label'lar ikkinchi ketma-ket create formada aralashadi
        # (Код→"Код сервера", Примечания→"Примечание" va h.k.) — barcha matn maydonlar
        # smtid orqali (dump 2026-07-30, create form: name/code/tin/note/short_name/
        # gln/working_hours/address).
        m.input(smtid="name", value=name)
        m.input(smtid="code", value=f"sup-code-{code}")
        m.input(smtid="tin", value=tin)
        m.input(smtid="note", value=f"Avto-test izohi {code}")
        m.input(smtid="short_name", value=f"sup-full-{code}")
        m.input(smtid="gln", value=gln)
        m.input(smtid="working_hours", value="Пн-Пт 09:00-18:00")

    with allure.step(f"Основное: Форма собственности = {form}, Статус = Активный, Тип = Поставщик"):
        m.select(form, label="Форма собственности")
        m.radio("Активный", label="Статус")
        m.radio("Поставщик", label="Тип Юр. лица")

    with allure.step(f"Адрес tab: Регион = {region}, Номер телефона = {phone}, Адрес"):
        m.select(region, label="Регион")
        m.input(label="Номер телефона", value=phone)
        m.input(smtid="address", value=f"Toshkent sh., Avto-test ko'chasi {code}")

    with allure.step(f"Характеристика товаров tab: Отрасль = Industry-{code}, Категория = Category-{code}"):
        m.click_button("Характеристика товаров")
        m.select(f"Industry-{code}", label="Отрасль")
        m.select(f"Category-{code}", label="Категория")

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
        # Inline grid qatori — 4 ta text input (Название, bank_account_code,
        # bank_name, mfo) va "Основное" switch; bir joyda ishlatilgani uchun inline
        account_row = page.locator("#main-content .smt-data-row").first
        cells = account_row.locator("input[type=text]")
        cells.nth(0).fill(f"Account-{code}")
        cells.nth(1).fill("20208000900000000001")
        cells.nth(2).fill("Ipoteka Bank")
        cells.nth(3).fill("00425")
        m.checkbox(locator=account_row.locator("smt-switch").first, checked=True)

    with allure.step("Сохранить"):
        # Saqlangach redirect barqaror emas (seansdagi keyingi saqlashlarda
        # ilova dashboard'ga qaytarib yuboradi) — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        flow_navigate(page, tab="Модератор", name="Поставщики")
        m.expect_heading("Поставщики")
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Поставщики")
@allure.story("Создание поставщика — все поля")
@allure.title("Поставщикни BARCHA maydonlar bilan yaratish")
def test_supplier_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_supplier_full(page, code)


#---------------------------------------------------------------------------------------------------


def run_supplier_edit(page: Page, code) -> None:
    """Yangi supplier yaratib, uni Изменить orqali tahrirlaydi va o'zgarish
    ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"supplier-edit-{code}"
    new_name = f"supplier-upd-{code}"

    run_supplier_basic(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        # run_supplier_basic ro'yxatni old_name bo'yicha qidirilgan holda qoldiradi
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
        flow_navigate(page, tab="Модератор", name="Поставщики")
        m.expect_heading("Поставщики")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        m.expect_no_row(old_name)


@allure.epic("Модератор")
@allure.feature("Поставщики")
@allure.story("Редактирование поставщика")
@allure.title("Поставщикни tahrirlash va o'zgarishni tekshirish")
def test_supplier_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_supplier_edit(page, code)


#---------------------------------------------------------------------------------------------------


def run_supplier_view(page: Page, code) -> None:
    """Yangi supplier yaratib, Просмотреть formasida kiritilgan ma'lumotlar
    to'g'ri ko'rsatilishini tekshiradi.

    Просмотр sahifasida qiymatlar barqaror smtid'li readonly inputlarda turadi
    (sv_main_name, sv_main_tin, ...) — MCP tasdiqlangan 2026-07-05."""
    m = BasePage(page)
    name = f"supplier-view-{code}"

    data = run_supplier_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Просмотр formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Просмотреть")
        m.expect_heading("Поставщик (Просмотр)")

    with allure.step("Основное: Название, ИНН, Статус, Форма собственности qiymatlari"):
        m.input(smtid="sv_main_name", expect_value=data["name"])
        m.input(smtid="sv_main_tin", expect_value=data["tin"])
        m.input(smtid="sv_main_status", expect_value="Активный")
        m.input(smtid="sv_main_legal_form", expect_value=data["form"])
        m.input(smtid="sv_main_short_name", expect_value=data["name"])

    with allure.step(f"Адрес: Регион = {data['region']} ko'rsatilgan"):
        # Регион readonly input emas, oddiy matn sifatida chiqadi
        expect(page.locator("#main-content")).to_contain_text(data["region"])


@allure.epic("Модератор")
@allure.feature("Поставщики")
@allure.story("Просмотр поставщика")
@allure.title("Поставщик ma'lumotlari Просмотр formasida to'g'ri ko'rinishi")
def test_supplier_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_supplier_view(page, code)


#---------------------------------------------------------------------------------------------------


def run_supplier_delete(page: Page, code) -> None:
    """Yangi supplier yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi.

    "Удалить" supplier rolini o'chiradi ("Удалить с юр. лицом" esa yuridik
    shaxsni butunlay o'chiradi — bu testda ishlatilmaydi). Tasdiqlash dialogi:
    "Вы хотите удалить {nom}?" → да (MCP tasdiqlangan 2026-07-05)."""
    m = BasePage(page)
    name = f"supplier-del-{code}"

    run_supplier_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        # run_supplier_basic ro'yxatni name bo'yicha qidirilgan holda qoldiradi
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        m.expect_no_row(name)


@allure.epic("Модератор")
@allure.feature("Поставщики")
@allure.story("Удаление поставщика")
@allure.title("Поставщикни o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_supplier_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_supplier_delete(page, code)


#---------------------------------------------------------------------------------------------------


def run_supplier_status(page: Page, code) -> None:
    """Status almashtirish ikki yo'nalishda tekshiriladi:

    1) Активный yaratilgan supplier "Изменить статус" orqali Пассивный qilinadi —
       default ro'yxatdan yo'qoladi, "Показать все" filtrida "Пассивный" bo'lib
       ko'rinadi. (UI'da "Неактивный" emas, "Пассивный" termini ishlatiladi.)
    2) Пассивный holatda yaratilgan supplier Активный qilinadi — default
       ro'yxatda "Активный" bo'lib paydo bo'ladi."""
    m = BasePage(page)
    active_name = f"supplier-stat-a-{code}"
    passive_name = f"supplier-stat-p-{code}"

    run_supplier_basic(page, code, name=active_name)

    with allure.step(f"1) '{active_name}' ni Пассивный qilish"):
        m.click_grid_row(active_name)
        m.change_status("Пассивный")

    with allure.step("1) Default ro'yxatda ko'rinmasligini tekshirish"):
        m.search(active_name)
        m.expect_no_row(active_name)

    with allure.step("1) Показать все filtrida 'Пассивный' bo'lib ko'rinishi"):
        m.show_all()
        m.grid_row(active_name, "Пассивный")

    run_supplier_basic(page, code, name=passive_name, status="Пассивный")

    with allure.step(f"2) Пассивный yaratilgan '{passive_name}' ni Активный qilish"):
        m.click_grid_row(passive_name)
        m.change_status("Активный")

    with allure.step("2) Ro'yxatda 'Активный' bo'lib ko'rinishini tekshirish"):
        m.search(passive_name)
        m.grid_row(passive_name, "Активный")


@allure.epic("Модератор")
@allure.feature("Поставщики")
@allure.story("Статус поставщика")
@allure.title("Поставщик statusini Пассивный/Активный qilish va tekshirish")
def test_supplier_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_supplier_status(page, code)


#---------------------------------------------------------------------------------------------------


def run_supplier_duplicate(page: Page, code) -> None:
    """Bir xil nom va ИНН bilan qayta yaratishga urinish xatolik berishini
    tekshiradi.

    ИНН bo'yicha unikal indeks bor: saqlashda "Ошибка" dialogi chiqadi
    (matnida "dup_val_on_index" va tin qiymati), forma ochiq qoladi va
    yozuv YARATILMAYDI (MCP tasdiqlangan 2026-07-05)."""
    m = BasePage(page)
    name = f"supplier-dup-{code}"

    data = run_supplier_basic(page, code, name=name)

    with allure.step(f"Xuddi shu nom '{name}' va ИНН {data['tin']} bilan qayta yaratish"):
        flow_navigate(page, tab="Модератор", name="Поставщики")
        m.expect_heading("Поставщики")
        m.open_create()
        m.expect_heading("Юр. Лицо (Создания)")
        m.input(label="Юр. лица название", value=name)
        m.input(label="Краткое название", value=name)
        m.input(label="ИНН", value=data["tin"])
        m.select(data["form"], label="Форма собственности")
        m.radio("Поставщик", label="Тип Юр. лица")
        m.click_button("Сохранить")

    with allure.step("Ошибка dialogi chiqishini tekshirish (ИНН dublikat)"):
        m.expect_error_dialog("Ошибка", "dup_val_on_index", data["tin"])

    with allure.step("Dialogni yopish — forma ochiq qoladi, yozuv saqlanmagan"):
        m.expect_heading("Юр. Лицо (Создания)")

    with allure.step(f"Ro'yxatda '{name}' faqat BITTA ekanini tekshirish"):
        flow_navigate(page, tab="Модератор", name="Поставщики")
        m.expect_heading("Поставщики")
        m.search(name)
        m.expect_row_count(name, 1)


@allure.epic("Модератор")
@allure.feature("Поставщики")
@allure.story("Дубликат поставщика")
@allure.title("Bir xil nom/ИНН bilan qayta yaratishda xatolik chiqishi")
def test_supplier_duplicate(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_supplier_duplicate(page, code)
