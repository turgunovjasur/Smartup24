"""Опросник — to'liq CRUD regression testlari.

Basic create (run_oprosniki/test_oprosniki) tests/test_setup/test_oprosniki.py
da turadi — bu yerda faqat CRUD ssenariylari: full create, edit, view, delete,
status, duplicate, savol biriktirish/ajratish.

Modul xususiyatlari:
- Forma: Название* (smtid=name), Дата начала* (smt-date-picker smtid=start_date,
  MAJBURIY), Конец* (smtid=end_date, MAJBURIY), Родительский набор
  (smt-data-select smtid=parent_id), Описание (smt-textarea smtid=description),
  Статус switch.
- Qator paneli: Просмотр / Изменить / Удалить / Прикрепление вопросов /
  Установить порядок вопросов / Неактивный|Активный (status toggle + "Да"
  tasdiqlash).
- Grid statuslari INGLIZCHA kichik harfda: "active"/"passive"; passiv qator
  default ro'yxatda KO'RINMAYDI — "Показать все" kerak.
- Просмотр formasi readonly smtid'lar bilan: qsv_name, qsv_state (ruscha
  "Активный"), qsv_start_date, qsv_end_date, qsv_description,
  qsv_parent_quiz_set_name; bo'limlar: Основное/Вопросы/История.
- Dublikat nom XATOLIK beradi: "Ошибка ... dup_val_on_index" dialogi (Закрыть).
- Savoli biriktirilgan опросникни O'CHIRIB BO'LMAYDI: "Ошибка ... child record
  found" — avval Открепить kerak.
- Прикрепление вопросов: tablar "Прикрепленные" (default) / "Доступные";
  savol qatori [role=checkbox] bilan tanlanadi → "Прикрепить N" → "Да";
  biriktirilgan qator bosilsa "Открепить" tugmasi chiqadi → "Да".
"""

import re

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_regression.test_vaprost import run_vaprost_basic
from tests.test_setup.test_oprosniki import OPROS_END, OPROS_START, run_oprosniki
from utils.base_page import BasePage

# Biriktirish testi uchun savol seansda BIR MARTA yaratiladi
_question_ready = set()


def ensure_question(page: Page, code) -> str:
    """Biriktirish testlari uchun savolni seansda bir marta yaratadi.

    Nom ataylab ALOHIDA (vaprost-attach-{code}): run_vaprost'ning default
    Vaprost{code} nomi zanjirdagi "10. Вопрос" qadami yoki alohida
    test_vaprost bilan bir seansda to'qnashib dup_val_on_index dialogi
    chiqarardi."""
    name = f"vaprost-attach-{code}"
    if code not in _question_ready:
        run_vaprost_basic(page, code, name=name)
        _question_ready.add(code)
    return name


def run_oprosniki_basic(page: Page, code, name=None) -> str:
    """CRUD testlari uchun yengil tayyorlov: majburiy maydonlar (Название,
    Дата начала, Конец) bilan опросник yaratadi. Ro'yxatni ``name`` bo'yicha
    qidirilgan holda qoldiradi."""
    m = BasePage(page)
    if name is None:
        name = f"oprosniki-basic-{code}"

    with allure.step(f"Tayyorlov: '{name}' опросник yaratish"):
        flow_navigate(page, tab="Модератор", name="Опросники")
        m.expect_heading("Опросники")
        m.open_create()
        m.expect_heading("Опросник (Создание)")
        m.input(label="Название", value=name)
        m.input(label="Дата начала", value=OPROS_START)
        m.input(label="Конец", value=OPROS_END)
        # Redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Опросники")
        m.expect_heading("Опросники")
        m.search(name)
        m.grid_row(name)

    return name


def run_oprosniki_full(page: Page, code) -> None:
    """Опросник formasining BARCHA to'ldiriladigan maydonlari bilan yaratish:
    Название, Дата начала, Конец, Родительский набор, Описание, Статус switch.
    Родительский набор uchun avval alohida опросник yaratiladi. Saqlangach
    qiymatlar Просмотр formasida (readonly qsv_* inputlar) tekshiriladi."""
    m = BasePage(page)
    name = f"oprosniki-full-{code}"
    parent = run_oprosniki_basic(page, code, name=f"oprs-parent-{code}")

    with allure.step("Навигация: Модератор → Опросники"):
        flow_navigate(page, tab="Модератор", name="Опросники")
        m.expect_heading("Опросники")

    with allure.step("Создать: yangi Опросник formasi ochish"):
        m.open_create()
        m.expect_heading("Опросник (Создание)")

    with allure.step(f"Форма: barcha maydonlar ({name}, Родительский = {parent})"):
        m.input(label="Название", value=name)
        m.input(label="Дата начала", value=OPROS_START)
        m.input(label="Конец", value=OPROS_END)
        m.select(parent, label="Родительский набор")
        m.input(label="Описание", value=f"Avto-test опросник izohi {code}")
        m.checkbox(label="Статус", checked=True)

    with allure.step("Сохранить"):
        # Redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Ro'yxatda '{name}' 'active' bo'lib ko'rinishi"):
        flow_navigate(page, tab="Модератор", name="Опросники")
        m.expect_heading("Опросники")
        m.search(name)
        m.grid_row(name, "active")

    with allure.step("Просмотр formasida saqlangan qiymatlar to'g'riligi"):
        m.click_grid_row(name)
        m.click_button("Просмотр")
        m.expect_heading("Опросник (Просмотр)")
        m.input(smtid="qsv_name", expect_value=name)
        m.input(smtid="qsv_state", expect_value="Активный")
        m.input(smtid="qsv_start_date", expect_value=OPROS_START)
        m.input(smtid="qsv_end_date", expect_value=OPROS_END)
        m.input(smtid="qsv_parent_quiz_set_name", expect_value=parent)
        m.input(smtid="qsv_description", expect_value=f"Avto-test опросник izohi {code}")

    with allure.step("Ro'yxatga qaytish"):
        flow_navigate(page, tab="Модератор", name="Опросники")
        m.expect_heading("Опросники")


@allure.epic("Модератор")
@allure.feature("Опросники")
@allure.story("Создание опросника — все поля")
@allure.title("Опросникни BARCHA maydonlar bilan yaratish")
def test_oprosniki_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_oprosniki_full(page, code)


#---------------------------------------------------------------------------------------------------


def run_oprosniki_edit(page: Page, code) -> None:
    """Yangi опросник yaratib, Изменить orqali tahrirlaydi va o'zgarish
    ro'yxatda aks etganini tekshiradi."""
    m = BasePage(page)
    old_name = f"oprosniki-edit-{code}"
    new_name = f"oprosniki-upd-{code}"

    run_oprosniki_basic(page, code, name=old_name)

    with allure.step(f"'{old_name}' qatorini tanlab Изменить formasini ochish"):
        m.click_grid_row(old_name)
        m.click_button("Изменить")
        m.expect_heading("Опросник (Редактирование)")

    with allure.step(f"Tahrirlash: nom {old_name} → {new_name}, Описание"):
        m.input(label="Название", value=new_name)
        m.input(label="Описание", value=f"Tahrirlangan izoh {code}")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        # Edit'dan keyin ham redirect barqaror emas — ro'yxatga o'zimiz kiramiz
        m.save()
        flow_navigate(page, tab="Модератор", name="Опросники")
        m.expect_heading("Опросники")

    with allure.step(f"Ro'yxatda yangi nom '{new_name}' bor"):
        m.search(new_name)
        m.grid_row(new_name)

    with allure.step(f"Eski nom '{old_name}' ro'yxatda YO'Q"):
        m.search(old_name)
        m.expect_no_row(old_name)


@allure.epic("Модератор")
@allure.feature("Опросники")
@allure.story("Редактирование опросника")
@allure.title("Опросникни tahrirlash va o'zgarishni tekshirish")
def test_oprosniki_edit(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_oprosniki_edit(page, code)


#---------------------------------------------------------------------------------------------------


def run_oprosniki_view(page: Page, code) -> None:
    """Yangi опросник yaratib, Просмотр formasida qiymatlar to'g'ri
    ko'rsatilishini tekshiradi."""
    m = BasePage(page)
    name = f"oprosniki-view-{code}"

    run_oprosniki_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Просмотр formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Просмотр")
        m.expect_heading("Опросник (Просмотр)")

    with allure.step("Qiymatlar: Название, Статус, Дата начала, Конец"):
        m.input(smtid="qsv_name", expect_value=name)
        m.input(smtid="qsv_state", expect_value="Активный")
        m.input(smtid="qsv_start_date", expect_value=OPROS_START)
        m.input(smtid="qsv_end_date", expect_value=OPROS_END)

    with allure.step("Ro'yxatga qaytish"):
        flow_navigate(page, tab="Модератор", name="Опросники")
        m.expect_heading("Опросники")


@allure.epic("Модератор")
@allure.feature("Опросники")
@allure.story("Просмотр опросника")
@allure.title("Опросник ma'lumotlari Просмотр formasida to'g'ri ko'rinishi")
def test_oprosniki_view(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_oprosniki_view(page, code)


#---------------------------------------------------------------------------------------------------


def run_oprosniki_delete(page: Page, code) -> None:
    """Yangi опросник yaratib, uni Удалить orqali o'chiradi va ro'yxatdan
    yo'qolganini tekshiradi (savol biriktirilmagan — o'chirish muvaffaqiyatli;
    biriktirilgani bilan salbiy holat run_oprosniki_attach da tekshiriladi)."""
    m = BasePage(page)
    name = f"oprosniki-del-{code}"

    run_oprosniki_basic(page, code, name=name)

    with allure.step(f"'{name}' qatorini tanlab Удалить bosish"):
        m.click_grid_row(name)
        m.click_button("Удалить")

    with allure.step("Tasdiqlash dialogida 'да' bosish"):
        m.confirm("да")

    with allure.step(f"'{name}' ro'yxatdan yo'qolganini tekshirish"):
        m.search(name)
        m.expect_no_row(name)


@allure.epic("Модератор")
@allure.feature("Опросники")
@allure.story("Удаление опросника")
@allure.title("Опросникни o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_oprosniki_delete(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_oprosniki_delete(page, code)


#---------------------------------------------------------------------------------------------------


def run_oprosniki_status(page: Page, code) -> None:
    """Status toggle tugmasi orqali o'zgartiriladi (tugma nomi MAQSAD statusi,
    tasdiqlash "Да"). Passiv опросник default ro'yxatdan YO'QOLADI, "Показать
    все" filtrida "passive" bo'lib ko'rinadi."""
    m = BasePage(page)
    name = f"oprosniki-stat-{code}"

    run_oprosniki_basic(page, code, name=name)

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
@allure.feature("Опросники")
@allure.story("Статус опросника")
@allure.title("Опросник statusini Неактивный/Активный qilish va tekshirish")
def test_oprosniki_status(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_oprosniki_status(page, code)


#---------------------------------------------------------------------------------------------------


def run_oprosniki_duplicate(page: Page, code) -> None:
    """Bir xil nom bilan qayta yaratishga urinish xatolik berishini tekshiradi.

    Опросник nomi unikal: saqlashda "Ошибка" dialogi chiqadi — matnida
    "dup_val_on_index"."""
    m = BasePage(page)
    name = f"oprosniki-dup-{code}"

    run_oprosniki_basic(page, code, name=name)

    with allure.step(f"Xuddi shu nom '{name}' bilan qayta yaratishga urinish"):
        m.open_create()
        m.expect_heading("Опросник (Создание)")
        m.input(label="Название", value=name)
        m.input(label="Дата начала", value=OPROS_START)
        m.input(label="Конец", value=OPROS_END)
        m.click_button("Сохранить")

    with allure.step("Ошибка dialogi chiqishini tekshirish (nom dublikat)"):
        m.expect_error_dialog("Ошибка", "dup_val_on_index")

    with allure.step("Dialogni yopish — forma ochiq qoladi, yozuv saqlanmagan"):
        m.expect_heading("Опросник (Создание)")

    with allure.step(f"Ro'yxatda '{name}' faqat BITTA ekanini tekshirish"):
        flow_navigate(page, tab="Модератор", name="Опросники")
        m.expect_heading("Опросники")
        m.search(name)
        m.expect_row_count(name, 1)


@allure.epic("Модератор")
@allure.feature("Опросники")
@allure.story("Дубликат опросника")
@allure.title("Bir xil nom bilan Опросник qayta yaratishda xatolik chiqishi")
def test_oprosniki_duplicate(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_oprosniki_duplicate(page, code)


#---------------------------------------------------------------------------------------------------


def run_oprosniki_attach(page: Page, code) -> None:
    """Savolni опросникка biriktirish/ajratish to'liq sikli:

    1) Savol biriktiriladi: Прикрепление вопросов → Доступные tab →
       qator [role=checkbox] → "Прикрепить 1" → "Да" → Прикрепленные tabда
       ko'rinadi.
    2) Salbiy holat: savoli biriktirilgan опросникни o'chirishga urinish —
       "Ошибка ... child record found" dialogi chiqadi, yozuv o'chmaydi.
    3) Savol ajratiladi (Открепить → "Да") va опросник endi o'chiriladi."""
    m = BasePage(page)
    name = f"oprosniki-attach-{code}"
    question = ensure_question(page, code)

    run_oprosniki_basic(page, code, name=name)

    with allure.step(f"'{name}' uchun Прикрепление вопросов formasini ochish"):
        m.click_grid_row(name)
        m.click_button("Прикрепление вопросов")
        m.expect_heading("Опросник (прикрепление вопросов)")

    with allure.step(f"Доступные tabда '{question}' ni tanlab biriktirish"):
        # DIQQAT: ilova bu tab nomini IKKI UI versiyasi orasida FLIP
        # qiladi — yangi "Доступные" ↔ eski "Неприкреплённые" (аттач tab: "Прикрепленные"
        # ↔ "Прикреплённые"). Bir run'да "Доступные", boshqasida "Неприкреплённые"
        # chiqadi (SANA emas, server UI-holatiga bog'liq flip) — ikkalasini ham qabul
        # qilamiz, aks holda test beqaror yiqiladi.
        m.click_button(re.compile(r"^(?:Доступные|Неприкреплённые)$"))
        row = m.grid_row(question)
        row.locator("[role=checkbox]").first.click()
        # UI tugma nomi ilova versiyalari orasida almashadi: "Прикрепить 1" (qavssiz,
        # 2026-07-31) ↔ "Прикрепить (1)" — ikkalasini
        # ham qabul qiladigan regex (UI yana almashsa ham chidasin).
        m.click_button(re.compile(r"^Прикрепить\s*\(?1\)?$"))
        m.confirm("да")

    with allure.step("Прикрепленные tabда savol ko'rinishini tekshirish"):
        # yangi "Прикрепленные" (е) ↔ eski "Прикреплённые" (ё) — ikkalasini qabul qilamiz
        m.click_button(re.compile(r"^Прикрепл[её]нные$"))
        m.grid_row(question)

    with allure.step("Salbiy holat: savolli опросникни o'chirish TAQIQLANGAN"):
        flow_navigate(page, tab="Модератор", name="Опросники")
        m.expect_heading("Опросники")
        m.search(name)
        m.click_grid_row(name)
        m.click_button("Удалить")
        m.confirm("да")
        m.expect_error_dialog("Ошибка", "child record found")
        m.grid_row(name)

    with allure.step(f"'{question}' ni ajratish (Открепить)"):
        # Ошибка dialogidan keyin qator tanlovi noaniq holatda qoladi (tanlangan
        # bo'lsa qayta bosish tanlovni BEKOR qiladi) — ro'yxatga yangidan kirib
        # toza holatdan boshlaymiz.
        flow_navigate(page, tab="Модератор", name="Опросники")
        m.expect_heading("Опросники")
        m.search(name)
        m.click_grid_row(name)
        m.click_button("Прикрепление вопросов")
        m.expect_heading("Опросник (прикрепление вопросов)")
        m.click_grid_row(question)
        m.click_button("Открепить")
        m.confirm("да")
        m.expect_no_row(question)

    with allure.step(f"Endi '{name}' muvaffaqiyatli o'chiriladi"):
        flow_navigate(page, tab="Модератор", name="Опросники")
        m.expect_heading("Опросники")
        m.search(name)
        m.click_grid_row(name)
        m.click_button("Удалить")
        m.confirm("да")
        m.expect_no_row(name)


@allure.epic("Модератор")
@allure.feature("Опросники")
@allure.story("Прикрепление вопросов")
@allure.title("Опросникка savol biriktirish, ajratish va o'chirish cheklovi")
def test_oprosniki_attach(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_oprosniki_attach(page, code)
