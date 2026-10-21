"""Mobil INFRA xatolarini tasniflash (test tekshiruvi xatolaridan ajratish).

Faqat shu sabablar conftest'da BIR marta qayta urinadi:
  (a) ilova splash'da qoldi / UiAutomator2 root node bermadi — ``MobileInfraError``
      (``wait_app_ready`` ko'taradi);
  (b) ilovada «Ошибка / Нет интернет соединения / Попробуйте еще раз» ekrani — yiqilish
      paytida ``page_source`` da shu matn bo'lsa (ekran matni content-desc'da; screenshot
      2026-10-20 bilan tasdiqlangan);
  (c) UiAutomator2 instrumentation qulagan (WebDriverException matni).
Qolgan har qanday xato (AssertionError «... ko'rinmasligi kerak edi» va h.k.) — infra EMAS.
"""
from selenium.common.exceptions import WebDriverException

NO_INTERNET_TEXT = "Нет интернет соединения"
_INSTRUMENTATION_MARKERS = (
    "instrumentation process is not running",
    "instrumentation process cannot be initialized",
)


class MobileInfraError(AssertionError):
    """Qurilma/ilova/tarmoq infra xatosi (tekshiruv natijasi emas). AssertionError'dan —
    mavjud chaqiruvchilar uchun xatti-harakat o'zgarmaydi."""


def instrumentation_crashed(exc: BaseException) -> bool:
    return isinstance(exc, WebDriverException) and any(
        m in str(exc) for m in _INSTRUMENTATION_MARKERS)


def offline_screen(drv) -> bool:
    """Ekranda ilovaning «Нет интернет соединения» xato ekrani bormi (xato bermaydi)."""
    if drv is None:
        return False
    try:
        return NO_INTERNET_TEXT in drv.page_source
    except Exception:
        return False


def infra_reason(exc: BaseException, drv=None) -> str | None:
    """Infra xato bo'lsa — qisqa sabab matni; aks holda None."""
    first = (str(exc).splitlines() or [""])[0][:300]
    if isinstance(exc, MobileInfraError):
        return f"infra: {first}"
    if instrumentation_crashed(exc):
        return f"UiAutomator2 instrumentation qulagan: {first}"
    if isinstance(exc, (AssertionError, WebDriverException)) and offline_screen(drv):
        return f"ilovada «Ошибка / {NO_INTERNET_TEXT}» ekrani (asl xato: {first})"
    return None
