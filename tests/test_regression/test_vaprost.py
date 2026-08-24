"""Вопрос — to'liq CRUD regression testlari.

Basic create (run_vaprost/test_vaprost) tests/test_setup/test_vaprost.py da
turadi — bu yerda faqat CRUD ssenariylari: full create, edit, view, delete,
status, duplicate (criterya/oprosniki bilan bir xil tuzilma).

Forma va ro'yxat MCP tasdiqlangan 2026-07-08:
- Ro'yxat ustunlari: Название | Тип вводимых данных | Тип вопроса |
  Обязательный вопрос (yes/no) | Статус (badge INGLIZCHA "active"/"passive",
  passiv qator default ro'yxatda KO'RINMAYDI — show_all kerak).
- Qator paneli: Изменить / Удалить / Неактивный|Активный (toggle RUSCHA,
  MAQSAD status nomi) — "Просмотр" tugmasi YO'Q (view Изменить orqali).
- Forma ("Вопрос (Создание)"/"Вопрос (Редактирование)"): Статус switch,
  Название * (smt-textarea), Тип вопроса radio (Свободный ответ default /
  Выбор из списка / Выбор из списка (со значением)), Тип вводимых данных *
  qidiruvsiz smt-select (Число default; Дата / Текст (строка) / Текст (абзац)),
  Минимальное/Максимальное значение (Число uchun), switchlar: Обязательный
  вопрос (Да) / Обязательное фото (Нет) / Принимать фото как ответ (Да).
- "Выбор из списка" tanlansa "Варианты ответов" bo'limi ochiladi: "Добавить"
  tugma + qatorlarda "Вариант ответа *" input.
- Dublikat nom: "Ошибка" dialogi, matnida "dup_val_on_index" (sbv_quizs).
"""
import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_vaprost_basic(page: Page, code, name=None) -> str:
    """CRUD testlari uchun yengil tayyorlov: faqat Название bilan savol
    yaratadi. Ro'yxatni ``name`` bo'yicha qidirilgan holda qoldiradi."""
    m = BasePage(page)
    if name is None:
        name = f"vaprost-basic-{code}"

    with allure.step(f"Tayyorlov: '{name}' savol yaratish"):
        flow_navigate(page, tab="Модератор", name="Вопросы")
        m.expect_heading("Вопросы")
        m.open_create()
        m.expect_heading("Вопрос (Создание)")
        m.input(label="Название", value=name)
        # Redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Вопросы")
        m.expect_heading("Вопросы")
        m.search(name)
        m.grid_row(name)

    return name


def run_vaprost_full(page: Page, code) -> None:
    """Вопрос formasining BARCHA maydonlari bilan yaratish: Название, Тип
    вопроса = Выбор из списка (Варианты ответов bilan), Тип вводимых данных =
    Текст (строка), Обязательный вопрос/Обязательное фото/Принимать фото как
    ответ switchlari (MCP tasdiqlangan 2026-07-08)."""
    m = BasePage(page)
    name = f"vaprost-full-{code}"

    with allure.step("Навигация: Модератор → Вопросы"):
        flow_navigate(page, tab="Модератор", name="Вопросы")
        m.expect_heading("Вопросы")

    with allure.step("Создать: yangi Вопрос formasi ochish"):
        m.open_create()
        m.expect_heading("Вопрос (Создание)")

    with allure.step(f"Форма: barcha maydonlar ({name})"):
        m.input(label="Название", value=name)
        m.radio("Выбор из списка", label="Тип вопроса")
        m.select("Текст (строка)", label="Тип вводимых данных")
        m.checkbox(label="Обязательный вопрос", checked=True)
        m.checkbox(label="Обязательное фото", checked=True)
        m.checkbox(label="Принимать фото как ответ", checked=True)

    with allure.step("Варианты ответов: ikkita variant qo'shish"):
        m.input(label="Вариант ответа", value=f"Variant-A-{code}")
        m.click_button("Добавить")
        m.input(label="Вариант ответа", value=f"Variant-B-{code}", index=1)

    with allure.step("Сохранить"):
        # Redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Ro'yxatda '{name}' 'active' bo'lib ko'rinishi"):
        flow_navigate(page, tab="Модератор", name="Вопросы")
        m.expect_heading("Вопросы")
        m.search(name)
        m.grid_row(name, "active")
        m.grid_row(name, "Выбор из списка")

    with allure.step("Изменить formasida saqlangan qiymatlar to'g'riligi"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.expect_heading("Вопрос (Редактирование)")
        m.input(label="Название", expect_value=name)
        m.checkbox(label="Обязательный вопрос", expect_checked=True)
        m.checkbox(label="Обязательное фото", expect_checked=True)
        m.input(label="Вариант ответа", expect_value=f"Variant-A-{code}")
        m.input(label="Вариант ответа", expect_value=f"Variant-B-{code}", index=1)

    with allure.step("Saqlamasdan ro'yxatga qaytish"):
        flow_navigate(page, tab="Модератор", name="Вопросы")
        m.expect_heading("Вопросы")


@allure.epic("Модератор")
@allure.feature("Вопросы")
@allure.story("Создание вопроса — все поля")
@allure.title("Вопросни BARCHA maydonlar bilan yaratish")
def test_vaprost_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_vaprost_full(page, code)


#---------------------------------------------------------------------------------------------------


def run_vaprost_edit(page: Page, code) -> None:
    """Yangi savol yaratib, Изменить orqali nomini o'zgartiradi va o'zgarish
    ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"vaprost-edit-{code}"
    new_name = f"vaprost-upd-{code}"

    run_vaprost_basic(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Вопрос (Редактирование)")

    with allure.step(f"Tahrirlash: nom {old_name} → {new_name}"):
        m.input(label="Название", value=new_name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        # Edit'dan keyin ham redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Вопросы")
        m.expect_heading("Вопросы")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        m.expect_no_row(old_name)


@allure.epic("Модератор")
@allure.feature("Вопросы")
@allure.story("Редактирование вопроса")
@allure.title("Вопросни tahrirlash va o'zgarishni tekshirish")
def test_vaprost_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_vaprost_edit(page, code)


#---------------------------------------------------------------------------------------------------


def run_vaprost_view(page: Page, code) -> None:
    """Yangi savol yaratib, saqlangan qiymatlar to'g'ri ekanini tekshiradi.

    Вопрос qatorida "Просмотр" tugmasi YO'Q (faqat Изменить/Удалить/status,
    MCP tasdiqlangan 2026-07-08) — shuning uchun qiymatlar Изменить formasida
    (saqlamasdan) tekshiriladi."""
    m = BasePage(page)
    name = f"vaprost-view-{code}"

    run_vaprost_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.expect_heading("Вопрос (Редактирование)")

    with allure.step("Qiymatlar: Название va Статус to'g'ri"):
        m.input(label="Название", expect_value=name)
        m.checkbox(label="Статус", expect_checked=True)

    with allure.step("Saqlamasdan ro'yxatga qaytish"):
        flow_navigate(page, tab="Модератор", name="Вопросы")
        m.expect_heading("Вопросы")


@allure.epic("Модератор")
@allure.feature("Вопросы")
@allure.story("Просмотр вопроса")
@allure.title("Вопрос ma'lumotlari to'g'ri saqlanganini tekshirish")
def test_vaprost_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_vaprost_view(page, code)


#---------------------------------------------------------------------------------------------------


def run_vaprost_delete(page: Page, code) -> None:
    """Yangi savol yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi (savol опросникка biriktirilmagan — o'chirish
    muvaffaqiyatli)."""
    m = BasePage(page)
    name = f"vaprost-del-{code}"

    run_vaprost_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        m.expect_no_row(name)


@allure.epic("Модератор")
@allure.feature("Вопросы")
@allure.story("Удаление вопроса")
@allure.title("Вопросни o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_vaprost_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_vaprost_delete(page, code)


#---------------------------------------------------------------------------------------------------


def run_vaprost_status(page: Page, code) -> None:
    """Status toggle tugmasi orqali o'zgartiriladi (tugma nomi MAQSAD statusi
    RUSCHA "Неактивный"/"Активный", tasdiqlash "да"). Grid badge INGLIZCHA:
    passiv savol default ro'yxatdan YO'QOLADI, "Показать все" filtrida
    "passive" bo'lib ko'rinadi (MCP tasdiqlangan 2026-07-08)."""
    m = BasePage(page)
    name = f"vaprost-stat-{code}"

    run_vaprost_basic(page, code, name=name)

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
@allure.feature("Вопросы")
@allure.story("Статус вопроса")
@allure.title("Вопрос statusini Неактивный/Активный qilish va tekshirish")
def test_vaprost_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_vaprost_status(page, code)


#---------------------------------------------------------------------------------------------------


def run_vaprost_duplicate(page: Page, code) -> None:
    """Bir xil nom bilan qayta yaratishga urinish xatolik berishini tekshiradi.

    Вопрос nomi unikal (sbv_quizs company_id+name indeksi): saqlashda "Ошибка"
    dialogi chiqadi — matnida "dup_val_on_index" (MCP tasdiqlangan 2026-07-08)."""
    m = BasePage(page)
    name = f"vaprost-dup-{code}"

    run_vaprost_basic(page, code, name=name)

    with allure.step(f"Xuddi shu nom '{name}' bilan qayta yaratishga urinish"):
        m.open_create()
        m.expect_heading("Вопрос (Создание)")
        m.input(label="Название", value=name)
        m.click_button("Сохранить")

    with allure.step("Ошибка dialogi chiqishini tekshirish (nom dublikat)"):
        m.expect_error_dialog("Ошибка", "dup_val_on_index")

    with allure.step("Dialogni yopish — forma ochiq qoladi, yozuv saqlanmagan"):
        m.expect_heading("Вопрос (Создание)")

    with allure.step(f"Ro'yxatda '{name}' faqat BITTA ekanini tekshirish"):
        flow_navigate(page, tab="Модератор", name="Вопросы")
        m.expect_heading("Вопросы")
        m.search(name)
        m.expect_row_count(name, 1)


@allure.epic("Модератор")
@allure.feature("Вопросы")
@allure.story("Дубликат вопроса")
@allure.title("Bir xil nom bilan Вопрос qayta yaratishda xatolik chiqishi")
def test_vaprost_duplicate(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_vaprost_duplicate(page, code)
