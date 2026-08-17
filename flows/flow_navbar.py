from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


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
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass
        if "intro/dashboard" in page.url:
            continue
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

