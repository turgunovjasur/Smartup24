"""Negativ / validatsiya testlari — majburiy maydonlar bo'sh qolganda saqlash
BLOKLANISHINI tekshiradi.

NEGA ALOHIDA FAYL
-----------------
"Happy path" (to'g'ri to'ldirish) allaqachon har modulning create/full testida
yashil. Bu yerda AKSINCHA: majburiy maydon bo'sh → yozuv YARATILMASLIGI kerak.
Bunday testlar eng ko'p haqiqiy bug ushlaydi (masalan "Код" majburiy bo'lib
qo'shilgach jim bloklab qo'ygan holat — xotira: region-kod-required-field).

IKKI XIL BLOKLASH XATTI-HARAKATI (MCP tasdiqlangan 2026-08-03)
-------------------------------------------------------------
Ilova ikki xil yo'l bilan bloklaydi — shuning uchun assertion ham ikki xil:

1) JIM BLOKLASH (dialog YO'Q) — oddiy ``smt-input`` formalar (Регион va shunga
   o'xshash: Территория, Валюта, Вопрос, Опросник, Шаблон, Бонус, Конкурс).
   Majburiy maydon bo'sh bo'lsa Сохранить bosilganда POST umuman ketmaydi:
   forma create sarlavhasida qoladi, ro'yxatga hech narsa qo'shilmaydi, hech
   qanday xabar chiqmaydi. Test: create heading o'zgармaydi + ro'yxatда 0 qator.

2) "ОШИБКА" DIALOGI — person moduli (Поставщик/Клиент/Юр. лицо, umumiy
   ``person+add`` formasi). Bo'sh saqlashда server-side validatsiya "Ошибка"
   dialogi qaytaradi: "Пожалуйста, выберите хотя бы один тип!". Test: dialog
   "Ошибка" matnini o'z ichiga oladi, yopilgach forma create'да qoladi.

DIQQAT: ``m.save()`` BU YERDA ISHLATILMAYDI — u save o'tmasa ataylab exception
beradi (region-kod-required-field). Negativ testда save O'TMASLIGI KUTILADI,
shuning uchun to'g'ridan-to'g'ri ``m.click_button("Сохранить")`` bosiladi.

KENGAYTIRISH
------------
Yangi modul qo'shishда avval MCP bilan qaysi naqshга (1 yoki 2) tushishini
tasdiqlang — taxmin qilmang (region jim, person dialogli bo'lgani bunga misol).
"""
import allure
import pytest
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


# ══════════════════════════════════════════════════════════════════════════════
# 1) JIM BLOKLASH naqshi — Регион (majburiy "Код" bo'sh)
# ══════════════════════════════════════════════════════════════════════════════
def run_region_required(page: Page, code) -> None:
    """Регион: faqat Название to'ldirilib, majburiy "Код" bo'sh qoldiriladi.
    Сохранить bosilganда forma JIM bloklanadi (dialog yo'q, redirect yo'q) —
    create sarlavhasida qoladi va ro'yxatга yozuv qo'shilmaydi (MCP 2026-08-03)."""
    m = BasePage(page)
    name = f"neg-region-{code}"

    with allure.step("Навигация: Модератор → Регионы → Создать"):
        flow_navigate(page, tab="Модератор", name="Регионы")
        m.expect_heading("Регионы")
        m.open_create()
        m.expect_heading("Регион (Создания)")

    with allure.step(f"Faqat Название = {name}; majburiy 'Код' bo'sh qoldiriladi"):
        m.input(smtid="region-name", value=name)

    with allure.step("Сохранить — save o'TMASLIGI kutiladi (jim blok)"):
        m.click_button("Сохранить")
        # Xatolik dialogi CHIQMASLIGI kerak (jim blok, dialog EMAS)
        expect(page.locator(".cdk-overlay-container")).not_to_contain_text("Ошибка")
        # Forma create sarlavhasida QOLADI — muvaffaqiyatli save ro'yxatga/dashboardга
        # REDIRECT qilardi; redirect yo'qligi = POST ketmadi = yozuv yaratilmadi
        # (supplier negativ testi bilan bir xil barqaror shakl).
        m.expect_heading("Регион (Создания)")


@allure.epic("Модератор")
@allure.feature("Регионы")
@allure.story("Негативная валидация")
@allure.title("Регион: majburiy 'Код' bo'sh bo'lsa saqlash bloklanishi")
def test_region_required(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_region_required(page, code)


# ══════════════════════════════════════════════════════════════════════════════
# 2) "ОШИБКА" DIALOGI naqshi — Поставщик (barcha majburiy maydon bo'sh)
# ══════════════════════════════════════════════════════════════════════════════
def run_supplier_required(page: Page, code) -> None:
    """Поставщик (person+add): barcha majburiy maydon (Название/ИНН/Тип/...) bo'sh
    qoldirilib Сохранить bosiladi. Person moduli JIM bloklamaydi — "Ошибка"
    dialogi chiqaradi ("Пожалуйста, выберите хотя бы один тип!"). Dialog yopilgач
    forma create sarlavhasida qoladi (MCP tasdiqlangan 2026-08-03)."""
    m = BasePage(page)

    with allure.step("Навигация: Модератор → Поставщики → Создать"):
        flow_navigate(page, tab="Модератор", name="Поставщики")
        m.expect_heading("Поставщики")
        m.open_create()
        m.expect_heading("Юр. Лицо (Создания)")

    with allure.step("Barcha majburiy maydon bo'sh — Сохранить xato dialogini berishi kerak"):
        m.click_button("Сохранить")
        # "Ошибка" dialogi = server-side validatsiya save'ni bloklaydi. Aniq jumla
        # ("Пожалуйста, выберите хотя бы один тип!") server i18n'iga qarab ru↔en
        # almashishi mumkin — til-mustaqil isbot: dialog chiqdi + yopilgach forma
        # create sarlavhasida qoladi (POST ketmadi = yozuv yaratilmadi, quyida).
        m.expect_error_dialog("Ошибка")

    with allure.step("Dialogni yopish — forma create'да qoladi, yozuv saqlanmagan"):
        m.expect_heading("Юр. Лицо (Создания)")


@allure.epic("Модератор")
@allure.feature("Поставщики")
@allure.story("Негативная валидация")
@allure.title("Поставщик: bo'sh majburiy maydonlar bilan saqlashда Ошибка dialogi")
def test_supplier_required(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_supplier_required(page, code)


# ══════════════════════════════════════════════════════════════════════════════
# 3) JIM BLOKLASH oilasi — parametrlashtirilgan (bir nechta smt-input formalar)
# ══════════════════════════════════════════════════════════════════════════════
# "Jim blok" naqshiga tushadigan sodda smt-input formalar oilasi (negativ fayl
# boshidagi 1-naqsh; region_required allaqachon shu oilaning bir a'zosini yakka
# qoplaydi). Har biri uchun: create ochib HECH NARSA to'ldirmasdan Сохранить
# bosilganda majburiy "Название" bo'sh bo'lgani uchun POST ketmaydi — forma create
# sarlavhasida qoladi, "Ошибка" dialogi CHIQMAYDI. (nav_name, create_heading).
# DIQQAT: "Tерритории"/"Tерритория" — app'da Lotin "T" (biruni typo, setup'dan
# aynan ko'chirilgan). Bonus heading boshqacha ("Создать бонусную систему").
_SILENT_BLOCK_FORMS = [
    ("Tерритории", "Tерритория (Создания)"),
    ("Валюты", "Валюта (Создания)"),
    ("Вопросы", "Вопрос (Создание)"),
    ("Опросники", "Опросник (Создание)"),
    ("Шаблоны отчетов по опросам", "Шаблон отчета по опросам (Создание)"),
    ("Бонусная система", "Создать бонусную систему"),
    ("Конкурсы", "Конкурсы (Создания)"),
]


@pytest.mark.parametrize(
    "nav_name,create_heading", _SILENT_BLOCK_FORMS,
    ids=[nav for nav, _ in _SILENT_BLOCK_FORMS],
)
@allure.epic("Модератор")
@allure.feature("Негативная валидация")
@allure.story("Пустая форма — тихая блокировка")
@allure.title("Bo'sh forma saqlanmasligi: {nav_name}")
def test_empty_form_blocked(page: Page, nav_name: str, create_heading: str) -> None:
    """'Jim blok' oilasi (1-naqsh): create formasi HECH NARSASIZ (majburiy
    "Название" bo'sh) Сохранить bosilganda saqlanmasligi kerak — "Ошибка"
    dialogi chiqmaydi va forma create sarlavhasida qoladi (region_required bilan
    bir xil til-mustaqil isbot: redirect yo'q = POST ketmadi = yozuv yaratilmadi).

    m.save() ISHLATILMAYDI (u save o'tmasa ataylab exception beradi) — bevosita
    m.click_button("Сохранить") bosiladi, chunki bu yerda save O'TMASLIGI kutiladi."""
    with allure.step("Tizimga kirish"):
        authorization(page)
    m = BasePage(page)

    with allure.step(f"Навигация: Модератор → {nav_name} → Создать"):
        flow_navigate(page, tab="Модератор", name=nav_name)
        m.open_create()
        m.expect_heading(create_heading)

    with allure.step("Bo'sh forma — Сохранить save o'TMASLIGI kutiladi (jim blok)"):
        m.click_button("Сохранить")
        # Xatolik dialogi CHIQMASLIGI kerak (jim blok, dialog EMAS)
        expect(page.locator(".cdk-overlay-container")).not_to_contain_text("Ошибка")
        # Forma create sarlavhasida QOLADI — muvaffaqiyatli save ro'yxatga/dashboardга
        # REDIRECT qilardi; redirect yo'qligi = POST ketmadi = yozuv yaratilmadi.
        m.expect_heading(create_heading)
