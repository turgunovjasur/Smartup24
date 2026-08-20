import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_menu, flow_navigate
from utils.base_page import BasePage

# Navbar tab + ro'yxat/forma sarlavhalari bir joyda — UI matni o'zgarsa bitta
# joy tuzatiladi. Regression moduli (test_regression/test_valyuta.py) shu
# konstantalar va `open_valyuta_list` ni import qiladi.
TAB = "Модератор"
LIST_HEADING = "Валюты"
CREATE_HEADING = "Валюта (Создания)"


def open_valyuta_list(page: Page, m: BasePage) -> None:
    """Модератор → Валюты ro'yxatiga o'tadi va sarlavhani tekshiradi —
    har run_* boshida takrorlanuvchi navigatsiya boilerplate'ini almashtiradi."""
    flow_navigate(page, tab=TAB, name=LIST_HEADING)
    m.expect_heading(LIST_HEADING)


def run_valyuta(page: Page, code, name=None, kod=None, active=True) -> dict:
    """Yangi Валюта yaratadi. ``name``/``kod`` berilmasa so`m{code}/{code};
    ``active=False`` bo'lsa Статус switch o'chirib yaratiladi. Yaratilgan
    qiymatlarni qaytaradi (Код unikal bo'lishi shart).

    Saqlashdan keyingi qidiruv+grid tekshiruvi ATAYLAB shu funksiyada:
    (1) Arrange sifatida chaqirilganda yaratish muvaffaqiyatini fail-fast
        tasdiqlaydi; (2) ro'yxatni yaratilgan yozuvga FILTRLAB qoldiradi —
        CRUD ssenariylari keyin to'g'ridan-to'g'ri ``click_grid_row(name)``
        chaqiradi, alohida qidiruvsiz.
    Bu yerdagi ``flow_menu`` Название bo'yicha qidiruvni user uchun serverda
    YOQADI (bir marta, sessiya davomida saqlanadi) — shuning uchun keyingi
    ``m.search(...)`` chaqiruvlari flow_menu'ni takrorlamaydi (dialog kliklari
    flaky manba). Har CRUD ssenariysi avval shu funksiyani chaqirgani uchun
    bu bog'liqlik doim bajariladi."""
    m = BasePage(page)
    if name is None:
        name = f"so`m{code}"
    if kod is None:
        kod = f"{code}"

    with allure.step("Навигация: Модератор → Валюты"):
        open_valyuta_list(page, m)

    with allure.step("Создать: yangi Валюта formasi ochish"):
        m.open_create()
        m.expect_heading(CREATE_HEADING)

    with allure.step(f"Форма: Название = {name}, Код = {kod}"):
        m.input(label="Название", value=name)
        m.input(smtid="code", value=kod)  # label "Код" ikkinchi formada "Код сервера" ga aralashadi
        m.input(label="Базовая денежная единица", value=kod)
        m.checkbox(label="Статус", checked=active)

    if active:
        with allure.step("Сохранить va ro'yxatda tekshirish"):
            # Saqlangach redirect barqaror emas (dashboard'ga ketishi mumkin) —
            # ro'yxatga o'zimiz kiramiz
            m.save()
            open_valyuta_list(page, m)
            # Валютыда qidiruv default Название bo'yicha ISHLAMAYDI —
            # "Настройки поиска" orqali yoqiladi
            flow_menu(page)
            m.search(name)
            m.grid_row(name)
    else:
        with allure.step("Сохранить va Показать все bilan tekshirish"):
            # Passiv yozuv default ro'yxatda ko'rinmaydi; redirect'ga tayanmay
            # ro'yxatga o'zimiz kiramiz
            m.save()
            open_valyuta_list(page, m)
            flow_menu(page)
            m.search(name)
            m.show_all()
            m.grid_row(name, "Неактивный")

    return {"name": name, "kod": str(kod)}


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Создание валюты")
@allure.title("Yangi Валюта yaratish")
def test_valyuta(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_valyuta(page, code)


# CRUD ssenariylari (run_valyuta_*) tests/test_regression/test_valyuta.py da —
# boshqa modullar kabi (test_region/test_supplier va h.k.).
