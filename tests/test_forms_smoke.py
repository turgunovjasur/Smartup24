"""Smartup24 formalari ochilish smoke testi (FAQAT Модератор oynasi).

Maqsad: **Модератор** menyusidagi HAR BIR formani ochib, forma to'g'ri
yuklanganini (aktiv sarlavha paydo bo'lishi) va ochilishda xato chiqmasligini
tekshirish. Har forma ALOHIDA test (pytest parametrize) — Allure/pytest'da 33 ta
test bo'lib ko'rinadi, qaysi forma yiqilsa aniq bilinadi.

DIZAYN (setup/main runnerlari bilan bir xil): **bitta seans / bitta login**.
Barcha testlar session-scope ``session_page`` fixture'ini oladi — butun fayl
uchun YAGONA browser+context+page. ``test_000_login`` bir marta admin bilan
kiradi, keyingi ``test_form_*`` testlari o'sha seansni ishlatadi (33 marta qayta
login QILINMAYDI — sekin bo'lardi va parallel-seans limitiga urardi).

DIQQAT: test faqat Модератор bo'limini qamraydi. Поставщик/Клиент tab'lari admin
sifatida ochilganda sessiya-qulf overlay'i navbar'ni to'sib flaky timeout beradi
(2026-09-18 tekshiruvi) — u bo'limlar o'z rollari bilan alohida testlarda ochiladi.

Bu test MUSTAQIL — mavjud testlarga (test_all va h.k.) aralashmaydi.
Formalar ro'yxati MCP bilan real menyudan aniqlangan.
"""
import re

import allure
import pytest
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from utils.base_page import BasePage, HEADING


# Модератор menyusidagi barcha formalar (Главное / Продажи / Справочники / Документы)
MODERATOR_FORMS = [
    # Главное ("Настройки шаблонов" 2026-09-18 da qo'shildi — Шаблоны отчетов bilan bir
    # listitem ichidagi ALOHIDA forma, "(создание)" create emas; MCP'da tasdiqlangan,
    # setting+add sahifasini ochadi, sarlavha "Настройки шаблонов")
    "Организации", "Роли", "Пользователи", "Шаблоны отчетов", "Настройки шаблонов",
    "Объявления", "Настройка", "Клиенты OAuth2 сервера для компании", "Перевод строки таблицы",
    # Продажи
    "Заказы", "Возвраты", "Дашборд по продажам", "Конструктор отчетов по продажам", "Воронка заказов",
    # Справочники
    "Юридическое лицо", "Поставщики", "Клиенты", "Валюты", "Бонусная система", "Регионы",
    "Виды оплаты", "Товары", "Регистрационные запросы", "Конкурсы", "Tерритории",
    "Вопросы", "Опросники", "Шаблоны отчетов по опросам",  # "Критерии" olib tashlangan
    # Документы ("Группа полей" 2026-09-11 da olib tashlandi → "Полевой отчет" hisoboti bilan almashdi)
    "Планирование визитов", "Визиты", "Анализ маршрутов", "Отслеживание пользователей", "Полевой отчет",
]

TAB = "Модератор"


def _norm(text):
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _visible_error(page: Page):
    """Ko'rinadigan xato banner/toast matnini qaytaradi (bo'lmasa "")."""
    for selector in ("[role='alert']", ".toast-message", ".toast-error", "#biruniAlert", "#biruniAlertExtended"):
        loc = page.locator(selector).first
        try:
            if loc.is_visible():
                text = re.sub(r"\s+", " ", loc.inner_text()).strip()
                if text:
                    return text[:140]
        except Exception:
            continue
    return ""


# Access-denied (ruxsat yo'q) — forma bug'i emas, joriy rol shu formani ocholmaydi
_NO_ACCESS_RE = re.compile(r"не может получить доступ|доступ запрещ|нет доступа|not allowed|access denied", re.IGNORECASE)


def _open_form(page: Page, tab: str, name: str, timeout=12_000):
    """Bir formani ochadi va natijani qaytaradi: {status, heading, note}.

    status: OK (ochildi) | NO_ACCESS (ruxsat yo'q — bug emas) | FAIL (xato/ochilmadi).
    """
    bp = BasePage(page)

    # Tab menyusini ochib menuitemni topamiz (menyu ochilmasa bir marta qayta urinamiz)
    item = None
    for _ in range(2):
        page.get_by_role("button", name=tab, exact=True).first.click()
        candidate = page.get_by_role("menuitem", name=name, exact=True).first
        try:
            expect(candidate).to_be_visible(timeout=4_000)
            item = candidate
            break
        except Exception:
            continue
    if item is None:
        return {"status": "FAIL", "heading": "", "note": "menuitem topilmadi yoki menyu ochilmadi"}

    item.click()
    bp._settle(timeout=timeout)

    # Xato darrov chiqadimi? (access-denied va h.k.) — heading uchun uzoq kutmaymiz
    error = _visible_error(page)
    heading = ""
    if not error:
        heading_loc = page.locator(HEADING).last
        try:
            expect(heading_loc).to_have_text(re.compile(r"\S"), timeout=timeout)
            heading = re.sub(r"\s+", " ", heading_loc.inner_text()).strip()
        except Exception:
            heading = ""
        if not heading:
            error = _visible_error(page)  # sarlavha kelmadi — kechroq chiqqan xato bormi?

    if error:
        if _NO_ACCESS_RE.search(error):
            return {"status": "NO_ACCESS", "heading": "", "note": "bu rol formani ocholmaydi (ruxsat yo'q)"}
        return {"status": "FAIL", "heading": heading, "note": f"ochilishda xato: {error}"}
    if not heading:
        return {"status": "FAIL", "heading": "", "note": "sarlavha ko'rinmadi (forma ochilmadi)"}

    note = "" if _norm(heading) == _norm(name) else f"sarlavha menyu nomidan farq qiladi: '{heading}'"
    return {"status": "OK", "heading": heading, "note": note}


@allure.title("Login (admin)")
def test_000_login(session_page: Page) -> None:
    """Bir marta admin bilan kiradi — keyingi test_form_* testlari shu seansdan
    foydalanadi, qayta login qilinmaydi."""
    authorization(session_page)


@allure.title("[Модератор] {name}")
@pytest.mark.parametrize("name", MODERATOR_FORMS, ids=MODERATOR_FORMS)
def test_form_opens(session_page: Page, name: str) -> None:
    """Модератор menyusidagi bitta formani ochadi va sarlavha paydo bo'lishini
    tekshiradi. Har forma alohida test — yiqilsa faqat o'zi qizil bo'ladi."""
    res = _open_form(session_page, TAB, name)

    heading = res.get("heading") or "—"
    allure.attach(
        f"[{TAB}] {name} -> {heading}" + (f"  ({res['note']})" if res["note"] else ""),
        name="natija",
        attachment_type=allure.attachment_type.TEXT,
    )

    if res["status"] == "NO_ACCESS":
        pytest.skip(f"[{TAB}] {name}: {res['note']}")
    assert res["status"] == "OK", f"[{TAB}] {name}: {res['note']}"
