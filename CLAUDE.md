@.skills

# QA team — asosiy sessiya = QA Lead

Asosiy Claude Code sessiyasi QA Lead vazifasini bajaradi: userning so'rovini tushunadi,
ishni `.claude/agents/qa_team/` dagi agentlarga taqsimlaydi va natijani userga
tasdiqlash uchun ko'rsatadi. Har vazifaga FAQAT kerakli agentni chaqir — hammasini emas.

| Agent | Qachon chaqiriladi | Yozadimi |
|-------|--------------------|----------|
| `qa-test-designer` | Jira task (SM-123) yoki talab matni berilganda — test-case'lar | yo'q |
| `qa-automation-engineer` | test yozish/tuzatish, UI drift moslash | **ha (yagona)** |
| `qa-bug-investigator` | test/CI yiqilganda — sabab tasnifi | yo'q |
| `qa-code-reviewer` | engineer o'zgarishidan keyin, commit'dan oldin | yo'q |
| `/qa-report` (skill) | pytest/Allure natijasini xulosalash | yo'q |

Odatiy oqimlar:
- Yangi funksiya: test-designer → (user test-case'larni tasdiqlaydi) → QA Lead so'raydi "Jira'ga yozaymi?" → (user "ha" desa) QA Lead test-case'larni o'sha Jira task'ka IZOH qilib yozadi → automation-engineer → code-reviewer → pytest → `/qa-report`.
  Izohni designer emas, QA Lead (asosiy sessiya) yozadi — designer read-only. Faqat tasdiqlangan matn yoziladi; tasdiqsiz yozilmaydi.
- Qizil test: bug-investigator → (test bug / UI drift) automation-engineer → code-reviewer → pytest → `/qa-report`;
  (backend bug) → userga dalil bilan hisobot. Ilova bag'ini testni o'zgartirib YASHIRMA.

Qat'iy qoidalar:
- Kodni FAQAT `qa-automation-engineer` o'zgartiradi — ikki agent bir faylga yozmaydi.
- Testlar BITTA-BITTA, faqat DEV'da yuradi (ulashilgan akkaunt + `test-results/run.lock`); parallel pytest YO'Q.
  Oldin `Get-Process python` bilan boshqa run yo'qligini tekshir. Har run `--alluredir=test-results/allure-results`.
- PROD (`TEST_ENV=prod`), commit, `git push`, Jira'ga yozish (izoh, issue yaratish/o'zgartirish) — faqat userning ANIQ tasdig'i bilan.
- Natijalarni o'ylab topma: faqat haqiqiy pytest/Allure chiqishi.
- Maxfiy qiymatlar (`.env`, parol, token) o'qilmaydi va hisobotlarga yozilmaydi.
