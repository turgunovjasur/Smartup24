"""Biznes tilida xato hisoboti — test yiqilganda Playwright stack trace o'rniga
INSON tushunadigan tavsif Telegram/Allure'ga chiqadi (conftest o'qiydi).

    from utils.qa_report import qa_step

    with qa_step(f"Ro'yxatdan '{name}' ni tanlash"):
        m.grid_row(name)          # topilmasa -> "…'{name}' ni tanlash — bajarilmadi"

Ichma-ich bo'lsa eng ichkisi ko'rsatiladi. Testlar ketma-ket (bitta jarayon)
ishlagani uchun bitta global stek yetarli.
"""
import functools
from contextlib import contextmanager

_stack: list[str] = []


def current_step_desc() -> str | None:
    """Joriy (eng ichki) biznes-qadam tavsifi; qadam yo'q bo'lsa None."""
    return _stack[-1] if _stack else None


@contextmanager
def qa_step(description: str):
    """Biznes qadam. Ichidagi xatoni YUTMAYDI — test baribir yiqiladi, faqat
    hisobotga tushunarli tavsif qo'shiladi."""
    _stack.append(description)
    try:
        yield
    finally:
        _stack.pop()


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
                desc = template
            with qa_step(desc):
                return method(*args, **kwargs)
        return wrapper
    return deco


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


def friendly_reason(exc: BaseException | None, page=None) -> str:
    """Xatoni qisqa biznes sababga o'giradi; ``page`` berilsa ochiq «Ошибка»
    dialogi ustun qo'yiladi."""
    if page is not None:
        err = visible_error_dialog_text(page)
        if err:
            return f"server xatosi: {err}"
    if exc is None:
        return "noma'lum xato"
    name = type(exc).__name__
    text = str(exc)
    if name == "AssertionError":
        # BasePage boyitilgan xabarlarining 1-qatori tushunarli sarlavha
        first = text.strip().splitlines()[0] if text.strip() else ""
        return first[:160] if first else "tekshiruv o'tmadi"
    if "Timeout" in name or "timeout" in text.lower():
        return "element vaqtida topilmadi / ko'rinmadi (kutish tugadi)"
    if "Strict" in name:
        return "bir nechta mos element topildi (aniq emas)"
    return f"{name}: {text.splitlines()[0][:120] if text else ''}".strip()
