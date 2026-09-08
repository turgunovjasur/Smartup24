# Smartup24 — E2E UI test avtomatizatsiyasi

Smartup24 (x24) ERP tizimining **uchidan-uchiga (E2E) UI testlari**. Testlar
haqiqiy brauzerda (Chromium) ilovaning veb-interfeysini xuddi foydalanuvchidek
boshqaradi: login qiladi, formalarni to'ldiradi, saqlaydi va natijani tekshiradi.

- **Framework:** [Playwright for Python](https://playwright.dev/python/) + [pytest](https://docs.pytest.org/)
- **Hisobot:** [Allure](https://allurereport.org/) (`allure-pytest`)
- **Til:** testlar va izohlar o'zbekcha; ERP UI matnlari ruscha (`Сохранить`, `Поиск` …)

## Nima uchun kerak
Smartup24 katta ERP — ma'lumotnomalar, hujjatlar, buyurtma oqimi, opros moduli va h.k.
Har relizda qo'lda tekshirish qimmat. Bu suite kritik oqimlarni (справочник CRUD,
Поставщик/Клиент, buyurtma va uning statusi, hisobotlar) avtomatik yugurtiradi va
xato chiqsa **skrinshot + tushunarli sabab + Allure trace** bilan xabar qiladi.

---

## 1. O'rnatish

```bash
# 1) Virtual muhit
python -m venv .venv
.venv\Scripts\activate            # Windows (PowerShell/CMD)
# source .venv/bin/activate       # Linux/Mac

# 2) Bog'liqliklar
pip install -r requirements.txt

# 3) Playwright brauzeri
playwright install chromium
```

Talablar: **Python 3.11+**. Paketlar: `pytest`, `playwright`, `allure-pytest`,
`openpyxl` (xlsx hisobot testlari), `requests`, `python-dotenv`.

Allure hisobotini ochish uchun **Allure CLI** ham kerak (Java asosida):
`scoop install allure` yoki `npm i -g allure-commandline`.

---

## 2. Muhit (dev / prod)

Suite ikki muhitда ishlaydi. Muhitni **`TEST_ENV`** environment variable tanlaydi —
faylni qo'lda tahrirlash shart emas:

| `TEST_ENV` | URL | Kompaniya | Admin |
|------------|-----|-----------|-------|
| `dev` (default) | `https://app2.greenwhite.uz/x24/a2/auth/login` | `sm24` | `admin@sm24` |
| `prod` | `https://app.smartup24.com/a2/auth/login` | `test` | `admin@test` |

Parol ikkala muhitда ham `greenwhite`. Konfiguratsiya: [`flows/flow_authorization.py`](flows/flow_authorization.py).

```bash
# Windows PowerShell
$env:TEST_ENV = "prod"; python -m pytest tests/test_setup/test_all_setup.py -v
# default (dev) — hech narsa qo'ymaslik
python -m pytest tests/test_setup/test_all_setup.py -v
```

> ⚠️ `app.smartup24.com/login.html` — **eski** UI, testlar u yerda ishlamaydi.
> Yangi UI: prod'da `/a2/...`, dev'da `/x24/a2/...`.

---

## 3. Testlarni ishga tushirish

Suite **bo'limlarga** bo'lingan; har bo'lim o'z runner faylida, bitta login (seans)
bilan ketma-ket ishlaydi. Turli jadvalda ishlashi uchun ajratilgan.

### Qisqa buyruqlar (tavsiya etiladi)
Guruhni qisqa nom bilan ishga tushiring — to'liq yo'l yozish shart emas:

```bash
pytest setup            # setup bo'limi (справочник create)
pytest group_a          # Поставщик/Клиент → buyurtma oqimi
pytest regression       # to'liq CRUD regressiya
pytest main             # "Главное" bo'limi
pytest document         # hujjat moduli
pytest visit            # vizit/marshrut testlari
pytest setup -v         # bayroqlar bilan birga ishlaydi
```

> Mexanizm: [`conftest.py`](conftest.py) `pytest_configure` — argument tanish
> guruh nomi bo'lsa va haqiqiy fayl BO'LMASA uni mos runner fayl(lar)iga
> almashtiradi. Standart `pytest <path>` / `-k` / `-m` ishlashi buzilmaydi.
> `python -m pytest` ham, bare `pytest` ham ishlaydi. Yangi guruh qo'shish —
> `conftest.py` dagi `GROUP_ALIASES` lug'atiga bitta qator.

### To'liq yo'l bilan (ekvivalent)

```bash
# Bo'lim runnerlari
python -m pytest tests/test_setup/test_all_setup.py -v              # справочник create (asos)
python -m pytest tests/test_group_a/test_all_group_a.py -v          # Поставщик/Клиент → buyurtma oqimi
python -m pytest tests/test_regression/test_all_regression.py -v    # to'liq CRUD regressiya
python -m pytest tests/test_main/test_all_main.py -v                # "Главное" (Организации/Роли …)
python -m pytest tests/test_document/test_all_document_runner.py -v # hujjat/vizit moduli

# Bitta modul (debug uchun) — har biri o'z login bilan
python -m pytest tests/test_setup/test_manufacturer.py -v
python -m pytest tests/test_regression/test_region.py -v

# HAMMASI bitta chaqiruvda (tartib saqlanadi, nomlar to'qnashmaydi)
python -m pytest tests/test_setup/test_all_setup.py tests/test_group_a/test_all_group_a.py \
  tests/test_regression/test_all_regression.py tests/test_main/test_all_main.py \
  tests/test_document/test_all_document_runner.py -v
```

**Allure hisoboti:**
```bash
allure serve test-results/allure-results
```

> Brauzer `headless=False` (ko'rinadigan) rejimda ochiladi — run paytida oynaga
> tegmang. Bir vaqtda **faqat bitta** run ishlashi mumkin (ulashilgan ERP
> akkaunt) — conftest global `run.lock` bilan ikkinchisini rad etadi.

### Kod varianti (nom to'qnashuvi bo'lmasligi uchun)
Testlar unikal nomlar uchun `code` fixture (random 4-xonali son) ishlatadi:
setup = `code`, group_a = `{code}2`, regression = `{code}3`. Shu sabab bo'limlar
birga ishlaganda yaratilgan yozuvlar bir-birini bosmaydi.

---

## 4. Loyiha tuzilmasi

```
conftest.py                — pytest fixtures, Allure setup, failure skrinshot,
                             Telegram xabar, session-lock/chunk-load handlerlar
requirements.txt           — bog'liqliklar
pytest.ini                 — testpaths, allure addopts, norecursedirs

flows/
  flow_authorization.py    — authorization(page, email, pwd), logout(page); TEST_ENV
  flow_navbar.py           — flow_navigate(page, tab, name), flow_search(), flow_menu()

utils/
  base_page.py             — BasePage: barcha forma amallari uchun universal metodlar
  base_api.py              — mobil vizit API klienti (VisitApi, requests)
  qa_report.py             — biznes tilidagi xato hisoboti (qa_step / friendly_reason)

tests/
  test_setup/              — справочник create namunalari + test_all_setup.py runner
  test_group_a/            — Поставщик/Клиент, userlar, hamkorlik, buyurtma + runner
  test_regression/         — to'liq CRUD (create/edit/view/delete/status/duplicate) + runner
  test_main/               — "Главное" bo'limi (Организации, Роли …) + runner
  test_document/           — hujjat/vizit moduli + runner

scripts/cleanup_test_data.py — test ma'lumotlarini bulk tozalash (o'chmasa deaktivatsiya)
tg_bot_runner.py             — Telegram bot: masofadan run start/stop
.github/workflows/e2e.yml    — jadvalli (cron) CI run
.skills                      — CHUQUR bilim bazasi: UI patternlar, DOM tafsilotlari, tarix
```

---

## 5. Test qanday yoziladi (konvensiya)

Har modul ikki funksiyaga ega:

- **`run_<nomi>(page, code)`** — biznes logika; login qilinganini kutadi (runner chaqiradi).
- **`test_<nomi>(page, code)`** — `authorization(page)` + `run_<nomi>(...)` (alohida ishlatish uchun).

Eng sodda namuna — [`tests/test_setup/test_manufacturer.py`](tests/test_setup/test_manufacturer.py).

```python
import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_manufacturer(page: Page, code) -> None:
    m = BasePage(page)
    name = f"Manufacturer-{code}"                     # unikal nom = nom + code

    with allure.step("Навигация: Модератор → Товары"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")

    with allure.step("Производители bo'limiga o'tish"):
        m.click_link("Производители")                 # list ichidagi sub-nav link
        m.expect_heading("Производители")

    with allure.step(f"Yangi ishlab chiqaruvchi: {name}"):
        m.open_create()
        m.expect_heading("Производитель (Создание)")
        m.input(label="Название", value=name)
        m.save_and_expect_heading("Производители")

    with allure.step(f"Ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.title("Setup: Производитель yaratish")
def test_manufacturer(page: Page, code) -> None:
    authorization(page)
    run_manufacturer(page, code)
```

**Qoidalar:**
1. Barcha forma amallari **`BasePage`** orqali (navbar/link uchun `flow_*` yoki raw `get_by_role`).
2. Unikal nom har doim `f"...{code}"`.
3. Har navigatsiya/save dan keyin `m.expect_heading(...)` bilan tasdiqla.
4. Qadamlarni `with allure.step("...")` bilan o'ra — hisobot va xato sababi shundan chiqadi.
5. Yangi test tegishli bo'lim runneriga alohida `test_...` sifatida qo'shiladi.

### BasePage — tez-tez ishlatiladigan metodlar
Element **`label`** (ko'rinadigan matn) yoki barqaror **`smtid`** orqali topiladi.

```python
m = BasePage(page)
m.input(label="Название", value="...")      # matn kiritish
m.select("кг", label="Ед. изм.")            # select (Подбор) / tree / multi — avtomatik
m.multiselect("A", "B", label="Роли")        # ko'p tanlov
m.radio("Активный", label="Статус")          # radio
m.checkbox(label="Статус", checked=True)     # switch/checkbox
m.search("matn")                             # ro'yxat qidiruvi
m.grid_row(name)                             # grid qatorini topish/tekshirish
m.click_grid_row(name)                       # qatorni ochish (action panel)
m.open_create()                              # "Создать"
m.click_button("Пользователи")               # ixtiyoriy tugma
m.save_and_expect_heading("Товары")           # "Сохранить" + heading tekshirish
m.expect_heading("...")                       # aktiv sarlavha
```

To'liq ro'yxat va UI patternlar (date-picker, tree-select, phone-input, view
formalari, wizard, opros moduli, status i18n va h.k.) — [`.skills`](.skills) da.

> Yangi UI patternni yozishdan oldin uni **Playwright MCP bilan real DOM'da tasdiqlang** — fieldlarni taxmin qilmang.

---

## 6. Xato bo'lganda — diagnostika

Test yiqilganда tushunarsiz Playwright stack o'rniga **biznes tilidagi sabab**
chiqadi (Telegram, Allure va traceback'da) + full-page skrinshot + Allure trace:

- **Grid qator topilmasa:** jami qator soni, searchbox qiymati, "Нет результатов"
  bor-yo'qligi, sahifa, ochiq `Ошибка` dialogi.
- **Saqlash o'tmasa:** backend `Ошибка` dialog matni (`dup_val_on_index`,
  precision, 500 …) asl sabab sifatida.
- **Select varianti yo'q:** dropdown'dagi mavjud variantlar ro'yxati.

Mexanizm: [`utils/qa_report.py`](utils/qa_report.py) (`qa_step` / `friendly_reason`) +
`conftest.py` `pytest_runtest_makereport`.

---

## 7. Telegram bot va CI

- **Bot** — [`tg_bot_runner.py`](tg_bot_runner.py): masofadan run boshqarish.
  `start [dev|prod] [all|setup_groupa|regression|main|document]` (default `dev all`);
  slash: `/start_dev`, `/regression_prod`, `/main_dev` … Jonli progress va yakuniy
  natija Telegram'ga yoziladi.
- **CI** — [`.github/workflows/e2e.yml`](.github/workflows/e2e.yml): jadvalli (cron)
  run — har 2 soatda setup+group_a, har 12 soatda regression (bitta concurrency
  guruhida, parallel yo'q).

Telegram uchun `.env` (ixtiyoriy): `TG_BOT_TOKEN`, `TG_CHAT_ID`, `HOST_LABEL`.

---

## 8. Ma'lumotlarni tozalash

Test yaratgan yozuvlarni bulk tozalash (o'chmasa deaktivatsiya qiladi):
```bash
python scripts/cleanup_test_data.py
```
Tozalash testdan **ajratilgan** — testni yiqitmaydi, kerak bo'lganda alohida ishlatiladi.

---

## 9. Muhim eslatmalar

- Bir vaqtda **bitta** run (ulashilgan akkaunt) — `run.lock` himoyasi bor.
- Login'dan ~30 daqiqa keyin chiqadigan **sessiya qulfi** va dev deploy paytidagi
  **chunk-load** xatosini conftest handlerlari avtomatik yechadi.
- Dinamik `input[name="ng.formN.*"]` / `#cdk-drop-list-N` selektorlarini
  **ishlatmang** — har run'da o'zgaradi; `smtid` yoki `label` ishlating.
- Chuqurroq kontekst, tarix va barcha UI nozikliklari — [`.skills`](.skills) faylida.
```
