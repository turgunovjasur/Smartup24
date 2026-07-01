---
name: debug-test
description: Muvaffaqiyatsiz testni tahlil qilib sabab topish va tuzatish. Test xatosi, timeout, locator muammolari haqida so'ralganda ishlatiladi.
allowed-tools: Read, Glob, Grep, Bash
---

# Muvaffaqiyatsiz Testni Debug Qilish

Test: `$ARGUMENTS`

## Tahlil tartibi

### 1. Log va trace fayllarni o'qi
```
test-results/logs/          — xato loglari
test-results/traces/        — Playwright trace (.zip)
test-results/allure-results/ — Allure natijalar
```

Avval `test-results/logs/` dagi tegishli log faylni o'qi.

### 2. Xato turini aniqlash

| Xato | Sabab | Yechim |
|------|-------|--------|
| `TimeoutError` | Element ko'rinmayapti | Locator tekshir, sahifa yuklangan-yuklangani |
| `StrictModeViolation` | Bir nechta element topildi | Locator aniqroq qil |
| `ElementNotFound` | Element yo'q | Page state tekshir, flow tartibini ko'r |
| `AssertionError` | Qiymat mos kelmayapti | Kutilgan vs haqiqiy qiymatni solishtir |
| `JSONDecodeError` | data_store.json buzilgan | Faylni o'chirib qayta run qil |
| `pytest.exit` | `code` fixture topilmadi | Avval `test_setup_runner.py` yoki `run_tests.sh` ishlatilsin |

### 3. Locator muammolari

Locator ishlayotganini tekshirish uchun Playwright konsolda:
```js
document.querySelectorAll('<selector>')
```

Yaxshi locator tartibi:
1. `data-testid` atributi (eng ishonchli)
2. `role` + `name` kombinatsiyasi
3. Matn orqali: `page.get_by_text()`
4. CSS selektor (oxirgi chora)

### 4. Session state muammolari

`session_page` ishlatilganda testlar ketma-ket ishlaydi. Agar oldingi test muvaffaqiyatsiz bo'lsa:
- `data_store.json` ni tekshir
- `code` fixture qiymati to'g'ri saqlanganmi

### 5. Tuzatish

1. Xato sababini aniq ko'rsat
2. Tuzatilgan kodni ko'rsat (faqat zarur qator)
3. Qayta test ishga tushirish buyrug'ini ber
4. Agar tizim muammosi bo'lsa (server, env) — foydalanuvchiga ayт

## Chiqish formati

```
Xato turi: <TimeoutError / AssertionError / ...>
Joyi: <fayl>:<qator>
Sabab: <nima bo'ldi>
Yechim: <nima qilish kerak>
```

## Loyiha Xususiyatlari

### #biruniConfirm modal (Bootstrap fade animatsiyasi)
- `да` tugmani bosishdan **oldin** modal opacity `1` bo'lishini kutish shart, aks holda click register bo'lmaydi:
  ```python
  expect(page.locator("#biruniConfirm")).to_have_css("opacity", "1")
  page.get_by_role("button", name="да", exact=True).click()
  page.locator("#biruniConfirm").wait_for(state="hidden")
  ```
  (`wait_for_function` emas — loyihada standart pattern `to_have_css`, `test_room.py` da ham shunday)
- `да` bosilgandan keyin modal **darhol** yopiladi, keyin loader (`wait_for_loader`) ishlaydi — `wait_for(state="hidden")` uchun uzun timeout kerak emas
- `да` tugmani har doim `#biruniConfirm` ga scope qilish kerak — `page.get_by_role("button", name="да")` butun sahifada qidiradi va animatsiya davomida noto'g'ri elementni bosishi mumkin

### session_page va domino effekti
- `session_page` barcha testlar uchun umumiy — bitta test fail bo'lib modal qolsa, keyingi barcha testlar ham fail bo'ladi
- `--maxfail=3` pytest.ini da sozlangan — 3 fail dan keyin sessiya to'xtatiladi
- Test yozish/debug iteratsiyasida precondition entity `data_store.json` da mavjud bo'lsa, masalan contract yaratilgan va code/name saqlangan bo'lsa, keyingi order xatosini tekshirish uchun contract testni qayta run qilish shart emas; mavjud qiymatdan foydalan.

### Form screenshot arxivi
- Smartup formalarini debug qilganda avval `skills/smartup-guide/references/forms/screenshots/<form-slug>/` ichida shu forma uchun screenshot bor-yo'qligini tekshir.
- Agar kerakli screenshot bo'lmasa yoki UI o'zgargan bo'lsa, formani ochib skill arxiviga saqla: `skills/smartup-guide/references/forms/screenshots/<form-slug>/<form-slug>__<state>__desktop-1920x1080.png`.
- `test-results/screens/smartup/` forma/debug screenshot arxivi uchun ishlatilmasin; `test-results/allure-results` faqat pytest/Allure failure attachment outputi.
- Yangi formaga kirilganda yoki URL/form state o'zgarganda screenshotni skill arxivida yangilab borish keyingi locator/debug ishlari uchun majburiy odat bo'lsin.

### to_contain_text() da exact parametri yo'q
- `expect(locator).to_contain_text("text", exact=True)` — **xato**, bu parametr mavjud emas
- To'liq mos kelish uchun `to_have_text("text")` ishlatiladi

### Orderda product chiqmasa
- Order add product qadamida tovar/product topilmasa, zaxira/balans yo'qligi yoki product bron qilingan orderlarda bandligi ehtimolini tekshir.
- Balans kerak bo'lsa setupdagi `test_20_init_balance` ni run qilib product balansini qo'shib kelish mumkin.
- Agar product bron qilingan bo'lsa, order listdagi bron qilingan orderlarni `Canceled/Отменен` statusga o'tkazish kerak.

### AI test summary
- Test run tugagandan keyingi xulosa uchun OpenAI emas, Gemini API ishlatiladi; default model `gemini-2.5-flash`, key esa faqat `GEMINI_API_KEY` environment variable orqali olinadi va repo/chat/logga yozilmaydi.
- `System summary` AI emas va har doim yoziladi: `test-results/system-summary.md/json`, Allure ichida `System Test Summary`; failed test, ichki Allure step, kod joyi, error turi, sabab va ta'sirni tizim o'zi chiqaradi.
- AI summary default holatda off; faqat `scripts/run_tests.py ... --ai-summary` flagi berilganda ishlaydi va faqat 1-2 gaplik qo'shimcha xulosa yozadi.
- AI xulosa `test-results/ai-summary.md/json` fayllariga yoziladi va Allure report ichida alohida `AI Test Summary` card sifatida attachment qilinadi; bu card test pass/fail statusini o'zgartirmaydi.
- Telegramdagi asosiy natija xabari AIga bog'liq bo'lmasin; xom Gemini API error, uzun stacktrace yoki locator logini asosiy xabar sifatida yuborma.
- `test_all_runner.py` kabi outer runner fail bo'lsa, Telegram xabarda faqat outer test nomi yetarli emas; Allure `steps` ichidan aynan qaysi ichki test/step yiqilganini (`inner_test`, `failed_step`, `source`) ko'rsatish shart.
