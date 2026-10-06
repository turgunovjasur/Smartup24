import logging
import re
import time

from playwright.sync_api import expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from utils.qa_report import qa_action, visible_error_dialog_text


logger = logging.getLogger(__name__)

_UNSET = object()

FORM_WIDGET = "app-form-stack-widget"
# Faqat title span: widgetning butun matni sub-nav link nomlarini ham oladi va
# transition tugamasdan noto'g'ri mos kelib qoladi.
HEADING = f"{FORM_WIDGET} span.font-semibold.truncate:visible"
PAGE_LOADER = "app-global-page-loader"

# Ochiq CDK backdrop'lar haqiqiy klikni to'sadi (dispatch esa Angular handlerni
# ishga tushirmaydi) — ularni pointer-events'siz qilib, keyin oddiy click yuboramiz.
_DISABLE_BACKDROPS_JS = (
    "() => document.querySelectorAll('.cdk-overlay-backdrop')"
    ".forEach(b => { b.style.pointerEvents = 'none'; })"
)


class BasePage:
    """Smartup24 (x24 Angular UI) uchun universal sahifa funksiyalari.

    Forma inputlari, selectlar, radio/checkbox, grid va saqlash amallari shu
    klass orqali bajariladi — testlarda raw ``page.locator(...)`` ishlatilmaydi.
    Elementlar barqaror ``smtid`` yoki ko'rinadigan label matni orqali topiladi
    (dinamik ``ng.formN.*`` name emas).

    Asosiy komponentlar:
      - text input : ``smt-input`` / ``smt-textarea`` / ``smt-date-picker`` /
                     ``smt-phone-input`` -> ichki ``input``/``textarea``
      - select     : ``smt-data-select`` / ``smt-multi-data-select`` -> ichki filtr input,
                     dropdown ``.cdk-overlay-container smt-select-dropdown li``
      - tree select: ``smt-tree-select[smtidfield]`` -> ``smt-select-trigger``, overlay'da
                     ``[role=tree]`` panel; tanlangan qiymat trigger MATNIDA
      - radio      : ``smt-radio-group`` -> ``label[smt-radio]``
      - toggle     : ``smt-switch`` / ``smt-checkbox`` -> ``input[type=checkbox]``
      - grid qatori: ``.smt-data-row``; qidiruv: ``searchbox "Поиск..."``
      - heading    : ``HEADING`` (faqat title span)
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

    @qa_action("«{0}» sahifasi ochilishini kutish")
    def expect_heading(self, text, *, timeout=30_000):
        """Aktiv forma sarlavhasi (title span) ``text`` ni o'z ichiga olishini kutadi."""
        expect(self.page.locator(HEADING).last).to_contain_text(text, timeout=timeout)

    def wait_for_loader(self, timeout=60_000):
        """Global sahifa loaderi ko'rinsa, yo'qolishini kutadi. Loader tez o'tsa no-op."""
        loader = self.page.locator(PAGE_LOADER)
        try:
            loader.wait_for(state="visible", timeout=1_000)
        except Exception:
            return
        try:
            loader.wait_for(state="hidden", timeout=timeout)
        except Exception as exc:
            logger.warning("Loader %s ms ichida yo'qolmadi: %s", timeout, exc)

    # ------------------------------------------------------------------------------------------------------------------
    # Label -> control topish (barcha field funksiyalari uchun umumiy)
    # ------------------------------------------------------------------------------------------------------------------

    # Label'dan yuqoriga "control'ni o'z ichiga olgan eng yaqin ajdod" qidiriladi.
    # YANGI field tag'i shu ro'yxatda bo'lishi SHART — aks holda wrapper butun
    # formagacha ko'tarilib, qo'shni field'ga yozib yuboradi.
    _CONTROL_XPATH = (
        "ancestor::*["
        ".//smt-input or .//smt-textarea or .//smt-date-picker or .//smt-phone-input"
        " or .//smt-data-select or .//smt-multi-data-select or .//smt-tree-select"
        " or .//smt-select"
        " or .//smt-radio-group or .//smt-switch or .//smt-checkbox or .//*[@smt-checkbox]"
        "][1]"
    )

    # Matnli field'lar. smt-date-picker'ga sana matn sifatida yoziladi (kalendar faqat
    # ikonkadan ochiladi).
    _INPUT_CSS = "smt-input, smt-textarea, smt-date-picker, smt-phone-input"

    # smt-data-select / smt-multi-data-select: ichida filtr input bor;
    # smt-tree-select va smt-select: input YO'Q, smt-select-trigger bosiladi.
    _SELECT_CSS = "smt-data-select, smt-multi-data-select, smt-tree-select, smt-select"

    _TREE_PANEL = ".cdk-overlay-container [role=tree]"

    # Server i18n / deploy'lar label nomini o'zgartirib turadi — testdagi bitta
    # label barcha variantlariga mos keladi (anchored: "Название" "Краткое
    # название"ga mos EMAS). Yangi rename chiqsa shu yerga qo'shiladi.
    _LABEL_SYNONYMS = {
        "Примечания": ("Примечания", "Примечание"),           # OAuth2 formasi i18n leak
        "Код": ("Код", "Код сервера"),                       # OAuth2 formasi i18n leak
        "Название": ("Название", "table.name"),              # OAuth2 prod: tarjimasiz kalit
        "Юр. лица название": ("Юр. лица название", "Название"),
        "Тип Юр. лица": ("Тип Юр. лица", "person kind"),           # tarjimasiz i18n kaliti
        "Краткое название": ("Краткое название", "Альтернативное название"),  # Продукт
        "Начало": ("Начало", "Дата начало", "Дата начала"),
        "Конец": ("Конец", "Дата окончания"),
        "measure": ("measure", "Единица измерения"),
        "Примечание о призе": ("Примечание о призе", "Примечание к призу"),
        "Правила": ("Правила", "Правила для анализа"),
    }

    # Status matni server i18n'iga qarab ruscha/inglizcha almashib turadi (grid,
    # toggle tugma, Просмотр input) — testda istalgan tilda yozish mumkin.
    _STATUS_SYNONYMS = {
        "Активный": r"Активный|active",
        "Неактивный": r"Неактивный|passive",
        "Пассивный": r"Пассивный|passive",
        "active": r"active|Активный",
        "passive": r"passive|Неактивный|Пассивный",
    }

    def _label_pattern(self, label):
        # "Название", "Название *", " Название * " — barchasi mos
        variants = self._LABEL_SYNONYMS.get(label, (label,))
        alt = "|".join(re.escape(v) for v in variants)
        return re.compile(rf"^\s*(?:{alt})\s*\*?\s*$")

    def _label_locator(self, label, root):
        """Avval ``<label>``, topilmasa ``<span>``/``<t>`` (switch labeli ba'zan span)."""
        pattern = self._label_pattern(label)
        loc = root.locator("label").filter(has_text=pattern)
        if loc.count() == 0:
            loc = root.locator("label, span, t").filter(has_text=pattern)
        return loc

    def _field_wrapper(self, label, *, index=0, root=None):
        """Label'ning control'ni o'z ichiga olgan eng yaqin ajdodi — vertikal va
        gorizontal (span "Статус" + smt-switch) layout'larda ham ishlaydi."""
        root = root or self.page
        wrapper = self._label_locator(label, root).nth(index).locator(f"xpath={self._CONTROL_XPATH}")
        if wrapper.count() == 0:
            wrapper = self._label_locator(label, root).nth(index).locator("xpath=..")
        return wrapper.first

    def _control(self, tag, *, label=None, smtid=None, index=0, root=None):
        """``tag`` elementini ``smtid``, ``label`` yoki (label'siz) ``root`` ichidan topadi."""
        root = root or self.page
        if smtid is not None:
            # tag bir nechta bo'lishi mumkin; smt-tree-select id'ni `smtidfield`da saqlaydi
            parts = []
            for t in tag.split(","):
                t = t.strip()
                attr = "smtidfield" if t == "smt-tree-select" else "smtid"
                parts.append(f'{t}[{attr}="{smtid}"]')
            return root.locator(", ".join(parts)).nth(index)
        if label is not None:
            return self._field_wrapper(label, index=index, root=root).locator(tag).first
        if root is not self.page:
            # Label'siz kontekst (masalan zakaz jadvali QATORI ichidagi select)
            return root.locator(tag).nth(index)
        raise ValueError(f"{tag}: label, smtid yoki root dan bittasini bering")

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
        """Matnli field (smt-input / smt-textarea / smt-date-picker / smt-phone-input).

        Topish: ``label="Название"`` yoki ``smtid="name"``.
        Amal:
          - ``value=...`` : tozalab (clear=True) shu qiymatni yozadi
          - ``expect_value=...`` : qiymatni tasdiqlaydi (value berilsa default = value)
          - ``return_value=True`` : joriy qiymatni qaytaradi
          - ``press_tab=True`` : yozgach Tab bosadi
        """
        control = self._control(self._INPUT_CSS, label=label, smtid=smtid, index=index, root=root)
        field = control.locator("input, textarea").first
        expect(field).to_be_visible()

        # Maskali raqam maydoni (inputmode="decimal", masalan "Порядковый номер"):
        # fill() ni JIM yutadi va qiymatni probel bilan formatlaydi ("4 549") —
        # harfma-harf yozamiz, tekshiruvda probellarni e'tiborsiz qoldiramiz.
        masked_decimal = (field.get_attribute("inputmode") or "") == "decimal"

        if value is not _UNSET:
            self._close_overlay()   # oldingi field'dan qolgan backdrop klikni to'sadi
            field.click()
            if clear:
                field.press("ControlOrMeta+A")
                field.press("Backspace")
            if masked_decimal:
                field.press_sequentially(str(value), delay=50)
            else:
                field.fill(str(value))
            if press_tab:
                field.press("Tab")

        expected = expect_value
        if expected is _UNSET and value is not _UNSET:
            expected = str(value)
        if expected is not _UNSET:
            synonyms = self._STATUS_SYNONYMS.get(expected)
            if synonyms:
                expect(field).to_have_value(re.compile(rf"^\s*(?:{synonyms})\s*$"))
            elif masked_decimal:
                pattern = r"\s*".join(re.escape(ch) for ch in str(expected))
                expect(field).to_have_value(re.compile(rf"^\s*{pattern}\s*$"))
            else:
                expect(field).to_have_value(expected)

        if return_value:
            return field.input_value()
        return field

    # ------------------------------------------------------------------------------------------------------------------
    # Select
    # ------------------------------------------------------------------------------------------------------------------

    def _open_select(self, label=None, smtid=None, index=0, root=None):
        """Selectni topib dropdownini ochadi. ``(select, trigger, tag_name)`` qaytaradi.

        ``trigger`` — filtr matni yoziladigan input: data-select'da komponent
        ichidagisi, tree-select'da overlay paneldagi "Поиск...", smt-select'da None."""
        select = self._control(self._SELECT_CSS, label=label, smtid=smtid, index=index, root=root)
        expect(select).to_be_visible()
        self._close_overlay()   # oldingi field'dan qolgan backdrop klikni to'sadi
        tag_name = select.evaluate("el => el.tagName.toLowerCase()")

        if tag_name == "smt-tree-select":
            select.locator("smt-select-trigger").first.click()
            trigger = self.page.locator(f'{self._TREE_PANEL} input[placeholder="Поиск..."]').last
            expect(trigger).to_be_visible()
            return select, trigger, tag_name

        if tag_name == "smt-select":
            select.locator("smt-select-trigger").first.click()
            return select, None, tag_name

        # Placeholder deploy'ga qarab "Подбор"/"Выбрать"/"Выберите..." — fallback: birinchi input
        trigger = select.locator('input[placeholder="Подбор"]').first
        if trigger.count() == 0:
            trigger = select.locator("input").first
        expect(trigger).to_be_visible()
        trigger.click()
        return select, trigger, tag_name

    def _click_option(self, option_text, *, exact=True, timeout=30_000):
        """Ochilgan dropdown/menu/tree'dan ``option_text`` variantini bosadi.

        Dropdown kechikib render bo'ladi va qaysi konteynerda chiqishi select turiga
        bog'liq — shuning uchun barcha nomzodlarni deadline'gacha qayta tekshiramiz.
        "Добавить «...»"/"Показать все" harakat elementlari chiqarib tashlanadi
        (``exact=False`` da ular ham mos kelib, yaratish formasini ochib yuborardi)."""
        pattern = re.compile(rf"^\s*{re.escape(option_text)}\s*$") if exact else re.compile(re.escape(option_text))
        action_items = re.compile(r"Добавить|Показать все")
        dropdown = self.page.locator("smt-select-dropdown").last
        overlay = self.page.locator(".cdk-overlay-container")

        # smt-select-dropdown variantlari (oddiy bosiladi)
        list_options = [
            dropdown.locator("li").filter(has_text=pattern, has_not_text=action_items).first,
            # Ko'p ustunli lookup: li matni bir nechta katakdan iborat va tor dropdown'da
            # 1-ustun span 0px (hidden) — span EMAS, uni o'z ichiga olgan li bosiladi.
            dropdown.locator("li")
            .filter(has=self.page.get_by_text(option_text, exact=exact))
            .filter(has_not_text=action_items)
            .first,
            dropdown.get_by_text(option_text, exact=exact).filter(has_not_text=action_items).first,
        ]
        # Backdrop'li menu/tree variantlari (backdrop o'chirilib bosiladi).
        # Tree'da treeitem accessible name'i ishonchsiz ("Свернуть … X X") — avval
        # ko'rinadigan matn bo'yicha qidiriladi.
        overlay_options = [
            self.page.locator(self._TREE_PANEL)
            .get_by_text(option_text, exact=exact)
            .filter(has_not_text=action_items)
            .first,
        ] + [
            overlay.get_by_role(role, name=option_text, exact=exact).filter(has_not_text=action_items).first
            for role in ("menuitemcheckbox", "menuitem", "option", "treeitem")
        ]

        deadline = time.monotonic() + timeout / 1000
        while True:
            option = next((o for o in list_options if o.count() > 0), None)
            if option is not None:
                break
            candidate = next((o for o in overlay_options if o.count() > 0), None)
            if candidate is not None:
                expect(candidate).to_be_visible(timeout=timeout)
                self.page.evaluate(_DISABLE_BACKDROPS_JS)
                candidate.click()
                return
            if time.monotonic() >= deadline:
                raise AssertionError(self._option_miss_message(option_text))
            self.page.wait_for_timeout(100)

        expect(option).to_be_visible(timeout=timeout)
        # Dropdown sahifa pastida ochilsa variant viewport'dan tashqarida qoladi va
        # oddiy click timeout beradi — scroll, baribir bo'lmasa DOM click.
        try:
            option.scroll_into_view_if_needed(timeout=5_000)
        except Exception:
            pass
        try:
            option.click(timeout=15_000)
        except PlaywrightTimeoutError:
            option.evaluate("el => el.click()")

    def _option_miss_message(self, option_text) -> str:
        """Variant topilmaganda dropdown'dagi MAVJUD variantlarni sanab beradi."""
        names: list[str] = []
        try:
            items = self.page.locator(
                ".cdk-overlay-container smt-select-dropdown li, "
                ".cdk-overlay-container [role=option], "
                ".cdk-overlay-container [role=menuitem], "
                ".cdk-overlay-container [role=menuitemcheckbox], "
                ".cdk-overlay-container [role=treeitem]"
            )
            for i in range(min(items.count(), 15)):
                t = " ".join((items.nth(i).inner_text() or "").split())
                if t and t not in names:
                    names.append(t)
        except Exception:
            pass
        avail = ", ".join(f'"{n}"' for n in names) if names else "(dropdown bo'sh yoki ochilmagan)"
        msg = f'Select varianti «{option_text}» dropdownda topilmadi. Mavjud variantlar: {avail}'
        err = visible_error_dialog_text(self.page)
        if err:
            msg += f"\n  • OCHIQ Ошибка dialogi: {err}"
        return msg

    @qa_action("«{0}» ni ro'yxatdan tanlash")
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
        """Select'dan bitta variant tanlaydi — data/multi/tree/smt-select avtomatik ajratiladi.

        Topish: ``label="Производитель"`` yoki ``smtid="producer_id"`` (tree uchun smtidfield).
        ``search``: filtrga yoziladigan matn (default = ``option_text``);
        ``exact``: aniq moslik; ``expect_selected``: tanlov qo'llanganini tasdiqlaydi.
        """
        select, trigger, tag_name = self._open_select(label=label, smtid=smtid, index=index, root=root)

        query = option_text if search is None else search
        # Server qidiruvi ba'zan bir lahza bo'sh natija qaytaradi (variant mavjud bo'lsa
        # ham) — filtrni qayta yozib 3 marta urinamiz; to'liq timeout faqat oxirgisida.
        attempts = 3
        for attempt in range(attempts):
            last = attempt == attempts - 1
            if query and trigger is not None:
                trigger.fill("")
                trigger.fill(query)
            try:
                self._click_option(option_text, exact=exact,
                                   timeout=timeout if last else 8_000)
                break
            except (AssertionError, PlaywrightTimeoutError):
                if last:
                    raise
                self.page.wait_for_timeout(800)

        if tag_name == "smt-select":
            # Tanlangan qiymat trigger MATNIDA, dropdown o'zi yopiladi
            if expect_selected:
                expect(select).to_contain_text(re.compile(re.escape(option_text)), timeout=timeout)
            self._close_overlay()
        elif tag_name == "smt-tree-select":
            # Qiymat trigger MATNIDA; multi rejimda panel ochiq qoladi — yopamiz
            if expect_selected:
                expect(select).to_contain_text(re.compile(re.escape(option_text)), timeout=timeout)
            self._close_tree_panel()
        elif expect_selected:
            # Klik dropdown qayta-render paytiga tushsa tanlov qo'llanmay qoladi —
            # ikkala holatda ham bir marta qayta bosamiz.
            if tag_name == "smt-multi-data-select":
                # Qiymat "chip" matni sifatida qo'shiladi (input tozalanadi)
                pattern = re.compile(re.escape(option_text))
                try:
                    expect(select).to_contain_text(pattern, timeout=10_000)
                except AssertionError:
                    self._click_option(option_text, exact=exact, timeout=timeout)
                    expect(select).to_contain_text(pattern, timeout=timeout)
            else:
                # Filtr matnini o'zimiz yozganimiz uchun to_have_value yolg'ondan o'tishi
                # mumkin — tanlov commit bo'lganining haqiqiy belgisi dropdown yopilishi.
                expect(trigger).to_have_value(re.compile(re.escape(option_text)), timeout=timeout)
                dropdown = self.page.locator("smt-select-dropdown").last
                try:
                    expect(dropdown).to_be_hidden(timeout=5_000)
                except AssertionError:
                    self._click_option(option_text, exact=exact, timeout=timeout)
                    expect(dropdown).to_be_hidden(timeout=timeout)
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
        """Bir nechta variant tanlaydi (dropdown ochiq qoladi); ``close=True`` — oxirida Escape."""
        select, trigger, _ = self._open_select(label=label, smtid=smtid, index=index, root=root)
        for option_text in option_texts:
            if trigger is not None:
                trigger.fill(option_text)
            self._click_option(option_text, exact=exact, timeout=timeout)
        if close:
            if trigger is not None:
                trigger.press("Escape")
            else:
                self.page.keyboard.press("Escape")
        return select

    # ------------------------------------------------------------------------------------------------------------------
    # Radio group — smt-radio-group
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
        """``smt-radio-group`` dan variant (masalan "Активный") tanlaydi."""
        option_pat = re.compile(rf"^\s*{re.escape(option_text)}\s*$")
        group = self._control("smt-radio-group", label=label, smtid=smtid, index=index, root=root)
        option = group.locator("label[smt-radio]").filter(has_text=option_pat).first
        try:
            expect(option).to_be_visible(timeout=8_000)
        except AssertionError:
            # Guruh label'i ba'zan render bo'lmaydi — option'ni to'g'ridan-to'g'ri
            # matn bo'yicha topamiz (#main-content navbar tugmalaridan ajratadi).
            scope = root if root is not None else self.page.locator("#main-content")
            option = scope.locator("smt-radio-group label[smt-radio]").filter(has_text=option_pat).first
            expect(option).to_be_visible(timeout=30_000)
        self._close_overlay()
        option.click()
        if expect_selected:
            radio = option.locator("input[type=radio], [role=radio]").first
            expect(radio).to_have_attribute("aria-checked", "true")
        return group

    # ------------------------------------------------------------------------------------------------------------------
    # Toggle — smt-switch va smt-checkbox
    # ------------------------------------------------------------------------------------------------------------------

    _TOGGLE_CSS = "smt-switch, smt-checkbox, [smt-checkbox]"

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
        """Switch/checkbox toggle.

        Topish: ``label="Статус"``, ``smtid="..."`` yoki ``locator`` (Locator/selector).
        Amal:
          - ``checked=True/False`` : shu holatga keltiradi (idempotent) va tasdiqlaydi
          - ``expect_checked=True/False`` : faqat tasdiqlaydi
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

        cb = toggle.locator("input[type=checkbox]").first           # holat (ko'pincha hidden)
        clickable = toggle.locator("[role=switch], [role=checkbox]").first

        if checked is not _UNSET and cb.is_checked() != checked:
            self._close_overlay()
            (clickable if clickable.count() > 0 else toggle).click()

        want = checked if checked is not _UNSET else expect_checked
        if want is not _UNSET:
            if want:
                expect(cb).to_be_checked()
            else:
                expect(cb).not_to_be_checked()
        if return_value:
            return cb.is_checked()
        return cb

    # ------------------------------------------------------------------------------------------------------------------
    # Grid / list
    # ------------------------------------------------------------------------------------------------------------------

    @qa_action("Ro'yxatdan «{0}» ni topish")
    def grid_row(self, text, *contains, row_selector=".smt-data-row"):
        """``text`` li grid qatorini topadi va ``contains`` dagi matnlarni tekshiradi
        (status so'zlari ikkala tilda qabul qilinadi).

        Topilmasa: (1) keyingi sahifalarda qidiradi — ba'zi ro'yxatlarda (Бонус)
        qidiruv nom bo'yicha filtrlamaydi; (2) qidiruvni qayta yuboradi — save'dan
        keyin server qidiruv indeksi kechikadi, ro'yxat esa o'zi yangilanmaydi."""
        row = self.page.locator(row_selector).filter(has_text=text).first

        def _row_visible(timeout) -> bool:
            try:
                expect(row).to_be_visible(timeout=timeout)
                return True
            except AssertionError:
                return False

        def _try_find() -> bool:
            if _row_visible(5_000):
                return True
            # 1) Per-sahifa "Next page" tugmasi bor ro'yxatlar
            next_btn = self.page.get_by_role("button", name="Next page").first
            while next_btn.count() and next_btn.is_enabled():
                next_btn.click()
                self.wait_for_loader()
                if _row_visible(3_000):
                    return True
            # 2) Raqamli sahifa tugmalari ("1"/"2"...); "Next pages" faqat sahifa GURUHINI siljitadi
            pagination = self.page.get_by_role("group", name="Pagination").first
            seen = set()
            for _ in range(30):  # cheksiz sikldan himoya
                if not pagination.count():
                    break
                num_buttons = pagination.get_by_role("button", name=re.compile(r"^\d+$"))
                advanced = False
                for i in range(num_buttons.count()):
                    # Sahifa bosilgach pagination qayta render bo'lib qisqarishi mumkin —
                    # yo'qolgan tugmani 60s kutmaymiz.
                    if i >= num_buttons.count():
                        break
                    btn = num_buttons.nth(i)
                    try:
                        label = (btn.text_content(timeout=3_000) or "").strip()
                    except PlaywrightTimeoutError:
                        break
                    if label in seen:
                        continue
                    seen.add(label)
                    advanced = True
                    btn.click()
                    self.wait_for_loader()
                    if _row_visible(3_000):
                        return True
                group_next = pagination.get_by_role("button", name="Next pages").first
                if group_next.count() and group_next.is_enabled():
                    group_next.click()
                    self.wait_for_loader()
                elif not advanced:
                    break
            return False

        if not _try_find():
            # Enter qayta bosilsa joriy filtrlar (show_all) saqlangan holda server qayta so'raladi
            searchbox = self.page.get_by_role("searchbox", name="Поиск").first
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if searchbox.count() and (searchbox.input_value() or "").strip():
                    searchbox.press("Enter")
                    self.wait_for_loader()
                self.page.wait_for_timeout(1_500)
                if _try_find():
                    break

        try:
            expect(row).to_be_visible(timeout=3_000)
        except AssertionError:
            raise AssertionError(self._grid_miss_message(text, row_selector)) from None
        for value in contains:
            synonyms = self._STATUS_SYNONYMS.get(value)
            expect(row).to_contain_text(re.compile(synonyms) if synonyms else value)
        return row

    def _grid_miss_message(self, text, row_selector) -> str:
        """Qator topilmaganda holatni yig'ib tushunarli sabab quradi."""
        try:
            total = self.page.locator(row_selector).count()
        except Exception:
            total = "?"
        try:
            sb = self.page.get_by_role("searchbox", name="Поиск").first
            sb_val = (sb.input_value() or "").strip() if sb.count() else ""
        except Exception:
            sb_val = ""
        try:
            empty = self.page.get_by_text(re.compile(r"Нет результатов|Ничего не найдено")).first
            empty_seen = bool(empty.count()) and empty.is_visible()
        except Exception:
            empty_seen = False
        empty_txt = "KO'RINDI" if empty_seen else "yo'q"
        parts = [
            f'"{text}" qatori grid\'da topilmadi',
            f"jami qator: {total}",
            f'searchbox = "{sb_val}"',
            f'empty-state ("Нет результатов"): {empty_txt}',
            f"sahifa: {self.current_heading_text() or '?'}",
        ]
        err = visible_error_dialog_text(self.page)
        if err:
            parts.append(f"OCHIQ Ошибка dialogi: {err}")
        parts.append(
            "ehtimoliy sabab: yozuv yaratilmagan / qidiruv nom bo'yicha "
            "filtrlamaydi / server indeks kechikdi"
        )
        return "\n  • ".join(parts)

    def _grid_row_selected(self, row) -> bool:
        """Qator tanlangan: yonida action panel ochilgan YOKI qator checkboxi belgilangan."""
        panel_buttons = (
            row.locator("xpath=following-sibling::*[position()<=2]")
            .locator("button")
            .filter(visible=True)
        )
        if panel_buttons.count():
            return True
        checked = row.locator(
            "[role=checkbox][aria-checked='true'], input[type=checkbox]:checked"
        )
        return bool(checked.count())

    # Publik aliaslar — testlar ichki `_` metodlarga bog'lanmasligi uchun
    def settle(self, timeout=10_000):
        """Sahifa transition (loader + networkidle) tugashini kutadi."""
        return self._settle(timeout)

    def close_overlay(self, timeout=5_000):
        """Ochiq CDK overlay (dropdown/menu) ni yopadi."""
        return self._close_overlay(timeout)

    def grid_row_selected(self, row) -> bool:
        """Qator tanlanganini (action panel ochiq / checkbox belgilangan) bildiradi."""
        return self._grid_row_selected(row)

    def expect_no_row(self, text, *, row_selector=".smt-data-row"):
        """Grid'da matnli qator YO'Qligini tasdiqlaydi."""
        expect(self.page.locator(row_selector).filter(has_text=text)).to_have_count(0)

    def expect_row_count(self, text, count, *, row_selector=".smt-data-row"):
        """Grid'da matnli qatorlar soni aniq ``count`` ekanini tasdiqlaydi."""
        expect(self.page.locator(row_selector).filter(has_text=text)).to_have_count(count)

    def expect_error_dialog(self, *substrings, close=True):
        """Ошибка dialogi ``substrings`` ni o'z ichiga olishini tasdiqlaydi va
        (``close=True``) "Закрыть" bilan yopadi."""
        dialog = self.page.locator(".cdk-overlay-container")
        for text in substrings:
            expect(dialog).to_contain_text(text)
        if close:
            dialog.get_by_role("button", name="Закрыть").first.click()

    @qa_action("«{0}» qatorini ochish")
    def click_grid_row(self, text, row_selector=".smt-data-row"):
        self._settle()
        row = self.grid_row(text, row_selector=row_selector)
        # Markaz o'rniga chap qismdan bosamiz: ba'zi ro'yxatlarda pastki markazda
        # suzuvchi tugma qatorni to'sadi.
        row.click(position={"x": 120, "y": 12})
        self._settle()
        # Qator oldindan TANLANGAN bo'lsa klik tanlovni bekor qiladi (panel ochilmaydi) —
        # tanlov belgisi chiqmasa bir marta qayta bosamiz.
        for _ in range(10):
            if self._grid_row_selected(row):
                return row
            self.page.wait_for_timeout(300)
        row.click(position={"x": 120, "y": 12})
        self._settle()
        return row

    @qa_action("«{0}» bo'yicha qidirish")
    def search(self, text):
        """List qidiruviga (``searchbox "Поиск..."``) yozib Enter bosadi."""
        field = self.page.get_by_role("searchbox", name="Поиск").first
        expect(field).to_be_visible()
        field.click()
        field.fill(text)
        field.press("Enter")
        # 1s-probe'li wait_for_loader kech chiqqan loaderni o'tkazib yuboradi — sekin
        # CI'da grid_row ESKI ro'yxatni o'qib qolardi. Natija yuklanguncha kutamiz.
        self._settle()
        return field

    def show_all(self, *, button_name="Показать все"):
        """Filtr (voronka) ni ochib "Показать все" ni bosadi — passiv qatorlar ham chiqadi.

        - Ba'zi dialoglarda ikkita "Показать все" bor (biri yashirin) — ko'rinadigani olinadi.
        - Overlay panel o'zi yopiladi; inline panel (Клиенты) "Закрыть фильтры" bilan yopiladi.
        - RACE: funnel ochilgach darhol bosilsa klik no-op bo'ladi — qisqa kutamiz va
          qidiruv bor holda grid "Нет результатов" bo'lsa (filtr qo'llanmagan) 3 martagacha
          qayta urinamiz."""
        self._settle()
        for _ in range(3):
            trigger = self.page.locator("smt-data-table-filter button").first
            expect(trigger).to_be_visible()
            trigger.click()
            button = (
                self.page.get_by_role("button", name=button_name)
                .filter(visible=True)
                .first
            )
            expect(button).to_be_visible()
            self.page.wait_for_timeout(500)   # Angular binding tayyor bo'lsin (RACE)
            button.click()
            self.wait_for_loader()
            try:
                expect(button).to_be_hidden(timeout=2_000)
            except AssertionError:
                self.page.get_by_role("button", name="Закрыть фильтры").first.click()
                expect(button).to_be_hidden()
            self.wait_for_loader()
            searchbox = self.page.get_by_role("searchbox", name="Поиск").first
            has_search = bool(searchbox.count() and (searchbox.input_value() or "").strip())
            if not has_search:
                return
            if self.page.get_by_text("Нет результатов", exact=True).count() == 0:
                return

    @qa_action("Statusni «{0}» ga o'zgartirish")
    def change_status(self, option_text, *, button_name="Изменить статус"):
        """Tanlangan qator (``click_grid_row``) statusini o'zgartiradi: "Изменить статус"
        → menyudan variant (role=menuitem) → tasdiqlash "да"."""
        self.click_button(button_name)
        option = self.page.locator(".cdk-overlay-container").get_by_role("menuitem", name=option_text, exact=True).first
        expect(option).to_be_visible()
        option.click()
        self.confirm("да")

    def confirm(self, answer="да"):
        """Tasdiqlash dialogida javob tugmasini bosadi ("да"/"Да" — harf kattaligiga befarq).

        ``click_button`` ISHLATILMAYDI: u boshida ``_close_overlay`` chaqirib, ochiq
        dialogni Escape bilan yopib yuboradi."""
        pattern = re.compile(rf"^{re.escape(answer)}$", re.IGNORECASE)
        button = self.page.locator(".cdk-overlay-container").get_by_role("button", name=pattern).first
        expect(button).to_be_visible()
        button.click()
        expect(button).to_be_hidden()
        self.wait_for_loader()

    # ------------------------------------------------------------------------------------------------------------------
    # Navigatsiya settle / tugmalar / saqlash
    # ------------------------------------------------------------------------------------------------------------------

    def _close_tree_panel(self, timeout=5_000):
        """Ochiq qolgan smt-tree-select panelini yopadi (multi rejimda o'zi yopilmaydi).
        Backdrop yo'q, sintetik keydown ishlamaydi — faqat haqiqiy Escape."""
        panel = self.page.locator(self._TREE_PANEL)
        if panel.count() == 0:
            return
        self.page.keyboard.press("Escape")
        try:
            panel.first.wait_for(state="hidden", timeout=timeout)
        except Exception:
            logger.warning("smt-tree-select paneli %s ms ichida yopilmadi", timeout)

    def _close_overlay(self, timeout=5_000):
        """Ochiq CDK overlay'ni yopadi va yo'qolishini kutadi (hech narsa ochiq bo'lmasa no-op).

          1. Backdrop'li overlay — fade-out o'zi tugashini qisqa kutamiz, bo'lmasa Escape.
          2. Backdrop'SIZ pane (masalan "Роли" multi-select) — Escape ham, sintetik klik
             ham yopmaydi, faqat HAQIQIY tashqi klik: forma heading'iga bosamiz (zararsiz).
             Pane ochiq qolsa keyingi klik (Сохранить) uning ustiga tushadi — shuning
             uchun yo'qolguncha 3 marta urinamiz."""
        backdrop = self.page.locator(".cdk-overlay-backdrop-showing")
        if backdrop.count() > 0:
            try:
                backdrop.first.wait_for(state="hidden", timeout=1_500)
            except Exception:
                self.page.keyboard.press("Escape")
                try:
                    backdrop.first.wait_for(state="hidden", timeout=timeout)
                except Exception:
                    logger.warning("cdk-overlay backdrop %s ms ichida yopilmadi", timeout)
        pane = self.page.locator(".cdk-overlay-container .cdk-overlay-pane")
        if pane.count() == 0:
            return
        for _ in range(3):
            try:
                self.page.locator(HEADING).last.click(timeout=2_000)
            except Exception:
                self.page.keyboard.press("Escape")
            try:
                pane.first.wait_for(state="hidden", timeout=2_000)
                return
            except Exception:
                continue
        logger.warning("cdk-overlay pane 3 urinishda yopilmadi")

    def _settle(self, timeout=10_000):
        """Sahifa transition tugashini kutadi (loader + networkidle).

        Sarlavha va asosiy kontent ALOHIDA router-outlet'larda asinxron yangilanadi —
        faqat heading kutilsa, eski list'ning "Создать" tugmasi bosilib qolishi mumkin."""
        self.wait_for_loader()
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            pass

    @qa_action("«{0}» bo'limiga o'tish")
    def click_link(self, name, *, exact=True):
        """Sub-nav bo'limiga (link) o'tadi va kontent almashishini kutadi.

        Katta ro'yxat (Товары ~13k) loaderi uzoq turib klikni to'sadi (ayniqsa sekin
        CI'da) — har urinishdan oldin loader yo'qolishini kutamiz, 3 marta urinamiz."""
        link = self.page.get_by_role("link", name=name, exact=exact).first
        attempts = 3
        for attempt in range(attempts):
            self._settle()
            self.wait_for_loader()   # loader kech (>1s) chiqsa _settle uni o'tkazib yuboradi
            expect(link).to_be_visible(timeout=30_000)
            try:
                link.click(timeout=20_000)
                break
            except PlaywrightTimeoutError:
                if attempt == attempts - 1:
                    raise
        self._settle()
        return link

    @qa_action("«{0}» tugmasini bosish")
    def click_button(self, name, *, exact=True, expect_heading=None):
        """Tugmani bosadi. ``expect_heading`` berilsa — shu sarlavha ochilishini kutadi;
        ochilmasa va tugma hali joyida bo'lsa (klik qator paneli qayta-render paytida
        yutilgan) BIR marta qayta bosadi."""
        button = self._click_button_once(name, exact=exact)
        if expect_heading is None:
            return button
        try:
            self.expect_heading(expect_heading, timeout=15_000)
            return button
        except AssertionError:
            pass
        if button.count() and button.is_visible():
            self._settle()
            if button.is_visible():
                button.click()
        self.expect_heading(expect_heading)
        return button

    def _click_button_once(self, name, *, exact=True):
        self._close_overlay()   # qolgan backdrop klikni to'smasin
        # Status toggle tugmalari ("active"/"Неактивный") tili almashib turadi
        synonyms = self._STATUS_SYNONYMS.get(name)
        if synonyms:
            name = re.compile(rf"^\s*(?:{synonyms})\s*$")
        button = self.page.get_by_role("button", name=name, exact=exact).first
        expect(button).to_be_visible()
        button.click()
        return button

    def wizard_step(self, name):
        """Wizard qadam tabini bosadi (``[role=listitem]`` + aria-label, masalan "Товары")."""
        self._close_overlay()
        step = self.page.get_by_role("listitem", name=name).first
        expect(step).to_be_visible()
        step.click()
        self._settle()

    @qa_action("Yangi yozuv formasini ochish (Создать)")
    def open_create(self, *, button_name="Создать"):
        """"Создать" ni bosib create formaga o'tadi.

        Uzoq run paytida dev qayta deploy qilinsa create-route chunk'i 404 bo'ladi va
        conftest sahifani ro'yxatga reload qiladi — forma ochilmay "Создать" yana
        ko'rinadi. Shuning uchun tugma yo'qolguncha (= forma ochildi) 3 marta bosamiz."""
        self._settle()
        button = self.page.get_by_role("button", name=button_name, exact=True).first
        for _ in range(3):
            # Oldingi klik sekin bo'lsa ham forma ochilgan (URL'da `add`) — qayta bosmaymiz
            if "add" in self.page.url.lower() and not button.is_visible():
                return button
            result = self.click_button(button_name)
            self._settle()
            try:
                expect(button).to_be_hidden(timeout=15_000)
                return result
            except AssertionError:
                continue
        return result

    @qa_action("Formani saqlash (Сохранить)")
    def save(self, *, button_name="Сохранить", exact=True):
        """Сохранить bosadi va saqlash haqiqatan amalga oshganini tasdiqlaydi.

        Muvaffaqiyatli saqlanganda forma yopiladi va tugma DOM'dan yo'qoladi. Klik
        overlay/loader ustiga tushib yutilsa forma ochiq qoladi — shunda (faqat tugma
        ENABLED bo'lsa) bir marta qayta bosamiz. Tugma DISABLED = submit ketyapti,
        qayta bosilmaydi (dubl submit ham, "not enabled" timeout ham bo'lmaydi)."""
        button = None
        for attempt in range(2):
            self._settle()
            # Forma oxirgi maydondan keyin asinxron qayta-validatsiya qiladi (tugma bir
            # lahza disabled) — enable bo'lishini kutib, loader-detach poygasidan qochamiz.
            save_btn = self.page.get_by_role("button", name=button_name, exact=exact).first
            try:
                expect(save_btn).to_be_enabled(timeout=15_000)
                self._settle()
            except (AssertionError, PlaywrightTimeoutError):
                pass  # baribir urinamiz — quyidagi tekshiruvlar sababni beradi
            try:
                button = self.click_button(button_name, exact=exact)
                break
            except PlaywrightTimeoutError:
                if attempt == 1:
                    raise
        self.wait_for_loader()
        try:
            expect(button).to_be_hidden(timeout=5_000)
            return
        except AssertionError:
            pass
        if button.count() and button.is_visible() and button.is_enabled():
            self.click_button(button_name, exact=exact)
            self.wait_for_loader()
        # Forma yopilishi SHART — aks holda saqlanmagan yozuv keyinroq chalg'ituvchi
        # "Нет результатов" bo'lib chiqadi. 30s: sekin server save'i ulgursin.
        try:
            expect(button).to_be_hidden(timeout=30_000)
        except AssertionError:
            err = visible_error_dialog_text(self.page)
            if err:
                raise AssertionError(f"Saqlash bajarilmadi — server xatosi: {err}") from None
            raise AssertionError(
                "Saqlash bajarilmadi — «Сохранить» bosildi, lekin forma yopilmadi "
                "(yozuv saqlanmadi). Ошибка dialogi ko'rinmadi; ehtimol majburiy "
                "maydon jim bloklagan yoki overlay klikni to'sgan."
            ) from None

    def save_and_expect_heading(self, expected_heading, *, button_name="Сохранить", exact=True, timeout=60_000):
        """Сохранить bosadi va kutilgan heading ochilishini tekshiradi."""
        self.save(button_name=button_name, exact=exact)
        self.expect_heading(expected_heading, timeout=timeout)
