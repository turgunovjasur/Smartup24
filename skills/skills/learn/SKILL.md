---
name: learn
description: Foydalanuvchi biror narsa tushuntirsa, o'rgatsa yoki xato sababini aytsa — bu bilimni avtomatik tegishli skill fayliga qo'shadi. PROAKTIV ishlatiladi, foydalanuvchi so'ramasdan ham.
allowed-tools: Read, Edit, Write, Glob
---

# Yangi Bilimni Skill ga Qo'shish

Argument: `$ARGUMENTS` (o'rganilgan narsa tavsifi)

## Qachon ishlatiladi (AVTOMATIK)

Quyidagi holatlarda foydalanuvchi so'ramasdan o'zing ishlat:
- Foydalanuvchi UI xatti-harakatini tushuntirsa ("modal shunday ishlaydi", "server shuncha vaqt ketadi")
- Xato sababini o'zi aytsa ("sabab hali modal ochilmasidan button bosilyapti")
- Loyiha qoidasini ko'rsatsa ("bu test faqat runner orqali ishlaydi")
- Avval qilgan yechim noto'g'ri chiqsa va to'g'ri yechim topilsa

## Ish tartibi

1. O'rganilgan bilimni qisqa va aniq jumlaga yaz
2. Qaysi skill fayliga tegishli ekanini aniqlash:
   - UI modal/animatsiya muammolari → `debug-test`
   - Test yozish qoidalari → `write-test`
   - Flow qoidalari → `new-flow`
   - Smartup biznes flowlari, UI joylashuvlari, entitylar, locatorlar → `smartup-guide` ichidagi mos reference fayl:
     - aniq forma bo'yicha bilimlar → `smartup-guide/references/forms/<form-slug>.md`
     - contract/order shartlari → `smartup-guide/references/contracts.md`
     - order flow/product/setup → `smartup-guide/references/orders.md`
     - locator/modal/grid/screenshot → `smartup-guide/references/ui-patterns.md`
     - debug/data_store/setup dependency → `smartup-guide/references/testing-debug.md`
   - Loyiha arxitekturasi → `write-test` yoki `review-test`
   - Agar hech biriga to'g'ri kelmasa → tegishli skill fayl yaratilsin
3. Skill fayliga `## Loyiha Xususiyatlari` bo'limiga qo'sh (yo'q bo'lsa yaratilsin)
4. Qo'shilgan joyni foydalanuvchiga ko'rsat

## Format

```markdown
## Loyiha Xususiyatlari

### <mavzu>
- <o'rganilgan narsa — qisqa va aniq>
```

## Muhim

- Umumiy ma'lumot emas, **bu loyihaga xos** narsalarni qo'sh
- Bir jumla yetarli — uzun tushuntirma kerak emas
- Bir xil narsani ikki marta qo'shma (avval mavjudligini tekshir)
- Smartup/test vazifasi yakunida ish xulosasi va o'rganilgan ma'lumotlarni mos `smartup-guide` form dossier yoki reference faylga tartibli yozib qo'y
