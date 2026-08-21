# Валюта refaktoring — optimizatsiya ro'yxati

Branch: `refactor/valyuta-regression`
Boshlangan: 2026-08-20

Har bir tuzatish bajarilgach shu jadvaldagi **Status** yangilanadi
(⬜ kutilmoqda · 🔄 jarayonda · ✅ bajarildi · ⏭️ o'tkazib yuborildi).

## Umumiy holat

| # | Muammo | Muhimlik | Status |
|---|--------|----------|--------|
| 1 | `m` fixture ishlatilmaydigan parametr — siblinglar bilan konsistensiya buzilgan | 🔴 Muhim | ✅ |
| 2 | Status so'zi tili aralash (Неактивный / passive / active) | 🟡 O'rta | ✅ |
| 3 | Navigatsiya/heading boilerplate ~8 marta takror + sehrli satrlar | 🟡 O'rta | ✅ |
| 4 | `run_valyuta` ikki vazifa: yaratish + to'liq verifikatsiya | 🟡 O'rta | ✅ (ataylab qoldirildi) |
| 5 | Yashirin tartib bog'liqligi (`flow_menu` idempotentligiga tayanish) | 🟢 Kichik | ✅ (hujjatlashtirildi) |
| 6 | Junk fayllar tracked bo'lmasin (after_step*.txt, .vscode/ va h.k.) | 🟢 Kichik | ✅ (qisman) |
| 7 | `.github/workflows/tests.yml` CI ni ko'rib commit qilish | 🟢 Kichik | ✅ (ko'rildi, tuzatish shart emas) |

---

## Tafsilotlar

### 1. `m` fixture ishlatilmaydigan parametr sifatida turibdi 🔴
**Fayl:** `tests/test_regression/test_valyuta.py:263,271,279,287,300,308`

Imzo `test_valyuta_full(m: BasePage, page: Page, code)` — `m` hech qachon
ishlatilmaydi, `run_valyuta_full` o'zining `BasePage(page)`'sini quradi.
`m` faqat login side-effect'i uchun so'ralgan.

Qo'shni modullarning hammasi boshqacha (`test_legal_person.py:121`):
```python
def test_legal_person_full(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_legal_person_full(page, code)
```
Valyuta yagona istisno → chalkash + suite bo'ylab bir xillik buzilgan.

**Taklif:** bitta uslubni tanlab hammasini moslashtirish. Siblinglar bilan
moslash uchun `(page, code)` + aniq `authorization(page)`.

**Status:** ✅ bajarildi (2026-08-20) — 6 ta test imzosi `(m, page, code)` →
`(page, code)` ga o'zgartirildi, har biriga `authorization(page)` +
`allure.step("Tizimga kirish")` qo'shildi; `authorization` import qilindi.
`test_legal_person.py` naqshiga to'liq mos.

---

### 2. Status so'zi tili aralash 🟡
**Fayllar:**
- `tests/test_setup/test_valyuta.py:55` → `grid_row(name, "Неактивный")` (ru)
- `tests/test_regression/test_valyuta.py:192,217` → `"passive"`/`"active"` (en)
- `tests/test_regression/test_valyuta.py:138` → `expect_value="active"` (en)

BasePage `_STATUS_SYNONYMS` qoplaydi (ishlaydi), lekin bitta modulda uch xil
til — kengaytiruvchi qaysi to'g'ri deb chalg'iydi.

**Taklif:** modul bo'ylab bitta tilga standartlashtirish.

**Status:** ✅ bajarildi (2026-08-20) — barcha status so'zlari RUSCHA
("Активный"/"Неактивный") ga standartlashtirildi (setup allaqachon shunday
edi). `click_button`, `grid_row`, `input expect_value` — hammasi BasePage
`_STATUS_SYNONYMS` (base_page.py:609) orqali ikkala tilni qabul qilishi
tasdiqlangan, shuning uchun UI ru↔en almashsa ham ishlaydi. Izohlar ham
yangilandi.

---

### 3. Navigatsiya/heading boilerplate takrori + sehrli satrlar 🟡
**Fayl:** `tests/test_regression/test_valyuta.py` (barcha run_*), `tests/test_setup/test_valyuta.py`

```python
flow_navigate(page, tab="Модератор", name="Валюты")
m.expect_heading("Валюты")
```
~8 marta qaytadi; `flow_menu + search + grid_row` naqshi ham.

**Taklif:** modul-ichi helper + konstantalar:
```python
TAB, LIST, CREATE_HEADING = "Модератор", "Валюты", "Валюта (Создания)"
def _open_list(page, m):
    flow_navigate(page, tab=TAB, name=LIST); m.expect_heading(LIST)
```

**Status:** ✅ bajarildi (2026-08-20) — `test_setup/test_valyuta.py` ga
`TAB`/`LIST_HEADING`/`CREATE_HEADING` konstantalari va `open_valyuta_list(page, m)`
helper'i qo'shildi (yagona manba). Regression moduli shularni import qiladi;
6 ta `flow_navigate(...)+expect_heading("Валюты")` juftligi va 3 ta
`expect_heading("Валюта (Создания)")` literal'i almashtirildi. `flow_navigate`
import regressiyadan olib tashlandi (endi ishlatilmaydi).

---

### 4. `run_valyuta` ikki vazifani bajaradi 🟡
**Fayl:** `tests/test_setup/test_valyuta.py:9-57`

Setup sifatida (Arrange) chaqirilganda `flow_menu + search + grid_row`
verifikatsiyasi ortiqcha ish; niyat noaniq.

**Taklif:** `verify=True/False` bayrog'i yoki sof `_create` + alohida
`_assert_in_list`.

**Status:** ✅ ATAYLAB qoldirildi (2026-08-20) — chuqurroq tekshiruvda
saqlashdan keyingi qidiruv+grid tekshiruvi YUK KO'TARUVCHI ekani aniqlandi:
ro'yxatni yaratilgan yozuvga filtrlab qoldiradi, CRUD ssenariylari esa keyin
to'g'ridan-to'g'ri `click_grid_row(name)` chaqiradi (alohida qidiruvsiz).
`verify=False` bilan ajratish edit/delete/status'ni sindirardi. Yaratish+
verifikatsiya setup helperida standart "fail-fast" pattern. Niyat endi
`run_valyuta` docstring'ida aniq hujjatlashtirildi (kod o'zgarmadi, faqat izoh).

---

### 5. Yashirin tartib bog'liqligi (`flow_menu`) 🟢
**Fayl:** `tests/test_regression/test_valyuta.py` run_valyuta_edit/status

Edit'dan keyingi `search` `flow_menu`'siz ishlaydi — oldingi `run_valyuta`
sozlamani serverda yoqqani uchun. Qayta tartiblansa sindiradi.

**Taklif:** izoh yoki har qidiruvdan oldin `flow_menu` (idempotent).

**Status:** ✅ HUJJATLASHTIRILDI (2026-08-20) — har qidiruvdan oldin `flow_menu`
qo'shish RAD ETILDI: u dialog kliklarini takrorlab flaky yuzani oshiradi
(`cdk-overlay-flaky-clicks` xotirasi) — sof zarar. Bog'liqlik aslida
strukturaviy jihatdan DOIM bajariladi (har CRUD ssenariysi avval `run_valyuta`
chaqiradi, u `flow_menu` bilan Название-qidiruvni serverda bir marta yoqadi,
sozlama sessiya davomida saqlanadi). Bu `run_valyuta` docstring'ida aniq
yozib qo'yildi.

---

### 6. Junk fayllar 🟢
`after_step1..8.txt`, `before.txt`, `bonus_page2.md`, `moderator-menu.md`,
`.vscode/` — `.gitignore`'ga qo'shish yoki o'chirish.

**Status:** ✅ qisman (2026-08-20) — `.gitignore`'ga qo'shildi: `.vscode/`
(kommentdan ochildi), `before.txt`, `after_step*.txt`. `bonus_page2.md` va
`moderator-menu.md` — ATAYLAB tegilmadi: ular scratch emas, foydalanuvchi
eslatmasi bo'lishi mumkin (fayl o'chirish "look before you leap"). User
qaroriga qoldirildi: kerak bo'lmasa o'chirish yoki `.gitignore`'ga qo'shish.

---

### 7. `.github/workflows/tests.yml` CI 🟢
Yangi CI — ataylab ko'rib commit qilish. DIQQAT: `headless=False` +
`--start-maximized` CI'da ishlamaydi, tekshirish kerak.

**Status:** ✅ ko'rildi (2026-08-20) — headless xavotir NOTO'G'RI chiqdi: CI
`HEADLESS: "1"` beradi (tests.yml:44), `conftest.py:210` uni o'qib brauzerni
headless ishga tushiradi, `--window-size=1920,1080` esa oyna o'lchamini
qoplaydi. CI to'g'ri tuzilgan (workflow_dispatch + tunги cron, concurrency
guard, Allure→gh-pages). Kod tuzatish SHART EMAS — user faylni ataylab
commit qilishi kifoya.
