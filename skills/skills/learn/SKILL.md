---
name: learn
description: Foydalanuvchi biror narsa tushuntirsa, o'rgatsa yoki xato sababini aytsa — bu bilimni tegishli skill fayliga qo'shadi. PROAKTIV ishlatiladi, foydalanuvchi so'ramasdan ham.
allowed-tools: Read, Edit, Write, Glob
---

# Yangi Bilimni Skill ga Qo'shish (Smartup24)

Argument: `$ARGUMENTS` (o'rganilgan narsa tavsifi)

## Qachon ishlatiladi (AVTOMATIK)

Quyidagi holatlarda foydalanuvchi so'ramasdan o'zing ishlat:
- Foydalanuvchi UI xatti-harakatini tushuntirsa ("select tanlangach qiymat input'da bo'ladi", "server shuncha vaqt ketadi")
- Xato sababini o'zi aytsa ("sabab heading sub-nav linkiga mos kelyapti")
- Loyiha qoidasini ko'rsatsa ("nom har doim `code` bilan unikal bo'lsin")
- Avval qilgan yechim noto'g'ri chiqib, to'g'ri yechim topilsa

## Ish tartibi

1. O'rganilgan bilimni qisqa va aniq jumlaga yoz.
2. Qaysi joyga tegishli ekanini aniqla:
   - **UI locator / komponent pattern** (yangi `smt-*` element, dropdown, heading, radio va h.k.) → `utils/base_page.py` ga yangi funksiya yoki mavjudini tuzatish sifatida qo'sh (base funksiyalar shu yerda markazlashgan), va kerak bo'lsa `debug-test` ga gotcha qatori.
   - **Debug/xato pattern / timing gotcha** → `debug-test` SKILL.md `## Loyiha xususiyatlari`.
   - **Test yozish qoidasi / struktura** → `write-test` SKILL.md.
   - **Flow qoidasi** → `new-flow` SKILL.md.
   - **Run/pytest qoidasi** → `run-smoke` SKILL.md.
   - **Review mezoni** → `review-test` SKILL.md.
3. Mavjud `## Loyiha xususiyatlari` bo'limiga qo'sh (yo'q bo'lsa yarat).
4. Qo'shilgan joyni foydalanuvchiga ko'rsat.

## Muhim

- Umumiy Playwright ma'lumoti emas — **bu loyihaga (Smartup24 x24 UI) xos** narsalarni qo'sh.
- Bir jumla yetarli; uzun tushuntirma kerak emas.
- Bir xil narsani ikki marta qo'shma (avval mavjudligini tekshir).
- **Locator/komponent bilimini** kod ichida (base_page.py docstring/komment) markazlashtir — shunda testlar avtomatik foydalanadi; SKILL.md ga faqat qoida/gotcha yoz.
- Yangi kashf qilingan UI patternni doim avval Playwright MCP bilan real DOM'da tasdiqlab, keyin yoz.
