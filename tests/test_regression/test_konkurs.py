"""Конкурс — to'liq CRUD regression testlari.

Basic create (run_konkurs/test_konkurs) tests/test_setup/test_konkurs.py da
turadi — bu yerda faqat CRUD ssenariylari: full create, edit, view, delete,
status. Dublikat testi YO'Q: ilova bir xil nomli konkurslarni yaratishga
RUXSAT beradi (unikal cheklov yo'q, MCP tasdiqlangan 2026-07-05).
Kod test_setup dan ko'chirilgan ishlaydigan nusxa.
"""
from datetime import date, timedelta

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_setup.test_konkurs import run_konkurs
from tests.test_setup.test_region import run_region
from utils.base_page import BasePage

# Konkurs uchun region seansda BIR MARTA yaratiladi (region konkursda
# ixtiyoriy, lekin full testda to'ldiriladi)
_region_ready = set()


def ensure_konkurs_region(page: Page, code) -> str:
    """Konkurs testlari uchun Region-k{code} ni seansda bir marta yaratadi."""
    name = f"Region-k{code}"
    if code not in _region_ready:
        run_region(page, code, name=name)
        _region_ready.add(code)
    return name


def run_konkurs_basic(page: Page, code, name=None) -> dict:
    """CRUD testlari uchun yengil tayyorlov: faqat majburiy maydonlar bilan
    konkurs yaratadi (Регион ixtiyoriy — to'ldirilmaydi, Начало/Конец default
    bugungi sana bilan keladi, Статус default Черновик; MCP 2026-07-05).
    Ro'yxatni ``name`` bo'yicha qidirilgan holda qoldiradi."""
    m = BasePage(page)
    if name is None:
        name = f"konkurs-basic-{code}"

    with allure.step(f"Tayyorlov: '{name}' konkurs yaratish"):
        flow_navigate(page, tab="Модератор", name="Конкурсы")
        m.expect_heading("Конкурсы")
        m.open_create()
        m.expect_heading("Конкурсы (Создания)")
        m.input(label="Название", value=name)
        m.input(label="Количество победителей", value=4)
        # Redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Конкурсы")
        m.expect_heading("Конкурсы")
        m.search(name)
        m.grid_row(name)

    return {"name": name, "rank_count": "4"}


def run_konkurs_full(page: Page, code, region=None) -> None:
    """Конкурс formasining BARCHA to'ldiriladigan maydonlari bilan yaratish:
    Название, Количество победителей, Примечания, Статус radio (Черновик),
    Регион, Начало/Конец, Примечание о призе, Тип конкурса radio (Количество).

    "Характеристики"/"Характеристики клиента" selectlari to'ldirilmaydi —
    ular muhitdagi alohida lug'atga bog'liq (bo'sh bo'lishi mumkin)."""
    m = BasePage(page)
    name = f"konkurs-full-{code}"
    if region is None:
        region = ensure_konkurs_region(page, code)

    with allure.step("Навигация: Модератор → Конкурсы"):
        flow_navigate(page, tab="Модератор", name="Конкурсы")
        m.expect_heading("Конкурсы")

    with allure.step("Создать: yangi Конкурс formasi ochish"):
        m.open_create()
        m.expect_heading("Конкурсы (Создания)")

    with allure.step(f"Форма: barcha maydonlar ({name}, Регион = {region})"):
        m.input(label="Название", value=name)
        m.input(label="Количество победителей", value=5)
        m.input(label="Примечания", value=f"Avto-test konkurs izohi {code}")
        m.radio("Черновик", label="Статус")
        m.select(region, label="Регион")
        # Lokal dinamik sanalar (konkurs view'da tekshirilmaydi) — start bugun, end +30 kun
        m.input(label="Начало", value=date.today().strftime("%d.%m.%Y"))
        m.input(label="Конец", value=(date.today() + timedelta(days=30)).strftime("%d.%m.%Y"))
        m.input(label="Примечание о призе", value=f"Sovg'a izohi {code}")
        m.radio("Количество", label="Тип конкурса")

    with allure.step("Сохранить"):
        # Redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        flow_navigate(page, tab="Модератор", name="Конкурсы")
        m.expect_heading("Конкурсы")
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Конкурсы")
@allure.story("Создание конкурса — все поля")
@allure.title("Конкурсни BARCHA maydonlar bilan yaratish")
def test_konkurs_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_konkurs_full(page, code)


#---------------------------------------------------------------------------------------------------


def run_konkurs_edit(page: Page, code) -> None:
    """Yangi konkurs yaratib, Изменить orqali tahrirlaydi va o'zgarish
    ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"konkurs-edit-{code}"
    new_name = f"konkurs-upd-{code}"

    run_konkurs_basic(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Конкурсы (Редактирования)")

    with allure.step(f"Tahrirlash: nom {old_name} → {new_name}, победителей = 7"):
        m.input(label="Название", value=new_name)
        m.input(label="Количество победителей", value=7)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        # Edit'dan keyin ham redirect barqaror emas (dashboard'ga tushadi) —
        # ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Конкурсы")
        m.expect_heading("Конкурсы")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        expect(page.locator(".smt-data-row").filter(has_text=old_name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Конкурсы")
@allure.story("Редактирование конкурса")
@allure.title("Конкурсни tahrirlash va o'zgarishni tekshirish")
def test_konkurs_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_konkurs_edit(page, code)


#---------------------------------------------------------------------------------------------------


def run_konkurs_view(page: Page, code) -> None:
    """Yangi konkurs yaratib, Просмотр formasida qiymatlar to'g'ri
    ko'rsatilishini tekshiradi (readonly cv_main_* inputlar, MCP 2026-07-05).

    Diqqat: konkursda tugma "Просмотреть" emas, "Просмотр" deb nomlangan."""
    m = BasePage(page)
    name = f"konkurs-view-{code}"

    data = run_konkurs_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Просмотр formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Просмотр")
        m.expect_heading("Конкурс (Просмотр)")

    with allure.step("Qiymatlar: Название, Количество победителей, Статус"):
        m.input(smtid="cv_main_name", expect_value=data["name"])
        m.input(smtid="cv_main_rank_count", expect_value=data["rank_count"])
        m.input(smtid="cv_main_status", expect_value="Черновик")


@allure.epic("Модератор")
@allure.feature("Конкурсы")
@allure.story("Просмотр конкурса")
@allure.title("Конкурс ma'lumotlari Просмотр formasida to'g'ri ko'rinishi")
def test_konkurs_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_konkurs_view(page, code)


#---------------------------------------------------------------------------------------------------


def run_konkurs_delete(page: Page, code) -> None:
    """Yangi konkurs yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi."""
    m = BasePage(page)
    name = f"konkurs-del-{code}"

    run_konkurs_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Конкурсы")
@allure.story("Удаление конкурса")
@allure.title("Конкурсни o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_konkurs_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_konkurs_delete(page, code)


#---------------------------------------------------------------------------------------------------


def run_konkurs_status(page: Page, code) -> None:
    """Konkurs statusi bosqichma-bosqich o'zgartiriladi: Черновик (yaratilganda
    default) → Активный → Завершен. "Изменить статус" tugmasi menyu ochadi
    (joriy statusdan boshqa variantlar), variant tanlangach tasdiqlash "да"
    (MCP tasdiqlangan 2026-07-05)."""
    m = BasePage(page)
    name = f"konkurs-stat-{code}"

    run_konkurs_basic(page, code, name=name)

    with allure.step("Yaratilganda status = Черновик"):
        m.grid_row(name, "Черновик")

    with allure.step(f"'{name}' ni Активный qilish"):
        m.click_grid_row(name)
        m.change_status("Активный")

    with allure.step("Ro'yxatda 'Активный' bo'lib ko'rinishini tekshirish"):
        m.search(name)
        m.show_all()
        m.grid_row(name, "Активный")

    with allure.step(f"'{name}' ni Завершен qilish"):
        m.click_grid_row(name)
        m.change_status("Завершен")

    with allure.step("Ro'yxatda 'Завершен' bo'lib ko'rinishini tekshirish"):
        m.search(name)
        m.show_all()
        m.grid_row(name, "Завершен")


@allure.epic("Модератор")
@allure.feature("Конкурсы")
@allure.story("Статус конкурса")
@allure.title("Конкурс statusini Черновик → Активный → Завершен qilish")
def test_konkurs_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_konkurs_status(page, code)
