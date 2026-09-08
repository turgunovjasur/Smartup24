"""QISQA GURUH NOMLARI — `pytest setup`, `pytest visit`, `pytest all` ...

Nima uchun ALOHIDA plagin (conftest.py EMAS): `pytest_load_initial_conftests`
hook'i FAQAT `-p` bilan yuklangan plaginlar uchun chaqiriladi — conftest.py'dan
ishlamaydi (pytest hujjatlashtirilgan cheklovi). Shu sabab bu fayl `pytest.ini`
``addopts = -p pytest_group_aliases`` bilan yuklanadi.

Ishlash tamoyili: buyruq argumenti AYNAN tanish guruh nomi bo'lsa VA haqiqiy
fayl/papka BO'LMASA — mos runner fayl(lar)iga almashtiriladi. Shu sabab standart
`pytest tests/...`, `-k`, `-m`, `-v` va boshqa bayroqlar buzilmaydi. Tartib
saqlanadi (masalan `all` 5 runnerni ketma-ket beradi).

Namuna:
    pytest setup            # setup bo'limi
    pytest visit            # vizit modulidagi testlar
    pytest all -v           # 5 bo'lim ketma-ket, verbose
    pytest setup_groupa     # setup + group_a
"""
import os

_SETUP      = "tests/test_setup/test_all_setup.py"
_GROUP_A    = "tests/test_group_a/test_all_group_a.py"
_REGRESSION = "tests/test_regression/test_all_regression.py"
_MAIN       = "tests/test_main/test_all_main.py"
_DOCUMENT   = "tests/test_document/test_all_document_runner.py"
_VISIT = [
    "tests/test_document/test_visit.py",
    "tests/test_document/test_Plan_visit_recurrence.py",
    "tests/test_document/test_agent_visit_tracking.py",
    "tests/test_document/test_route_analysis.py",
]

GROUP_ALIASES = {
    "setup":         [_SETUP],
    "group_a":       [_GROUP_A],
    "groupa":        [_GROUP_A],
    "regression":    [_REGRESSION],
    "reg":           [_REGRESSION],
    "main":          [_MAIN],
    "document":      [_DOCUMENT],
    "doc":           [_DOCUMENT],
    "visit":         list(_VISIT),
    "setup_groupa":  [_SETUP, _GROUP_A],
    "all":           [_SETUP, _GROUP_A, _REGRESSION, _MAIN, _DOCUMENT],
}


def pytest_load_initial_conftests(early_config, parser, args):
    """Qisqa guruh nomlarini mos runner fayl(lar)iga almashtiradi (joyida)."""
    new_args = []
    for arg in args:
        mapped = GROUP_ALIASES.get(arg.lower())
        if mapped and not os.path.exists(arg):
            new_args.extend(mapped)
        else:
            new_args.append(arg)
    args[:] = new_args
