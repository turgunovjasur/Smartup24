"""Валюта — to'liq CRUD regression testlari.

Basic create (run_valyuta/test_valyuta) tests/test_setup/test_valyuta.py da
turadi — bu yerda faqat CRUD ssenariylari: full create, edit, view, delete,
status, duplicate. Har test o'z unikal Код bilan ishlaydi (kod prefikslari:
1..7 + {code}). Kod test_setup dan ko'chirilgan ishlaydigan nusxa
(MCP tasdiqlangan 2026-07-05).
"""

import allure
from playwright.sync_api import Page, expect

from flows.flow_navbar import flow_menu, flow_navigate
from tests.test_setup.test_valyuta import run_valyuta
from utils.base_page import BasePage


def run_valyuta_full(page: Page, code) -> None:
    """Валюта formasining BARCHA maydonlari bilan yaratish: Код, Название,
    Базовая/Разменная денежная единица, Постфикс radio + qo'shimcha matn,
    Статус (MCP tasdiqlangan 2026-07-05)."""
    m = BasePage(page)
    name = f"val-full-{code}"
    kod = f"1{code}"

    with allure.step("Навигация: Модератор → Валюты"):
        flow_navigate(page, tab="Модератор", name="Валюты")
        m.expect_heading("Валюты")

    with allure.step("Создать: yangi Валюта formasi ochish"):
        m.open_create()
        m.expect_heading("Валюта (Создания)")

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

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        flow_navigate(page, tab="Модератор", name="Валюты")
        m.expect_heading("Валюты")
        # Валютыда qidiruv default Название bo'yicha ISHLAMAYDI —
        # "Настройки поиска" orqali yoqiladi
        flow_menu(page)
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Создание валюты — все поля")
@allure.title("Валютани BARCHA maydonlar bilan yaratish")
def test_valyuta_full(m: BasePage, page: Page, code) -> None:
    run_valyuta_full(page, code)


#---------------------------------------------------------------------------------------------------


def run_valyuta_edit(page: Page, code) -> None:
    """Yangi valyuta yaratib, Изменить orqali nomini o'zgartiradi va o'zgarish
    ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"val-edit-{code}"
    new_name = f"val-upd-{code}"

    run_valyuta(page, code, name=old_name, kod=f"2{code}")

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
        flow_navigate(page, tab="Модератор", name="Валюты")
        m.expect_heading("Валюты")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        expect(page.locator(".smt-data-row").filter(has_text=old_name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Редактирование валюты")
@allure.title("Валютани tahrirlash va o'zgarishni tekshirish")
def test_valyuta_edit(m: BasePage, page: Page, code) -> None:
    run_valyuta_edit(page, code)


#---------------------------------------------------------------------------------------------------


def run_valyuta_view(page: Page, code) -> None:
    """Yangi valyuta yaratib, Просмотр formasida qiymatlar to'g'ri
    ko'rsatilishini tekshiradi (readonly cv_* inputlar, MCP 2026-07-05).

    Diqqat: valyutada tugma "Просмотреть" emas, "Просмотр" deb nomlangan."""
    m = BasePage(page)
    name = f"val-view-{code}"
    kod = f"3{code}"

    data = run_valyuta(page, code, name=name, kod=kod)

    with allure.step(f"'{name}' qatorini tanlab Просмотр formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Просмотр")
        m.expect_heading("Валюта (просмотр)")

    with allure.step("Qiymatlar: Название, Код, Статус, Базовая единица"):
        m.input(smtid="cv_name", expect_value=data["name"])
        m.input(smtid="cv_code", expect_value=data["kod"])
        # cv_state ruscha emas, INGLIZCHA kod ko'rsatadi (opros modulidagi
        # "active"/"passive" patterni; regression 2026-07-08)
        m.input(smtid="cv_state", expect_value="active")
        m.input(smtid="cv_decimal_name", expect_value=data["kod"])


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Просмотр валюты")
@allure.title("Валюта ma'lumotlari Просмотр formasida to'g'ri ko'rinishi")
def test_valyuta_view(m: BasePage, page: Page, code) -> None:
    run_valyuta_view(page, code)


#---------------------------------------------------------------------------------------------------


def run_valyuta_delete(page: Page, code) -> None:
    """Yangi valyuta yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi."""
    m = BasePage(page)
    name = f"val-del-{code}"

    run_valyuta(page, code, name=name, kod=f"4{code}")

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Удаление валюты")
@allure.title("Валютани o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_valyuta_delete(m: BasePage, page: Page, code) -> None:
    run_valyuta_delete(page, code)


#---------------------------------------------------------------------------------------------------


def run_valyuta_status(page: Page, code) -> None:
    """Status ikki yo'nalishda tekshiriladi. Валютада status qator action
    paneldagi MAQSAD status nomidagi toggle tugma bilan almashtiriladi
    (tasdiqlash: "да"). Tugma va grid badge nomlari INGLIZCHA "passive"/
    "active" (opros modulidagi pattern; regression 2026-07-08).

    1) Aktiv yaratilgan valyuta passive qilinadi — default ro'yxatdan
       yo'qoladi, "Показать все"da "passive" ko'rinadi.
    2) Passiv yaratilgan valyuta active qilinadi — ro'yxatda "active"."""
    m = BasePage(page)
    active_name = f"val-stat-a-{code}"
    passive_name = f"val-stat-p-{code}"

    run_valyuta(page, code, name=active_name, kod=f"5{code}")

    with allure.step(f"1) '{active_name}' ni passive qilish"):
        m.click_grid_row(active_name)
        m.click_button("passive")
        m.confirm("да")

    with allure.step("1) Default ro'yxatda ko'rinmasligini tekshirish"):
        m.search(active_name)
        expect(page.locator(".smt-data-row").filter(has_text=active_name)).to_have_count(0)

    with allure.step("1) Показать все filtrida 'passive' bo'lib ko'rinishi"):
        m.show_all()
        m.grid_row(active_name, "passive")

    run_valyuta(page, code, name=passive_name, kod=f"6{code}", active=False)

    with allure.step(f"2) Passiv yaratilgan '{passive_name}' ni active qilish"):
        m.click_grid_row(passive_name)
        m.click_button("active")
        m.confirm("да")

    with allure.step("2) Ro'yxatda 'active' bo'lib ko'rinishini tekshirish"):
        m.search(passive_name)
        m.grid_row(passive_name, "active")


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Статус валюты")
@allure.title("Валюта statusini Неактивный/Активный qilish va tekshirish")
def test_valyuta_status(m: BasePage, page: Page, code) -> None:
    run_valyuta_status(page, code)


#---------------------------------------------------------------------------------------------------


def run_valyuta_duplicate(page: Page, code) -> None:
    """Bir xil Код bilan qayta yaratishga urinish xatolik berishini tekshiradi.

    Код unikal: saqlashda "Ошибка" dialogi chiqadi — matni "Этот код уже
    используется (код: X) Попробуйте другой" (MCP tasdiqlangan 2026-07-05)."""
    m = BasePage(page)
    name = f"val-dup-{code}"
    kod = f"7{code}"

    run_valyuta(page, code, name=name, kod=kod)

    with allure.step(f"Xuddi shu Код {kod} bilan qayta yaratishga urinish"):
        m.open_create()
        m.expect_heading("Валюта (Создания)")
        m.input(label="Название", value=f"{name}-2")
        m.input(smtid="code", value=kod)  # label "Код" ikkinchi formada "Код сервера" ga aralashadi
        m.click_button("Сохранить")

    with allure.step("Ошибка dialogi chiqishini tekshirish (Код dublikat)"):
        dialog = page.locator(".cdk-overlay-container")
        # "Ошибка" dialogi + xabarda to'qnashgan Код ko'rsatiladi ("...(код: X)...").
        # To'liq jumla ("Этот код уже используется") server i18n'iga qarab ru↔en
        # almashishi mumkin — shuning uchun til-mustaqil qism (Код qiymati) tekshiriladi
        # (dublikat YARATILMAGANI quyida count==1 bilan ham isbotlanadi).
        expect(dialog).to_contain_text("Ошибка")
        expect(dialog).to_contain_text(kod)

    with allure.step("Dialogni yopish — forma ochiq qoladi, yozuv saqlanmagan"):
        dialog.get_by_role("button", name="Закрыть").first.click()
        m.expect_heading("Валюта (Создания)")

    with allure.step(f"Ro'yxatda '{name}' faqat BITTA ekanini tekshirish"):
        flow_navigate(page, tab="Модератор", name="Валюты")
        m.expect_heading("Валюты")
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(1)


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Дубликат валюты")
@allure.title("Bir xil Код bilan Валюта qayta yaratishda xatolik chiqishi")
def test_valyuta_duplicate(m: BasePage, page: Page, code) -> None:
    run_valyuta_duplicate(page, code)
