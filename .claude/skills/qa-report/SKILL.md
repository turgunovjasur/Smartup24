---
name: qa-report
description: SmartUp24 pytest/Allure natijalaridan o'zbek tilida QA hisoboti tuzadi — passed/failed/broken/skipped soni, yiqilgan testlar, yiqilgan qadam va xato. Test run'dan keyin yoki user "hisobot", "natija qanday" deganda ishlatiladi. Natijalarni FAQAT fayllardan oladi.
---

# /qa-report — QA natija hisoboti

1. Xulosani skript bilan chiqar (o'zing sanama):
   ```
   .venv/Scripts/python.exe .claude/skills/qa-report/summarize.py [natija_papkasi]
   ```
   Default papka `test-results/allure-results`. CI natijasi uchun avval
   `gh run download <id> -D test-results/ci/<id>` va shu papkani ber.
2. Skript chiqishidagi raqamlar va jadvalni O'ZGARTIRMASDAN hisobotga qo'y.
3. Hisobotni o'zbek tilida shu tartibda ber:
   - **Qisqa xulosa** (1–2 gap): nima yurdi (bo'lim, DEV/PROD — agar ma'lum bo'lsa), umumiy holat.
   - **Raqamlar** jadvali (skriptdan).
   - **Yiqilganlar** (skriptdan) — agar `qa-bug-investigator` tahlili shu suhbatda bo'lsa,
     har biriga uning tasnifini (ilova bag'i / UI drift / flaky / muhit / test bag'i) qo'sh.
   - **Bloklangan / kaskad**: runner zanjirida oldingi test yiqilgani uchun yiqilganlar — faqat tahlil bo'lsa.
   - **Keyingi qadamlar**: kim nima qiladi.

## Qoidalar
- Natijani O'YLAB TOPMA. Skript "Natija topilmadi" desa — shuni ayt.
- Muhit (DEV/PROD) yoki bo'lim noma'lum bo'lsa "ko'rsatilmagan" deb yoz, taxmin qilma.
- `pytest.ini` dagi `--clean-alluredir` sababli papkada faqat OXIRGI run bor — eski run bilan solishtirish so'ralsa buni ayt.
- Hisobotni tashqariga (Telegram, Jira) yuborma — faqat userga ko'rsat.
