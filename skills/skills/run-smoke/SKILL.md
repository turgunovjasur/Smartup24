---
name: run-smoke
description: Smartup24 testlarini ishga tushirish va natijalarni ko'rsatish. "testlarni ishga tushir", "smoke run", "pytest ishga tushir", "test_all run" so'ralganda ishlatiladi.
allowed-tools: Bash, Read, Glob
---

# Testlarni Ishga Tushirish (Smartup24)

Argument: `$ARGUMENTS` (test nomi, fayl yoki bo'sh)

Loyiha oddiy pytest bilan ishlaydi — eski `scripts/run_tests.py`, `run_tests.sh`, `.env`, company/telegram mexanizmi YO'Q. Testlar `.venv` ichida ishga tushiriladi.

## Qaysi buyruqni ishlating

### Barcha testlar (to'liq zanjir):
```bash
.venv/bin/python -m pytest tests/test_all.py -v
```
`test_all` bir marta login qilib manufacturer → industry → category → product zanjirini bitta `page` va `code` bilan yuritadi.

### Bitta test fayl:
```bash
.venv/bin/python -m pytest tests/test_manufacturer.py -v
```

### Bitta test funksiya:
```bash
.venv/bin/python -m pytest tests/test_product.py::test_product -v
```

### Formalar ochilish smoke testi (barcha navbar formalari):
```bash
.venv/bin/python -m pytest tests/test_forms_smoke.py -s -v
```
Модератор/Поставщик/Клиент menyusidagi har bir formani ketma-ket ochib, sarlavha
paydo bo'lishi va xato chiqmasligini tekshiradi; oxirida OK / "ruxsat yo'q" (rol
cheklovi, bug emas) / xato hisobotini beradi (`-s` bilan konsolda ko'rinadi,
Allure attachmentда ham). Faqat HAQIQIY xato bo'lsa yiqiladi. Bu test mustaqil —
`test_all` ga kirmaydi.

### Foydali flaglar:
```bash
--tb=short        # qisqa traceback
-s                # print/stdout ko'rsatish
-x                # birinchi xatoda to'xtash
```

### Allure hisobot ko'rish:
```bash
allure serve test-results/allure-results
```

## Muhim

- **Barcha buyruqlar `.venv` python bilan**: `.venv/bin/python -m pytest ...`. Agar `.venv` bo'sh bo'lsa: `.venv/bin/python -m pip install -r requirements.txt && .venv/bin/python -m playwright install chromium`.
- **Headed default** — `conftest.py` da `headless=False`, `--start-maximized`. Browser ekranда ko'rinadi (bu to'g'ri holat).
- `pytest.ini`: `testpaths = .`, `python_files = test_*.py`, `python_functions = test_*`.
- Trace fayllari `test-results/traces/` ga, failure screenshot va Allure natijalar `test-results/allure-results/` ga yoziladi.
- Login credential `flows/flow_authorization.py` da (`admin@autotest` / `greenwhite`) va login URL shu faylda.
- Test teardownida `logout` avtomatik chaqiriladi (seansni yopadi).

## Ish tartibi

1. `$ARGUMENTS` bo'sh bo'lsa — `.venv/bin/python -m pytest tests/test_all.py -v` bilan to'liq run
2. `$ARGUMENTS` fayl nomi bo'lsa — faqat shu faylni ishga tushir
3. `$ARGUMENTS` test nomi bo'lsa — `::test_<nomi>` bilan faqat shu testni ishga tushir
4. Natijalarni tahlil qil:
   - **PASSED** testlar sonini ko'rsat
   - **FAILED** bo'lsa — traceback dan xato turini va joyini o'qib sababini tushuntir, kerak bo'lsa `debug-test` skilliga o't
5. Flaky natijada testni bir necha marta qayta ishga tushirib barqarorlikni tekshir (UI testlar timing'ga sezgir)
