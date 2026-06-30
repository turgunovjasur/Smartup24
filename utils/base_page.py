import logging
import re
from datetime import datetime, timedelta

from playwright.sync_api import expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


logger = logging.getLogger(__name__)

_UNSET = object()


class BasePage:
    def __init__(self, page):
        self.page = page

    # ------------------------------------------------------------------------------------------------------------------

    def current_heading_text(self):
        try:
            headings = [item.strip() for item in self.page.get_by_role("heading").all_inner_texts()]
        except Exception:
            return ""
        return " | ".join(item for item in headings if item)

    # ------------------------------------------------------------------------------------------------------------------

    def visible_error_text(self, timeout=1_000):
        selectors = (
            "#biruniAlertExtended",
            "#biruniAlert",
            "[role='alert']:visible",
            ".alert-danger:visible",
            ".toast-message:visible",
            ".toast:visible",
        )
        for index, selector in enumerate(selectors):
            locator = self.page.locator(selector).first
            try:
                if index == 0 and timeout:
                    expect(locator).to_be_visible(timeout=timeout)
                elif not locator.is_visible():
                    continue
                text = re.sub(r"\s+", " ", locator.inner_text(timeout=timeout)).strip()
            except Exception:
                continue
            if text:
                return text
        return ""

    # ------------------------------------------------------------------------------------------------------------------

    def _transition_failure_message(
        self,
        *,
        action,
        expected,
        before_state,
        actual_state,
        ui_error="",
        location_hint="",
    ):
        lines = [
            "Smartup transition failed",
            f"Before page: {before_state or 'unknown'}",
            f"Action: {action}",
            f"Expected: {expected}",
            f"Actual: {actual_state or 'unknown'}",
        ]
        if ui_error:
            lines.append(f"UI error: {ui_error}")
        if location_hint:
            lines.append(f"Location hint: {location_hint}")
        return "\n".join(lines)

    # ------------------------------------------------------------------------------------------------------------------

    def save_and_expect_heading(
        self,
        expected_heading,
        *,
        action="Сохранить",
        before_state=None,
        expected_state=None,
        confirm_text=None,
        button_name="Сохранить",
        exact_button=True,
        timeout=120_000,
        location_hint="",
    ):
        before = before_state or self.current_heading_text()
        button = self.page.get_by_role("button", name=button_name, exact=exact_button).first
        expect(button).to_be_visible()
        button.click()

        if confirm_text is not None:
            self.confirm_biruni(confirm_text or None)
        self.wait_for_loader(timeout=timeout)

        expected = expected_state or f"{expected_heading} heading ochilishi"
        ui_error = self.visible_error_text(timeout=1_000)
        if ui_error:
            actual = f"still on {self.current_heading_text() or before or 'unknown'}"
            raise AssertionError(
                self._transition_failure_message(
                    action=action,
                    expected=expected,
                    before_state=before,
                    actual_state=actual,
                    ui_error=ui_error,
                    location_hint=location_hint,
                )
            )

        heading = self.page.get_by_role("heading").filter(has_text=expected_heading).first
        try:
            expect(heading).to_be_visible(timeout=timeout)
        except (AssertionError, PlaywrightTimeoutError) as exc:
            actual = f"still on {self.current_heading_text() or before or 'unknown'}; url={self.page.url}"
            raise AssertionError(
                self._transition_failure_message(
                    action=action,
                    expected=expected,
                    before_state=before,
                    actual_state=actual,
                    ui_error=self.visible_error_text(timeout=500),
                    location_hint=location_hint,
                )
            ) from exc

    # ------------------------------------------------------------------------------------------------------------------

    def checkbox(
        self,
        locator=None,
        checked=_UNSET,
        *,
        ng_model=None,
        label=None,
        check_all=False,
        first_visible=False,
        grid_name=None,
        expect_checked=_UNSET,
        return_value=False,
        index=0,
        root=None,
    ):
        """Smartup checkbox/switch bilan ishlash uchun yagona universal funksiya.

        Checkboxni topish (faqat bittasini bering):
          - label="НДС": ko'rinadigan field label orqali (asosiy usul)
          - ng_model="d.vat_enabled": input[ng-model=...] orqali
          - locator: tayyor Locator yoki selector string (grid checkbox va h.k.)
          - check_all=True: grid "hammasini belgilash" (input[bcheckall])
          - first_visible=True: birinchi ko'rinadigan grid checkbox

        Amal:
          - checked=True/False: shu holatga keltiradi (idempotent) va tasdiqlaydi
          - expect_checked=True/False: faqat holatni tasdiqlaydi
          - return_value=True: joriy bool holatni qaytaradi

        `root` (Page yoki modal Locator) va `index` topishni cheklaydi.
        """
        root = root or self.page

        # --- topish: bitta strategiya ---
        if label is not None:
            cb = self._field_locator_by_label(label, index=index, root=root, target="switch")
        elif ng_model is not None:
            cb = root.locator(f'input[ng-model="{ng_model}"]').nth(index)
        elif check_all or first_visible:
            # Grid ko'pincha loader (block-ui-overlay) ortidan kech render bo'ladi;
            # loader tushmasdan click qilinsa kaskad ko'rinmas input ustiga tushib qoladi.
            self.wait_for_loader()
            if first_visible:
                self.page.wait_for_load_state("networkidle")
                scope = root.locator(f'b-grid[name="{grid_name}"]') if grid_name else self.page
                cb = scope.locator("b-grid:visible input[type='checkbox']").first
            else:
                scope = root.locator(f'b-grid[name="{grid_name}"]') if grid_name else root
                cb = scope.locator("input[bcheckall]").first
            if cb.count() == 0:
                cb = scope.locator("input[type='checkbox']").first
            expect(cb).to_be_attached()
        elif locator is not None:
            cb = root.locator(locator).first if isinstance(locator, str) else locator
        else:
            raise ValueError(
                "checkbox(): label, ng_model, locator, check_all yoki first_visible dan bittasini bering"
            )

        # --- bosish: input opacity:0 (ko'rinmas) bo'lishi mumkin, shuning uchun click
        #     ko'rinadigan label/grid-cell/wrapper ustiga cascade qilinadi ---
        if checked is not _UNSET and cb.is_checked() != checked:
            def reached():
                try:
                    expect(cb).to_be_checked(timeout=1_000) if checked else expect(cb).not_to_be_checked(timeout=1_000)
                    return True
                except (AssertionError, PlaywrightTimeoutError):
                    return False

            label_el = cb.locator("xpath=ancestor::label[1]")
            cell_el = cb.locator(
                "xpath=ancestor::*[contains(@class,'tbl-checkbox-cell') or contains(@class,'tbl-header-cell')][1]"
            )
            wrap_el = cb.locator(
                "xpath=ancestor::*[contains(@class,'switch') or contains(@class,'checkbox') or contains(@class,'smt-checkbox') or contains(@class,'custom-control')][1]"
            )

            done = False
            if label_el.count() > 0 and label_el.first.is_visible():
                label_el.first.click()
                done = True
            elif label_el.count() > 0:
                # label bor, lekin ko'rinmas (masalan grid header'da balandligi 0) —
                # checkbox koordinatasi bo'yicha to'g'ridan-to'g'ri mouse click
                label_box = label_el.first.bounding_box()
                cb_box = cb.bounding_box()
                if label_box is not None and cb_box is not None and label_box["width"] > 0:
                    self.page.mouse.click(
                        label_box["x"] + min(10, label_box["width"] / 2),
                        cb_box["y"] + cb_box["height"] / 2,
                    )
                    done = reached()

            if not done and cell_el.count() > 0 and cell_el.first.is_visible():
                cell = cell_el.first
                cell.scroll_into_view_if_needed()
                box = cell.bounding_box()
                if box is not None and box["width"] > 0 and box["height"] > 0:
                    y = box["height"] / 2
                    for x in (min(24, box["width"] / 2), min(12, box["width"] / 2), box["width"] / 2):
                        cell.click(position={"x": x, "y": y})
                        if reached():
                            break
                done = True

            if not done:
                if wrap_el.count() > 0 and wrap_el.first.is_visible():
                    wrap_el.first.click()
                else:
                    expect(cb).to_be_visible()
                    cb.click()

        want = checked if checked is not _UNSET else expect_checked
        if want is not _UNSET:
            expect(cb).to_be_checked() if want else expect(cb).not_to_be_checked()
        if return_value:
            return cb.is_checked()
        return cb

    # ------------------------------------------------------------------------------------------------------------------

    def wait_for_loader(self, timeout=300_000):
        """
        Loader (overlay) paydo bo'lishini va keyin yo'qolishini kutadi.
        Sahifa settled bo'lsa True qaytaradi; loader timeout ichida
        yo'qolmasa xato ko'taradi.
        """
        overlay = self.page.locator(".block-ui-overlay")
        try:
            overlay.wait_for(state="visible", timeout=2_000)
        except Exception:
            # Agar loader 2 soniyada chiqmasa, demak jarayon tugagan yoki juda tez o'tgan
            return True

        try:
            overlay.wait_for(state="hidden", timeout=timeout)
        except Exception as exc:
            logger.warning("Loader %s ms ichida yo'qolmadi: %s", timeout, exc)
            raise
        return True

    # ------------------------------------------------------------------------------------------------------------------

    def confirm_biruni(self, expected_text=None, button_name="да"):
        """Biruni confirm modalini barqaror tasdiqlaydi."""
        confirm = self.page.locator("#biruniConfirm")
        expect(confirm).to_be_visible()
        if expected_text:
            expect(confirm).to_contain_text(expected_text)
        expect(confirm).to_have_css("opacity", "1")
        confirm.get_by_role("button", name=button_name, exact=True).click()
        confirm.wait_for(state="hidden")

    # ------------------------------------------------------------------------------------------------------------------

    def grid_row(self, text, *contains, grid_selector="b-grid"):
        """`text` bo'yicha grid qatorini topadi, ko'rinishini va (berilgan bo'lsa)
        `contains` dagi har bir matnni (nom, status va h.k.) o'z ichiga olishini tekshiradi."""
        grid = self.page.locator(grid_selector)
        row = grid.locator(".tbl-row").filter(has_text=text).first
        expect(row).to_be_visible()
        for value in contains:
            expect(row).to_contain_text(value)
        return row

    # ------------------------------------------------------------------------------------------------------------------

    def click_grid_row(self, text, grid_selector="b-grid"):
        row = self.grid_row(text, grid_selector=grid_selector)
        row.click()
        return row

    # ------------------------------------------------------------------------------------------------------------------

    def grid_controller(
        self,
        *,
        search=None,
        expand=False,
        reload=False,
        open_filter=False,
        open_setting=False,
        controller_selector="b-grid-controller",
    ):
        """List formadagi `b-grid-controller` boshqaruvlari. Tanlovga qarab bittasi bajariladi:

          - search="matn": qidiruv maydoniga yozib Enter bosadi (loader kutiladi)
          - expand=True: "X / Y" (page size, fa-arrow-down) tugmasini bosib ko'proq qator yuklaydi
          - reload=True: ro'yxatni yangilaydi (fa-redo)
          - open_filter=True: filtr oynasini ochadi (fa-filter)
          - open_setting=True: setting/ustunlar menyusini ochadi (fa-bars)
        """
        gc = self.page.locator(controller_selector).first

        if search is not None:
            field = gc.locator('input[ng-model="o.searchValue"]').first
            expect(field).to_be_visible()
            field.fill(search)
            field.press("Enter")
            self.wait_for_loader()
            return
        if expand:
            gc.locator("button:has(i.fa-arrow-down)").first.click()
            self.wait_for_loader()
            return
        if reload:
            gc.locator('button[ng-click="reload()"]').first.click()
            self.wait_for_loader()
            return
        if open_filter:
            gc.locator('button[ng-click="openFilter()"]').first.click()
            return
        if open_setting:
            gc.locator("button.dropdown-toggle:has(span.fa-bars)").first.click()
            return

        raise ValueError(
            "grid_controller(): search, expand, reload, open_filter yoki open_setting dan bittasini bering"
        )

    # ------------------------------------------------------------------------------------------------------------------

    def select_option(self, ng_model, option_text, clear=False):
        b_input = self.page.locator(f'b-input:has(input[ng-model="{ng_model}"])')
        b_input.locator("input").click()
        if clear:
            edit = b_input.locator(".edit")
            if edit.count() > 0 and edit.first.is_visible():
                edit.first.click()
                b_input.locator("input").click()
        option = b_input.locator("div.hint").get_by_text(option_text, exact=True).first
        expect(option).to_be_visible()
        option.click()

    # ------------------------------------------------------------------------------------------------------------------

    def select_b_input(self, ng_model, option_text, clear=False):
        b_input = self.page.locator(f'b-input:has(input[ng-model="{ng_model}"])')
        search = b_input.get_by_placeholder("Поиск")
        search.click()
        if clear:
            edit = b_input.locator(".edit")
            if edit.count() > 0 and edit.first.is_visible():
                edit.first.click()
            search.click()
        search.fill(option_text)
        option = b_input.locator("div.hint").get_by_text(option_text, exact=True)
        expect(option).to_be_visible()
        option.click()
        expect(search).to_have_value(option_text)

    # ------------------------------------------------------------------------------------------------------------------

    def _label_pattern(self, label):
        return re.compile(rf"^\s*{re.escape(label)}\s*(?:\*)?\s*$", re.IGNORECASE)

    # ------------------------------------------------------------------------------------------------------------------

    def _field_target(self, container, target):
        if target == "b-input":
            return container.locator("b-input:has(input[placeholder])").first
        if target == "switch":
            return container.locator("input[type='checkbox'], [role='switch']").first
        if target == "input":
            return container.locator(
                "xpath=.//*[self::input or self::textarea]"
                "[not(ancestor::b-input) and not(@type='checkbox') and not(@type='radio')]"
                "[not(starts-with(@id,'focusser-'))]"
            ).first
        return container.locator("input, textarea, b-input, [role='switch']").first

    # ------------------------------------------------------------------------------------------------------------------

    def _field_container_by_label(self, label, needs_search=False, index=0, root=None, target=None):
        root = root or self.page
        target = target or ("b-input" if needs_search else "input")
        label_locator = root.locator(
            "label, t, span, .control-label, .col-form-label, .form-label"
        ).filter(has_text=self._label_pattern(label))
        if label_locator.count() == 0:
            label_locator = root.get_by_text(self._label_pattern(label))

        match_index = 0
        ancestor_paths = (
            "ancestor::*[contains(concat(' ', normalize-space(@class), ' '), ' col ') or contains(@class,'col-')][1]",
            "ancestor::*[contains(@class,'input-group')][1]",
            "ancestor::*[contains(@class,'form-group')][1]",
            "ancestor::*[contains(@class,'form-row')][1]",
            "ancestor::*[contains(@class,'row')][1]",
            "..",
        )

        for label_index in range(label_locator.count()):
            label_item = label_locator.nth(label_index)
            try:
                expect(label_item).to_be_visible(timeout=1_000)
            except (AssertionError, PlaywrightTimeoutError):
                continue

            for ancestor in ancestor_paths:
                container = label_item.locator(f"xpath={ancestor}")
                if container.count() == 0:
                    continue
                field_target = self._field_target(container.first, target)
                if field_target.count() == 0:
                    continue
                if match_index == index:
                    return container.first
                match_index += 1
                break

        raise AssertionError(f"Field container not found by label: {label} (target={target})")

    # ------------------------------------------------------------------------------------------------------------------

    def _field_locator_by_label(self, label, *, index=0, root=None, target="input"):
        root = root or self.page
        label_locator = root.locator(
            "label, t, span, .control-label, .col-form-label, .form-label"
        ).filter(has_text=self._label_pattern(label))
        if label_locator.count() == 0:
            label_locator = root.get_by_text(self._label_pattern(label))

        target_xpath = {
            "input": (
                "following::*[(self::input or self::textarea)"
                " and not(ancestor::b-input)"
                " and not(@type='checkbox') and not(@type='radio') and not(@type='hidden')"
                " and not(starts-with(@id,'focusser-'))][1]"
            ),
            "b-input": "following::b-input[.//input][1]",
            "switch": "following::input[@type='checkbox'][1]",
        }[target]

        match_index = 0
        for label_index in range(label_locator.count()):
            label_item = label_locator.nth(label_index)
            try:
                expect(label_item).to_be_visible(timeout=1_000)
            except (AssertionError, PlaywrightTimeoutError):
                continue

            if target == "switch":
                field = label_item.locator("xpath=ancestor::label[1]//input[@type='checkbox'][1]")
                if field.count() == 0:
                    field = label_item.locator(f"xpath={target_xpath}")
            else:
                field = label_item.locator(f"xpath={target_xpath}")

            if field.count() == 0:
                container = self._field_container_by_label(label, index=match_index, root=root, target=target)
                field = self._field_target(container, target)
            if field.count() == 0:
                continue

            if target != "switch":
                try:
                    expect(field.first).to_be_visible(timeout=500)
                except (AssertionError, PlaywrightTimeoutError):
                    continue

            if match_index == index:
                return field.first
            match_index += 1

        raise AssertionError(f"Field not found by label: {label} (target={target})")

    # ------------------------------------------------------------------------------------------------------------------

    def b_input_by_label(
        self,
        label,
        value=_UNSET,
        *,
        expect_value=_UNSET,
        return_value=False,
        search_text=None,
        clear=False,
        exact=True,
        server_search=False,
        delay=50,
        index=0,
        root=None,
        timeout=30_000,
    ):
        b_input = self._field_locator_by_label(label, index=index, root=root, target="b-input")
        search = b_input.locator("input[placeholder]").first
        expect(search).to_be_visible()

        if value is not _UNSET:
            option_text = str(value)
            search.click()

            if clear:
                edit = b_input.locator(".edit")
                if edit.count() > 0 and edit.first.is_visible():
                    edit.first.click()
                search.click()

            query = search_text or option_text
            if server_search:
                search.press("ControlOrMeta+A")
                search.press("Backspace")
                search.press_sequentially(query, delay=delay)
            else:
                search.fill(query)

            option = b_input.locator(".hint-item").filter(has_text=option_text).first
            if option.count() == 0:
                option = b_input.locator("div.hint").get_by_text(option_text, exact=exact).first
            if option.count() == 0:
                option = b_input.get_by_text(option_text, exact=exact).last
            expect(option).to_be_visible(timeout=timeout)
            option.click()

        expected = expect_value
        if expected is _UNSET and value is not _UNSET:
            expected = str(value)
        if expected is not _UNSET:
            if isinstance(expected, str):
                expected = re.compile(re.escape(expected))
            expect(search).to_have_value(expected)

        if return_value:
            return search.input_value()
        return search

    # ------------------------------------------------------------------------------------------------------------------

    def _label_field_container(self, label, index=0, root=None, target="input"):
        """Label matni orqali form-group/col/form-row konteynerini topadi."""
        return self._field_container_by_label(label, index=index, root=root, target=target)

    # ------------------------------------------------------------------------------------------------------------------

    def input_by_label(
        self,
        label,
        value=_UNSET,
        *,
        expect_value=_UNSET,
        return_value=False,
        index=0,
        root=None,
        clear=True,
        press_tab=False,
    ):
        input_el = self._field_locator_by_label(label, index=index, root=root, target="input")
        expect(input_el).to_be_visible()

        if value is not _UNSET:
            input_el.click()
            if clear:
                input_el.press("ControlOrMeta+A")
                input_el.press("Backspace")
            input_el.fill(str(value))
            if press_tab:
                input_el.press("Tab")

        expected = expect_value
        if expected is _UNSET and value is not _UNSET:
            expected = str(value)
        if expected is not _UNSET:
            expect(input_el).to_have_value(expected)

        if return_value:
            return input_el.input_value()
        return input_el

    # ------------------------------------------------------------------------------------------------------------------

    def close_extended_alert(self):
        alert = self.page.locator("#biruniAlertExtended")
        expect(alert).to_be_visible()
        alert.locator("button.close").click()
        alert.wait_for(state="hidden")

    # ------------------------------------------------------------------------------------------------------------------

    def select_date(self, ng_model, option="custom", day=None, add_days=0):
        today = datetime.today()

        if option == "first":
            target = today.replace(day=1)
        elif option == "last":
            next_month = today.replace(day=28) + timedelta(days=4)
            target = next_month - timedelta(days=next_month.day)
        elif option == "today":
            target = today + timedelta(days=add_days)
        else:  # custom
            target = today.replace(day=day)

        self.page.locator(f'input[ng-model="{ng_model}"]').click()
        # self.page.get_by_role("cell", name=str(target.day)).first.click()
        self.page.get_by_role("cell", name=str(target.day), exact=True).first.click()

    # ------------------------------------------------------------------------------------------------------------------
