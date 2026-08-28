"""Biznes tilида xato hisoboti (TZ formati) — qa_step context manager.

Maqsad: test yiqilganда tushunarsiz Playwright lokator/stack trace o'rniga
INSON tushunadigan tavsif Telegram'ga chiqsin. Riskli amalni ``qa_step`` bilan
o'raysiz; ichida xato bo'lsa, tavsif conftest orqali Telegram xatolik xabariga
uzatiladi (skrinshot bilan birga).

Namuna (test ichida):
    from utils.qa_report import qa_step

    with qa_step(f"Yaratilgan ro'yxatдан '{name}' ni tanlash"):
        m.grid_row(name)          # topilmasa -> "…'{name}' ni tanlash — bajarilmadi"

Ichma-ich ham bo'ladi (eng ichkisi ko'rsatiladi):
    with qa_step("Kategoriya biriktirish"):
        with qa_step(f"'{cat}' ni ro'yxatdan tanlash"):
            m.select(cat, label="Категории")

Test KETMA-KET ishlaydi (session_page, bitta jarayon), shuning uchun bitta global
holat yetarli — thread/parallel murakkabligi yo'q.
"""
import functools
from contextlib import contextmanager

# Joriy biznes-qadam tavsiflari steki (ichma-ich qadamlar uchun)
_stack: list[str] = []


def current_step_desc() -> str | None:
    """Ayni ishlayotган (eng ichki) biznes-qadam tavsifi — conftest makereport
    xato bo'lganда shuni o'qib, Telegram'ga uzatadi. Qadam yo'q bo'lsa None."""
    return _stack[-1] if _stack else None


@contextmanager
def qa_step(description: str):
    """Biznes tilидаги qadam. Ichидаги istalgan xato (Playwright timeout, assert,
    va h.k.) yuz berса, conftest shu ``description`` ni xato hisobotiga qo'yadi.
    Xatoning O'ZINI YUTMAYDI — test baribir yiqiladi (stack trace Allure/log'da
    qoladi), faqat Telegram'ga TUSHUNARLI tavsif ham qo'shiladi."""
    _stack.append(description)
    try:
        yield
    finally:
        _stack.pop()


def qa_action(template: str):
    """DEKORATOR — BasePage metodini biznes tavsif bilan o'raydi (metod mantig'iga
    TEGMAYDI). ``template`` — metod argumentlaridan to'ldiriladigan format:
    ``{0}`` = 1-foydali argument (self'дан keyingi). To'ldirib bo'lmasa (argument
    kwarg bilan berilса) template o'zi ishlatiladi.

    Namuna:
        @qa_action("Ro'yxatдан «{0}» ni topish")
        def grid_row(self, text, ...): ...
    -> grid_row yiqilса Telegram'да: "↳ Ro'yxatдан «field-group-123» ni topish —
       element vaqtida topilmadi"
    """
    def deco(method):
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            try:                      # args[0]=self; foydali argumentlar args[1:]
                desc = template.format(*args[1:], **kwargs)
            except Exception:
                desc = template
            with qa_step(desc):
                return method(*args, **kwargs)
        return wrapper
    return deco


def friendly_reason(exc: BaseException | None) -> str:
    """Xato turini biznes tilига o'giradi (lokator/stack o'rniga qisqa sabab)."""
    if exc is None:
        return "noma'lum xato"
    name = type(exc).__name__
    text = str(exc)
    if "Timeout" in name or "timeout" in text.lower():
        return "element vaqtida topilmadi / ko'rinmadi (kutish tugadi)"
    if name == "AssertionError":
        # Ko'pincha expect(...) — qisqa matn qoldiramiz
        first = text.strip().splitlines()[0] if text.strip() else ""
        return f"tekshiruv o'tmadi{(' — ' + first[:120]) if first else ''}"
    if "Strict" in name:
        return "bir nechta mos element topildi (aniq emas)"
    return f"{name}: {text.splitlines()[0][:120] if text else ''}".strip()
