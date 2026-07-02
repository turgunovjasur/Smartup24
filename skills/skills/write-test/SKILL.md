---
name: write-test
description: Smartup24 (x24) uchun yangi Playwright + pytest test yozish. Foydalanuvchi yangi test, test funksiya yoki test fayl yaratmoqchi bo'lganda ishlatiladi.
---

# Yangi Test Yozish (Smartup24)

Quyidagi qoidalarga qat'iy rioya qil.

## 1. Loyiha strukturasi

Loyiha **tekis (flat)** strukturada — eski `tests/smoke/...`, group runner, `scripts/run_tests.py` YO'Q.

- Testlar: `tests/test_<nomi>.py`
- Flowlar: `flows/flow_<nomi>.py` (`flow_authorization.py`, `flow_navbar.py`)
- Base funksiyalar: `utils/base_page.py` — `BasePage` klassi
- All runner: `tests/test_all.py`
- Fixtures: `conftest.py`
- Config: `pytest.ini` (`testpaths = .`, `python_files = test_*.py`)

## 2. Test fayl shabloni (`run_` + `test_` ikki funksiya)

Har bir test fayl IKKI funksiyadan iborat:

- **`run_<nomi>(page, code)`** — qayta ishlatiladigan biznes logika; `test_all` zanjiri shuni chaqiradi. `page` ni **allaqachon login qilingan** deb qabul qiladi (ichida `authorization` chaqirmaydi). Docstringda raqamlangan testcase qadamlari.
- **`test_<nomi>(page, code)`** — pytest entry (alohida/debug run uchun). `authorization(page)` qilib, so'ng `run_<nomi>(page, code)` ni chaqiradi.

```python
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_<nomi>(page: Page, code) -> None:
    """Testcase: <maqsad>.

    1. Модератор -> <Menyu> ro'yxatini ochish.
    2. "Создать" -> majburiy maydonlarni to'ldirish.
    3. Saqlab, ro'yxatda nom/kod bo'yicha ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"<entity>-{code}"

    flow_navigate(page, tab="Модератор", name="<Menyu>")
    m.expect_heading("<Ro'yxat heading>")

    m.open_create()
    m.expect_heading("<Create heading>")
    m.input(label="Название", value=name)
    m.save_and_expect_heading("<Ro'yxat heading>")

    m.grid_row(name)


def test_<nomi>(page: Page, code) -> None:
    authorization(page)
    run_<nomi>(page, code)
```

### `run_` / `test_` konvensiya qoidalari
- **Barcha forma amallari `BasePage` orqali** (input, select, multiselect, radio, checkbox, grid_row, save_and_expect_heading, expect_heading). Raw `page.get_by_role/locator` faqat mos base funksiya yo'q joyda — masalan navbar tab, sub-nav LINK (`page.get_by_role("link", name=...)`), "Создать"/"Сохранить"/"Подтипы" tugmalari uchun (tugmalar uchun `BasePage.click_button(...)` ham bor).
- **`run_` auth qilmaydi** — `page` login qilingan deb keladi. `test_all` bir marta login qilib zanjirni yuritadi.
- **Unikal nom** — `code` fixture (session-scoped 4 xonali son) bilan: `f"Manufacturer-{code}"`. Bu testni qayta ishga tushirsa ham xatosiz qiladi. Alohida o'zgaruvchiga yig'ib olma, kerakli joyda `f"...{code}"` yoz.
- **Har navigatsiya/save dan keyin `expect_heading(...)`** — bu keyingi amal to'g'ri formada bajarilishini kafolatlaydi (form-stack race'ining oldini oladi, [debug-test] ga qara).
- **Verifikatsiya zanjiri**: `open_create` -> forma to'ldir -> `save_and_expect_heading(list heading)` -> (kerak bo'lsa `search(...)`) -> `grid_row(name)`.
- **Cross-test dependency**: agar test oldingi test yaratgan qiymatga bog'liq bo'lsa (masalan product Производитель/Отрасль ni tanlaydi), bir xil `code` bilan `f"...{code}"` orqali topiladi; `test_all` da tartib to'g'ri bo'lsin.

## 3. Umumiy qoidalar

- **Fixtures** — `conftest.py` dan keladi, import qilma:
  - `page` — har test uchun fresh browser+context (trace yoziladi, teardownda `logout`)
  - `session_page` — session-scoped yagona page (chain uchun)
  - `code` — session-scoped 4 xonali unikal son (nom sifatida ishlat)
  - `save_data("key", value)` / `load_data("key")` — `test-results/data/data_store.json`
- **Locator**: barqaror `smtid` yoki ko'rinadigan label ishlatilsin (BasePage buni o'zi qiladi). **Dinamik `input[name="ng.formN.*"]` va `#cdk-drop-list-N` ISHLATMA** — ular har run'da o'zgaradi.
- **Assert**: `expect(locator).to_be_visible()` (BasePage ichida). Python `assert` va `time.sleep()` ishlatma.
- **Timeout**: `DEFAULT_TIMEOUT` (10s) yetarli; kutish kerak bo'lsa `expect(...)` yoki `wait_for_loader()`.
- **MCP bilan tekshir**: yangi forma yozganda avval Playwright MCP bilan sahifani ochib real DOM/label/smtid ni tekshir; fieldlarni taxmin qilma.

## 4. Runner ga qo'shish

Yangi test yozilgach `tests/test_all.py` ga `run_` ni import qilib zanjirga qo'sh:

```python
from tests.test_<nomi> import run_<nomi>

def test_all(page: Page, code) -> None:
    authorization(page)
    run_manufacturer(page, code)
    ...
    run_<nomi>(page, code)
```

## 5. Loyiha xususiyatlari (Smartup24 x24 UI)

Yangi UI Angular `smt-*` komponentlaridan iborat. `BasePage` shu patternlarni qamraydi:

| Element | Selektor | BasePage funksiyasi |
|---------|----------|---------------------|
| Text input | `smt-input[smtid]` → `input` | `input(label=/smtid=, value=)` |
| Select (Подбор) | `smt-data-select[smtid]`, dropdown `.cdk-overlay-container smt-select-dropdown li` | `select(text, label=/smtid=)` |
| Multi-select | `smt-data-select` (bir nechta) | `multiselect(*texts, label=)` |
| Radio (Статус) | `smt-radio-group[smtid]` → `label[smt-radio]` (value A/P/S) | `radio(text, label=)` |
| Switch / Checkbox (Статус) | `smt-switch` / `smt-checkbox` (ichki `input[type=checkbox]`, `[role=switch]`) | `checkbox(label=, checked=)` |
| Grid qatori | `.smt-data-row` | `grid_row(text, *contains)` / `click_grid_row(text)` |
| Qidiruv | `searchbox "Поиск..."` | `search(text)` |
| Heading | `app-form-stack-widget` title span | `expect_heading(text)` / `current_heading_text()` |
| Loader | `app-global-page-loader` | `wait_for_loader()` |
| Sub-nav bo'lim (link) | `app-form-stack-widget` ichidagi `link` | `click_link(name)` |
| "Создать" | tugma | `open_create()` |
| Boshqa tugma | — | `click_button(name)` |
| Saqlash | "Сохранить" | `save_and_expect_heading(heading)` |

- **`smtid` — barqaror identifikator** (masalan `smt-input[smtid="name"]`). Ba'zi selectlarda `smtid` yo'q (`null`) — bunda `label` bilan top (masalan `select("кг", label="measure")`).
- **Label bilan topish**: control labelning eng yaqin ajdodi ichida bo'ladi — vertikal (`div.flex.flex-col > label + smt-input`) ham, gorizontal (`div.flex.items-center > span "Статус" + smt-switch`) ham ishlaydi. Label matni anchored regex bilan mos keladi ("Название" "Краткое название" ni tutmaydi).
- **Select tanlangach** qiymat select MATNIDA emas, Подбор INPUT value'sida bo'ladi — `select()` buni to'g'ri tekshiradi.
- **Статус turi formaga qarab farq qiladi**: radio (`radio(...)`) yoki switch (`checkbox(...)`). Avval MCP bilan formani ochib turini aniqla.
- **Sub-nav bo'limga `click_link(name)` bilan o't** (raw `get_by_role("link").click()` emas): sub-header va asosiy kontent alohida router-outletда asinxron yangilanadi, `click_link`/`open_create` ichidagi `_settle()` transition tugashini kutadi va noto'g'ri formada "Создать" bosilishini oldini oladi.
- **Xarakteristика (product)**: product formada Отрасль/Бренд selectlari "Характеристика" tugmasi bosilgach ko'rinadi; "Категория" product-level select emas.
- **Namunalar**: `tests/test_manufacturer.py` (sodda, sub-nav link), `tests/test_region.py` (menyudan to'g'ridan-to'g'ri + switch), `tests/test_product.py` (select/multiselect, cross-test dependency).

## 6. Ish tartibi

1. `$ARGUMENTS` bo'yicha kerakli fayllarni o'qi
2. Mavjud o'xshash testni (`tests/test_manufacturer.py` — eng sodda namuna) o'rganib shablon chiqar
3. Kerak bo'lsa Playwright MCP bilan formani ochib real label/smtid ni tekshir
4. `run_`/`test_` juftligini yoz
5. `tests/test_all.py` ga qo'sh
6. `.venv/bin/python -m pytest tests/test_<nomi>.py -v` bilan tekshir (yoki `tests/test_all.py`)
7. Foydalanuvchiga qaysi fayllarga nima qo'shilganini ko'rsat
