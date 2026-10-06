from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from utils.qa_report import qa_action


def flow_menu(page, field="Название") -> None:
    """Ro'yxatning "Настройки поиска" dialogida ``field`` ustuni bo'yicha
    qidiruvni yoqadi (Валютыда default faqat "Базовая денежная единица" va
    "Код" yoqilgan — Название bo'yicha qidiruv topmaydi).

    DIQQAT: checkboxlar grid qatorlarida ham bor va DOM'da dialogdan OLDIN
    keladi — indeks (nth) bilan olish noto'g'ri elementga tushadi. Shuning
    uchun faqat dialog ichida, ustun NOMI bilan qidiriladi. Har variantda
    IKKITA checkbox bor (nomlisi holat, nomsizi vizual) — bosish uchun
    ko'rinadigan matn ishlatiladi (MCP tasdiqlangan 2026-07-16)."""
    page.locator('//smt-button-group-item[@smtvalue="menu"]').click()
    page.get_by_role("menuitem", name="Настройки поиска").click()
    dialog = page.get_by_role("dialog")
    checkbox = dialog.get_by_role("checkbox", name=field).first
    if not checkbox.is_checked():
        dialog.get_by_text(field, exact=True).first.click()
    dialog.get_by_role("button", name="Сохранить").click()


@qa_action("Menyu: {tab} → {name}")
def flow_navigate(page: Page, tab, name, expect_url=None) -> None:
    # Oldingi amal (odatda Сохранить) so'rovi hali tugamagan bo'lishi mumkin:
    # uning KECHIKKAN redirecti (ro'yxat YOKI dashboard) allaqachon bosilgan
    # menyu navigatsiyasini yutib yuboradi — bonus 2026-07-10: save javobi
    # flow_navigate kliklaridan KEYIN kelib, app dashboard'da qolib ketgan.
    # Shuning uchun avval network tinchishini kutamiz (idle sahifada ~0s).
    try:
        page.wait_for_load_state("networkidle", timeout=10_000)
    except Exception:
        pass
    # Kutish o'zi yetarli EMAS (bonus 2026-07-14): save javobi 10s dan ham kech
    # kelsa (yoki redirect javobdan keyin client tomonda kechikib otilsa) poyga
    # qaytadan yuzaga keladi va app dashboard'da qolib ketadi. Menyu modullari
    # hech qachon dashboard emas — shuning uchun bosilgandan keyin NATIJANI
    # tekshiramiz: URL intro/dashboard'da qolsa, redirect yutgan — qayta bosamiz.
    start_url = page.url
    # Allaqachon shu modul ro'yxatida turibmiz (masalan save'dan keyin) — qayta
    # bosilganda URL O'ZGARMAYDI, quyidagi URL-o'zgarish kutishi har safar behuda
    # 20s timeout bo'lardi (MCP tasdiqlangan 2026-10-06). Boshqa moduldan kelsak
    # sarlavha boshqacha — kutish saqlanadi.
    try:
        heading = page.locator("app-form-stack-widget span.font-semibold.truncate:visible").last
        already_there = heading.inner_text(timeout=1_000).strip() == name
    except Exception:
        already_there = False
    for attempt in range(3):
        # Klik juftligi himoyalanadi: sessiya qulfi (app-session-lock) menyu
        # ochiq turganda tushsa, handler qulfni yechadi-yu, ochilgan dropdown
        # YOPILIB ketadi — menuitem endi hech qachon chiqmaydi va klik timeout
        # bo'ladi (2026-07-19 run, 1:42 da shablon edit'da). Timeout'da tabni
        # QAYTA bosib menyuni qayta ochamiz. Timeout 60s — qulf handleri vaqti
        # amal timeout'iga KIRADI (conftest DEFAULT_TIMEOUT bilan bir xil sabab),
        # 30s qulf yechilishiga yetmay qolishi mumkin.
        try:
            # Navbar tabi (Модератор/Поставщик/Клиент) TOGGLE tugma: bosilganda
            # menyuni ochadi YOKI yopadi. Ko'r-ko'rona bosish xato edi — menyu
            # allaqachon ochiq bo'lsa (masalan oldingi urinish uni ochiq
            # qoldirgan bo'lsa) klik uni YOPADI, keyin menuitem hech qachon
            # chiqmay 60s timeout bo'ladi (MCP tasdiqlangan 2026-07-21: bosh
            # xatoning aynan sababi). Shuning uchun aria-expanded holatini
            # tekshirib, faqat YOPIQ bo'lsa ochamiz.
            tab_btn = page.get_by_role("button", name=tab)
            if tab_btn.get_attribute("aria-expanded") != "true":
                tab_btn.click(timeout=60_000)
            page.get_by_role("menuitem", name=name, exact=True).click(timeout=60_000)
        except PlaywrightTimeoutError:
            if attempt == 2:
                raise
            # Ochilib qolgan menyuni tozalaymiz — keyingi urinish toza (yopiq)
            # holatdan boshlansin, aks holda toggle ochiq/yopiq tebranib qoladi.
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
            # Menyu TO'LIQ RENDER bo'lmagan bo'lishi mumkin: dev churn/qisman yuklanish
            # paytida Модератор menyusi kerakli itemsiz chiqadi (2026-07-30 runner —
            # 24 ta item bilan ochilgan, ammo "Критерии" YO'Q; 60s timeout). Menyuni
            # qayta ochish yordam bermaydi (bir xil chala menyu) — reload to'liq
            # menyuni oladi.
            try:
                page.reload(wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle", timeout=15_000)
            except Exception:
                pass
            continue
        # Login'dan keyingi BIRINCHI navigatsiya dashboard'dan boshlanadi va sekin
        # CI VM'da (sovuq lazy chunk + ~13k Товары) URL o'zgarishi 15s+ kechikadi.
        # Avval URL'ni BIR ZUMDA tekshirardik → hali dashboard → "redirect yutdi"
        # deb tabni qayta bosib, allaqachon ochilayotgan modul ustida menyuni
        # yopib qo'yardik → 3-urinish menuitem'ni topmay 60s timeout (CI 2026-10-05:
        # test_010 Товары, test_410 Регионы — ikkalasi 61s, screenshot'da modul
        # OCHIQ). Endi URL dashboard'dan CHIQISHINI kutamiz; chiqmasa — qayta bosamiz.
        try:
            page.wait_for_url(lambda url: "intro/dashboard" not in url, timeout=30_000)
        except Exception:
            continue
        # Kontent outleti (list + "Создать") URL bilan birga, title'dan KECH
        # almashadi — URL hali OLDINGI modulda bo'lsa open_create eski ro'yxatning
        # "Создать"ini bosadi (CI 2026-10-05: Юр.лица → Валюты, "Валюта (Создания)"
        # o'rniga "Юр. Лицо (Создания)" ochildi). URL o'zgarishini kutamiz; shu
        # modulning o'zi qayta bosilgan bo'lsa URL o'zgarmaydi — kutib, davom etamiz.
        if page.url == start_url and not already_there:
            try:
                page.wait_for_url(lambda url: url != start_url, timeout=20_000)
            except Exception:
                pass
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass
        # URL tekshiruvi o'tgan bo'lsa ham KECHIKKAN save-redirect hali otilishi
        # mumkin (client full 2026-07-18: networkidle'dan KEYIN dashboard'ga
        # uloqtirdi — oldingi tekshiruv buni ko'rmay o'tib ketgan). Qisqa grace
        # oynasida URL dashboard'ga qaytsa — redirect yutgan, qayta bosamiz.
        try:
            page.wait_for_url(lambda url: "intro/dashboard" in url, timeout=2_500)
            continue  # grace ichida dashboard keldi — redirect yutgan, qayta bosamiz
        except Exception:
            pass  # dashboard kelmadi — navigatsiya barqaror
        # Kontent outleti mo'ljallangan modulga o'tganini URL bilan TASDIQLAYMIZ.
        # Sub-header (title span) va asosiy kontent alohida router-outlet'da ASINXRON
        # yangilanadi: menyu bosilganda title darhol yangi modulga o'tadi, ammo URL
        # va kontent (list + "Создать") biruni→Angular o'tishida ~2s KECH keladi
        # (MCP tasdiqlangan 2026-08-17: OAuth2 menyusi bosilganda title darhol, URL
        # 2s keyin company_client_list bo'ldi). Faqat heading kutish yetmaydi —
        # expect_heading erta mos kelib, open_create() eski list'ning STALE "Создать"
        # tugmasini bosadi (2026-08-15 runner: Пользователи→Объявления o'tishida
        # "Пользователь (создание)" ochilib, 16 ta main test cascade bilan yiqildi).
        # expect_url berilgan bo'lsa mo'ljal URL kelguncha kutamiz; kelmasa qayta bosamiz.
        if expect_url is not None:
            try:
                page.wait_for_url(lambda url: expect_url in url, timeout=30_000)
            except Exception:
                if attempt == 2:
                    raise
                continue
        return

