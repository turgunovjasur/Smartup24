#!/usr/bin/env python
"""Standalone cleanup — test yaratgan ma'lumotni jonli bazadan o'chiradi.

NEGA KERAK
----------
Suite har run'da nomli obyektlar (``Region-{code}``, ``supplier-{code}`` va h.k.)
yaratadi, lekin o'zidan keyin TOZALAMAYDI — baza abadiy o'sadi. Bu esa dublikat
(dup_val_on_index) va pagination muammolarining (kerakli qator 2-sahifaga
tushib ketishi) ILDIZI. Bu skript o'sha yig'ilib qolgan test yozuvlarini
qidirib topib o'chiradi.

DIZAYN
------
- Pytest testi EMAS — qo'lda yoki davriy ishga tushiriladi:
      python scripts/cleanup_test_data.py            # o'chiradi
      python scripts/cleanup_test_data.py --dry-run   # faqat ko'rsatadi
- Mavjud qismlarni qayta ishlatadi: ``authorization``/``logout``
  (flows.flow_authorization), ``flow_navigate`` (flows.flow_navbar),
  ``BasePage`` (utils.base_page), sessiya-qulf/chunk-recover handlerlari
  (conftest) — yangi selektor logikasi yozilmaydi.
- Har modul uchun bir xil o'chirish naqshi (regression ``run_*_delete`` bilan
  bir xil): ``search(prefix)`` → qator tanlash → "Удалить" → tasdiqlash "да".

CHEKLOVLAR (bilib qo'ying)
--------------------------
- **Faqat dev (sm24) uchun.** Prefikslar test yaratgan ma'lumotга mos; prod
  ``test`` kompaniyasida ishga tushirish ``--force`` talab qiladi (himoya).
- **Child-record bloki:** boshqa yozuvga bog'langan (masalan savoli biriktirilgan
  опросник) o'chmaydi — skript uni O'TKAZIB YUBORADI (best-effort) va davom etadi.
- **Faqat joriy sahifa:** har modulда bir o'tishda ko'rinadigan (filtrlangan)
  qatorlar o'chiriladi; juda katta backlog bir necha run talab qilishi mumkin.
- **Ma'lumotnomalar va Валюта kiritilmagan:** Производители/Отрасль/Категория
  Товары ичидаги sub-link, MCHJ Форма собственности'да, Валюта qidiruvi
  ``flow_menu`` talab qiladi — ular alohida deskriptor bilan keyin qo'shiladi
  (TARGETS ro'yxatiga qo'shish yetarli).
"""
import argparse
import os
import re
import sys

# Repo root'ni sys.path'ga qo'shamiz — skript qayerdan chaqirilishidan qat'i nazar
# flows/utils/conftest import bo'lsin.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from playwright.sync_api import sync_playwright

from conftest import (
    DEFAULT_TIMEOUT,
    NAVIGATION_TIMEOUT,
    _auto_continue_session,
    _auto_recover_chunk_error,
)
from flows.flow_authorization import COMPANY_CODE, authorization, logout
from flows.flow_navbar import flow_menu, flow_navigate
from utils.base_page import BasePage


# ── O'chiriladigan modullar ───────────────────────────────────────────────────
# Har element: modul menyusi + o'chiriladigan nom prefikslari. Heading odatda
# menyu bilan bir xil (farq bo'lsa `heading` beriladi). `show_all=True` — passiv
# (default yashiringan) qatorlar ham qamralsin.
TARGETS = [
    dict(tab="Модератор", menu="Регионы", prefixes=["Region-"], show_all=True),
    dict(tab="Модератор", menu="Поставщики", prefixes=["supplier-", "Supplier-", "Sup-"], show_all=True),
    dict(tab="Модератор", menu="Клиенты", prefixes=["client-"], show_all=True),
    # LegalPerson-/LP- (setup) + lp- (regression: lp-full-/lp-edit-/...)
    dict(tab="Модератор", menu="Юридическое лицо", prefixes=["LegalPerson-", "LP-", "lp-"], show_all=True),
    dict(tab="Модератор", menu="Товары", prefixes=["product-"], show_all=True),
    dict(tab="Модератор", menu="Конкурсы", prefixes=["konkurs-"], show_all=False),
    dict(tab="Модератор", menu="Бонусная система", prefixes=["bonus-"], show_all=True),
    # Территория (setup territory-{code} + regression territory-edit-/...)
    dict(tab="Модератор", menu="Tерритории", prefixes=["territory-"], show_all=True),
    # Вопросы (setup Vaprost{code} + regression vaprost-basic-/...); savoli biriktirilgan
    # опросник child-record bilan bloklanadi — skript uni o'tkazib yuboradi
    dict(tab="Модератор", menu="Вопросы", prefixes=["vaprost-", "Vaprost"], show_all=True),
    dict(tab="Модератор", menu="Опросники", prefixes=["oprosniki-", "oprs-parent-"], show_all=True),
    dict(tab="Модератор", menu="Шаблоны отчетов по опросам", prefixes=["Shablon-"], show_all=True),
    # ── Ma'lumotnomalar ── Manufacturer/MCHJ bitta sub-link; Отрасль/Категория esa
    # "Характеристика товаров" ostidagi подтип (qator → Подтипы, `char_subtype`).
    dict(tab="Модератор", menu="Товары", sublink="Производители", prefixes=["Manufacturer-"], show_all=True),
    dict(tab="Модератор", menu="Товары", char_subtype="Отрасль", prefixes=["Industry-"], show_all=True),
    dict(tab="Модератор", menu="Товары", char_subtype="Категория", prefixes=["Category-"], show_all=True),
    dict(tab="Модератор", menu="Юридическое лицо",
         sublink="Организационно-правовые формы", prefixes=["MCHJ-"], show_all=True),
    # ── Yangi modullar ──
    dict(tab="Модератор", menu="Группа полей", prefixes=["field-group-", "fg-"], show_all=True),
    # Валюта: Название bo'yicha qidiruv flow_menu bilan yoqiladi
    dict(tab="Модератор", menu="Валюты", prefixes=["val-", "so`m", "tiyin"], show_all=True, flow_menu=True),
    # Agentlar/userlar — ko'pi visit/filialга bog'langan → o'chmaydi, Неактивный (best-effort)
    dict(tab="Модератор", menu="Пользователи", prefixes=["agent-", "supplier_user-", "client_user-"], show_all=True),
]


def _dismiss_error(page) -> None:
    """Ochiq "Ошибка"/tasdiqlash dialogini "Закрыть" bilan yopadi (best-effort)."""
    try:
        dialog = page.locator(".cdk-overlay-container")
        btn = dialog.get_by_role("button", name="Закрыть").first
        if btn.count() and btn.is_visible():
            btn.click()
    except Exception:
        pass


def _try_deactivate(m, page) -> bool:
    """Delete BLOKLANGAN (child record) yozuvni Неактивный qilishga urinadi
    (best-effort). Qator TANLANGAN (action panel ochiq) bo'lishi kutiladi. Mavjud
    naqshlarni ketma-ket sinaydi; har biri try/except — hech qachon skriptni
    yiqitmaydi. Muvaffaqiyatда True.

    1) "Изменить статус": menyu chiqsa passiv variant, aks holda to'g'ridan-to'g'ri "да"
       (supplier/client/legal_person/product/bonus/konkurs/field_group).
    2) passiv toggle tugma ("Пассивный"/"Неактивный"/"passive") + "да"
       (currency/territoriya/opros/shablon/vaprost).
    3) switch-asosli: "Изменить" → Статус switch OFF → Сохранить (region/agent).
    """
    overlay = page.locator(".cdk-overlay-container")
    # 1) Изменить статус
    try:
        btn = page.get_by_role("button", name="Изменить статус")
        if btn.count() and btn.first.is_visible():
            btn.first.click()
            page.wait_for_timeout(400)
            for opt in ("Пассивный", "Неактивный", "passive"):
                cand = overlay.get_by_role("menuitem", name=opt, exact=True)
                if not cand.count():
                    cand = overlay.get_by_role("button", name=opt, exact=True)
                if cand.count() and cand.first.is_visible():
                    cand.first.click()
                    break
            m.confirm("да")
            m.wait_for_loader()
            return True
    except Exception:
        _dismiss_error(page)
    # 2) passiv toggle tugma
    for label in ("Пассивный", "Неактивный", "passive"):
        try:
            b = page.get_by_role("button", name=label, exact=True)
            if b.count() and b.first.is_visible():
                b.first.click()
                m.confirm("да")
                m.wait_for_loader()
                return True
        except Exception:
            _dismiss_error(page)
    # 3) switch-asosli: Изменить → Статус OFF → Сохранить
    try:
        edit = page.get_by_role("button", name="Изменить", exact=True)
        if edit.count() and edit.first.is_visible():
            edit.first.click()
            m.wait_for_loader()
            m.checkbox(locator="smt-switch", checked=False)
            m.save()
            return True
    except Exception:
        _dismiss_error(page)
    return False


def _matching_names(page, prefixes) -> list:
    """Joriy (filtrlangan) ro'yxatdagi qatorlardan prefiksga mos nom tokenlarini
    yig'adi. Token = ``prefix`` + bo'sh joygacha bo'lgan belgilar (test uslubi:
    ``re.search(r"Region-\\S+", ...)``)."""
    patterns = [re.compile(re.escape(p) + r"\S+") for p in prefixes]
    names = set()
    for row in page.locator(".smt-data-row").all():
        try:
            txt = row.inner_text(timeout=2_000)
        except Exception:
            continue
        for pat in patterns:
            for match in pat.finditer(txt):
                names.add(match.group(0))
    return sorted(names)


def cleanup_target(page, target, *, dry_run) -> dict:
    """Bitta modul uchun mos yozuvlarni o'chiradi; o'chib bo'lmasa (child record)
    Неактивный qiladi. {deleted, deactivated, blocked, found} qaytaradi."""
    m = BasePage(page)
    tab = target["tab"]
    menu = target["menu"]
    prefixes = target["prefixes"]
    show_all = target.get("show_all", False)

    def _goto_list():
        """Modul ro'yxatiga o'tadi: TOP menyu, yoki sub-link (Производители/МЧЖ),
        yoki "Характеристика товаров" подтипи (Отрасль/Категория)."""
        heading = target.get("heading", menu)
        flow_navigate(page, tab=tab, name=menu)
        char = target.get("char_subtype")
        sublink = target.get("sublink")
        if char:
            m.click_link("Характеристика товаров")
            m.expect_heading("Характеристика товаров")
            m.click_grid_row(char)
            m.click_button("Подтипы")
            heading = char
        elif sublink:
            m.click_link(sublink)
            heading = sublink
        m.expect_heading(heading)
        if target.get("flow_menu"):
            try:
                flow_menu(page)
            except Exception:
                pass

    _goto_list()

    # Nomlar ro'yxatini bir marta yig'amiz (birinchi prefiks bo'yicha qidirib,
    # keyin barcha prefikslarni matndan ajratamiz).
    m.search(prefixes[0])
    if show_all:
        try:
            m.show_all()
        except Exception:
            pass
    names = _matching_names(page, prefixes)

    deleted, deactivated, blocked = 0, 0, []
    for name in names:
        if dry_run:
            continue
        try:
            m.search(name)
            if show_all:
                try:
                    m.show_all()
                except Exception:
                    pass
            row = page.locator(".smt-data-row").filter(has_text=name)
            if not row.count():
                continue  # allaqachon o'chgan (dublikat token yoki oldingi o'tish)
            m.click_grid_row(name)
            m.click_button("Удалить")
            m.confirm("да")
            m.wait_for_loader()
            deleted += 1
        except Exception:
            # Delete BLOKLANDI (child record) — o'chirib bo'lmadi. Неактивный
            # qilishga urinamiz (default ro'yxatдан yo'qolsin).
            _dismiss_error(page)
            done = False
            try:
                m.click_grid_row(name)   # qatorni qayta tanlash (action panel)
                done = _try_deactivate(m, page)
            except Exception:
                _dismiss_error(page)
            if done:
                deactivated += 1
            else:
                blocked.append(name)
            # Keyingi nom uchun TOZA holat — ro'yxatga qaytamiz (deaktivatsiya forma
            # ochib qolgan bo'lsa ham keyingi qadam buzilmasin).
            try:
                _goto_list()
            except Exception:
                pass

    return {"deleted": deleted, "deactivated": deactivated,
            "blocked": blocked, "found": len(names)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Test yaratgan ma'lumotni bazadan tozalaydi.")
    parser.add_argument("--dry-run", action="store_true", help="O'chirmaydi, faqat topilganlarni ko'rsatadi")
    parser.add_argument("--force", action="store_true", help="Prod (kompaniya 'test') da ham ishlashga ruxsat")
    parser.add_argument("--headless", action="store_true", help="Brauzerni ko'rsatmasdan ishlash")
    args = parser.parse_args()

    # Himoya: prod 'test' kompaniyasida tasodifan o'chirmaslik uchun.
    if COMPANY_CODE == "test" and not args.force:
        print(
            "[cleanup] TO'XTATILDI: faol muhit PROD (kompaniya 'test'). "
            "Prod'da tozalash uchun --force bering yoki flow_authorization.py'ni dev'ga o'tkazing."
        )
        sys.exit(1)

    print(f"[cleanup] Muhit: kompaniya '{COMPANY_CODE}' | dry-run={args.dry_run}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=args.headless,
            args=["--start-maximized", "--window-size=1920,1080"],
        )
        context = browser.new_context(no_viewport=True)
        context.set_default_timeout(DEFAULT_TIMEOUT)
        context.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
        page = context.new_page()
        _auto_continue_session(page)
        _auto_recover_chunk_error(page)

        totals = {"deleted": 0, "deactivated": 0, "blocked": 0, "found": 0}
        try:
            authorization(page)
            for target in TARGETS:
                label = f"{target['tab']} → {target['menu']}"
                if target.get("sublink") or target.get("char_subtype"):
                    label += f" → {target.get('sublink') or target.get('char_subtype')}"
                try:
                    res = cleanup_target(page, target, dry_run=args.dry_run)
                except Exception as exc:
                    print(f"[cleanup] {label}: XATO (o'tkazildi) — {exc}")
                    continue
                totals["deleted"] += res["deleted"]
                totals["deactivated"] += res["deactivated"]
                totals["blocked"] += len(res["blocked"])
                totals["found"] += res["found"]
                verb = "topildi" if args.dry_run else (
                    f"o'chirildi={res['deleted']}, deaktiv={res['deactivated']}")
                extra = f", bloklangan={len(res['blocked'])}" if res["blocked"] else ""
                print(f"[cleanup] {label}: {res['found']} topildi ({verb}{extra})")
        finally:
            logout(page)
            context.close()
            browser.close()

        print(
            f"[cleanup] YAKUN: topildi={totals['found']}, "
            f"o'chirildi={totals['deleted']}, deaktiv={totals['deactivated']}, "
            f"bloklangan={totals['blocked']}"
        )


if __name__ == "__main__":
    main()
