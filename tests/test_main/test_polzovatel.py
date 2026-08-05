"""Пользователи — CRUD testlari.

DIQQAT: Пользователи moduli IKKI joyda bor (MCP tasdiqlangan 2026-07-23, dev sm24):
- Модератор → Пользователи  =  person/user_list — bu yerда yaratilgan user sb
  proyekt filialiga AVTOMATIK biriktiriladi (sbr_users_f1) va O'CHIRIB BO'LMAYDI
  ("child record found" Ошибка).
- Модератор → Роли → yonidagi "Пользователи" LINK  =  biruni/md/user_list — to'liq
  CRUD shu yerда: qator tanlanganda Просмотреть / Изменить / Удалить / "Изменить
  статус" / "Прикрепление доступов" chiqadi. Bu yerда yaratilgan user sb proyektga
  biriktirilmaydi va O'CHIRILADI. User talabi: status/o'chirish aynan shu
  "roldan yonidagi Пользователи"дан qilinadi — shuning uchun BUTUN CRUD shu
  ro'yxatда.

Muhim jihatlar:
- Yaratish majburiy maydonlari: Название (ФИО emas!), Логин, Пароль. Телефon bu
  formada majburiy EMAS. Barcha inputlar sahifa ochilganda readonly (autofill
  himoyasi) — FOCUS qilinganda tahrirlanadi; BasePage.input avval click qilib
  keyin fill qilgani uchun ishlaydi. To'liq login = "<Логин>@sm24".
- Sarlavhalar: "Пользователь (создание)" / "Пользователь (изменение)" /
  "Пользователь (просмотр)" (biruni/md — kichik harf bilan).
- Ro'yxatда qidiruv Название (ФИО) bo'yicha ishlaydi. Passiv (Неактивный) user
  default yashirin — "Показать все" (show_all) bilan ko'rinadi.
- Статус: qatorni tanlab "Изменить статус" → tasdiqlash "Да" (Активный↔Неактивный
  TOGGLE, alohida menyu emas). O'chirish: "Удалить" → tasdiqlash "Да".
"""
import time

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def _goto_users(m: BasePage, page: Page) -> None:
    """Модератор → Роли → yonidagi "Пользователи" link (biruni/md/user_list —
    to'liq CRUD ro'yxati)."""
    flow_navigate(page, tab="Модератор", name="Роли")
    m.expect_heading("Роли")
    m.click_link("Пользователи")
    m.expect_heading("Пользователи")


def run_user(page: Page, code, name=None) -> dict:
    """Yangi Пользователь yaratadi (majburiy: Название, Логин, Пароль). Yaratilgan
    qiymatlarni qaytaradi."""
    m = BasePage(page)
    if name is None:
        name = f"User-{code}"
    login = name.lower()

    with allure.step("Навигация: Модератор → Роли → Пользователи"):
        _goto_users(m, page)

    with allure.step("Создать: yangi Пользователь formasi ochish"):
        m.open_create()
        m.expect_heading("Пользователь (создание)")

    with allure.step(f"Форма: Название={name}, Логин={login}, Пароль"):
        m.input(label="Название", value=name)
        # Логин/Пароль sahifa ochilganda readonly — input() avval click (focus)
        # qilib readonly'ni ochadi, keyin fill qiladi
        m.input(label="Логин", value=login)
        m.input(label="Пароль", value="1")

    with allure.step("Сохранить va ro'yxatda tekshirish"):
        # Redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()
        _goto_users(m, page)
        m.search(name)
        m.grid_row(name)

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


def run_user_full(page: Page, code) -> None:
    """Пользовательni ixtiyoriy maydonlar bilan ham yaratadi: Пол (Женский),
    Код, Эл. адрес."""
    m = BasePage(page)
    name = f"User-full-{code}"
    login = name.lower()

    with allure.step("Навигация: Модератор → Роли → Пользователи"):
        _goto_users(m, page)

    with allure.step("Создать: yangi Пользователь formasi ochish"):
        m.open_create()
        m.expect_heading("Пользователь (создание)")

    with allure.step(f"Форма (to'liq): {name}"):
        m.input(label="Название", value=name)
        m.input(label="Логин", value=login)
        m.input(label="Пароль", value="1")
        m.input(label="Код", value=f"code-{code}")
        m.input(label="Эл. адрес", value=f"{login}@example.com")
        m.radio("Женский", label="Пол")

    with allure.step("Сохранить va ro'yxatda tekshirish"):
        m.save()
        _goto_users(m, page)
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.story("Создание пользователя — все поля")
@allure.title("Пользовательni barcha maydonlar bilan yaratish")
def test_user_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_user_full(page, code)


# ---------------------------------------------------------------------------------------------------


def run_user_view(page: Page, code) -> None:
    """Yangi user yaratib, Просмотреть formasi ochilishini tekshiradi (view
    formasi qiymatlarni oddiy inputда ko'rsatmaydi — sarlavha tekshiriladi)."""
    m = BasePage(page)
    name = f"User-view-{code}"

    run_user(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Просмотреть formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Просмотреть")
        m.expect_heading("Пользователь (просмотр)")

    with allure.step("Ro'yxatga qaytish"):
        _goto_users(m, page)


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.story("Просмотр пользователя")
@allure.title("Пользователь Просмотреть formasi ochilishi")
def test_user_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_user_view(page, code)


# ---------------------------------------------------------------------------------------------------


def run_user_edit(page: Page, code) -> None:
    """Yangi user yaratib, Изменить orqali Название ni o'zgartiradi va o'zgarish
    ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"User-edit-{code}"
    new_name = f"User-upd-{code}"

    run_user(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Пользователь (изменение)")

    with allure.step(f"Tahrirlash: Название {old_name} → {new_name}"):
        m.input(label="Название", value=new_name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save()
        _goto_users(m, page)

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
    """Yangi user yaratib, "Изменить статус" bilan Активный → Неактивный qiladi
    (toggle, tasdiqlash "Да") va passiv holatda ko'rinishini tekshiradi."""
    m = BasePage(page)
    name = f"User-stat-{code}"

    run_user(page, code, name=name)

    with allure.step(f"'{name}' ni tanlab 'Изменить статус' → Неактивный"):
        m.click_grid_row(name)
        m.click_button("Изменить статус")
        m.confirm("да")

    with allure.step("Default ro'yxatda ko'rinmasligini tekshirish (passiv yashirin)"):
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(0)

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
    ro'yxatdan yo'qolganini tekshiradi. biruni/md'да yaratilgan user sb proyektga
    biriktirilmagani uchun o'chadi (person'дагиси o'chmasdi)."""
    m = BasePage(page)
    name = f"User-del-{code}"

    run_user(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'Да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(0)


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.story("Удаление пользователя")
@allure.title("Пользовательni o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_user_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_user_delete(page, code)


# ---------------------------------------------------------------------------------------------------


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.story("Полный CRUD цикл")
@allure.title("Пользователь: barcha CRUD testlari — bitta seansda zanjir")
def test_user_all(page: Page, code) -> None:
    """Barcha Пользователь testlarini bitta login bilan ketma-ket ishga tushiradi
    (test_role_all patterni)."""
    # Bir sessiyada individual testlar bilan nom to'qnashmasligi uchun zanjir
    # o'z code'i bilan ishlaydi
    code = str(int(time.time()))[-7:]
    with allure.step("Tizimga kirish"):
        authorization(page)

    with allure.step("1. Создание"):
        run_user(page, code)

    with allure.step("2. Создание — barcha maydonlar"):
        run_user_full(page, code)

    with allure.step("3. Просмотр"):
        run_user_view(page, code)

    with allure.step("4. Редактирование"):
        run_user_edit(page, code)

    with allure.step("5. Статус — Неактивный"):
        run_user_status(page, code)

    with allure.step("6. Удаление"):
        run_user_delete(page, code)
