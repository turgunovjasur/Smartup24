---
name: review-test
description: Smartup24 test kodini senior QA ko'zi bilan review qilish. Sifat, barqarorlik, base funksiya ishlatilishi, fixture va anti-patternlarni tekshiradi.
allowed-tools: Read, Glob, Grep
---

# Test Kodni Review Qilish (Smartup24)

Fayl: `$ARGUMENTS`

## Review tekshiruv ro'yxati

### 1. Struktura
- [ ] Fayl `run_<nomi>(page, code)` + `test_<nomi>(page, code)` juftligidan iborat
- [ ] `run_` auth qilmaydi (page login qilingan deb keladi); `test_` `authorization(page)` qilib `run_` ni chaqiradi
- [ ] `run_` `tests/test_all.py` zanjiriga qo'shilgan (agar umumiy oqim bo'lsa)
- [ ] Docstringda raqamlangan testcase qadamlari bor

### 2. Base funksiya ishlatilishi (ENG MUHIM)
- [ ] Barcha forma amallari `BasePage` orqali: `input`, `select`, `multiselect`, `radio`, `checkbox`, `grid_row`, `click_grid_row`, `search`, `save_and_expect_heading`, `expect_heading`, `open_create`, `click_button`
- [ ] Raw `page.locator/get_by_role` faqat base funksiya yo'q joyda (navbar tab, sub-nav link, forma bo'lmagan tugma)
- [ ] Element `label` yoki `smtid` orqali topilgan — **dinamik `input[name="ng.formN.*"]` yoki `#cdk-drop-list-N` YO'Q**

### 3. Barqarorlik
- [ ] Har navigatsiya/save dan keyin `expect_heading(...)` bor (form-stack race'ining oldini oladi)
- [ ] Unikal nom `f"...{code}"` bilan (hardcode "Manufacturer-1" kabi emas) — test qayta run bo'lsa ham ishlaydi
- [ ] Cross-test dependency bir xil `code` orqali hal qilingan
- [ ] `time.sleep()` / `page.wait_for_timeout()` yo'q — `expect(...)` yoki `wait_for_loader()`

### 4. Fixture ishlatilishi
- [ ] `code` parametr sifatida kelgan (import qilinmagan)
- [ ] `save_data` / `load_data` kerak bo'lsa to'g'ri ishlatilgan
- [ ] `page` (izolyatsiya) va `session_page` (chain) to'g'ri tanlangan

### 5. Anti-patternlar
- [ ] Python `assert` emas, `expect(...)` (BasePage ichida)
- [ ] `try/except` bilan xatolar yashirilmagan (logout teardowndan tashqari)
- [ ] Hardcode literal qiymat (`autotest`, `product-1`) test ichida emas — `code`/`load_data` dan
- [ ] Biznes logika `run_` da, takrorlanadigan navigatsiya `flows/` da; 1 qatorlik wrapper yo'q
- [ ] Testcase noto'g'ri, ortiqcha yoki biznes flowga mos kelmasa — alohida ko'rsatilgan

## Natija formati

Har bir muammo uchun:
- **Muammo**: nima xato
- **Joyi**: fayl:qator
- **Yechim**: qanday tuzatish kerak

Oxirida umumiy baho: `Yaxshi / O'rta / Qayta ko'rib chiqish kerak`
