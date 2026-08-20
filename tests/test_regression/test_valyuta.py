"""Валюта — to'liq CRUD regression testlari.

Basic create (run_valyuta/test_valyuta) tests/test_setup/test_valyuta.py da
turadi — bu yerda faqat CRUD ssenariylari: full create, edit, view, delete,
status (deactivate/activate), duplicate. Har test o'z unikal Код bilan
ishlaydi (kod prefikslari CODE_PREFIX + {code}). Tuzilma boshqa regression
modullari (test_region/test_supplier va h.k.) bilan bir xil: run_* mantiq
shu faylda, runner ham shu fayldan import qiladi (MCP tasdiqlangan 2026-07-05).
"""
import allure
import pytest
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_menu
from tests.test_setup.test_valyuta import (
    CREATE_HEADING,
    open_valyuta_list,
    run_valyuta,
)
from utils.base_page import BasePage


# Har CRUD ssenariysi Код'ni o'z prefiksi + sessiya {code}'sidan quradi — shunda
# bitta runda ssenariylar bir-birining yozuviga urilmaydi (Код bazada unikal).
# DIQQAT: status ikkita yozuv yaratadi (aktiv va passiv) — shuning uchun ikki
# alohida prefiks (status_active/status_passive).
CODE_PREFIX = {
    "full": "1",
    "edit": "2",
    "view": "3",
    "delete": "4",
    "status_active": "5",
    "status_passive": "6",
    "duplicate": "7",
}


def run_valyuta_full(page: Page, code) -> None:
    """Валюта formasining BARCHA maydonlari bilan yaratish: Код, Название,
    Базовая/Разменная денежная единица, Постфикс radio + qo'shimcha matn,
    Статус (MCP tasdiqlangan 2026-07-05)."""
    m = BasePage(page)
    name = f"val-full-{code}"
    kod = f"{CODE_PREFIX['full']}{code}"

    # Arrange — Валюты ro'yxatiga o't va yangi forma och
    with allure.step("Навигация: Модератор → Валюты"):
        open_valyuta_list(page, m)

    with allure.step("Создать: yangi Валюта formasi ochish"):
        m.open_create()
        m.expect_heading(CREATE_HEADING)

    # Act — barcha maydonlarni to'ldirib saqla
    with allure.step(f"Форма: barcha maydonlar ({name}, Код = {kod})"):
        m.input(smtid="code", value=kod)  # label "Код" ikkinchi formada "Код сервера" ga aralashadi
        m.input(label="Название", value=name)
        # Базовая денежная единица bazada GLOBAL unikal ("уже используется"
        # xatosi) — har run o'z qiymatini ishlatadi (2026-07-07 regression)
        m.input(label="Базовая денежная единица", value=f"so`m{kod}")
        m.input(label="Разменная денежная единица", value=f"tiyin{kod}")
        m.radio("Постфикс", label="Префикс")
        m.input(smtid="addon", value="so`m")
        m.checkbox(label="Статус", checked=True)

    with allure.step("Сохранить"):
        # Saqlangach redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()

    # Assert — ro'yxatda yaratilgan yozuv ko'rinishini tasdiqla
    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        open_valyuta_list(page, m)
        # Валютыда qidiruv default Название bo'yicha ISHLAMAYDI —
        # "Настройки поиска" orqali yoqiladi
        flow_menu(page)
        m.search(name)
        m.grid_row(name)


def run_valyuta_edit(page: Page, code) -> None:
    """Yangi valyuta yaratib, Изменить orqali nomini o'zgartiradi va o'zgarish
    ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"val-edit-{code}"
    new_name = f"val-upd-{code}"

    # Arrange — tahrirlanadigan yozuvni yarat
    run_valyuta(page, code, name=old_name, kod=f"{CODE_PREFIX['edit']}{code}")

    # Act — Изменить formasini ochib nomini o'zgartir va saqla
    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Валюта (Редактирования)")

    with allure.step(f"Tahrirlash: nom {old_name} → {new_name}"):
        m.input(label="Название", value=new_name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        # Edit'dan keyin ham redirect barqaror emas (dashboard'ga tushadi) —
        # ro'yxatga o'zimiz kiramiz
        m.save()
        open_valyuta_list(page, m)

    # Assert — yangi nom bor, eski nom yo'q
    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        m.expect_no_grid_row(old_name)


def run_valyuta_view(page: Page, code) -> None:
    """Yangi valyuta yaratib, Просмотр formasida qiymatlar to'g'ri
    ko'rsatilishini tekshiradi (readonly cv_* inputlar, MCP 2026-07-05).

    Diqqat: valyutada tugma "Просмотреть" emas, "Просмотр" deb nomlangan."""
    m = BasePage(page)
    name = f"val-view-{code}"
    kod = f"{CODE_PREFIX['view']}{code}"

    # Arrange — ko'riladigan yozuvni yarat (qaytgan qiymatlar bilan solishtiramiz)
    data = run_valyuta(page, code, name=name, kod=kod)

    # Act — Просмотр formasini och
    with allure.step(f"'{name}' qatorini tanlab Просмотр formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Просмотр")
        m.expect_heading("Валюта (просмотр)")

    # Assert — readonly maydonlar yaratilgan qiymatlarni ko'rsatadi
    with allure.step("Qiymatlar: Название, Код, Статус, Базовая единица"):
        m.input(smtid="cv_name", expect_value=data["name"])
        m.input(smtid="cv_code", expect_value=data["kod"])
        # Status modul bo'ylab RUSCHA yoziladi; UI tili ru↔en almashsa ham
        # BasePage `_STATUS_SYNONYMS` ikkala qiymatni ("Активный"/"active")
        # qabul qiladi (regression 2026-07-08).
        m.input(smtid="cv_state", expect_value="Активный")
        m.input(smtid="cv_decimal_name", expect_value=data["kod"])


def run_valyuta_delete(page: Page, code) -> None:
    """Yangi valyuta yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi."""
    m = BasePage(page)
    name = f"val-del-{code}"

    # Arrange — o'chiriladigan yozuvni yarat
    run_valyuta(page, code, name=name, kod=f"{CODE_PREFIX['delete']}{code}")

    # Act — qatorni tanlab o'chir va tasdiqla
    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    # Assert — yozuv ro'yxatdan yo'qoldi
    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        m.expect_no_grid_row(name)


def run_valyuta_status_deactivate(page: Page, code) -> None:
    """Aktiv yaratilgan valyuta passiv qilinadi — default ro'yxatdan yo'qoladi,
    "Показать все"da "Неактивный" bo'lib ko'rinadi.

    Валютада status qator action paneldagi MAQSAD status nomidagi toggle tugma
    bilan almashtiriladi (tasdiqlash: "да"). Status modul bo'ylab RUSCHA
    yoziladi; UI tili ru↔en almashsa ham BasePage `_STATUS_SYNONYMS` tugma va
    grid badge'ni ikkala tilda topadi (regression 2026-07-08)."""
    m = BasePage(page)
    active_name = f"val-stat-a-{code}"

    # Arrange — aktiv yozuv yarat
    run_valyuta(page, code, name=active_name, kod=f"{CODE_PREFIX['status_active']}{code}")

    # Act — passiv qil
    with allure.step(f"'{active_name}' ni Неактивный qilish"):
        m.click_grid_row(active_name)
        m.click_button("Неактивный")
        m.confirm("да")

    # Assert — default ro'yxatda yo'q, "Показать все"da Неактивный
    with allure.step("Default ro'yxatda ko'rinmasligini tekshirish"):
        m.search(active_name)
        m.expect_no_grid_row(active_name)

    with allure.step("Показать все filtrida 'Неактивный' bo'lib ko'rinishi"):
        m.show_all()
        m.grid_row(active_name, "Неактивный")


def run_valyuta_status_activate(page: Page, code) -> None:
    """Passiv yaratilgan valyuta aktiv qilinadi — ro'yxatda "Активный" bo'lib
    ko'rinadi.

    Status qator action paneldagi MAQSAD status nomidagi toggle tugma bilan
    almashtiriladi (tasdiqlash: "да"). Status modul bo'ylab RUSCHA yoziladi;
    UI tili ru↔en almashsa ham BasePage `_STATUS_SYNONYMS` tugma va grid
    badge'ni ikkala tilda topadi (regression 2026-07-08)."""
    m = BasePage(page)
    passive_name = f"val-stat-p-{code}"

    # Arrange — passiv yozuv yarat
    run_valyuta(page, code, name=passive_name, kod=f"{CODE_PREFIX['status_passive']}{code}", active=False)

    # Act — aktiv qil
    with allure.step(f"Passiv yaratilgan '{passive_name}' ni Активный qilish"):
        m.click_grid_row(passive_name)
        m.click_button("Активный")
        m.confirm("да")

    # Assert — ro'yxatda Активный
    with allure.step("Ro'yxatda 'Активный' bo'lib ko'rinishini tekshirish"):
        m.search(passive_name)
        m.grid_row(passive_name, "Активный")


def run_valyuta_duplicate(page: Page, code) -> None:
    """Bir xil Код bilan qayta yaratishga urinish xatolik berishini tekshiradi.

    Код unikal: saqlashda "Ошибка" dialogi chiqadi — matni "Этот код уже
    используется (код: X) Попробуйте другой" (MCP tasdiqlangan 2026-07-05)."""
    m = BasePage(page)
    name = f"val-dup-{code}"
    kod = f"{CODE_PREFIX['duplicate']}{code}"

    # Arrange — dastlabki yozuvni yarat (Код egallanadi)
    run_valyuta(page, code, name=name, kod=kod)

    # Act — xuddi shu Код bilan qayta yaratishga urin
    with allure.step(f"Xuddi shu Код {kod} bilan qayta yaratishga urinish"):
        m.open_create()
        m.expect_heading(CREATE_HEADING)
        m.input(label="Название", value=f"{name}-2")
        m.input(smtid="code", value=kod)  # label "Код" ikkinchi formada "Код сервера" ga aralashadi
        m.click_button("Сохранить")

    # Assert — Ошибка dialogi chiqadi va dublikat YARATILMAYDI
    with allure.step("Ошибка dialogi chiqishini tekshirish (Код dublikat)"):
        # "Ошибка" dialogi + xabarda to'qnashgan Код ko'rsatiladi ("...(код: X)...").
        # To'liq jumla ("Этот код уже используется") server i18n'iga qarab ru↔en
        # almashishi mumkin — shuning uchun til-mustaqil qism (Код qiymati) tekshiriladi
        # (dublikat YARATILMAGANI quyida count==1 bilan ham isbotlanadi).
        m.expect_error_dialog("Ошибка", kod)

    with allure.step("Dialogni yopish — forma ochiq qoladi, yozuv saqlanmagan"):
        m.close_dialog()
        m.expect_heading(CREATE_HEADING)

    with allure.step(f"Ro'yxatda '{name}' faqat BITTA ekanini tekshirish"):
        open_valyuta_list(page, m)
        m.search(name)
        m.expect_grid_row_count(name, 1)


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Создание валюты — все поля")
@allure.title("Валютани BARCHA maydonlar bilan yaratish")
def test_valyuta_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_valyuta_full(page, code)


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Редактирование валюты")
@allure.title("Валютани tahrirlash va o'zgarishni tekshirish")
def test_valyuta_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_valyuta_edit(page, code)


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Просмотр валюты")
@allure.title("Валюта ma'lumotlari Просмотр formasida to'g'ri ko'rinishi")
def test_valyuta_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_valyuta_view(page, code)


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Удаление валюты")
@allure.title("Валютани o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_valyuta_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_valyuta_delete(page, code)


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Статус валюты")
@allure.title("Валюта statusini Неактивный/Активный qilish va tekshirish")
@pytest.mark.parametrize(
    "run",
    [run_valyuta_status_deactivate, run_valyuta_status_activate],
    ids=["deactivate", "activate"],
)
def test_valyuta_status(page: Page, code, run) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run(page, code)


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Дубликат валюты")
@allure.title("Bir xil Код bilan Валюта qayta yaratishda xatolik chiqishi")
def test_valyuta_duplicate(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_valyuta_duplicate(page, code)
