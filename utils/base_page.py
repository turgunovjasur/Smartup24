import logging
import re
import time

from playwright.sync_api import expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


logger = logging.getLogger(__name__)

_UNSET = object()

# Smartup24 (x24 / Angular) yagona sahifa konteynerlari
FORM_WIDGET = "app-form-stack-widget"   # forma heading / breadcrumb (list va create formada bir xil)
# Aktiv forma sarlavhasi — faqat title span. `app-form-stack-widget` ning butun matni
# sarlavha + sub-nav LINK matnlarini (masalan "Производители") o'z ichiga oladi, shuning
# uchun uni to'liq o'qib bo'lmaydi (link matni transition tugamasdan mos kelib qoladi).
HEADING = f"{FORM_WIDGET} span.font-semibold.truncate:visible"
PAGE_LOADER = "app-global-page-loader"  # global sahifa loaderi


class BasePage:
    """Smartup24 (x24 Angular UI) uchun universal sahifa funksiyalari.

    Butun loyiha bo'ylab form inputlari, selectlari (Подбор), radio/checkbox,
    grid va saqlash amallari shu klass orqali bajariladi — testlarda raw
    ``page.locator(...)`` ishlatilmaydi. Elementlar barqaror ``smtid`` yoki
    ko'rinadigan label matni orqali topiladi (dinamik ``ng.formN.*`` name emas).

    Asosiy komponentlar (MCP bilan tasdiqlangan, 2026-07-01):
      - text input : ``smt-input[smtid]`` -> ichki ``input``/``textarea``
      - textarea   : ``smt-textarea`` ("Описание" va h.k.)
      - date picker: ``smt-date-picker`` ("Начало"/"Конец") -> ichki input'ga sana
                     matn sifatida yoziladi (kalendar ochilmaydi)
      - select     : ``smt-data-select[smtid]`` -> ``input[placeholder="Подбор"]``,
                     dropdown ``.cdk-overlay-container`` ichida ``smt-select-dropdown li``
      - tree select: ``smt-tree-select[smtidfield]`` ("Регион") -> ``smt-select-trigger``
                     bosiladi, overlay'da ``[role=tree]`` panel: "Поиск..." input +
                     ``[role=treeitem]``; tanlangan qiymat trigger MATNIDA
      - radio      : ``smt-radio-group[smtid]`` -> ``label[smt-radio]`` (Статус: Активный/...)
      - checkbox   : ``label[smt-checkbox]`` -> ``input[type=checkbox]``
      - grid qatori: ``.smt-data-row``
      - qidiruv    : ``searchbox "Поиск..."``
      - heading    : ``app-form-stack-widget`` matni
    """

    def __init__(self, page):
        self.page = page

    # ------------------------------------------------------------------------------------------------------------------
    # Heading / sahifa holati
    # ------------------------------------------------------------------------------------------------------------------

    def current_heading_text(self):
        """Joriy aktiv forma heading matni (sub-nav linklarisiz)."""
        heading = self.page.locator(HEADING).last
        try:
            text = heading.inner_text(timeout=2_000)
        except Exception:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    def expect_heading(self, text, *, timeout=30_000):
        """Aktiv forma sarlavhasi (title span) berilgan matnni o'z ichiga olishini kutadi.

        `app-form-stack-widget` butun matni sarlavha + sub-nav link matnlarini
        (masalan "Производители") o'z ichiga oladi; shuning uchun faqat title span
        tekshiriladi — aks holda link matni transition tugamasdan mos kelib, keyingi
        amal (Создать va h.k.) noto'g'ri formada bajariladi."""
        expect(self.page.locator(HEADING).last).to_contain_text(text, timeout=timeout)

    def wait_for_loader(self, timeout=60_000):
        """Global sahifa loaderi ko'rinsa, yo'qolishini kutadi. Loader tez o'tsa no-op."""
        loader = self.page.locator(PAGE_LOADER)
        try:
            loader.wait_for(state="visible", timeout=1_000)
        except Exception:
            return True
        try:
            loader.wait_for(state="hidden", timeout=timeout)
        except Exception as exc:  # pragma: no cover - diagnostika uchun
            logger.warning("Loader %s ms ichida yo'qolmadi: %s", timeout, exc)
        return True

    # ------------------------------------------------------------------------------------------------------------------
    # Label -> control topish (barcha field funksiyalari uchun umumiy)
    # ------------------------------------------------------------------------------------------------------------------

    # Field control tag'lari — label wrapperini aniqlashda "control ichida bo'lgan
    # eng yaqin ajdod" predikati uchun ishlatiladi (layout klassiga bog'lanmaydi).
    _CONTROL_XPATH = (
        "ancestor::*["
        ".//smt-input or .//smt-textarea or .//smt-date-picker"
        " or .//smt-data-select or .//smt-multi-data-select or .//smt-tree-select"
        " or .//smt-radio-group or .//smt-switch or .//smt-checkbox or .//*[@smt-checkbox]"
        "][1]"
    )

    # input() qamrab oladigan matnli field komponentlari. smt-date-picker ham shu yerda:
    # ichida oddiy yozsa bo'ladigan input bor (placeholder "Выберите дату", kalendar
    # faqat ikonkadan ochiladi) — sana matn sifatida to'g'ridan-to'g'ri kiritiladi.
    # Bu tag'lar _CONTROL_XPATH da ham bo'lishi SHART, aks holda label wrapper butun
    # formagacha ko'tarilib, qo'shni fieldning inputiga yozib yuboradi (bonus formasida
    # "Начало" shu sabab "Название" ni ustidan yozgan edi).
    _INPUT_CSS = "smt-input, smt-textarea, smt-date-picker"

    # Select komponentlari (uch xil, MCP bilan tasdiqlangan 2026-07-02):
    #   - smt-data-select       : bitta variant, ichki input[placeholder="Подбор"]
    #   - smt-multi-data-select : ko'p variant (masalan "Отрасль"), ham Подбор input
    #   - smt-tree-select       : daraxt variant (masalan "Регион"), input EMAS —
    #     smt-select-trigger bosiladi, qidiruv inputi overlay'dagi [role=tree] panelda
    _SELECT_CSS = "smt-data-select, smt-multi-data-select, smt-tree-select"

    # smt-tree-select ochilganda cdk-overlay ichidagi daraxt paneli
    _TREE_PANEL = ".cdk-overlay-container [role=tree]"

    def _label_pattern(self, label):
        # "Название", "Название *", " Название * " — barchasi mos; "Краткое название" MOS EMAS (anchored)
        return re.compile(rf"^\s*{re.escape(label)}\s*\*?\s*$")

    def _label_locator(self, label, root):
        """Label matnli elementni topadi. Avval ``<label>`` (input/select/radio),
        topilmasa ``<span>``/``<t>`` (switch/toggle labeli ba'zan span, masalan "Статус")."""
        pattern = self._label_pattern(label)
        loc = root.locator("label").filter(has_text=pattern)
        if loc.count() == 0:
            loc = root.locator("label, span, t").filter(has_text=pattern)
        return loc

    def _field_wrapper(self, label, *, index=0, root=None):
        """Label matni orqali eng yaqin field konteynerini topadi.

        Field control (smt-input/smt-data-select/smt-radio-group/smt-switch/smt-checkbox)
        labelning eng yaqin ajdodi ichida bo'ladi. Bu vertikal (``div.flex.flex-col >
        label + smt-input``) va gorizontal (``div.flex.items-center > span "Статус" +
        smt-switch``) layoutlarning IKKALASIDA ham ishlaydi — layout klassiga bog'liq emas.
        """
        root = root or self.page
        wrapper = self._label_locator(label, root).nth(index).locator(f"xpath={self._CONTROL_XPATH}")
        if wrapper.count() == 0:
            # control topolmasa (kutilmagan layout) — labelning roditeliga tush
            wrapper = self._label_locator(label, root).nth(index).locator("xpath=..")
        return wrapper.first

    def _control(self, tag, *, label=None, smtid=None, index=0, root=None):
        """``tag`` (smt-input/smt-data-select/smt-radio-group) elementini
        ``smtid`` yoki ``label`` orqali topadi."""
        root = root or self.page
        if smtid is not None:
            # `tag` bir nechta bo'lishi mumkin ("smt-data-select, smt-multi-data-select") —
            # smtid filtrini har biriga alohida qo'llaymiz. smt-tree-select barqaror id'ni
            # `smtid` emas, `smtidfield` atributida saqlaydi (masalan smtidfield="region_id").
            parts = []
            for t in tag.split(","):
                t = t.strip()
                attr = "smtidfield" if t == "smt-tree-select" else "smtid"
                parts.append(f'{t}[{attr}="{smtid}"]')
            sel = ", ".join(parts)
            return root.locator(sel).nth(index)
        if label is not None:
            wrapper = self._field_wrapper(label, index=index, root=root)
            return wrapper.locator(tag).first
        raise ValueError(f"{tag}: label yoki smtid dan bittasini bering")

    # ------------------------------------------------------------------------------------------------------------------
    # Text input / textarea
    # ------------------------------------------------------------------------------------------------------------------

    def input(
        self,
        value=_UNSET,
        *,
        label=None,
        smtid=None,
        expect_value=_UNSET,
        return_value=False,
        index=0,
        root=None,
        clear=True,
        press_tab=False,
    ):
        """Matnli field bilan ishlash uchun universal funksiya —
        ``smt-input`` (text/number), ``smt-textarea`` va ``smt-date-picker``
        (sana matn ko'rinishida yoziladi, masalan "01.07.2026").

        Inputni topish (bittasini bering):
          - ``label="Название"`` : ko'rinadigan field label orqali (asosiy usul)
          - ``smtid="name"``     : barqaror ``smt-input[smtid]`` orqali

        Amal:
          - ``value=...`` : maydonni tozalab (clear=True) shu qiymat bilan to'ldiradi
          - ``expect_value=...`` : qiymatni tasdiqlaydi (value berilsa default expect_value=value)
          - ``return_value=True`` : joriy qiymatni qaytaradi
          - ``press_tab=True`` : to'ldirgach Tab bosadi
        """
        control = self._control(self._INPUT_CSS, label=label, smtid=smtid, index=index, root=root)
        field = control.locator("input, textarea").first
        expect(field).to_be_visible()

        if value is not _UNSET:
            field.click()
            if clear:
                field.press("ControlOrMeta+A")
                field.press("Backspace")
            field.fill(str(value))
            if press_tab:
                field.press("Tab")

        expected = expect_value
        if expected is _UNSET and value is not _UNSET:
            expected = str(value)
        if expected is not _UNSET:
            expect(field).to_have_value(expected)

        if return_value:
            return field.input_value()
        return field

    # ------------------------------------------------------------------------------------------------------------------
    # Select (Подбор) — smt-data-select
    # ------------------------------------------------------------------------------------------------------------------

    def _open_select(self, label=None, smtid=None, index=0, root=None):
        """Selectni topib, dropdownini ochadi. ``(select, trigger, tag_name)`` qaytaradi.

        ``trigger`` — qidiruv matni yoziladigan input: smt-data-select/multi'da
        komponent ichidagi Подбор input, smt-tree-select'da esa overlay'dagi
        [role=tree] panel ichidagi "Поиск..." input (komponentda input yo'q,
        smt-select-trigger bosib ochiladi)."""
        select = self._control(self._SELECT_CSS, label=label, smtid=smtid, index=index, root=root)
        expect(select).to_be_visible()
        tag_name = select.evaluate("el => el.tagName.toLowerCase()")

        if tag_name == "smt-tree-select":
            select.locator("smt-select-trigger").first.click()
            trigger = self.page.locator(f'{self._TREE_PANEL} input[placeholder="Поиск..."]').last
            expect(trigger).to_be_visible()
            return select, trigger, tag_name

        trigger = select.locator('input[placeholder="Подбор"]').first
        if trigger.count() == 0:
            trigger = select.locator("input").first
        expect(trigger).to_be_visible()
        trigger.click()
        return select, trigger, tag_name

    def _click_option(self, option_text, *, exact=True, timeout=30_000):
        """Ochilgan dropdowndan ``option_text`` variantini bosadi.

        Uch xil dropdown qo'llab-quvvatlanadi:
          - bitta variantli ``smt-data-select`` : ``smt-select-dropdown`` ichida ``<li>``;
          - ko'p variantli ``smt-multi-data-select`` : CDK ``role="menu"`` ichida
            ``role="menuitemcheckbox"`` (masalan "Отрасль");
          - daraxt ``smt-tree-select`` : overlay'da ``role="tree"`` panel ichida
            ``role="treeitem"`` (masalan "Регион").
        "Добавить"/"Показать все" harakat elementlari matn bo'yicha aniq filtrlanib
        chetlab o'tiladi.

        Dropdown/menu Angular'da fill'dan keyin KECHIKIB render bo'ladi — shuning uchun
        variant qaysi konteynerda paydo bo'lishini deadline'gacha qayta-qayta tekshiramiz
        (bir martalik ``count()`` tekshiruvi poyga tufayli noto'g'ri locatorda qotib
        qolar edi)."""
        pattern = re.compile(rf"^\s*{re.escape(option_text)}\s*$") if exact else re.compile(re.escape(option_text))
        dropdown = self.page.locator("smt-select-dropdown").last
        li_option = dropdown.locator("li").filter(has_text=pattern).first
        text_option = dropdown.get_by_text(option_text, exact=exact).first
        overlay = self.page.locator(".cdk-overlay-container")
        role_options = [
            overlay.get_by_role(role, name=option_text, exact=exact).first
            for role in ("menuitemcheckbox", "menuitem", "option", "treeitem")
        ]

        deadline = time.monotonic() + timeout / 1000
        while True:
            if li_option.count() > 0:
                option = li_option
                break
            if text_option.count() > 0:
                option = text_option
                break
            # smt-select-dropdown topilmasa — ko'p variantli menu (menuitemcheckbox/
            # menuitem) yoki tree panel (treeitem). Menu transparent cdk-overlay-backdrop
            # bilan ochilib oddiy klikni "intercepts pointer events" bilan to'sadi
            # (dispatch esa Angular handlerni ishga tushirmaydi) — backdrop'ni
            # pointer-events'siz qilib, haqiqiy klik yuboramiz.
            candidate = next((c for c in role_options if c.count() > 0), None)
            if candidate is not None:
                expect(candidate).to_be_visible(timeout=timeout)
                self.page.evaluate(
                    "() => document.querySelectorAll('.cdk-overlay-backdrop')"
                    ".forEach(b => { b.style.pointerEvents = 'none'; })"
                )
                candidate.click()
                return
            if time.monotonic() >= deadline:
                # Hech qaysi konteynerда topilmadi — diagnostika uchun asosiy locator
                # bo'yicha aniq assertion xatosi beramiz.
                option = li_option
                break
            self.page.wait_for_timeout(100)

        expect(option).to_be_visible(timeout=timeout)
        option.click()

    def select(
        self,
        option_text,
        *,
        label=None,
        smtid=None,
        search=None,
        exact=True,
        expect_selected=True,
        index=0,
        root=None,
        timeout=30_000,
    ):
        """Select'dan bitta variant tanlaydi — ``smt-data-select`` (Подбор),
        ``smt-multi-data-select`` va ``smt-tree-select`` ("Регион") avtomatik ajratiladi.

        Selectni topish (bittasini bering):
          - ``label="Производитель"`` : field label orqali
          - ``smtid="producer_id"``   : barqaror ``smt-data-select[smtid]`` orqali
            (tree-select uchun ``smtidfield`` qiymati, masalan ``smtid="region_id"``)

        ``search``: dropdownda filtrlash uchun yoziladigan matn (default = ``option_text``);
        ``exact``: variant matnini aniq moslashtirish; ``expect_selected``: tanlangach
        Подбор inputida tanlangan qiymat ko'rinishini tasdiqlaydi.
        """
        select, trigger, tag_name = self._open_select(label=label, smtid=smtid, index=index, root=root)

        query = option_text if search is None else search
        if query:
            trigger.fill(query)

        self._click_option(option_text, exact=exact, timeout=timeout)

        if tag_name == "smt-tree-select":
            # Daraxt select ("Регион"): tanlangan qiymat trigger MATNIDA ko'rinadi
            # (Подбор input yo'q). Ko'p variantli (aria-multiselectable) rejimda panel
            # tanlangach ochiq qoladi — keyingi amallarni to'sib qo'ymasligi uchun yopamiz.
            if expect_selected:
                expect(select).to_contain_text(re.compile(re.escape(option_text)), timeout=timeout)
            self._close_tree_panel()
        elif expect_selected:
            # Bitta variantli select (smt-data-select): tanlangan qiymat Подбор input
            # value'siga tushadi. Ko'p variantli (smt-multi-data-select, "Отрасль"):
            # qiymat "chip" (matn) sifatida qo'shiladi va input tozalanadi — shuning
            # uchun input value emas, komponent matnini tekshiramiz.
            if tag_name == "smt-multi-data-select":
                pattern = re.compile(re.escape(option_text))
                try:
                    expect(select).to_contain_text(pattern, timeout=10_000)
                except AssertionError:
                    # Flaky: klik menu qayta-render (filtr natijasi kelishi) paytiga
                    # to'g'ri kelsa tanlov qo'llanmay qoladi — dropdown ochiq, filtr
                    # yozilgan holda turadi. Variantni bir marta qayta bosamiz.
                    self._click_option(option_text, exact=exact, timeout=timeout)
                    expect(select).to_contain_text(pattern, timeout=timeout)
                # Ko'p variantli menu tanlangach ochiq qoladi — keyingi amal (Сохранить)
                # overlay backdrop ostida qolmasligi uchun yopamiz va yo'qolishini kutamiz.
                self._close_overlay()
            else:
                # DIQQAT: trigger inputga filtr matnini O'ZIMIZ yozganmiz, shuning uchun
                # to_have_value yolg'ondan o'tishi mumkin — tanlov commit bo'lganining
                # haqiqiy belgisi dropdown O'ZI yopilishi. Klik dropdown qayta-render
                # (filtr natijasi kelishi) paytiga to'g'ri kelib qo'llanmay qolsa,
                # dropdown ochiq qoladi — variantni bir marta qayta bosamiz. Aks holda
                # Сохранить'da majburiy select bo'sh qolib, forma jim ochiq qolaveradi.
                expect(trigger).to_have_value(re.compile(re.escape(option_text)), timeout=timeout)
                dropdown = self.page.locator("smt-select-dropdown").last
                try:
                    expect(dropdown).to_be_hidden(timeout=5_000)
                except AssertionError:
                    self._click_option(option_text, exact=exact, timeout=timeout)
                    expect(dropdown).to_be_hidden(timeout=timeout)
                # Backdrop fade-out ham kechikib keyingi klikni to'sishi mumkin —
                # yopilishini kutamiz (flaky manbai).
                self._close_overlay()
        return select

    def multiselect(
        self,
        *option_texts,
        label=None,
        smtid=None,
        exact=True,
        close=True,
        index=0,
        root=None,
        timeout=30_000,
    ):
        """``smt-data-select`` multi-select rejimida bir nechta variant tanlaydi.

        Har bir variant uchun dropdownga qidiruv matni yoziladi va mos ``li`` bosiladi;
        dropdown ochiq qoladi. ``close=True`` — oxirida Escape bilan yopiladi.
        """
        select, trigger, _ = self._open_select(label=label, smtid=smtid, index=index, root=root)
        for option_text in option_texts:
            trigger.fill(option_text)
            self._click_option(option_text, exact=exact, timeout=timeout)
        if close:
            trigger.press("Escape")
        return select

    # ------------------------------------------------------------------------------------------------------------------
    # Radio group (Статус) — smt-radio-group
    # ------------------------------------------------------------------------------------------------------------------

    def radio(
        self,
        option_text,
        *,
        label=None,
        smtid=None,
        expect_selected=True,
        index=0,
        root=None,
    ):
        """``smt-radio-group`` dan berilgan variant (masalan "Активный") ni tanlaydi."""
        group = self._control("smt-radio-group", label=label, smtid=smtid, index=index, root=root)
        expect(group).to_be_visible()
        option = group.locator("label[smt-radio]").filter(has_text=option_text).first
        option.click()
        if expect_selected:
            radio = option.locator("input[type=radio], [role=radio]").first
            expect(radio).to_have_attribute("aria-checked", "true")
        return group

    # ------------------------------------------------------------------------------------------------------------------
    # Toggle — smt-switch (Статус va h.k.) va smt-checkbox
    # ------------------------------------------------------------------------------------------------------------------

    # Toggle turlari: forma switchi (smt-switch, gorizontal "Статус" layout) va
    # checkbox (smt-checkbox — grid/forma). Ikkalasida ham ichki input[type=checkbox]
    # va ko'rinadigan [role=switch]/[role=checkbox] bo'ladi.
    _TOGGLE_CSS = "smt-switch, smt-checkbox, label[smt-checkbox], [smt-checkbox]"

    def checkbox(
        self,
        *,
        label=None,
        smtid=None,
        locator=None,
        checked=_UNSET,
        expect_checked=_UNSET,
        return_value=False,
        index=0,
        root=None,
    ):
        """Switch/checkbox (on-off toggle) bilan ishlash — ``smt-switch`` va ``smt-checkbox``.

        Toggle'ni topish (bittasini bering):
          - ``label="Статус"`` : field/span label orqali (asosiy usul)
          - ``smtid="..."``    : barqaror smtid orqali
          - ``locator``        : tayyor Locator yoki selector string (grid checkbox va h.k.)

        Amal:
          - ``checked=True/False`` : shu holatga keltiradi (idempotent) va tasdiqlaydi
          - ``expect_checked=True/False`` : faqat holatni tasdiqlaydi
          - ``return_value=True`` : joriy bool holatni qaytaradi
        """
        root = root or self.page
        if locator is not None:
            toggle = root.locator(locator).nth(index) if isinstance(locator, str) else locator
        elif smtid is not None:
            toggle = root.locator(f'[smtid="{smtid}"]').nth(index)
        elif label is not None:
            toggle = self._field_wrapper(label, index=index, root=root).locator(self._TOGGLE_CSS).first
        else:
            raise ValueError("checkbox(): label, smtid yoki locator dan bittasini bering")

        cb = toggle.locator("input[type=checkbox]").first
        # Ko'rinadigan bosiladigan element (input ko'pincha hidden/sr-only)
        clickable = toggle.locator("[role=switch], [role=checkbox]").first

        if checked is not _UNSET and cb.is_checked() != checked:
            (clickable if clickable.count() > 0 else toggle).click()

        want = checked if checked is not _UNSET else expect_checked
        if want is not _UNSET:
            expect(cb).to_be_checked() if want else expect(cb).not_to_be_checked()
        if return_value:
            return cb.is_checked()
        return cb

    # ------------------------------------------------------------------------------------------------------------------
    # Grid / list
    # ------------------------------------------------------------------------------------------------------------------

    def grid_row(self, text, *contains, row_selector=".smt-data-row"):
        """``text`` bo'yicha grid qatorini (``.smt-data-row``) topadi, ko'rinishini va
        (berilgan bo'lsa) ``contains`` dagi har bir matnni o'z ichiga olishini tekshiradi."""
        row = self.page.locator(row_selector).filter(has_text=text).first
        expect(row).to_be_visible()
        for value in contains:
            expect(row).to_contain_text(value)
        return row

    def click_grid_row(self, text, row_selector=".smt-data-row"):
        self._settle()
        row = self.grid_row(text, row_selector=row_selector)
        row.click()
        return row

    def search(self, text):
        """List formadagi qidiruv (``searchbox "Поиск..."``) ga yozib Enter bosadi."""
        field = self.page.get_by_role("searchbox", name="Поиск").first
        expect(field).to_be_visible()
        field.click()
        field.fill(text)
        field.press("Enter")
        self.wait_for_loader()
        return field

    # ------------------------------------------------------------------------------------------------------------------
    # Navigatsiya settle / tugmalar / saqlash
    # ------------------------------------------------------------------------------------------------------------------

    def _close_tree_panel(self, timeout=5_000):
        """Ochiq qolgan smt-tree-select panelini (``[role=tree]``) yopadi.

        Bitta variantli tree'da panel tanlangach O'ZI yopiladi (no-op); ko'p variantli
        (aria-multiselectable, masalan supplier/client "Регион") rejimda ochiq qoladi.
        Backdrop YO'Q, sintetik keydown ishlamaydi — faqat haqiqiy Escape yopadi
        (MCP bilan tasdiqlangan 2026-07-02)."""
        panel = self.page.locator(self._TREE_PANEL)
        if panel.count() == 0:
            return
        self.page.keyboard.press("Escape")
        try:
            panel.first.wait_for(state="hidden", timeout=timeout)
        except Exception:  # pragma: no cover - diagnostika uchun
            logger.warning("smt-tree-select paneli %s ms ichida yopilmadi", timeout)

    def _close_overlay(self, timeout=5_000):
        """Ochiq CDK overlay (dropdown/menu) backdrop'ini yopadi va yo'qolishini kutadi.

        ``.cdk-overlay-backdrop-showing`` darrov yo'qolmaydi va keyingi klikni
        "intercepts pointer events" bilan to'sadi (masalan select tanlangach
        Характеристика/Сохранить). Avval fade-out o'zi tugashini qisqa kutamiz
        (bitta variantli select'da normal holat), yopilmasa Escape bosamiz.
        Backdrop bo'lmasa no-op."""
        backdrop = self.page.locator(".cdk-overlay-backdrop-showing")
        if backdrop.count() == 0:
            return
        try:
            backdrop.first.wait_for(state="hidden", timeout=1_500)
            return
        except Exception:
            pass
        self.page.keyboard.press("Escape")
        try:
            backdrop.first.wait_for(state="hidden", timeout=timeout)
        except Exception:  # pragma: no cover - diagnostika uchun
            logger.warning("cdk-overlay backdrop %s ms ichida yopilmadi", timeout)

    def _settle(self, timeout=10_000):
        """Sahifa transition tugashini kutadi.

        Smartup24 da sub-header (``app-form-stack-widget`` title) va asosiy kontent
        (``smartup24-app-*-list`` — Создать shu yerda) ALOHIDA router-outlet'larda va
        ASINXRON yangilanadi: title yangi bo'limga o'tsa ham, asosiy kontentda eski
        list bir zum qolib turishi mumkin. Shu sabab faqat heading kutish yetmaydi —
        aks holda "Создать" eski forma tugmasini bosib, noto'g'ri create formasi ochiladi.
        Loader + network idle bilan kontent to'liq almashguncha kutamiz."""
        self.wait_for_loader()
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            pass

    def click_link(self, name, *, exact=True):
        """List forma ichidagi sub-nav bo'limiga (link, masalan "Производители") o'tadi
        va kontent to'liq almashishini kutadi."""
        link = self.page.get_by_role("link", name=name, exact=exact).first
        expect(link).to_be_visible()
        link.click()
        self._settle()
        return link

    def click_button(self, name, *, exact=True):
        # Oldingi amaldan (select/dropdown) qolgan backdrop klikni "intercepts
        # pointer events" bilan to'smasligi uchun avval yopilishini kutamiz.
        self._close_overlay()
        button = self.page.get_by_role("button", name=name, exact=exact).first
        expect(button).to_be_visible()
        button.click()
        return button

    def open_create(self, *, button_name="Создать"):
        """List formada "Создать" tugmasini bosadi. Avval kontent settled bo'lishini kutadi —
        transition paytida eski formaning "Создать" tugmasi bosilib qolmasligi uchun."""
        self._settle()
        return self.click_button(button_name)

    def save(self, *, button_name="Сохранить", exact=True):
        self.click_button(button_name, exact=exact)
        self.wait_for_loader()

    def save_and_expect_heading(self, expected_heading, *, button_name="Сохранить", exact=True, timeout=60_000):
        """Сохранить bosadi va aktiv forma sarlavhasida kutilgan heading ochilishini tekshiradi."""
        self.save(button_name=button_name, exact=exact)
        self.expect_heading(expected_heading, timeout=timeout)
