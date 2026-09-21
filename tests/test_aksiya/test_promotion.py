"""Поставщик "Акция" (aksiya/promotion) — to'liq CRUD + zakaz bonusi tekshiruvi.

MODUL HAQIDA (MCP bilan real DOM'da tasdiqlangan 2026-09-14/15)
--------------------------------------------------------------
Aksiya supplier'ning Просмотр formasidagi "Акция" bo'limidan boshqariladi
(``supplier_view`` → "Акция" tugma → ro'yxat + "Создать"). Forma 2 qadamli sehrgar:

**1-qadam «Основное»** (majburiy: Название, Дата начало, Дата окончания,
Характеристики клиента ≥1):
  - ``Название`` (smt-input), ``Дата начало`` / ``Дата окончания`` (smt-date-picker)
  - ``Тип акции`` (smt-select): ``Количество`` / ``Сумма`` / ``Смешанный``
  - ``Бонусы за заказ`` (smt-select): ``Множественный`` / ``Один``
  - ``Характеристики клиента`` — grid, MAJBURIY ("Подтип по умолчанию" default)
  - "ДАЛЕЕ" majburiy maydonlar to'lmaguncha DISABLED

**2-qadam «Уровни»** ("shart → mukofot"):
  - Условие: ``Тип условия`` (Обычный/Цикличный), ``Окупаемость`` (Значения/Процент),
    ``Мин. значение`` + ``Максимум`` (Обычный) / ``Макс. значение`` (Цикличный)
  - Бонус: ``Тип бонуса`` (``Количество``=tekin tovar / ``Скидка``=chegirma);
    tovar QIDIRUV "Поиск" → cdk-overlay ``<listitem>`` (inline "Нет результатов"
    chalg'itmasin) → grid qatoriga tushadi, qatorда ``Значения`` inputi (id="null")
  - "Сохранить" → "Сохранить?" confirm "да" → supplier_view

**CRUD action panel** (Акция ro'yxatida qator tanlanganда):
  - ``Просмотреть`` → "Акция (просмотр)" (Основное/Уровни/История изменений)
  - ``Изменить``    → "Акция (Редактирования)" (2 qadam, ДАЛЕЕ→Сохранить+да)
  - ``Неактивный``/``Активный`` (status TOGGLE) → "Изменить статус ... на X?" → да
  - ``Удалить``     → "Вы хотите удалить ...?" → да
  - Dublikat: nom BAZADA UNIKAL — bir xil nom bilan create → Ошибка
    "Этот название уже используется ... Попробуйте другой."

**Zakaz bonusi**: klient tovarni Мин.значение dan ko'p (masalan 2) buyurtма qilгач,
order Просмотр (Модератор → Продажи → Заказы → Просмотреть) sahifasidagi ALOHIDA
"Акция" tab'ida bonus tovar Кол-во=1 bilan chiqadi — draft (Черновик) holatidayoq.
Акция grid qatori: to'g'ridan-to'g'ri ``<div>`` kataklar → [Название, Кол-во(nth 1), Вес, Литр].

DIQQAT: bonus tovar qidiruvi supplier'ga BIRIKTIRILGAN (В наличие + narxli) tovarni
ko'rsatadi — aksiya ``run_product_linking`` DAN KEYIN yaratiladi.
"""
import re
from datetime import datetime, timedelta

import allure
import pytest
from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage
from utils.qa_report import visible_error_dialog_text


# Top-5 asosiy case (Тип акции × Тип бонуса). "min_value" — Условие "Мин. значение"
# (dona/summa chegarasi); "bonus_value" — bonus qatoridagi "Значения" (tekin dona
# yoki chegirma foizi); "max_value" — "Максимум" (Обычный; Цикличный'да None).
PROMOTION_CASES = {
    # buy N dona → M dona tekin ("2 cola → 1 fanta" misoli)
    "qty_free":     dict(akciya_type="Количество", bonus_type="Количество", min_value="2", max_value="10", bonus_value="1"),
    # buy N dona → chegirma %
    "qty_discount": dict(akciya_type="Количество", bonus_type="Скидка",     min_value="2", max_value="10", bonus_value="10"),
    # summa ≥ X → mahsulot tekin
    "sum_free":     dict(akciya_type="Сумма",      bonus_type="Количество", min_value="100000", max_value="1000000", bonus_value="1"),
    # summa ≥ X → chegirma %
    "sum_discount": dict(akciya_type="Сумма",      bonus_type="Скидка",     min_value="100000", max_value="1000000", bonus_value="10"),
    # cyclic: har N donaga takroriy bonus (Цикличный — faqat "Макс. значение")
    "cyclic_free":  dict(akciya_type="Количество", bonus_type="Количество", min_value="3", max_value=None, bonus_value="1", cyclic=True),
}


# ══════════════════════════════════════════════════════════════════════════════
# Umumiy helperlar
# ══════════════════════════════════════════════════════════════════════════════
def _pick_overlay_listitem(page: Page, text: str, *, exact: bool = False, timeout: int = 15_000):
    """Ochilgan cdk-overlay ``<list>`` ichidan ``text`` li ``<listitem>`` ni bosadi.

    Xarakteristika/bonus-tovar pickerlari label'siz (smt-select-trigger + input),
    variantlar overlay'da role=listitem — BasePage.select bu grid-ichi pickerlarni
    qoplamaydi, shuning uchun overlay bevosita bosiladi."""
    overlay = page.locator(".cdk-overlay-container")
    pattern = re.compile(rf"^\s*{re.escape(text)}\s*$") if exact else re.compile(re.escape(text))
    item = overlay.get_by_role("listitem").filter(has_text=pattern).first
    expect(item).to_be_visible(timeout=timeout)
    # cdk-overlay backdrop oddiy klikni to'sadi — pointer-events'siz qilib, klik
    # yiqilsa DOM click (JS) fallback bilan bosamiz. [[cdk-overlay-flaky-clicks]]
    page.evaluate(
        "() => document.querySelectorAll('.cdk-overlay-backdrop')"
        ".forEach(b => { b.style.pointerEvents = 'none'; })"
    )
    try:
        item.scroll_into_view_if_needed(timeout=3_000)
    except Exception:
        pass
    try:
        item.click(timeout=8_000)
    except Exception:
        item.evaluate("el => el.click()")


def _open_supplier_akciya(page: Page, m: BasePage, supplier_name: str) -> None:
    """Модератор → Поставщики → supplier Просмотр → "Акция" bo'limini ochadi.

    Акция ro'yxati default'да faqat Активный statusni ko'rsatadi (funnel filtri);
    passiv (Неактивный) aksiyalar ham ko'rinishi uchun darrov "Показать все"
    qo'llaymiz (status testida deaktivatsiyadан keyin qatorni topish uchun SHART)."""
    flow_navigate(page, tab="Модератор", name="Поставщики")
    m.expect_heading("Поставщики")
    m.search(supplier_name)
    m.click_grid_row(supplier_name)
    m.click_button("Просмотреть")
    m.expect_heading("Поставщик (Просмотр)")
    m.click_button("Акция")
    m.settle()
    try:
        m.show_all()
    except Exception:
        pass


def _select_akciya_row(page: Page, m: BasePage, name: str):
    """Акция ro'yxatida ``name`` qatorini tanlaydi (action panel ochiladi).

    Акция ro'yxati qidiruvi nom bo'yicha ba'zan "Нет результатов" qaytaradi (flaky) —
    yangi supplier'да aksiyalar oz, shuning uchun QIDIRUVSIZ to'g'ridan-to'g'ri
    grid_row bilan topamiz; avvalgi filtr qolgan bo'lsa tozalaymiz."""
    # Qidiruv qoldig'ini tozalaymiz (akciya qidiruvi nom bo'yicha flaky "Нет
    # результатов" berardi — ro'yxat kichik, qidiruvsiz grid_row bilan topamiz).
    # Barcha statuslar _open_supplier_akciya'даги show_all bilan allaqachon ochiq.
    sb = page.get_by_role("searchbox", name="Поиск").first
    if sb.count() and (sb.input_value() or "").strip():
        sb.fill("")
        sb.press("Enter")
        m.wait_for_loader()
    m.settle()
    row = m.grid_row(name)
    cell = row.get_by_text(name, exact=True).first
    cell.click()
    # Tanlov toggle himoyasi: action panel ochilmagan bo'lsa bir marta qayta bosamiz.
    for _ in range(10):
        if m.grid_row_selected(row):
            break
        page.wait_for_timeout(300)
    else:
        cell.click()
    return row


def _row_action(page: Page, name: str):
    """Tanlangan qator ACTION PANELIdagi tugma (Просмотреть/Изменить/Неактивный/
    Активный/Удалить). "Изменить" supplier-view TOP tugmasida ham bor (Юр.Лицо
    tahriri) — chalkashmaslik uchun panelni Просмотреть+Удалить orqali scope qilamiz."""
    panel = (
        page.locator("div")
        .filter(has=page.get_by_role("button", name="Просмотреть"))
        .filter(has=page.get_by_role("button", name="Удалить"))
        .last
    )
    return panel.get_by_role("button", name=name, exact=True)


def _fill_step1(page: Page, m: BasePage, *, name: str, akciya_type: str, char: str) -> None:
    """1-qadam «Основное»: majburiy maydonlar + Характеристики клиента, ДАЛЕЕ."""
    # Boshlanish = bugun; tugash = +1 yil (kun raqami bir xil, aniq KEYINGI yil).
    start = datetime.now().strftime("%d.%m.%Y")
    end = (datetime.now() + timedelta(days=365)).strftime("%d.%m.%Y")

    m.input(label="Название", value=name)
    # Sana label'lari 2026-09-18 da o'zgardi: "Дата начала"→"Дата начало",
    # "Конец"→"Дата окончания" (MCP'да Saber OOO Акция создание formasida tasdiqlangan).
    m.input(label="Дата начало", value=start)
    m.input(label="Дата окончания", value=end)
    m.select(akciya_type, label="Тип акции")

    with allure.step(f"Характеристики клиента: {char}"):
        page.keyboard.press("Escape")  # smt-date-picker backdrop'ini yopish
        page.get_by_role("textbox", name="Выберите...").first.click()
        _pick_overlay_listitem(page, char)

    next_btn = page.get_by_role("button", name="ДАЛЕЕ")
    expect(next_btn).to_be_enabled(timeout=10_000)
    next_btn.click()
    m.settle()


def _fill_step2(page: Page, m: BasePage, *, bonus_type: str, min_value: str,
                max_value, bonus_product: str, bonus_value: str, cyclic: bool = False) -> None:
    """2-qadam «Уровни»: shart (Мин.значение + Максимум) + bonus (tovar + Значения)."""
    if cyclic:
        # Цикличный: "Окупаемость"/"Мин. значение" YO'Q — "Макс. значение" bor.
        m.select("Цикличный", label="Тип условия")
        m.input(label="Макс. значение", value=min_value)
    else:
        m.input(label="Мин. значение", value=min_value)
        if max_value is not None:
            m.input(label="Максимум", value=max_value)
    # "Тип бонуса" default = "Количество"; faqat undan FARQ qilsa (Скидка) tanlaymiz
    # (Цикличный rejimida bu select qat'iy Количество — qayta ochilmaydi).
    if bonus_type != "Количество":
        m.select(bonus_type, label="Тип бонуса")

    with allure.step(f"Бонус tovar: '{bonus_product}' qidirib qo'shish, Значения={bonus_value}"):
        # Overlay variant klik ba'zan qo'shmasдан ochiq qoladi (race) — "qidir →
        # tanla → qator paydo bo'ldimi" ni QATOR ko'ringuncha retry qilamiz.
        bonus_row = page.locator(".smt-data-row").filter(
            has=page.get_by_role("button", name="Удалить")
        ).last
        for attempt in range(3):
            search = page.get_by_role("textbox", name="Поиск").last
            search.click()
            search.fill("")
            search.fill(bonus_product)
            page.wait_for_timeout(600)   # server qidiruv natijasi settle bo'lsin
            try:
                _pick_overlay_listitem(page, bonus_product, exact=False, timeout=8_000)
                expect(bonus_row).to_be_visible(timeout=5_000)
                break
            except (AssertionError, PlaywrightTimeoutError):
                if attempt == 2:
                    raise AssertionError(
                        f"Бонус tovar '{bonus_product}' qatorga qo'shilmadi (overlay pick race)"
                    )
        value_input = bonus_row.locator("input").first
        expect(value_input).to_be_visible()
        # Qiymat TURG'UN bo'lguncha yozamiz (qator modeli kechikib "Значения"ni tozalashi mumkin).
        for _ in range(5):
            value_input.click()
            value_input.fill(bonus_value)
            page.wait_for_timeout(400)
            if (value_input.input_value() or "").strip() == bonus_value:
                break


def _save_promotion(page: Page, m: BasePage) -> None:
    """Уровни'да Сохранить + "Сохранить?" confirm "да" → supplier_view."""
    m.click_button("Сохранить")
    m.confirm("да")
    try:
        m.expect_heading("Поставщик (Просмотр)", timeout=15_000)
    except AssertionError:
        err = visible_error_dialog_text(page) or "(dialog yo'q — noma'lum sabab)"
        raise AssertionError(f"Aksiya saqlanmadi, formada qoldi. Ошибка: {err}")


# ══════════════════════════════════════════════════════════════════════════════
# CRUD run_* funksiyalari
# ══════════════════════════════════════════════════════════════════════════════
def run_promotion(page: Page, code, *, supplier_name: str, bonus_product: str,
                  case: str = "qty_free", char: str = "Подтип по умолчанию",
                  name: str = None) -> str:
    """``supplier_name`` uchun bitta aksiya YARATADI (``case`` — PROMOTION_CASES
    kaliti) va nomini qaytaradi. Admin login kutiladi; ``bonus_product`` supplier'ga
    biriktirilgan (В наличие) tovar bo'lishi shart."""
    m = BasePage(page)
    params = PROMOTION_CASES[case]
    name = name or f"aksiya-{case}-{code}"

    with allure.step(f"'{supplier_name}' → Акция → Создать"):
        _open_supplier_akciya(page, m, supplier_name)
        m.open_create()
        m.expect_heading("Акция (Создания)")

    with allure.step(f"1-qadam Основное: {name} (Тип акции={params['akciya_type']})"):
        _fill_step1(page, m, name=name, akciya_type=params["akciya_type"], char=char)

    with allure.step(
        f"2-qadam Уровни: Мин={params['min_value']}, Тип бонуса={params['bonus_type']}, "
        f"Значения={params['bonus_value']}"
    ):
        _fill_step2(
            page, m,
            bonus_type=params["bonus_type"], min_value=params["min_value"],
            max_value=params.get("max_value"), bonus_product=bonus_product,
            bonus_value=params["bonus_value"], cyclic=params.get("cyclic", False),
        )
        _save_promotion(page, m)

    with allure.step(f"'Акция' ro'yxatida '{name}' tekshirish"):
        m.click_button("Акция")
        m.grid_row(name)

    return name


def run_promotion_view(page: Page, *, supplier_name: str, name: str) -> None:
    """Aksiyani Просмотреть — "Акция (просмотр)" + bo'limlarini ochib tekshiradi."""
    m = BasePage(page)
    _open_supplier_akciya(page, m, supplier_name)
    _select_akciya_row(page, m, name)
    _row_action(page, "Просмотреть").click()
    m.expect_heading("Акция (просмотр)")
    m.click_button("Основное")
    m.click_button("Уровни")
    m.click_button("История изменений")


def run_promotion_edit(page: Page, *, supplier_name: str, name: str, new_name: str) -> str:
    """Aksiyani Изменить — Название'ni ``new_name`` ga o'zgartirib saqlaydi."""
    m = BasePage(page)
    _open_supplier_akciya(page, m, supplier_name)
    _select_akciya_row(page, m, name)
    _row_action(page, "Изменить").click()
    m.expect_heading("Акция (Редактирования)")
    m.input(label="Название", value=new_name)
    next_btn = page.get_by_role("button", name="ДАЛЕЕ")
    expect(next_btn).to_be_enabled(timeout=10_000)
    next_btn.click()
    m.settle()
    m.click_button("Сохранить")
    m.confirm("да")
    m.settle()
    with allure.step(f"Yangi nom '{new_name}' ro'yxatда tekshirish"):
        _open_supplier_akciya(page, m, supplier_name)
        m.grid_row(new_name)
    return new_name


def run_promotion_status(page: Page, *, supplier_name: str, name: str) -> None:
    """Aksiya statusini Активный → Неактивный → Активный (toggle + confirm)."""
    m = BasePage(page)
    _open_supplier_akciya(page, m, supplier_name)
    with allure.step("Активный → Неактивный"):
        _select_akciya_row(page, m, name)
        _row_action(page, "Неактивный").click()
        m.confirm("да")
    with allure.step("Неактивный → Активный (reaktivatsiya passiv qatorni topishi = deaktivatsiya bo'ldi)"):
        # _select_akciya_row passiv qatorni show_all bilan topadi; action panelda
        # "Активный" toggle borligi = qator hozir Неактивный (deaktivatsiya o'tdi).
        _select_akciya_row(page, m, name)
        _row_action(page, "Активный").click()
        m.confirm("да")
        m.grid_row(name, "Активный")


def run_promotion_deactivate(page: Page, *, supplier_name: str, name: str) -> None:
    """Aksiyani FAQAT deaktivatsiya qiladi (Активный → Неактивный, toggle + confirm).
    Case 4 (Неактивный aksiya → bonus yo'q) uchun: deaktivatsiyadан keyin zakaz
    urilsa bonus qo'llanmasligini tekshirish maqsadida."""
    m = BasePage(page)
    _open_supplier_akciya(page, m, supplier_name)
    _select_akciya_row(page, m, name)
    _row_action(page, "Неактивный").click()
    m.confirm("да")
    m.settle()
    with allure.step(f"'{name}' Неактивный statusга o'tganini tekshirish"):
        _open_supplier_akciya(page, m, supplier_name)
        m.grid_row(name, "Неактивный")


def run_promotion_duplicate(page: Page, code, *, supplier_name: str, bonus_product: str,
                            name: str, case: str = "qty_free",
                            char: str = "Подтип по умолчанию") -> None:
    """Mavjud ``name`` bilan yana aksiya yaratishga urinib, server "уже используется"
    Ошибка qaytarishini tasdiqlaydi (nom BAZADA unikal)."""
    m = BasePage(page)
    params = PROMOTION_CASES[case]
    _open_supplier_akciya(page, m, supplier_name)
    m.open_create()
    m.expect_heading("Акция (Создания)")
    _fill_step1(page, m, name=name, akciya_type=params["akciya_type"], char=char)
    _fill_step2(
        page, m,
        bonus_type=params["bonus_type"], min_value=params["min_value"],
        max_value=params.get("max_value"), bonus_product=bonus_product,
        bonus_value=params["bonus_value"], cyclic=params.get("cyclic", False),
    )
    m.click_button("Сохранить")
    m.confirm("да")
    with allure.step("Dublikat nom → Ошибка 'уже используется'"):
        err = visible_error_dialog_text(page) or ""
        assert "использ" in err.lower(), f"Dublikat nom xatosi kutilgan, olindi: {err!r}"
        page.locator(".cdk-overlay-container").get_by_role(
            "button", name=re.compile("Закрыть", re.I)
        ).first.click()


def run_promotion_delete(page: Page, *, supplier_name: str, name: str) -> None:
    """Aksiyani Удалить — tasdiqlab, ro'yxatdan yo'qolishini tekshiradi."""
    m = BasePage(page)
    _open_supplier_akciya(page, m, supplier_name)
    _select_akciya_row(page, m, name)
    _row_action(page, "Удалить").click()
    m.confirm("да")
    m.settle()
    with allure.step(f"'{name}' ro'yxatда yo'qligini tekshirish"):
        expect(page.locator(".smt-data-row").filter(has_text=name)).to_have_count(0)


# ══════════════════════════════════════════════════════════════════════════════
# Zakaz bonusi tekshiruvi — Модератор → Продажи → Заказы
# ══════════════════════════════════════════════════════════════════════════════
def verify_order_bonus(page: Page, *, bonus_product: str, client_name: str,
                       expected_qty: str = "1") -> None:
    """Модератор → Продажи → Заказы: ``client_name`` zakazini ochib, order Просмотр
    "Акция" tab'ida aksiya bonusi (tekin tovar) qo'llanganini tasdiqlaydi —
    bonus tovar qatori mavjud va Кол-во = ``expected_qty`` (MCP 2026-09-15)."""
    m = BasePage(page)

    with allure.step("Навигация: Модератор → Продажи → Заказы"):
        flow_navigate(page, tab="Модератор", name="Заказы")
        m.expect_heading("Заказы")
        m.settle()

    with allure.step(f"'{client_name}' Черновик zakazini tanlab 'Просмотреть'"):
        m.search(client_name)
        # Qatordagi klient/postavshik kataklari BUTTON — status katagi (Черновик,
        # oddiy matn) orqali tanlanadi (order_status_change patterni).
        row = m.grid_row(client_name, "Черновик")
        cell = row.get_by_text("Черновик", exact=True).first
        cell.click()
        for _ in range(10):
            if m.grid_row_selected(row):
                break
            page.wait_for_timeout(300)
        else:
            cell.click()
        m.click_button("Просмотреть")
        m.expect_heading("Заказ (просмотр)")

    with allure.step(f"'Акция' tab: bonus '{bonus_product}' Кол-во={expected_qty}"):
        m.click_button("Акция")
        m.settle()
        # Акция grid qatori: to'g'ridan-to'g'ri <div> kataklar (smt-cell-content EMAS —
        # 2026-09-18 UI'да bu grid oddiy div kataklardan iborat, MCP tasdiqlangan):
        # [Название продукта(0), Кол-во(1), Вес нетто(2), Литр(3)].
        bonus_row = m.grid_row(bonus_product)
        qty_cell = bonus_row.locator("xpath=./div").nth(1)
        expect(qty_cell).to_have_text(re.compile(rf"^\s*{re.escape(expected_qty)}\s*$"))


def verify_no_order_bonus(page: Page, *, bonus_product: str, client_name: str) -> None:
    """NEGATIV: ``client_name`` ning ENG YANGI Черновик zakazini ochib, order
    Просмотр "Акция" tab'ida aksiya bonusi qo'llanMAGANini tasdiqlaydi — trigger
    sharti bajarilmagan (masalan buyurtma miqdori Мин.значение dan KAM). Bonus tovar
    qatori "Акция" tab'ida BO'LMASLIGI kerak (Кол-во=0 ⇒ min=2 aksiyasi ishlamaydi).

    DIQQAT: klientning bir nechta Черновик zakazi bo'lsa (masalan test_210 qty=2
    bonusli + bu qty=1 bonussiz), ro'yxat eng yangi zakazni birinchi ko'rsatadi —
    ``grid_row(...).first`` shu qty=1 negativ zakazni oladi (verify_order_bonus
    bilan bir xil naqsh)."""
    m = BasePage(page)

    with allure.step("Навигация: Модератор → Продажи → Заказы"):
        flow_navigate(page, tab="Модератор", name="Заказы")
        m.expect_heading("Заказы")
        m.settle()

    with allure.step(f"'{client_name}' eng yangi Черновик zakazini tanlab 'Просмотреть'"):
        m.search(client_name)
        row = m.grid_row(client_name, "Черновик")
        cell = row.get_by_text("Черновик", exact=True).first
        cell.click()
        for _ in range(10):
            if m.grid_row_selected(row):
                break
            page.wait_for_timeout(300)
        else:
            cell.click()
        m.click_button("Просмотреть")
        m.expect_heading("Заказ (просмотр)")

    with allure.step(f"'Акция' tab: bonus '{bonus_product}' qatori YO'Q (bonus qo'llanmagan)"):
        m.click_button("Акция")
        m.settle()
        expect(
            page.locator(".smt-data-row").filter(has_text=bonus_product)
        ).to_have_count(0)


def _order_summary_number(page: Page, label_re: str) -> int:
    """Order Просмотр "Основное" summary'sidagi ``label: N`` span'idan N ni (probel/vergul
    tozalab) butun son sifatida qaytaradi. ``label_re`` anchored bo'lsin (masalan
    ``r"^Общая сумма:"`` — "Общая сумма скидки"/"...НДС" ga tegib ketmasin)."""
    span = page.locator("span").filter(has_text=re.compile(label_re)).first
    expect(span).to_be_visible(timeout=10_000)
    txt = span.inner_text()
    digits = re.sub(r"[^\d]", "", txt.split(":", 1)[1])
    return int(digits or "0")


def verify_order_discount(page: Page, *, client_name: str) -> None:
    """POZITIV (Скидка bonusi): ``client_name`` ning ENG YANGI Черновик zakazini ochib,
    order Просмотр "Основное" summary'sida CHEGIRMA qo'llanganini tasdiqlaydi —
    "Сумма к оплате" < "Общая сумма" (qty_discount aksiyasi: Тип бонуса=Скидка,
    masalan 10% → 200 000 dan 20 000 chegirma → to'lov 180 000). MCP 2026-09-21:
    order summary span'lari "Общая сумма: N" / "Сумма к оплате: N" (probel-formatли)."""
    m = BasePage(page)

    with allure.step("Навигация: Модератор → Продажи → Заказы"):
        flow_navigate(page, tab="Модератор", name="Заказы")
        m.expect_heading("Заказы")
        m.settle()

    with allure.step(f"'{client_name}' eng yangi Черновик zakazini tanlab 'Просмотреть'"):
        m.search(client_name)
        row = m.grid_row(client_name, "Черновик")
        cell = row.get_by_text("Черновик", exact=True).first
        cell.click()
        for _ in range(10):
            if m.grid_row_selected(row):
                break
            page.wait_for_timeout(300)
        else:
            cell.click()
        m.click_button("Просмотреть")
        m.expect_heading("Заказ (просмотр)")
        m.settle()

    with allure.step("'Основное' summary: Сумма к оплате < Общая сумма (chegirma qo'llangan)"):
        gross = _order_summary_number(page, r"^Общая сумма:")
        payable = _order_summary_number(page, r"^Сумма к оплате:")
        assert payable < gross, (
            f"Chegirma qo'llanmagan: Общая сумма={gross}, Сумма к оплате={payable} "
            f"(qty_discount aksiyasi to'lov summasini kamaytirishi kutilgan edi)"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Standalone (debug) — tovari bor mavjud supplier (Saber OOO) ustida create
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Акция")
@allure.feature("Создание")
@allure.title("Акция (standalone): Saber OOO'da '{case}' aksiya yaratish")
@pytest.mark.parametrize("case", list(PROMOTION_CASES))
def test_promotion(page: Page, code, case) -> None:
    """Flow kodini to'liq group_a zanjirisiz sinash uchun — Saber OOO (tovari bor)."""
    with allure.step("Tizimga kirish (admin)"):
        authorization(page)
    run_promotion(
        page, code,
        supplier_name="Saber OOO",
        bonus_product="B Fresh Classic lemonade",
        case=case,
    )


@allure.epic("Акция")
@allure.feature("Создание — негатив")
@allure.title("Акция (negativ): Характеристики клиента majburiy — ДАЛЕЕ disabled")
def test_promotion_requires_characteristic(page: Page, code) -> None:
    """NEGATIV biznes-qoida: "Характеристики клиента" tanlanmasa 1-qadamdagi "ДАЛЕЕ"
    tugmasi DISABLED bo'lib qoladi (majburiy maydon; MCP 2026-09-14). Faqat 1-qadam,
    Saber OOO — order/setup zanjiriga bog'liq emas (ishonchli)."""
    with allure.step("Tizimga kirish (admin)"):
        authorization(page)
    m = BasePage(page)
    _open_supplier_akciya(page, m, "Saber OOO")
    m.open_create()
    m.expect_heading("Акция (Создания)")
    start = datetime.now().strftime("%d.%m.%Y")
    end = (datetime.now() + timedelta(days=365)).strftime("%d.%m.%Y")
    m.input(label="Название", value=f"aksiya-neg-{code}")
    m.input(label="Дата начало", value=start)
    m.input(label="Дата окончания", value=end)
    m.select("Количество", label="Тип акции")
    page.keyboard.press("Escape")  # date-picker overlay'ini yopish
    with allure.step("Характеристики клиента to'ldirilmadi → ДАЛЕЕ DISABLED"):
        expect(page.get_by_role("button", name="ДАЛЕЕ")).to_be_disabled()
