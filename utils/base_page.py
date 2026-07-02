import logging
import re

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
      - select     : ``smt-data-select[smtid]`` -> ``input[placeholder="Подбор"]``,
                     dropdown ``.cdk-overlay-container`` ichida ``smt-select-dropdown li``
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
        ".//smt-input or .//smt-data-select or .//smt-radio-group"
        " or .//smt-switch or .//smt-checkbox or .//*[@smt-checkbox]"
        "][1]"
    )

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
            return root.locator(f'{tag}[smtid="{smtid}"]').nth(index)
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
        """``smt-input`` (text/number/textarea) bilan ishlash uchun universal funksiya.

        Inputni topish (bittasini bering):
          - ``label="Название"`` : ko'rinadigan field label orqali (asosiy usul)
          - ``smtid="name"``     : barqaror ``smt-input[smtid]`` orqali

        Amal:
          - ``value=...`` : maydonni tozalab (clear=True) shu qiymat bilan to'ldiradi
          - ``expect_value=...`` : qiymatni tasdiqlaydi (value berilsa default expect_value=value)
          - ``return_value=True`` : joriy qiymatni qaytaradi
          - ``press_tab=True`` : to'ldirgach Tab bosadi
        """
        control = self._control("smt-input", label=label, smtid=smtid, index=index, root=root)
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
        select = self._control("smt-data-select", label=label, smtid=smtid, index=index, root=root)
        expect(select).to_be_visible()
        trigger = select.locator('input[placeholder="Подбор"]').first
        if trigger.count() == 0:
            trigger = select.locator("input").first
        expect(trigger).to_be_visible()
        trigger.click()
        return select, trigger

    def _click_option(self, option_text, *, exact=True, timeout=30_000):
        """Ochilgan dropdown (``.cdk-overlay-container`` ichidagi ``smt-select-dropdown``)
        dan ``option_text`` variantini bosadi. "Добавить"/"Показать все" harakat
        elementlari inobatga olinmaydi (matn bo'yicha aniq filtrlanadi)."""
        dropdown = self.page.locator("smt-select-dropdown").last
        option = dropdown.locator("li").filter(
            has_text=re.compile(rf"^\s*{re.escape(option_text)}\s*$") if exact else re.compile(re.escape(option_text))
        ).first
        if option.count() == 0:
            option = dropdown.get_by_text(option_text, exact=exact).first
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
        """``smt-data-select`` (Подбор) dan bitta variant tanlaydi.

        Selectni topish (bittasini bering):
          - ``label="Производитель"`` : field label orqali
          - ``smtid="producer_id"``   : barqaror ``smt-data-select[smtid]`` orqali

        ``search``: dropdownda filtrlash uchun yoziladigan matn (default = ``option_text``);
        ``exact``: variant matnini aniq moslashtirish; ``expect_selected``: tanlangach
        Подбор inputida tanlangan qiymat ko'rinishini tasdiqlaydi.
        """
        select, trigger = self._open_select(label=label, smtid=smtid, index=index, root=root)

        query = option_text if search is None else search
        if query:
            trigger.fill(query)

        self._click_option(option_text, exact=exact, timeout=timeout)

        # Tanlangach matn select textiga emas, Подбор inputining value'siga tushadi.
        if expect_selected:
            expect(trigger).to_have_value(re.compile(re.escape(option_text)), timeout=timeout)
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
        select, trigger = self._open_select(label=label, smtid=smtid, index=index, root=root)
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
