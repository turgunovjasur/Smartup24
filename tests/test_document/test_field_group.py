"""Группа полей (Field group) — CRUD + status + Подтипы (Поля) testlari.

Модератор → Документы → Группа полей (URL: .../moderator/field_group_list).
Loyiha uslubida qayta yozilgan (avval xom Playwright codegen edi: buzuq login
`admin2sm24`, dinamik `#cdk-drop-list-N`/`ng.formN.*` selektorlari, unikal bo'lmagan
nomlar). Endi: authorization/flow_navigate/BasePage/allure, unikal `code` nomlari,
barqaror selektorlar.

Modul xususiyatlari:
- Yaratish tugmasi "Создать" EMAS, **"Добавить"** (exact) — heading "Группа полей (Создания)".
- Forma: Статус switch, Название * (smt-input), Порядковый номер (spinbutton, ixtiyoriy).
- Ro'yxat — standart grid (Название | Порядковый номер | Создал | Статус=Активный/Неактивный).
  Qator paneli: Изменить / Подтипы / Удалить / Изменить статус.
- "Изменить статус" TO'G'RIDAN-TO'G'RI qarama-qarshi statusга o'tkazadi (tasdiqlash "да");
  passiv yozuv default ro'yxatда ko'rinmaydi — "Показать все" kerak.
- Подтипы → "Поля" ro'yxati → "Добавить" → "Поля (Создания)": Название *, Тип поля *
  radio (default "Выпадающий список"; "Текст (строка)" Элементы поля talab qilmaydi).
"""
import re

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage

MENU = "Группа полей"
CREATE_HEADING = "Группа полей (Создания)"


def run_field_group(page: Page, code, name=None, order="50") -> str:
    """Yangi Группа полей yaratadi (Название + ixtiyoriy Порядковый номер) va
    ro'yxatni ``name`` bo'yicha qidirilgan holda qoldiradi. Nomni qaytaradi."""
    m = BasePage(page)
    if name is None:
        name = f"field-group-{code}"

    with allure.step("Навигация: Модератор → Группа полей"):
        flow_navigate(page, tab="Модератор", name=MENU)
        m.expect_heading(MENU)

    with allure.step(f"Добавить: yangi Группа полей formasi ({name})"):
        # DIQQAT: bu modulda yaratish tugmasi "Добавить" (open_create'ning "Создать"i EMAS)
        m.click_button("Добавить", exact=True)
        m.expect_heading(CREATE_HEADING)
        m.input(label="Название", value=name)
        if order is not None:
            m.input(label="Порядковый номер", value=order)

    with allure.step("Сохранить va ro'yxatда tekshirish"):
        # Saqlangach redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name=MENU)
        m.expect_heading(MENU)
        m.search(name)
        m.grid_row(name)

    return name


@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.story("Создание группы полей")
@allure.title("Группа полей yaratish")
def test_field_group_create(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_field_group(page, code)


#---------------------------------------------------------------------------------------------------


def run_field_group_edit(page: Page, code) -> None:
    """Yangi guruh yaratib, Изменить orqali nomini o'zgartiradi va o'zgarishni
    ro'yxatда tekshiradi."""
    m = BasePage(page)
    old_name = f"fg-edit-{code}"
    new_name = f"fg-upd-{code}"

    run_field_group(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        # Edit heading modul bo'yicha tasdiqlanmagan — Название maydonini kutish yetarli
        m.input(label="Название", value=new_name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save()
        flow_navigate(page, tab="Модератор", name=MENU)
        m.expect_heading(MENU)

    with allure.step(f"Ro'yxatда yangi nom '{new_name}' bor, eskisi YO'Q"):
        m.search(new_name)
        m.grid_row(new_name)
        m.search(old_name)
        m.expect_no_row(old_name)


@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.story("Редактирование группы полей")
@allure.title("Группа полейni tahrirlash va o'zgarishni tekshirish")
def test_field_group_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_field_group_edit(page, code)


#---------------------------------------------------------------------------------------------------


def run_field_group_status(page: Page, code) -> None:
    """Status ikki yo'nalishda. Qator paneli MAQSAD status nomidagi TOGGLE tugma
    ko'rsatadi ("Неактивный" — aktiv qatorда; "Активный" — passiv qatorда) +
    tasdiqlash "да" — opros/vizit modullari bilan bir xil ("Изменить статус"
    menyusi EMAS). Aktiv → Неактивный (default ro'yxatдан yo'qoladi, "Показать
    все"да ko'rinadi) → qayta Активный."""
    m = BasePage(page)
    name = f"fg-stat-{code}"

    run_field_group(page, code, name=name)

    with allure.step(f"'{name}' ni Неактивный qilish"):
        m.click_grid_row(name)
        m.click_button("Неактивный")
        m.confirm("да")

    with allure.step("'Показать все'да Неактивный bo'lib ko'rinishi (passiv default yashirin)"):
        # DIQQAT: bu yerда oldin `m.search(name)` + `expect_no_row` bor edi — u
        # grid'ni BO'SHATib qo'yardi, keyingi `show_all` esa bo'sh grid'да filtr
        # tugmasini topolmay buzilardi (jonli run: qator "topilmadi"). run_field_group
        # ro'yxatni allaqachon `name` bo'yicha qidirilgan qoldiradi — to'g'ridan-to'g'ri
        # show_all qilib passiv qatorni ochamiz (opros/vizit status testi bilan bir xil oqim).
        m.show_all()
        m.grid_row(name, "Неактивный")

    with allure.step(f"'{name}' ni qayta Активный qilish"):
        m.click_grid_row(name)
        m.click_button("Активный")
        m.confirm("да")

    with allure.step("Ro'yxatда 'Активный' bo'lib ko'rinishi"):
        m.grid_row(name, "Активный")


@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.story("Статус группы полей")
@allure.title("Группа полей statusini Неактивный/Активный qilish")
def test_field_group_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_field_group_status(page, code)


#---------------------------------------------------------------------------------------------------


def run_field_group_subtypes(page: Page, code) -> None:
    """Guruh yaratib, Подтипы → Поля ro'yxatiga yangi maydon (Поле) qo'shadi:
    Тип поля = "Текст (строка)" (Элементы поля talab qilmaydi) va ro'yxatда
    ko'rinishini tekshiradi."""
    m = BasePage(page)
    group = f"fg-sub-{code}"
    field_name = f"field-{code}"

    run_field_group(page, code, name=group)

    with allure.step(f"'{group}' → Подтипы (Поля ro'yxati)"):
        m.click_grid_row(group)
        m.click_button("Подтипы")
        # DIQQAT (ikki router-outlet): Подтипы field_list'ga o'tsa ham, oldingi
        # Группа полей LIST outlet'i (o'zining "Добавить" tugmasi bilan) darrov
        # yo'q bo'lmaydi. _settle'siz keyingi click_button("Добавить").first aynan
        # STALE guruh-ro'yxat "Добавить"ini bosib, field_group+add (guruh yaratish)
        # formasini ochib yuborardi — heading "Группа полей (Создания)" bo'lib flaky
        # yiqilardi. field_list URL + settle bilan
        # stale outlet yo'qolguncha kutamiz, keyingina to'g'ri "Добавить" bosiladi.
        page.wait_for_url(re.compile(r"field_list"), timeout=30_000)
        m.settle()
        m.expect_heading("Поля")

    with allure.step(f"Добавить: yangi Поле ({field_name}), Тип поля = Текст (строка)"):
        m.click_button("Добавить", exact=True)
        # field-add'ga o'tishni tasdiqlaymiz (agar noto'g'ri/stale "Добавить" bosilsa
        # field_group+add'ga ketardi — bu kutish aniq xato beradi).
        page.wait_for_url(re.compile(r"field%2[Bb]add|field\+add"), timeout=30_000)
        m.settle()
        m.expect_heading("Поля (Создания)")
        m.input(label="Название", value=field_name)
        # "Текст (строка)" — Элементы поля bo'limini talab qilmaydi (Выпадающий список'дан farqli)
        m.radio("Текст (строка)", label="Тип поля")

    with allure.step("Сохранить va Поля ro'yxatда tekshirish"):
        m.save()
        m.expect_heading("Поля")
        m.search(field_name)
        m.grid_row(field_name)


@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.story("Подтипы (Поля)")
@allure.title("Группа полейга Подтипы orqali Поле qo'shish")
def test_field_group_subtypes(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_field_group_subtypes(page, code)


#---------------------------------------------------------------------------------------------------


def run_field_group_delete(page: Page, code) -> None:
    """Yangi guruh yaratib, uni Удалить orqali o'chiradi va ro'yxatдан
    yo'qolganini tekshiradi."""
    m = BasePage(page)
    name = f"fg-del-{code}"

    run_field_group(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatдан yo'qolganini tekshirish"):
        m.search(name)
        m.expect_no_row(name)


@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.story("Удаление группы полей")
@allure.title("Группа полейni o'chirish va ro'yxatдан yo'qolganini tekshirish")
def test_field_group_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_field_group_delete(page, code)


#---------------------------------------------------------------------------------------------------


def run_field_group_required(page: Page, code) -> None:
    """Negativ: majburiy "Название" bo'sh qoldirilib Сохранить bosiladi. Modul JIM
    bloklaydi (dialog YO'Q, redirect YO'Q) — forma create sarlavhasida qoladi va
    yozuv YARATILMAYDI."""
    m = BasePage(page)

    with allure.step("Навигация: Модератор → Группа полей → Добавить"):
        flow_navigate(page, tab="Модератор", name=MENU)
        m.expect_heading(MENU)
        m.click_button("Добавить", exact=True)
        m.expect_heading(CREATE_HEADING)

    with allure.step("Faqat Порядковый номер; majburiy Название bo'sh qoldiriladi"):
        m.input(label="Порядковый номер", value="7")

    with allure.step("Сохранить — save o'TMASLIGI kutiladi (jim blok)"):
        # m.save() ISHLATILMAYDI (jim blokда ataylab exception beradi) — to'g'ridan-to'g'ri tugma
        m.click_button("Сохранить")
        # Xatolik dialogi CHIQMASLIGI kerak (jim blok, dialog EMAS)
        expect(page.locator(".cdk-overlay-container")).not_to_contain_text("Ошибка")
        # Forma create sarlavhasida qoladi — redirect bo'lmadi = yozuv yaratilmadi
        m.expect_heading(CREATE_HEADING)


@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.story("Негативная валидация")
@allure.title("Группа полей: majburiy 'Название' bo'sh bo'lsa saqlash bloklanishi")
def test_field_group_required(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_field_group_required(page, code)


#---------------------------------------------------------------------------------------------------


def run_field_group_duplicate(page: Page, code) -> None:
    """Bir xil nom bilan qayta yaratishга urinish xatolik berishini tekshiradi.
    Nom unikal (sbr_field_groups company_id+name indeksi): saqlashда "Ошибка"
    dialogi chiqadi — matnida "dup_val_on_index".
    Yozuv YARATILMAYDI (ro'yxatда faqat bitta qoladi)."""
    m = BasePage(page)
    name = f"fg-dup-{code}"

    run_field_group(page, code, name=name)

    with allure.step(f"Xuddi shu nom '{name}' bilan qayta yaratishга urinish"):
        m.click_button("Добавить", exact=True)
        m.expect_heading(CREATE_HEADING)
        m.input(label="Название", value=name)
        m.click_button("Сохранить")

    with allure.step("Ошибка dialogi chiqishini tekshirish (nom dublikat)"):
        m.expect_error_dialog("Ошибка", "dup_val_on_index")

    with allure.step("Dialogni yopish — forma ochiq qoladi, yozuv saqlanmagan"):
        m.expect_heading(CREATE_HEADING)

    with allure.step(f"Ro'yxatда '{name}' faqat BITTA ekanini tekshirish"):
        flow_navigate(page, tab="Модератор", name=MENU)
        m.expect_heading(MENU)
        m.search(name)
        m.expect_row_count(name, 1)


@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.story("Дубликат группы полей")
@allure.title("Bir xil nom bilan Группа полей qayta yaratishда xatolik chiqishi")
def test_field_group_duplicate(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_field_group_duplicate(page, code)
