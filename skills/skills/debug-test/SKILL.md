---
name: debug-test
description: Muvaffaqiyatsiz Smartup24 testini tahlil qilib sabab topish va tuzatish. Test xatosi, timeout, locator muammolari haqida so'ralganda ishlatiladi.
allowed-tools: Read, Glob, Grep, Bash
---

# Muvaffaqiyatsiz Testni Debug Qilish (Smartup24)

Test: `$ARGUMENTS`

## Tahlil tartibi

### 1. Testni ishga tushirib xatoni ko'r
```bash
.venv/bin/python -m pytest tests/test_<nomi>.py -v --tb=short
```
Trace va failure screenshot:
```
test-results/traces/            — Playwright trace (.zip), test nomi bo'yicha
test-results/allure-results/    — Allure natijalar + failure screenshot (conftest avtomatik attach qiladi)
```

### 2. Real DOM ni MCP bilan tekshir
Locator/flow muammosida Playwright MCP bilan sahifani och, login qil va real DOM ni ko'r. Bu eng ishonchli usul — selektorni taxmin qilma. Konsolda tekshirish:
```js
document.querySelectorAll('smt-input[smtid="name"]')
document.querySelector('app-form-stack-widget span.font-semibold.truncate')?.innerText
[...document.querySelectorAll('smt-select-dropdown li')].map(l=>l.innerText)
```

### 3. Xato turini aniqlash

| Xato | Sabab | Yechim |
|------|-------|--------|
| `TimeoutError` / `to_be_visible` | Element ko'rinmayapti yoki noto'g'ri formada | Label/smtid tekshir, `expect_heading` bilan to'g'ri formada ekaniga ishonch hosil qil |
| `AssertionError: Locator expected to contain text` | Heading mos kelmadi | Aktiv title span ni tekshir (pastdagi form-stack race) |
| `StrictModeViolation` | Bir nechta element topildi | `index=`, `root=` yoki aniqroq `smtid`/`label` |
| Select tanlanmadi | Dropdown ochilmadi yoki qiymat topilmadi | `search=` matnini tekshir, option `.cdk-overlay-container` da render bo'ladi |
| `NameError` teardownda | flow import qilinmagan | `conftest.py` da kerakli import bor-yo'qligini tekshir |

## Loyiha xususiyatlari (Smartup24 x24 gotcha'lar)

### Heading race — `app-form-stack-widget` butun matni
- `app-form-stack-widget` matni **sarlavha + sub-nav LINK nomlarini** o'z ichiga oladi (masalan Товары sahifasida "Производители", "Характеристика товаров" linklari matnda bor).
- Shuning uchun `expect(widget).to_contain_text("Производители")` eski sahifada (sub-nav linkiga) **transition tugamasdan** mos kelib qoladi va keyingi amal (Создать) noto'g'ri formada bajariladi.
- **Yechim**: faqat aktiv title span tekshiriladi — `BasePage.expect_heading(...)` shuni qiladi (`app-form-stack-widget span.font-semibold.truncate:visible`). Har navigatsiya/save dan keyin `expect_heading(...)` chaqir.

### Ikki router-outlet — heading yangilanadi, lekin kontent hali eski (JIDDIY)
- Sub-header (`app-form-stack-widget` title) va asosiy kontent (`smartup24-app-*-list`, "Создать" shu yerda) **alohida router-outlet**da va **asinxron** yangilanadi.
- Товары -> Производители o'tishда title "Производители" ga o'tishi mumkin, lekin asosiy kontentда bir zum hali `product-list` (product'ning "Создать" tugmasi bilan) turadi. Faqat `expect_heading` bilan gate qilsang, `open_create` eski (product) formaning "Создать" ini bosib, **"Продукт (создание)"** ochilib qoladi.
- **Yechim**: navigatsiya/link'dan keyin kontent to'liq almashishini kut. `BasePage.open_create()`, `click_link()`, `click_grid_row()` ichida `_settle()` (loader + `networkidle`) bor. Sub-nav bo'limlariga `page.get_by_role("link").click()` emas, **`BasePage.click_link(name)`** bilan o't.

### Switch (Статус) vs radio vs checkbox
- Статус ba'zi formalarda `smt-radio-group` (product), ba'zilarida `smt-switch` (region). `smt-switch` gorizontal layoutda, labeli `<span>` ("Статус") — vertikal `div.flex.flex-col` emas.
- `BasePage.checkbox(label="Статус", checked=True)` ikkala `smt-switch` va `smt-checkbox` ni qamraydi (ichki `input[type=checkbox]` orqali holat, `[role=switch]/[role=checkbox]` bosiladi). Radio uchun esa `BasePage.radio("Активный", label="Статус")`. Formani MCP bilan ochib qaysi turini avval aniqlab ol.

### Select (Подбор) — qiymat input value'sida
- `smt-data-select` tanlangach tanlangan matn select TEXTIDA emas, ichki `input[placeholder="Подбор"]` VALUE'sida bo'ladi. `to_contain_text` bilan tekshirsang xato beradi; `BasePage.select()` input value orqali tasdiqlaydi.
- Dropdown `.cdk-overlay-container` ichida `smt-select-dropdown li` sifatida (body'ga portal) render bo'ladi — select elementi ichida emas.

### Ochiq dropdown backdrop clicklarni bloklaydi
- Select dropdown ochilganda `cdk-overlay-backdrop` paydo bo'ladi; agar oldingi select yopilmay qolsa, keyingi click "backdrop intercepts pointer events" xatosini beradi.
- **Yechim**: option tanlash dropdownni yopadi; kerak bo'lsa `Escape`. `BasePage.select/multiselect` buni boshqaradi (`close=True`).

### Dinamik locatorlar — ISHLATMA
- `input[name="ng.formN.name"]` (`N` har run'da o'zgaradi) va `#cdk-drop-list-N` (dinamik CDK id) — **ishonchsiz**. Buning o'rniga `smt-input[smtid]`, `smt-data-select[smtid]`, `.smt-data-row`, label asosidagi `BasePage` funksiyalarini ishlat.

### Radio (Статус) checkbox emas
- Smartup24 da Статус `smt-radio-group` (value `A`/`P`/`S`), checkbox emas. `BasePage.radio("Активный", label="Статус")` bilan tanlanadi, `checkbox(...)` bilan emas.

### logout teardown
- `page`/`session_page` fixture teardownida `flows.flow_authorization.logout(page)` chaqiriladi (avatar → "Выйти", himoyalangan try/except). U seansni yopib parallel seans limitini bo'shatadi; xato bersa testni buzmaydi.

## Chiqish formati

```
Xato turi: <TimeoutError / AssertionError / ...>
Joyi: <fayl>:<qator>
Sabab: <nima bo'ldi>
Yechim: <nima qilish kerak>
```
