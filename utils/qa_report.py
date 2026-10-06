"""Biznes tilida xato hisoboti — test yiqilganda Playwright stack trace o'rniga
INSON tushunadigan tavsif Telegram/Allure'ga chiqadi (conftest o'qiydi):

    ❌ test_010_setup_manufacturer
       ↳ Навигация: Модератор → Товары › Menyu: Модератор → Товары
         — «Товары» menyu bandi 60 s ichida bosilmadi · sahifa: «Товары»

Kontekst ikki manbadan yig'iladi:
  - testdagi ``allure.step(...)`` sarlavhalari (biznes qadam — avtomatik kuzatiladi);
  - ``qa_step`` / ``@qa_action`` (BasePage/flow amali — qaysi element).

    from utils.qa_report import qa_step

    with qa_step(f"Ro'yxatdan '{name}' ni tanlash"):
        m.grid_row(name)

Yiqilgan qadam XATO PAYTIDA qayd etiladi (qadam stekdan chiqib ketgandan keyin ham
hisobotda ko'rinsin) va o'sha xato obyektiga bog'lanadi — test ichida ushlab
olingan (kutilgan) xatolar hisobotni chalg'itmaydi. Testlar ketma-ket (bitta
jarayon) ishlagani uchun global holat yetarli.
"""
import functools
import re
from contextlib import contextmanager

import allure_commons

_qa_stack: list[str] = []
_allure_stack: list[str] = []
# (tavsif, xato obyekti) — eng ICHKI yiqilgan qadam (birinchi qayd etilgani)
_failed = {"qa": None, "allure": None}

HEADING_CSS = "app-form-stack-widget span.font-semibold.truncate:visible"


def reset() -> None:
    """Har test boshida chaqiriladi (conftest) — oldingi testning izi qolmasin."""
    _qa_stack.clear()
    _allure_stack.clear()
    _failed["qa"] = _failed["allure"] = None


def _remember(kind: str, description: str, exc: BaseException) -> None:
    current = _failed[kind]
    # Xato ichkaridan tashqariga ko'tariladi — birinchi qayd = eng ichki qadam.
    # Yangi (boshqa) xato bo'lsa — oldingisi ushlab olingan edi, almashtiramiz.
    if current is None or current[1] is not exc:
        _failed[kind] = (description, exc)


def _belongs_to(exc_saved: BaseException, exc: BaseException | None) -> bool:
    """Saqlangan xato testni yiqitgan xato (yoki uning sababi/konteksti)mi."""
    seen = 0
    while exc is not None and seen < 10:
        if exc is exc_saved:
            return True
        exc = exc.__cause__ or exc.__context__
        seen += 1
    return False


def current_step_desc(exc: BaseException | None = None) -> str | None:
    """Yiqilgan biznes qadam: "allure qadami › BasePage amali" (yo'q bo'lsa None).

    ``exc`` berilsa faqat shu xatoga tegishli qayd olinadi; aks holda (yoki qayd
    yo'q bo'lsa) hozir ochiq turgan eng ichki qadam."""
    parts = []
    for kind, stack in (("allure", _allure_stack), ("qa", _qa_stack)):
        saved = _failed[kind]
        if saved and (exc is None or _belongs_to(saved[1], exc)):
            parts.append(saved[0])
        elif stack:
            parts.append(stack[-1])
    parts = [p for i, p in enumerate(parts) if p and p not in parts[:i]]
    return " › ".join(parts) or None


@contextmanager
def qa_step(description: str):
    """Biznes qadam. Ichidagi xatoni YUTMAYDI — test baribir yiqiladi, faqat
    hisobotga tushunarli tavsif qo'shiladi."""
    _qa_stack.append(description)
    try:
        yield
    except BaseException as exc:
        _remember("qa", description, exc)
        raise
    finally:
        _qa_stack.pop()


def qa_action(template: str):
    """Dekorator — BasePage metodini ``qa_step`` bilan o'raydi. ``{0}`` = self'dan
    keyingi 1-argument; to'ldirib bo'lmasa template o'zi ishlatiladi.

        @qa_action("Ro'yxatdan «{0}» ni topish")
        def grid_row(self, text, ...): ...
    """
    def deco(method):
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            try:
                desc = template.format(*args[1:], **kwargs)
            except Exception:
                desc = re.sub(r"\s*«?\{[^}]*\}»?\s*", " ", template).strip()
            with qa_step(desc):
                return method(*args, **kwargs)
        return wrapper
    return deco


class _AllureStepTracker:
    """Testdagi ``allure.step`` sarlavhalarini kuzatadi — har bir BasePage metodiga
    dekorator qo'ymasdan ham "qaysi biznes qadamda yiqildi" ma'lum bo'ladi."""

    @allure_commons.hookimpl
    def start_step(self, uuid, title, params):
        _allure_stack.append(title)

    @allure_commons.hookimpl
    def stop_step(self, uuid, exc_type, exc_val, exc_tb):
        title = _allure_stack.pop() if _allure_stack else None
        if exc_val is not None and title:
            _remember("allure", title, exc_val)


_TRACKER_NAME = "smartup24_qa_step_tracker"
if allure_commons.plugin_manager.get_plugin(_TRACKER_NAME) is None:
    allure_commons.plugin_manager.register(_AllureStepTracker(), name=_TRACKER_NAME)


# ------------------------------------------------------------------------------
# Sababni inson tiliga o'girish
# ------------------------------------------------------------------------------

_ROLE_UZ = {
    "menuitem": "menyu bandi", "menuitemcheckbox": "menyu bandi", "button": "tugmasi",
    "link": "havolasi", "textbox": "maydoni", "searchbox": "qidiruv maydoni",
    "checkbox": "belgisi (checkbox)", "radio": "varianti (radio)", "dialog": "dialogi",
    "option": "varianti", "treeitem": "daraxt varianti", "listitem": "qadami",
    "row": "qatori", "tab": "tabi",
}
_ACTION_UZ = {
    "click": "bosilmadi", "fill": "yozilmadi", "press": "tugma bosilmadi",
    "check": "belgilanmadi", "hover": "ustiga borilmadi", "select_option": "tanlanmadi",
    "text_content": "o'qilmadi", "inner_text": "o'qilmadi", "input_value": "o'qilmadi",
    "wait_for": "kutilgan holatga kelmadi", "set_input_files": "fayl yuklanmadi",
}


def _target(text: str) -> str | None:
    """Call log'dagi "waiting for <locator>" dan elementning odamga tushunarli nomi."""
    m = re.search(r'waiting for (.+)', text)
    if not m:
        return None
    loc = m.group(1)
    role = re.search(r'get_by_role\("([\w-]+)",\s*name="([^"]+)"', loc)
    if role:
        kind = _ROLE_UZ.get(role.group(1), role.group(1))
        return f"«{role.group(2)}» {kind}"
    by_text = re.search(r'get_by_(?:text|label|placeholder)\("([^"]+)"', loc)
    if by_text:
        return f"«{by_text.group(1)}» matnli element"
    if "app-form-stack-widget" in loc:
        return "sahifa sarlavhasi"
    if "smt-select-dropdown" in loc:
        return "select ro'yxati (dropdown)"
    if ".smt-data-row" in loc:
        return "jadval qatori"
    return f"element {loc.strip()[:80]}"


def _seconds(text: str) -> str:
    m = re.search(r"(?:Timeout|timeout)\s*(\d+)\s*ms", text)
    return f"{int(m.group(1)) // 1000} s" if m else "belgilangan vaqt"


def _expect_reason(text: str) -> str | None:
    """Playwright ``expect(...)`` xabarini o'giradi (kutilgan va amaldagi qiymat)."""
    m = re.search(r'Locator expected (not )?to ([\w ]+?)(?: \'(.*?)\')?\s*\n\s*Actual value:\s*(.*)', text)
    if not m:
        return None
    negated, what, expected, actual = m.groups()
    actual = (actual or "").strip()
    target = _target(text) or "element"
    if "not found" in text or actual in ("None", ""):
        return f"{target} topilmadi"
    what = what.strip()
    if "heading" in target or "sarlavha" in target or "app-form-stack-widget" in text:
        if expected:
            return f"«{expected}» sahifasi kutilgan edi, lekin «{actual}» ochiq"
    if what in ("be visible",):
        return f"{target} ko'rinmadi"
    if what in ("be hidden",):
        return f"{target} yopilmadi (hali ko'rinib turibdi)"
    if what in ("be enabled",):
        return f"{target} faol (enabled) bo'lmadi"
    if what in ("be checked",):
        state = "belgilanmagan" if negated else "belgilangan"
        return f"{target} {state} bo'lishi kutilgan edi"
    if expected is not None:
        return f"{target}: «{expected}» kutilgan edi, amalda «{actual}»"
    return f"{target}: kutilgan holat ({what}) bo'lmadi, amalda «{actual}»"


def visible_error_dialog_text(page) -> str | None:
    """Ko'rinib turgan backend «Ошибка» dialogi matni (yo'q bo'lsa None).

    Asl server sababi (``dup_val_on_index``, ``number precision too large`` ...)
    ko'pincha shu dialogda turadi, test esa 2 qadam keyin "element topilmadi"
    bilan yiqiladi — shu matn bilan ASL sabab ko'rsatiladi."""
    try:
        dialog = page.get_by_role("dialog").filter(has_text="Ошибка").first
        if dialog.count() and dialog.is_visible():
            return " ".join((dialog.inner_text() or "").split())[:300]
    except Exception:
        pass
    return None


def _page_where(page) -> str:
    """Xato paytida ochiq turgan sahifa sarlavhasi (" · sahifa: «...»")."""
    try:
        heading = page.locator(HEADING_CSS).last
        title = " ".join((heading.inner_text(timeout=1_000) or "").split())
        return f" · sahifa: «{title}»" if title else ""
    except Exception:
        return ""


def friendly_reason(exc: BaseException | None, page=None) -> str:
    """Xatoni qisqa biznes sababga o'giradi; ``page`` berilsa ochiq «Ошибка»
    dialogi ustun qo'yiladi va qaysi sahifada bo'lgani qo'shiladi."""
    if page is not None:
        err = visible_error_dialog_text(page)
        if err:
            return f"server xatosi: {err}"
    where = _page_where(page) if page is not None else ""
    if exc is None:
        return "noma'lum xato" + where
    name = type(exc).__name__
    text = str(exc)

    if "Timeout" in name:
        target = _target(text) or "element"
        action = re.search(r"Locator\.(\w+)", text)
        verb = _ACTION_UZ.get(action.group(1), "topilmadi") if action else "topilmadi"
        return f"{target} {_seconds(text)} ichida {verb}{where}"

    if name == "AssertionError":
        reason = _expect_reason(text)
        if reason is None:
            # BasePage o'zi boyitgan xabarlar — 1-qatori tushunarli sarlavha
            first = text.strip().splitlines()[0] if text.strip() else ""
            reason = first[:200] if first else "tekshiruv o'tmadi"
        return reason + where

    if "Strict" in name or "strict mode violation" in text:
        target = _target(text) or "element"
        return f"{target}: bir nechta mos element topildi (aniq emas){where}"
    if "detached" in text.lower():
        return f"element bosish paytida sahifadan o'chib ketdi (qayta render){where}"
    first = text.splitlines()[0][:150] if text else ""
    return f"{name}: {first}".strip() + where
