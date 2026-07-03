"""Smartup24 formalari ochilish smoke testi.

Maqsad: har bir navbar bo'limini (Модератор / Поставщик / Клиент menyusidagi
formalar) ketma-ket ochib, forma to'g'ri yuklanganini (aktiv sarlavha paydo
bo'lishi) va ochilishda xato chiqmasligini tekshirish. Bitta forma yiqilsa ham
to'xtamaydi — keyingisini ochadi va oxirida qaysi formalar ochilgani/xato
bergani haqida to'liq hisobot beradi (konsolga + Allure attachmentga).

Bu test MUSTAQIL — mavjud testlarga (test_all va h.k.) aralashmaydi.
Formalar ro'yxati MCP bilan real menyudan aniqlangan (2026-07-01).
"""
import re

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from utils.base_page import BasePage, HEADING


# (tab, menyu nomi) — navbar menyusidagi barcha bo'limlar
MODERATOR_FORMS = [
    # Главное
    "Организации", "Роли", "Пользователи", "Шаблоны отчетов", "Объявления",
    "Настройка", "Клиенты OAuth2 сервера для компании", "Перевод строки таблицы",
    # Продажи
    "Заказы", "Возвраты", "Дашборд по продажам", "Конструктор отчетов по продажам", "Воронка заказов",
    # Справочники
    "Юридическое лицо", "Поставщики", "Клиенты", "Валюты", "Бонусная система", "Регионы",
    "Виды оплаты", "Товары", "Регистрационные запросы", "Конкурсы", "Tерритории",
    "Вопросы", "Опросники", "Критерии", "Шаблоны отчетов по опросам",
    # Документы
    "Планирование визитов", "Визиты", "Анализ маршрутов", "Отслеживание пользователей", "Группа полей",
]

SUPPLIER_FORMS = [
    # Главное
    "Запросы", "Рейтинги и отзывы", "Пользователи", "Бонусы", "Настройки",
    # Справочники
    "Клиенты", "Характеристика клиента", "Товары", "Портфели", "Склады", "Тип цены", "Акции", "Скидки",
]

CLIENT_FORMS = [
    # Главное
    "Запросы", "Рейтинги и отзывы", "Пользователи", "Настройки",
    # Справочник
    "Поставщики", "Шаблоны документооборота", "Начисления бонусов", "Бонусный кошелек",
]

ALL_FORMS = (
    [("Модератор", name) for name in MODERATOR_FORMS]
    + [("Поставщик", name) for name in SUPPLIER_FORMS]
    + [("Клиент", name) for name in CLIENT_FORMS]
)


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


@allure.title("Smartup24 — barcha formalar ochilish smoke testi")
def test_forms_smoke(page: Page) -> None:
    authorization(page)

    results = []
    for tab, name in ALL_FORMS:
        with allure.step(f"[{tab}] {name}"):
            try:
                res = _open_form(page, tab, name)
            except Exception as exc:  # forma yiqilsa ham to'xtamaymiz
                res = {"status": "FAIL", "heading": "", "note": f"kutilmagan xato: {exc}"[:140]}
            res.update(tab=tab, name=name)
            results.append(res)

    # --- Hisobot ---
    ok = [r for r in results if r["status"] == "OK"]
    no_access = [r for r in results if r["status"] == "NO_ACCESS"]
    failed = [r for r in results if r["status"] == "FAIL"]
    marks = {"OK": "✓", "NO_ACCESS": "•", "FAIL": "✗"}

    lines = [
        f"Formalar ochilish natijasi: {len(ok)} OK, {len(no_access)} ruxsat yo'q, "
        f"{len(failed)} xato ({len(results)} tadan)",
        "",
    ]
    for r in results:
        row = f"{marks[r['status']]} [{r['tab']}] {r['name']} -> {r['heading'] or '—'}"
        if r["note"]:
            row += f"  ({r['note']})"
        lines.append(row)
    report = "\n".join(lines)

    print("\n" + report)
    try:
        allure.attach(report, name="Formalar ochilish hisoboti", attachment_type=allure.attachment_type.TEXT)
    except Exception:
        pass

    # Test faqat HAQIQIY xato (ochilmagan/xato bergan forma) bo'lsa yiqiladi.
    # "Ruxsat yo'q" (NO_ACCESS) — forma bug'i emas, joriy rol cheklovi, shuning uchun
    # hisobotда ko'rsatiladi lekin testni yiqitmaydi.
    assert not failed, (
        f"{len(failed)} ta forma ochilmadi/xato berdi:\n"
        + "\n".join(f"- [{r['tab']}] {r['name']}: {r['note']}" for r in failed)
        + f"\n\nTo'liq hisobot:\n{report}"
    )
