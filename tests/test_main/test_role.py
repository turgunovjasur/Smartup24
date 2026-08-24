"""Роли (Модератор → Роли, biruni role_list) — CRUD testlari.

test_organization.py patterni. Biruni farqlar:
- komponentlarda smtid BOR (role-name, role-order-no) — filialdan farqli;
  "Порядок" oddiy type=number input (maskasiz, fill ishlaydi).
- sarlavhalar: "Роль (создание)" / "Роль (изменение)" / "Роль (Просмотр)"
  (Просмотр bosh harf bilan!).
- action panel: Просмотр (ПросмотрЕТЬ emas) / Изменить / Удалить / Прикрепление.
- view bo'limlari BUTTON: Основная информация / Пользователи / Формы /
  Продукты / История изменений; view ichida "Изменить" tugmasi ham bor.
- create save ro'yxatga qaytaradi, edit save esa Просмотр'ga o'tadi —
  ikkalasida ham ro'yxatga flow_navigate bilan qaytamiz.
- dublikat nom "dup_val_on_index" (md_roles) Ошибка dialogi; delete confirm
  "Да/Нет"; passiv rol default yashirin ("Показать все" + Неактивный).
- DIQQAT: tizim rollari (Админ (Поставщик) va h.k.) ishlatilmoqda — testlar
  faqat o'zi yaratgan Role-{code} yozuvlari bilan ishlaydi.
"""
import re

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_role(page: Page, code, name=None) -> dict:
    """Yangi Роль yaratadi. ``name`` berilmasa Role-{code}. Yaratilgan
    qiymatlarni qaytaradi."""
    m = BasePage(page)
    if name is None:
        name = f"Role-{code}"
    # Порядок ustuni bazada kichik precision'li — 7 xonali qiymatda server
    # "PL/SQL: numeric or value error: number precision too large" qaytaradi
    # (zanjir code'i 7 xonali), 4 xona bilan cheklaymiz
    order_no = str(code)[-4:]

    with allure.step("Навигация: Модератор → Роли"):
        flow_navigate(page, tab="Модератор", name="Роли")
        m.expect_heading("Роли")

    with allure.step("Создать: yangi Роль formasi ochish"):
        m.open_create()
        m.expect_heading("Роль (создание)")

    with allure.step(f"Форма: Название = {name}, Порядок = {order_no}"):
        m.input(label="Название", value=name)
        # Tartib maydoni: prod'da label "Порядок"дан "Порядковый номер"ga o'zgargan
        # — barqaror smtid ishlatamiz (label'ga bog'liq emas).
        m.input(smtid="role-order-no", value=order_no)

    with allure.step("Сохранить va ro'yxatda tekshirish"):
        # Saqlangach redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Роли")
        m.expect_heading("Роли")
        m.search(name)
        m.grid_row(name)

    return {"name": name, "order_no": order_no}


@allure.epic("Модератор")
@allure.feature("Роли")
@allure.story("Создание роли")
@allure.title("Yangi Роль yaratish")
def test_role_create(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_role(page, code)


# ---------------------------------------------------------------------------------------------------


def run_role_minimal(page: Page, code) -> None:
    """Faqat majburiy maydon (Название) bilan yaratish — Порядок to'ldirilmaydi."""
    m = BasePage(page)
    name = f"Role-min-{code}"

    with allure.step("Навигация: Модератор → Роли"):
        flow_navigate(page, tab="Модератор", name="Роли")
        m.expect_heading("Роли")

    with allure.step("Создать: yangi Роль formasi ochish"):
        m.open_create()
        m.expect_heading("Роль (создание)")

    with allure.step(f"Форма (minimal): Название = {name}"):
        m.input(label="Название", value=name)

    with allure.step("Сохранить va ro'yxatda tekshirish"):
        m.save()
        flow_navigate(page, tab="Модератор", name="Роли")
        m.expect_heading("Роли")
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Роли")
@allure.story("Создание роли — минимальные поля")
@allure.title("Рольni minimal maydonlar bilan yaratish")
def test_role_minimal(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_role_minimal(page, code)


# ---------------------------------------------------------------------------------------------------


def run_role_view(page: Page, code) -> None:
    """Yangi rol yaratib, Просмотр formasida qiymatlarni tekshiradi va view
    bo'limlarini (BUTTON: Пользователи, Формы, Продукты, История изменений)
    aylanib chiqadi."""
    m = BasePage(page)
    name = f"Role-view-{code}"

    data = run_role(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Просмотр formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Просмотр")
        # Просмотр biruni forma — stale-heading race'ni oldini olish uchun view URL'ini
        # kutamiz
        page.wait_for_url(re.compile(r"role_view"), timeout=30_000)
        m.settle()
        m.expect_heading("Роль (Просмотр)")

    with allure.step("Qiymatlar: Название/Порядок/Статус view formada ko'rinishi"):
        # PROD'da Просмотр forma maydonlari label-bog'liq smt-input EMAS, oddiy
        # (label'siz) readonly textbox'lar va biruni forma #main-content'да EMAS —
        # qiymatni label bo'yicha ham, #main-content scope bilan ham o'qib bo'lmaydi
        #. Shuning uchun BUTUN page textbox'lari orasidan qidiramiz.
        values = {(tb.input_value() or "").strip()
                  for tb in page.get_by_role("textbox").all()}
        assert data["name"] in values, f"Название '{data['name']}' view'da yo'q: {values}"
        # order_no bazада RAQAM — boshidagi nol yutiladi ('0815'→'815'), shuning uchun
        # int-normallashtirib solishtiramiz (chain code'i leading-zero'li bo'lishi mumkin)
        order_norm = str(int(data["order_no"]))
        assert order_norm in values, f"Порядок '{order_norm}' view'da yo'q: {values}"
        # Статус qiymati til bo'yicha almashadi (ruscha "Активный" ↔ inglizcha "active")
        assert values & {"Активный", "active"}, f"Статус (Активный/active) view'da yo'q: {values}"

    with allure.step("View bo'limlari: Пользователи → Формы → Продукты → История изменений"):
        m.click_button("Пользователи")
        m.click_button("Формы")
        m.click_button("Продукты")
        m.click_button("История изменений")

    with allure.step("Ro'yxatga qaytish"):
        # "Go back" bo'lim almashganda yo'qolishi mumkin (Организация patterni) —
        # unga tayanmay navbar orqali qaytamiz
        flow_navigate(page, tab="Модератор", name="Роли")
        m.expect_heading("Роли")


@allure.epic("Модератор")
@allure.feature("Роли")
@allure.story("Просмотр роли")
@allure.title("Роль ma'lumotlari Просмотр formasida to'g'ri ko'rinishi")
def test_role_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_role_view(page, code)


# ---------------------------------------------------------------------------------------------------


def run_role_edit(page: Page, code) -> None:
    """Yangi rol yaratib, Изменить orqali nomini o'zgartiradi va o'zgarish
    ro'yxatda aks etganini tekshiradi (edit save Просмотр'ga qaytaradi —
    ro'yxatga flow_navigate bilan kiramiz)."""
    m = BasePage(page)
    old_name = f"Role-edit-{code}"
    new_name = f"Role-upd-{code}"

    run_role(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Роль (изменение)")

    with allure.step(f"Tahrirlash: nom {old_name} → {new_name}"):
        m.input(label="Название", value=new_name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save()
        flow_navigate(page, tab="Модератор", name="Роли")
        m.expect_heading("Роли")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        m.expect_no_row(old_name)


@allure.epic("Модератор")
@allure.feature("Роли")
@allure.story("Редактирование роли")
@allure.title("Рольni tahrirlash va o'zgarishni tekshirish")
def test_role_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_role_edit(page, code)


# ---------------------------------------------------------------------------------------------------


def run_role_status(page: Page, code) -> None:
    """Status ikki yo'nalishda tekshiriladi — Изменить formasidagi Статус
    switch orqali (Организация patterni):

    1) Aktiv rol Неактивный qilinadi — default ro'yxatdan yo'qoladi,
       "Показать все"da Неактивный badge bilan ko'rinadi.
    2) Qayta Активный qilinadi — ro'yxatda Активный badge bilan ko'rinadi."""
    m = BasePage(page)
    name = f"Role-stat-{code}"

    run_role(page, code, name=name)

    with allure.step(f"1) '{name}' ni Изменить orqali Неактивный qilish"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.expect_heading("Роль (изменение)")
        m.checkbox(label="Статус", checked=False)
        m.save()

    with allure.step("1) Default ro'yxatda ko'rinmasligini tekshirish"):
        flow_navigate(page, tab="Модератор", name="Роли")
        m.expect_heading("Роли")
        m.search(name)
        m.expect_no_row(name)

    with allure.step("1) Показать все filtrida Неактивный bo'lib ko'rinishi"):
        m.show_all()
        m.grid_row(name, "Неактивный")

    with allure.step(f"2) '{name}' ni qayta Активный qilish"):
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.expect_heading("Роль (изменение)")
        m.checkbox(label="Статус", checked=True)
        m.save()

    with allure.step("2) Ro'yxatda Активный bo'lib ko'rinishini tekshirish"):
        flow_navigate(page, tab="Модератор", name="Роли")
        m.expect_heading("Роли")
        m.search(name)
        m.grid_row(name, "Активный")


@allure.epic("Модератор")
@allure.feature("Роли")
@allure.story("Статус роли")
@allure.title("Роль statusini Неактивный/Активный qilish va tekshirish")
def test_role_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_role_status(page, code)


# ---------------------------------------------------------------------------------------------------


def run_role_delete(page: Page, code) -> None:
    """Yangi rol yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi (confirm dialogi "Да/Нет")."""
    m = BasePage(page)
    name = f"Role-del-{code}"

    run_role(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'Да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        m.expect_no_row(name)


@allure.epic("Модератор")
@allure.feature("Роли")
@allure.story("Удаление роли")
@allure.title("Рольni o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_role_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_role_delete(page, code)


# ---------------------------------------------------------------------------------------------------


def run_role_duplicate(page: Page, code) -> None:
    """Bir xil Название bilan qayta yaratishga urinish xatolik berishini
    tekshiradi — server "dup_val_on_index" (md_roles) Ошибка dialogini
    qaytaradi."""
    m = BasePage(page)
    name = f"Role-dup-{code}"

    run_role(page, code, name=name)

    with allure.step(f"Xuddi shu nom '{name}' bilan qayta yaratishga urinish"):
        m.open_create()
        m.expect_heading("Роль (создание)")
        m.input(label="Название", value=name)
        m.click_button("Сохранить")

    with allure.step("Ошибка dialogi chiqishini tekshirish (dup_val_on_index)"):
        m.expect_error_dialog("dup_val_on_index")

    with allure.step("Dialogni yopish — ochiq dialog navbar'ni to'sib qo'yadi"):
        m.expect_heading("Роль (создание)")

    with allure.step(f"Ro'yxatda '{name}' faqat BITTA ekanini tekshirish"):
        flow_navigate(page, tab="Модератор", name="Роли")
        m.expect_heading("Роли")
        m.search(name)
        m.expect_row_count(name, 1)


@allure.epic("Модератор")
@allure.feature("Роли")
@allure.story("Дубликат роли")
@allure.title("Bir xil nom bilan Роль qayta yaratishda xatolik chiqishi")
def test_role_duplicate(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_role_duplicate(page, code)
