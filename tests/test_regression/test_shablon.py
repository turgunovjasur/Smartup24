"""Шаблон отчета по опросам — to'liq CRUD regression testlari.

Basic create (run_shablon/test_shablon) tests/test_setup/test_shablon.py da
turadi — bu yerda faqat CRUD ssenariylari: full create, edit, view, delete,
status, hisobot sahifasi. Dublikat testi YO'Q: ilova bir xil nomli shablonlarni
yaratishga RUXSAT beradi.

Modul xususiyatlari:
- Forma: Название* (smtid=name), Описание (smt-textarea smtid=description),
  Статус switch; "Вопросы" bo'limi — "Добавить" tugmasi qator qo'shadi, qatorda
  LABEL'siz smt-data-select (savol tanlash, placeholder "Поиск") va "Удалить".
- Qator paneli: Открыть / Изменить / Удалить / Неактивный|Активный (status
  toggle + "Да" tasdiqlash). "Открыть" yozuvni EMAS, hisobot sahifasini ochadi
  (heading "Отчет по опросу": Параметры/История, "Сформировать") — shuning
  uchun view tekshiruvi Изменить formasida bajariladi.
- Grid statuslari inglizcha kichik harfda: "active"/"passive"; passiv qator
  default ro'yxatda KO'RINMAYDI — "Показать все" kerak.
"""

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_regression.test_oprosniki import ensure_question
from tests.test_setup.test_shablon import run_shablon
from utils.base_page import BasePage


def run_shablon_basic(page: Page, code, name=None) -> str:
    """CRUD testlari uchun tayyorlov: ``run_shablon`` ni chaqiradi (faqat
    majburiy Название). ``name`` berilmasa Shablon-basic-{code} — setup'ning
    "Shablon-{code}" nomi bilan to'qnashmaslik uchun alohida. Ro'yxatni ``name``
    bo'yicha qidirilgan holda qoldiradi (client/legal_person bilan bir xil naqsh)."""
    if name is None:
        name = f"Shablon-basic-{code}"
    return run_shablon(page, code, name=name)


def run_shablon_full(page: Page, code) -> None:
    """Шаблон formasining BARCHA to'ldiriladigan maydonlari bilan yaratish:
    Название, Описание, Статус switch va "Вопросы" bo'limida bitta savol
    ("Добавить" → qatordagi label'siz smt-data-select, root rejimda tanlanadi).
    Saqlangach qiymatlar Изменить formasida qayta ochib tekshiriladi."""
    m = BasePage(page)
    name = f"Shablon-full-{code}"
    question = ensure_question(page, code)

    with allure.step("Навигация: Модератор → Шаблоны отчетов по опросам"):
        flow_navigate(page, tab="Модератор", name="Шаблоны отчетов по опросам")
        m.expect_heading("Шаблоны отчетов по опросам")

    with allure.step("Создать: yangi Шаблон formasi ochish"):
        m.open_create()
        m.expect_heading("Шаблон отчета по опросам (Создание)")

    with allure.step(f"Форма: barcha maydonlar ({name}, Вопрос = {question})"):
        m.input(label="Название", value=name)
        m.input(label="Описание", value=f"Avto-test shablon izohi {code}")
        m.checkbox(label="Статус", checked=True)
        # Вопросы bo'limi: Добавить qator qo'shadi, undagi select label'siz —
        # formada yagona smt-data-select, root rejimda topiladi
        m.click_button("Добавить")
        m.select(question, root=page.locator("#main-content"))

    with allure.step("Сохранить"):
        # Redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Ro'yxatda '{name}' 'active' bo'lib ko'rinishi"):
        flow_navigate(page, tab="Модератор", name="Шаблоны отчетов по опросам")
        m.expect_heading("Шаблоны отчетов по опросам")
        m.search(name)
        m.grid_row(name, "active")

    with allure.step("Изменить formasida saqlangan qiymatlar to'g'riligi"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.expect_heading("Шаблон отчета по опросам (Редактирование)")
        m.input(smtid="name", expect_value=name)
        m.input(smtid="description", expect_value=f"Avto-test shablon izohi {code}")
        # Tanlangan savol qatordagi select inputida ko'rinadi
        expect(page.locator("#main-content smt-data-select input").first).to_have_value(question)
        m.checkbox(label="Статус", expect_checked=True)

    with allure.step("Saqlamasdan ro'yxatga qaytish"):
        flow_navigate(page, tab="Модератор", name="Шаблоны отчетов по опросам")
        m.expect_heading("Шаблоны отчетов по опросам")


@allure.epic("Модератор")
@allure.feature("Шаблоны отчетов")
@allure.story("Создание шаблона — все поля")
@allure.title("Шаблонни BARCHA maydonlar (savol bilan) yaratish")
def test_shablon_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_shablon_full(page, code)


#---------------------------------------------------------------------------------------------------


def run_shablon_edit(page: Page, code) -> None:
    """Yangi shablon yaratib, Изменить orqali tahrirlaydi va o'zgarish
    ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"Shablon-edit-{code}"
    new_name = f"Shablon-upd-{code}"

    run_shablon_basic(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Шаблон отчета по опросам (Редактирование)")

    with allure.step(f"Tahrirlash: nom {old_name} → {new_name}, Описание"):
        m.input(label="Название", value=new_name)
        m.input(label="Описание", value=f"Tahrirlangan izoh {code}")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        # Edit'dan keyin ham redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Шаблоны отчетов по опросам")
        m.expect_heading("Шаблоны отчетов по опросам")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        m.expect_no_row(old_name)


@allure.epic("Модератор")
@allure.feature("Шаблоны отчетов")
@allure.story("Редактирование шаблона")
@allure.title("Шаблонни tahrirlash va o'zgarishni tekshirish")
def test_shablon_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_shablon_edit(page, code)


#---------------------------------------------------------------------------------------------------


def run_shablon_view(page: Page, code) -> None:
    """Yangi shablon yaratib, saqlangan qiymatlar to'g'ri ekanini tekshiradi.

    Шаблон qatorida "Просмотр" tugmasi YO'Q — "Открыть" yozuvni emas, hisobot
    sahifasini ochadi. Shuning uchun qiymatlar
    Изменить formasida (saqlamasdan) tekshiriladi."""
    m = BasePage(page)
    name = f"Shablon-view-{code}"

    run_shablon_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.expect_heading("Шаблон отчета по опросам (Редактирование)")

    with allure.step("Qiymatlar: Название va Статус to'g'ri to'ldirilgan"):
        m.input(smtid="name", expect_value=name)
        m.checkbox(label="Статус", expect_checked=True)

    with allure.step("Saqlamasdan ro'yxatga qaytish"):
        flow_navigate(page, tab="Модератор", name="Шаблоны отчетов по опросам")
        m.expect_heading("Шаблоны отчетов по опросам")


@allure.epic("Модератор")
@allure.feature("Шаблоны отчетов")
@allure.story("Просмотр шаблона")
@allure.title("Шаблон ma'lumotlari to'g'ri saqlanganini tekshirish")
def test_shablon_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_shablon_view(page, code)


#---------------------------------------------------------------------------------------------------


def run_shablon_report(page: Page, code) -> None:
    """Qator panelidagi "Открыть" hisobot sahifasini ochishini tekshiradi:
    heading "Отчет по опросу", Параметры/История bo'limlari va "Сформировать"
    tugmasi. Hisobot generatsiya QILINMAYDI —
    faqat sahifa ochilishi tekshiriladi."""
    m = BasePage(page)
    name = f"Shablon-rep-{code}"

    run_shablon_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Открыть bosish"):
        m.click_grid_row(name)
        m.click_button("Открыть")
        m.expect_heading("Отчет по опросу")

    with allure.step("Сформировать tugmasi ko'rinishini tekshirish"):
        expect(page.get_by_role("button", name="Сформировать").first).to_be_visible()

    with allure.step("Ro'yxatga qaytish"):
        flow_navigate(page, tab="Модератор", name="Шаблоны отчетов по опросам")
        m.expect_heading("Шаблоны отчетов по опросам")


@allure.epic("Модератор")
@allure.feature("Шаблоны отчетов")
@allure.story("Отчет по шаблону")
@allure.title("Шаблон 'Открыть' hisobot sahifasini ochishi")
def test_shablon_report(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_shablon_report(page, code)


#---------------------------------------------------------------------------------------------------


def run_shablon_delete(page: Page, code) -> None:
    """Yangi shablon yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi (tasdiqlash: "Удалить шаблон X ?")."""
    m = BasePage(page)
    name = f"Shablon-del-{code}"

    run_shablon_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        m.expect_no_row(name)


@allure.epic("Модератор")
@allure.feature("Шаблоны отчетов")
@allure.story("Удаление шаблона")
@allure.title("Шаблонни o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_shablon_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_shablon_delete(page, code)


#---------------------------------------------------------------------------------------------------


def run_shablon_status(page: Page, code) -> None:
    """Status toggle tugmasi orqali o'zgartiriladi (tugma nomi MAQSAD statusi,
    tasdiqlash "Да"). Passiv shablon default ro'yxatdan YO'QOLADI, "Показать
    все" filtrida "passive" bo'lib ko'rinadi."""
    m = BasePage(page)
    name = f"Shablon-stat-{code}"

    run_shablon_basic(page, code, name=name)

    with allure.step(f"'{name}' ni Неактивный qilish"):
        m.click_grid_row(name)
        m.click_button("Неактивный")
        m.confirm("да")

    with allure.step("Default ro'yxatda ko'rinmasligini tekshirish"):
        m.search(name)
        m.expect_no_row(name)

    with allure.step("Показать все filtrida 'passive' bo'lib ko'rinishi"):
        m.show_all()
        m.grid_row(name, "passive")

    with allure.step(f"'{name}' ni qayta Активный qilish"):
        m.click_grid_row(name)
        m.click_button("Активный")
        m.confirm("да")

    with allure.step("Ro'yxatda 'active' bo'lib ko'rinishini tekshirish"):
        m.search(name)
        m.grid_row(name, "active")


@allure.epic("Модератор")
@allure.feature("Шаблоны отчетов")
@allure.story("Статус шаблона")
@allure.title("Шаблон statusini Неактивный/Активный qilish va tekshirish")
def test_shablon_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_shablon_status(page, code)
