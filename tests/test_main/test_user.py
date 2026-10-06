"""Пользователи — CRUD testlari (Модератор → Главное → Пользователи).

DIQQAT (user tasdiqlagan 2026-09-24): Пользователи moduli IKKI joyda ko'rinadi:
- Главное → "Пользователи" menyu bandi = ``sb/sbr/moderator/person/user_list`` —
  BIZNIKI (sm24). Testlar FAQAT shu yerda. Oldin bu yerda "Удалить" yo'q edi,
  endi qo'shilgan.
- Главное → Роли → sub-link "Пользователи" = ``biruni/md/user_list`` — biruni,
  sm24'ga TEGISHLI EMAS, unga test yozilmaydi (u yerdan o'chirish 500
  "md_users child record found sbr_users_f1" beradi).

DOM (MCP dev/sm24 tasdiqlangan 2026-09-24):
- Sarlavhalar: ro'yxat "Пользователи", yaratish "Пользователь (Создание)",
  tahrir "Пользователь (Редактирования)"; create va edit save ikkalasi ham
  ro'yxatga qaytadi.
- Forma smtid'lari: ``moderator-user-name`` (ФИО *), ``moderator_user_login``
  (Логин *), ``moderator_user_password`` (Пароль *); "Язык *" default "ru"
  bilan to'lgan. To'liq login = "<Логин>@sm24".
- Qator paneli: Просмотреть / Изменить / Неактивный (status TOGGLE — passiv qatorda
  "Активный") / Настройка форм / Удалить. Tasdiqlash dialogi "Да/Нет".
- Qator paneli 2026-09-29 dan "Просмотреть" ham bor → "Пользователь (Просмотр)",
  readonly ``uv_*`` smtid'lar (uv_name/uv_login/uv_code/uv_position/uv_email/uv_state).
- Passiv (Неактивный) user default ro'yxatda yashirin — "Показать все" bilan
  ko'rinadi. Qidiruv ФИО bo'yicha ishlaydi.
"""
import allure
import pytest
from playwright.sync_api import Page

from flows.flow_authorization import COMPANY_CODE, authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def _goto_users(m: BasePage, page: Page) -> None:
    """Модератор → Главное → "Пользователи" (sbr person/user_list).

    Allaqachon shu ro'yxatda tursak menyuni QAYTA bosmaymiz — CRUD testlari
    zanjirdagi oldingi test qayerda tugaganiga bog'liq bo'lmasligi uchun.
    Qayta bosish ilova bag'ini qo'zg'atadi (keyingi save biruni dashboard'ga
    uloqtiradi) — bu bag' alohida ``run_user_menu_reclick`` testida tekshiriladi."""
    if "person/user_list" not in page.url:
        flow_navigate(page, tab="Модератор", name="Пользователи")
    m.expect_heading("Пользователи")


def run_user(page: Page, code, name=None, extra=None) -> dict:
    """Yangi Пользователь yaratadi (majburiy: ФИО, Логин, Пароль; Язык default
    to'lgan). ``extra`` — ixtiyoriy maydonlar {smtid: qiymat} (masalan
    ``moderator-user-code``). Yaratilgan qiymatlarni qaytaradi."""
    m = BasePage(page)
    if name is None:
        name = f"User-{code}"
    login = name.lower()

    with allure.step("Навигация: Модератор → Пользователи"):
        _goto_users(m, page)

    with allure.step("Создать: yangi Пользователь formasi ochish"):
        m.open_create()
        m.expect_heading("Пользователь (Создание)")

    with allure.step(f"Форма: ФИО={name}, Логин={login}, Пароль"):
        m.input(smtid="moderator-user-name", value=name)
        m.input(smtid="moderator_user_login", value=login)
        m.input(smtid="moderator_user_password", value="1")
        for smtid, value in (extra or {}).items():
            m.input(smtid=smtid, value=value)

    with allure.step("Сохранить va ro'yxatda tekshirish"):
        m.save_and_expect_heading("Пользователи")
        m.search(name)
        m.grid_row(name, "Активный")

    return {"name": name, "login": login}


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.story("Создание пользователя")
@allure.title("Yangi Пользователь yaratish")
def test_user_create(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_user(page, code)


# ---------------------------------------------------------------------------------------------------


def run_user_view(page: Page, code) -> None:
    """Ixtiyoriy maydonlari (Код, Должность, Эл. адрес) bilan user yaratib,
    "Просмотреть" formasida barcha kiritilgan qiymatlar ko'rinishini tekshiradi.

    View maydonlari readonly ``smt-input[smtid=uv_*]`` (MCP-probe tasdiqlangan
    2026-09-29). Пол tekshirilmaydi — view'da i18n kaliti ("UI-SB348:male")
    chiqadi, tarjima emas."""
    m = BasePage(page)
    name = f"User-view-{code}"
    login = name.lower()
    user_code = f"code-{code}"
    position = f"Tester-{code}"
    email = f"{login}@example.com"

    run_user(page, code, name=name, extra={
        "moderator-user-code": user_code,
        "moderator-user-position": position,
        "moderator-user-email": email,
    })

    with allure.step(f"'{name}' qatorini tanlab Просмотреть formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Просмотреть", expect_heading="Пользователь (Просмотр)")

    with allure.step("Qiymatlar: ФИО/Логин/Код/Должность/Эл. адрес/Статус view formada"):
        m.input(smtid="uv_name", expect_value=name)
        m.input(smtid="uv_login", expect_value=f"{login}@{COMPANY_CODE}")
        m.input(smtid="uv_code", expect_value=user_code)
        m.input(smtid="uv_position", expect_value=position)
        m.input(smtid="uv_email", expect_value=email)
        m.input(smtid="uv_state", expect_value="Активный")

    with allure.step("Ro'yxatga qaytish"):
        _goto_users(m, page)


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.story("Просмотр пользователя")
@allure.title("Пользователь Просмотр formasida kiritilgan qiymatlar ko'rinishi")
def test_user_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_user_view(page, code)


# ---------------------------------------------------------------------------------------------------


def run_user_edit(page: Page, code) -> None:
    """Yangi user yaratib, Изменить orqali ФИО ni o'zgartiradi va o'zgarish
    ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"User-edit-{code}"
    new_name = f"User-upd-{code}"

    run_user(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить", expect_heading="Пользователь (Редактирования)")

    with allure.step(f"Tahrirlash: ФИО {old_name} → {new_name}"):
        m.input(smtid="moderator-user-name", value=new_name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Пользователи")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        # Eski nom "yo'q" tekshirilmaydi — qidiruv LOGIN bo'yicha ham qidiradi,
        # login tahrirda o'zgarmaydi (user-edit-{code})
        m.search(new_name)
        m.grid_row(new_name)


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.story("Редактирование пользователя")
@allure.title("Пользовательni tahrirlash va o'zgarishni tekshirish")
def test_user_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_user_edit(page, code)


# ---------------------------------------------------------------------------------------------------


def run_user_status(page: Page, code) -> None:
    """Yangi user yaratib, qator panelidagi "Неактивный" toggle bilan statusini
    o'zgartiradi (tasdiqlash "Да") va passiv holatda ko'rinishini tekshiradi."""
    m = BasePage(page)
    name = f"User-stat-{code}"

    run_user(page, code, name=name)

    with allure.step(f"'{name}' ni tanlab 'Неактивный' → tasdiqlash 'Да'"):
        m.click_grid_row(name)
        m.click_button("Неактивный")
        m.confirm("да")

    with allure.step("Default ro'yxatda ko'rinmasligini tekshirish (passiv yashirin)"):
        m.search(name)
        m.expect_no_row(name)

    with allure.step("'Показать все' filtrida Неактивный bo'lib ko'rinishi"):
        m.show_all()
        m.grid_row(name, "Неактивный")


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.story("Статус пользователя")
@allure.title("Пользователь statusini Неактивный qilish va tekshirish")
def test_user_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_user_status(page, code)


# ---------------------------------------------------------------------------------------------------


def run_user_delete(page: Page, code) -> None:
    """Yangi user yaratib, "Удалить" bilan o'chiradi (tasdiqlash "Да") va
    ro'yxatdan yo'qolganini tekshiradi (passivlar bilan ham — "Показать все")."""
    m = BasePage(page)
    name = f"User-del-{code}"

    run_user(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'Да' bosish — server $delete muvaffaqiyatli"):
        # Qator yo'qolishi o'zi yetmaydi (passiv qator ham default yashirin) —
        # server haqiqatan o'chirganini javob statusidan tasdiqlaymiz.
        with page.expect_response(lambda r: "user_list$delete" in r.url) as resp_info:
            m.confirm("да")
        resp = resp_info.value
        assert resp.ok, f"$delete {resp.status}: {resp.text()[:300]}"

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        m.expect_no_row(name)


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.story("Удаление пользователя")
@allure.title("Пользовательni o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_user_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_user_delete(page, code)


# ---------------------------------------------------------------------------------------------------


# ILOVA BAG'I (2026-09-29, oddiy kliklar bilan takrorlangan — test funksiyalarisiz):
# Пользователи ro'yxatida turib menyudan YANA "Пользователи" bosilsa, keyingi
# Создать → Сохранить ro'yxatga emas, biruni/intro/dashboard'ga uloqtiradi
# (konsolda assets/i18n/biruni/md/ru.json 404). User baribir saqlanadi.
# Bag' tuzalsa test XPASS bo'ladi (strict) → xfail belgisini olib tashlash kerak.
MENU_RECLICK_BUG = (
    "Ilova bag'i: Пользователи ro'yxatida menyuni qayta bosgach, Сохранить "
    "biruni/intro/dashboard'ga uloqtiradi (ro'yxatga qaytmaydi)"
)


def run_user_menu_reclick(page: Page, code) -> None:
    """Ro'yxatda turib menyudan yana "Пользователи" bosib user yaratadi va
    Сохранить'dan keyin Пользователи ro'yxatiga qaytishini tekshiradi.

    Avval user HAQIQATAN saqlanganini tasdiqlaymiz, keyin qaytish sahifasini —
    shunda yiqilish aynan redirect bag'ini ko'rsatadi (saqlash xatosini emas)."""
    m = BasePage(page)
    name = f"User-reclick-{code}"

    with allure.step("Пользователи ro'yxatini ochish"):
        _goto_users(m, page)

    with allure.step("Ro'yxatda turib menyudan yana 'Пользователи' bosish"):
        flow_navigate(page, tab="Модератор", name="Пользователи")
        m.expect_heading("Пользователи")

    with allure.step(f"Создать: {name} → Сохранить"):
        m.open_create()
        m.expect_heading("Пользователь (Создание)")
        m.input(smtid="moderator-user-name", value=name)
        m.input(smtid="moderator_user_login", value=name.lower())
        m.input(smtid="moderator_user_password", value="1")
        m.save()
        try:
            page.wait_for_url(lambda url: "person/user_list" in url, timeout=15_000)
        except Exception:
            pass
        landed = page.url

    with allure.step(f"User saqlangan: '{name}' ro'yxatda bor"):
        _goto_users(m, page)
        m.search(name)
        m.grid_row(name, "Активный")

    with allure.step("Сохранить'dan keyin Пользователи ro'yxatiga qaytgan"):
        assert "person/user_list" in landed, f"{MENU_RECLICK_BUG}. Save'dan keyingi URL: {landed}"


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.story("Menyuni qayta bosish → Сохранить (ilova bag'i)")
@allure.title("Ro'yxatda menyuni qayta bosgach Сохранить ro'yxatga qaytishi")
@pytest.mark.xfail(strict=True, raises=AssertionError, reason=MENU_RECLICK_BUG)
def test_user_menu_reclick(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_user_menu_reclick(page, code)
