---
name: write-test
description: Yangi Playwright + pytest smoke test yozish. Foydalanuvchi yangi test, test funksiya yoki test fayl yaratmoqchi bo'lganda ishlatiladi.
---

# Yangi Test Yozish

Quyidagi qoidalarga qat'iy rioya qil:

## 1. Loyiha strukturasini tushun

- Testlar: `tests/smoke/test_setup/` yoki `tests/smoke/test_life_cycle/`
- Flowlar: `tests/smoke/flows/`
- User setup runner: `tests/smoke/test_setup/test_setup_runner.py`
- Group runnerlar: `tests/smoke/test_groups/test_<X>_grup/test_<x>_group_runner.py`
- All runner: `tests/smoke/test_all_runner.py`
- Fixtures: `tests/smoke/conftest.py`

## 2. Test fayl shabloni (`run_` + `test_` ikki funksiya)

Har bir test fayl IKKI funksiyadan iborat (test_legal_person / test_filial / test_room / test_robot real namunalari):

- **`run_<nomi>(page, code, ...)`** — qayta ishlatiladigan biznes logika; setup/group runner zanjiri shuni chaqiradi. `page` ni **allaqachon login qilingan** deb qabul qiladi (auth ichida chaqirilmaydi). Raqamlangan docstring testcase + `with allure.step("N - ...")` bloklari.
- **`test_<nomi>(page, code, ...)`** — `@allure.title(...)` bilan pytest entry; alohida/debug run uchun. `authorization(...)` (+ forma faqat filialda ko'rinsa `switch_filial(...)`) qilib, so'ng `run_<nomi>(...)` ni chaqiradi. Kerakli fixturalarni (`save_data`/`load_data`) qabul qilib `run_` ga uzatadi.

```python
import allure
from playwright.sync_api import expect            # Python assert emas, faqat kerak bo'lsa import
from tests.smoke.flows.flow_authorization import authorization
from tests.smoke.flows.flow_navigate import navigate_to, expect_page, switch_filial
from utils.base_page import BasePage

pytestmark = [allure.epic("Smoke"), allure.feature("<Feature>"), allure.story("<Story>")]

# ----------------------------------------------------------------------------------------------------------------------

def run_<nomi>(page, code, save_data=None):
    """Testcase: <maqsad>.

    1. <Tab> -> <Menyu> ro'yxatini ochish.
    2. "Создать" -> majburiy maydonlarni to'ldirish.
    3. Saqlab, ro'yxatda nom/kod/status ko'rinishini tekshirish.
    """
    entity_name = f"<entity>-pw{code}"
    entity_code = f"cod_<entity>_pw{code}"

    with allure.step("1 - <Entity> ro'yxatiga o'tish"):
        navigate_to(page, tab="<Tab>", name="<Menyu>")
        expect_page(page, heading="<Ro'yxat heading>")

    with allure.step("2 - Yangi <entity> formasini to'ldirish"):
        page.get_by_role("button", name="Создать").click()
        expect_page(page, heading="<Create heading>")
        BasePage(page).input(label="Код", value=entity_code)
        BasePage(page).input(label="Название", value=entity_name)
        BasePage(page).checkbox(label="Статус", expect_checked=True)

    with allure.step("3 - Saqlash va ro'yxatda tekshirish"):
        page.get_by_role("button", name="Сохранить", exact=True).first.click()
        expect_page(page, heading="<Ro'yxat heading>")
        BasePage(page).grid_row(entity_name, entity_code, "Активный")

    # Downstream testlarga kerak bo'lsa (oxirgi step):
    #     save_data("<key>", entity_code)

# ----------------------------------------------------------------------------------------------------------------------

@allure.title("<Inson o'qiydigan test nomi>")
def test_<nomi>(page, code, save_data):
    authorization(page, who='admin')
    # switch_filial(page, name=f"filial-pw{code}")   # forma faqat o'sha filialda ko'rinsa
    run_<nomi>(page, code, save_data=save_data)
```

### `run_` / `test_` konvensiyasi qoidalari
- **Maksimal base funksiya**: `navigate_to`, `expect_page`, `switch_filial` (flow) va `BasePage(page).input_by_label/b_input_by_label/multiselect/checkbox/grid_controller/grid_row/click_grid_row/confirm_biruni/wait_for_loader`. Raw `page.get_by_role/locator` faqat mos base funksiya yo'q joyda (masalan "Создать"/"Сохранить" tugmasi).
- **allure.step raqamlari docstring qadamlari bilan mantiqan mos** kelsin; step nomi qisqa va professional.
- **Test data** — `run_` boshida lokal `f"...{code}"` o'zgaruvchilar; downstream testga kerak bo'lsa oxirgi stepda `save_data(...)`.
- **`run_` auth qilmaydi** (page login qilingan deb keladi). Istisno: rolni almashtirish kerak bo'lsa `run_` ichida boshqa rol bilan kiriladi (masalan `run_room_attachment` `authorization(who="user"...)` qiladi).
- **Takroriy `switch_filial` qo'yma**: setup zanjiri bitta `session_page` ni bo'lishadi, shuning uchun filial konteksti `run_` lar orasida saqlanadi. Zanjirda filialga BIR MARTA o'tiladi (birinchi kerak bo'lgan `run_` — masalan `run_room` filial-pw{code} ga o'tadi), keyingi `run_` lar (robot, natural_person, ...) o'sha filialni meros qilib oladi va QAYTA `switch_filial` qilmaydi (ortiqcha kod). Standalone/debug run uchun `switch_filial` ni `test_` wrapper'ga qo'y (run_ ichiga emas) — shunda zanjirda takrorlanmaydi, alohida run'da esa default filialdan to'g'ri filialga o'tadi.
- **Verifikatsiya zanjiri**: save → `expect_page(list heading)` → (ro'yxatda topish uchun kerak bo'lsa) `grid_controller(search=...)` → `grid_row(code, name, "Активный")`.
- **Lokal helper** (`_select_grid_checkall` kabi) faqat shu faylda ishlatilsa faylda `_` prefiksi bilan qoladi; bir nechta testda kerak bo'lsa `flows/` yoki `BasePage` ga chiqariladi (1 qatorlik wrapper yozilmaydi).
- Fayl boshida module-level `pytestmark = [allure.epic, allure.feature, allure.story]` va funksiyalar orasida `# ---...---` separator.

## 3. Qoidalar

- **Fixtures** — conftest.py dan keladi, import qilma:
  - `page` — yakka test uchun fresh page; `session_page` — setup chain; `group_user_page` — group chain (login qilingan)
  - `code` — 6 xonali unikal son; `test_scope` — "smoke"/"regression"; `save_data` / `load_data` / `require_data` — data_store; `logger`
- **Allure**: har bir test `@allure.title()` va `with allure.step()` bilan bo'lishi SHART
- **Locator**: `page.locator()` ishlatilsin, `page.find_element()` EMAS
- **Assert**: `expect(locator).to_be_visible()` ishlatilsin, Python `assert` EMAS
- **Timeout**: DEFAULT_TIMEOUT (10s) yetarli; kerak bo'lsa `page.wait_for_timeout()` emas, `expect(...).to_be_visible()` kutish
- **Session data**: `save_data("key", value)` va `load_data("key")` orqali ma'lumot almashing
- **`code`**: har bir test uchun unikal identifikator, nom sifatida ishlating

## 4. Runner ga qo'shish

Yangi user setup testi yozilgandan keyin `tests/smoke/test_setup/test_setup_runner.py` ga import va `@allure.title` bilan qo'sh:

```python
from tests.smoke.test_setup.test_<nomi> import test_<nomi> as run_<nomi>

@allure.title("XX - <Nomi>")
def test_XX_<nomi>(session_page: Page, code):
    run_<nomi>(session_page, code)
```

## 5. Loyiha Xususiyatlari

### Runner config va dinamik qiymatlar
- Repo rootda `.env` mavjud bo'lsa direct `pytest`/PyCharm run konfiguratsiyasi undan olinadi; `.env` yo'q bo'lsa terminal/CI flaglari ishlaydi.
- Har bir run uchun `--url` va company mode majburiy: mavjud company uchun `--company-code/--company-password`, yangi company uchun `--create-company --head-email/--head-password`.
- Dinamik email va shunga o'xshash qiymatlar test/flow ichida active company code bilan quriladi:
  ```python
  user_email = f"user-pw{code}@{active_company_code}"
  ```

### code fixture
- `pytest.mark.user_setup` runner orqali ishlaganda: yangi `random.randint(100000, 999999)` yaratadi (6 xonali)
- Yakka test ishlaganda: `test-results/data/data_store.json` dan `"code"` kalitini o'qiydi
- Agar `data_store.json` bo'lmasa: `pytest.exit()` bilan aniq xato beradi

### authorization (rolga qarab login)
- Yagona funksiya: `authorization(page, who="admin"|"user"|"head", *, email=None, password=None, code=None, generated_code="new")`. **Eski `authorization_user` OLIB TASHLANGAN — ishlatma.**
- `who="user"` → `user-pw{code}@{company}` + `USER_PASSWORD`/`USER_PASS`. Avvalgi `authorization_user(page, code)` o'rniga `authorization(page, who="user", code=code)` yoz.
- `who="admin"` → `ADMIN_EMAIL`/`admin@{company}` + `ADMIN_PASSWORD`/`COMPANY_PASSWORD`. Avvalgi `authorization(page)` shu (default `who="admin"`).
- `who="head"` → `HEAD_ADMIN_EMAIL`/`HEAD_ADMIN_PASSWORD` (company yaratish uchun).
- `generated_code="new"` → yangi random code; `"old"` → `data_store.json` dagi `code` (yakka/debug run uchun). `code` berilsa — `generated_code` e'tiborsiz, o'sha ishlatiladi.
- `email`/`password` to'g'ridan-to'g'ri berilsa — `who` e'tiborsiz, o'shalar ishlatiladi.
- Credentiallar `.env` dan olinadi (precedence: `.env` yutadi — `conftest._option_or_env`).

### Selenium migratsiya source fayli
- Foydalanuvchi Selenium test kodini rootdagi `for_migratsiya.py` fayliga qo'yadi; migratsiya so'ralganda shu fayldan o'qib Playwright + pytest smoke testga o'tkaz, UI da run qilib xatolarini tuzat.
- Migratsiya qilingan Playwright kodni ham `for_migratsiya.py` faylining davomiga yoz; runnerga yoki test flowga avtomatik qo'shma, foydalanuvchi tekshirib o'zi ko'chiradi.
- Migratsiyada foydalanuvchi `run_tests.sh` oldin run qilinganini aytsa, user setup tayyor deb hisobla; user bilan login qil va `code` qiymatini `test-results/data/data_store.json` dan ol.
- Agar foydalanuvchi Playwright codegen pytest kodini bersa, Seleniumdan taxminiy migratsiya qilma; codegen kodini asos qilib olib loyiha fixture, Allure step, `code`, `authorization(who="user", code=code)`, helper flow va locator patternlariga moslab ber.
- Codegen kodini moslashda har bir ochilgan sahifa, forma yoki view uchun `expect(...)` bilan ochilganini tasdiqla; mavjud login/navbar flowlari bo'lsa, codegen qatorlari o'rniga o'shalarni ishlat.
- Codegen `page.goto("https://...")` kabi hardcode to'liq URL yozadi; bularni hech qachon kodda qoldirma. Conftest `--url` ni `os.environ["COMPANY_URL"]` ga yozadi va `tests/smoke/flows/flow_authorization.company_url()` shuni o'qiydi. Har bir hardcode URL ni `f"{company_url()}/login.html"`, `f"{company_url()}/a2/biruni/md/company_list"` kabi global URL ga bog'la (path qismi qoladi, domen `company_url()` dan keladi). `company_url` ni `flow_authorization` dan import qil.
- Umumiy test ma'lumotlarini ajratish uchun random ishlatma, `code` fixture qiymatini ishlat; bu test boshida generatsiya bo'ladi va butun sessiya davomida saqlanadi.
- `code` fixture umumiy entity nomlari va testlarni ajratish uchun ishlatiladi; agar formaning o'z `code`/`number` maydoni keyingi testlarda kerak bo'lsa, alohida `contract_code_{random_son}` kabi qiymat generatsiya qil, listda aynan shu qiymat bilan hozir yaratilgan recordni top, test muvaffaqiyatli tugaganda `save_data` orqali `data_store.json` ga saqla.
- Contract add formasida generated `contract_code_{random_son}` qiymati `Код` inputiga yoziladi; `Номер` inputi bilan almashtirib yuborma.
- Dinamik test qiymatlarini test boshida alohida o'zgaruvchiga yig'ib olma; kerakli joyida `f"...{code}"` ko'rinishida yoz.
- Barcha testlarda qayta ishlatiladigan umumiy helperlar, masalan `b-input` tanlash, local test helper emas `utils/base_page.py` ichidagi `BasePage` methodi bo'lsin.
- `input[ng-model=...]` kabi Angularga bog'langan locatorlardan iloji boricha foydalanma; label/role/text asosidagi `BasePage.fill_textbox_by_label`, `BasePage.select_b_input_by_label`, `page.get_by_role(...)` kabi locatorlarni afzal ko'r.
- Smoke UI testlarda form inputlarini to'ldirish, switch/radio/checkbox/button bosish uchun `page.evaluate()` ishlatma; real user action bo'lgan `locator.click()`, `locator.fill()`, `locator.press()` va `expect(...)` ishlat. `page.evaluate()` faqat o'qish/diagnostika yoki haqiqiy user flowga ta'sir qilmaydigan yordamchi holatlarda ishlatiladi.
- Test nomi, Allure title va step nomlari professional, sodda va test maqsadini darhol tushuntiradigan bo'lsin.
- Har bir test boshida docstringda testcase qadamlarini yoz; docstringdagi qadamlar test ichidagi `with allure.step(...)` bo'limlari bilan mantiqan mos kelsin.
- Add form testlarida birinchi navbatda `Код` inputini qidir va recordni listda code bo'yicha top; agar `Код` inputi bo'lmasa keyin nom/name bo'yicha yur.
- Add formadagi barcha majburiy `*` inputlarni albatta to'ldir.
- Test add qilgan har bir element list formada ham, view formada ham ko'ringanini tekshirishi shart.
- Agar qo'shilgan elementni list formadan topish uchun kerakli ustun yoki search yo'q bo'lsa, grid settingdan kerakli ustunni va shu ustun bo'yicha searchni yoq; Smartup listlarida bu umumiy pattern.
- Add formaga kiritiladigan nom, kompaniya, shaxs, manzil kabi biznes qiymatlarni mantiqan `Faker` bilan generatsiya qil; testda qidirish/bog'lash oson bo'lishi uchun kerakli joyda `code` yoki saqlangan entity code qo'shimchasini saqla.
- Smartup test yozish jarayonida yangi formaga kirilganda yoki URL/form state o'zgarganda screenshotni `skills/smartup-guide/references/forms/screenshots/<form-slug>/` ichiga saqla; `test-results/screens/smartup/` forma arxivi uchun ishlatilmasin.
- Natural Person alohida entity flow/test hisoblanadi; Legal Person regressionda director natural person kerak bo'lsa Natural Person helperini import qilib ishlatadi, natural person locator/fill/assert logikasini Legal Person ichida dublikat qilmaydi.

### Smoke va Regression farqi
- Smoke testlarda forma minimal yurishi uchun kerak bo'lgan majburiy maydonlar va minimal harakatlar bajariladi; maqsad forma ishlashini tez tekshirish.
- Regression testlarda formaning barcha imkoniyatlari qamrab olinadi: mavjud barcha muhim inputlar to'ldiriladi, qo'shimcha sozlamalar/holatlar ishlatiladi va kengroq tekshiruvlar yoziladi.
- Bu loyihada smoke/regression scope global arxitektura: `scripts/run_tests.py` default `smoke`, `--regression` yoki `--scope=regression` esa pytest `--scope` ga uzatiladi; `test_scope` fixture runner va biznes `run_*` funksiyalarga beriladi.
- Yangi test yozganda alohida smoke test va alohida regression test yaratma; bitta biznes `run_*` funksiyada `scope: str = "smoke"` parametr bo'lsin.
- Runner wrapperlar `test_scope` fixture qabul qilib `run_*(..., scope=test_scope)` chaqirsin; group/setup chain funksiyalari ham `scope` qabul qilib ichki `run_*` funksiyalarga uzatsin.
- Smoke branch minimal: real formani saqlash uchun kerakli majburiy maydonlar, keyingi testlarga kerak data-store keylari, save, listdagi asosiy `code/name/status` check.
- Regression branch full: forma ichidagi real mavjud barcha muhim inputlar, checkbox/switchlar, tablar va modal/quick-addlar browserda ko'rib aniqlanadi; Faker bilan real nom/manzil/shaxs qiymatlari to'ldiriladi; add qilingan data list va viewda tekshiriladi.
- Foydalanuvchi “shu testni regression qilamiz” desa, bu avtomatik ravishda add formani full to'ldirish, list check, view check, viewdagi mos card/tab/module holatlarini check qilish degani.
- Fieldlarni taxmin qilma. Har yangi regression forma uchun avval browserda add/view ochib screenshot/field state ol, screenshotlarni `smartup-guide/references/forms/screenshots/<form-slug>/` ichiga arxivla va forma bilimini `smartup-guide/references/forms/<form-slug>.md` ga yoz.
- Regression-only qiymatlar `data_store.json` da eski runlardan qolib ketmasin: smoke branch ularni `None`/null qilib tozalasin, regression branch esa view/list assert uchun kerak hamma muhim qiymatlarni saqlasin.
- Scope bilan yozilgan testni yakunda ikki mode bilan tekshir: smoke minimal path, regression full path. Cross-platform runnerda mavjud company uchun `python scripts/run_tests.py --url <server_url> --company-code <company_code> --company-password <company_password>` va `python scripts/run_tests.py --url <server_url> --company-code <company_code> --company-password <company_password> --regression` ishlatiladi; yangi company kerak bo'lsa `--create-company --head-email <head_email> --head-password <head_password>` mode ishlatiladi.

### Setup va Group test dependency modeli
- Yangi testlar har doim yangi server/baza holatida ham ishlashi kerak; lokal debugda oldingi rerunlardan data ko'paygan bo'lsa ham, testni mavjud dataga suyanib yozma.
- Fresh bazada feature settinglar default o'chirilgan bo'lishi mumkin; testga kerak bo'lgan settingni mavjud holatga suyanmay, idempotent tarzda yoqib/sozlab keyin asosiy flowga o't.
- User setup testlari bir-biriga bog'liq: oldingi setup test keyingi setup test uchun kerakli ma'lumot yoki entity yaratadi; setup ichida test yiqilsa keyingi setup test yura olmasligi mumkin.
- User setup testlari muvaffaqiyatli o'tgandan keyin group testlar boshlanadi: masalan `A group`, `B group` va boshqa guruhlar.
- Har bir group test user setup natijalariga bog'liq, lekin boshqa group testlarga bog'liq emas.
- Bir group ichida test yiqilsa, shu groupning qolgan testlari skip qilinadi; keyingi group testlari esa run bo'lishda davom etadi.
- Group testlar boshqa group yaratgan data yoki statega suyanmasin; A failed bo'lsa ham B, C, D... group testlari user_setup natijalaridan mustaqil run bo'lishi kerak.
- Har bir group ichki dependency uchun o'z data_store key prefixidan foydalansin (`a_group_*`, `b_group_*`, `c_group_*`), boshqa group prefixlarini o'qimasin.
- Group runnerlar `tests/smoke/test_groups/test_<X>_grup/test_<x>_group_runner.py` ko'rinishida bo'lsin; group ichidagi tartib wrapper test nomlari orqali `X-01`, `X-02` tarzida aniq berilsin.
- Har yangi group runner qo'shilganda `tests/smoke/test_all_runner.py` ichidagi import/listga ham qo'shilsin; full run faqat shu all runner orqali yuradi.
- `tests/smoke/test_all_runner.py` individual testlarni qayta e'lon qilmaydi; u user setup runner va group runner fayllarini setup -> A -> B -> ... tartibida ketma-ket chaqiradigan umumiy runner bo'lsin.
- Mexanizm pytest hook/marker orqali bo'lsin: `pytest.mark.user_setup` setup chain uchun, `pytest.mark.smoke_group("A")` kabi markerlar group chain uchun ishlatiladi.
- Bitta group testi failed bo'lsa faqat shu groupning keyingi testlari skip qilinadi, boshqa group markerlari skip qilinmaydi; user_setup failed bo'lsa barcha group testlar skip qilinadi.
- Grouplar bir-birining browser/page holatini meros qilib olmasin: full runnerda har group `group_page` bilan alohida oyna oladi, alohida group runner faylida esa testlar `group_user_page` bilan bitta module-scoped oyna va bitta loginni bo'lishadi.
- Har bir group runner ichida `*_GROUP_TEST_SCENARIO` constant bo'lsin; unda shu groupdagi testcaselar jamlangan biznes ssenariy yozilsin va `run_*_group_chain` boshida `allure.dynamic.description(...)` orqali reportga berilsin.
- Group ichidagi `run_*` funksiyalarda `login=True` default bo'lsin; group chain yoki group runner wrapperlari boshida bir marta login qilib, ichki chaqiruvlarga `login=False` bersin.
- B-group leaf testlari alohida fayllarda turadi: har bir `test_b_XX_*.py` ichida faqat bitta pytest test bo'lsin; umumiy order logikasi `order_helpers.py` ichidagi `run_*` funksiyalarda saqlanadi va `test_b_group_runner.py` shu `run_*` funksiyalarni zanjir qilib yig'adi.
- Bitta testga xos local yordamchi funksiyalar shu test faylida qolsin; helper/flow alohida faylga faqat funksiya bir nechta testda qayta ishlatilsa yoki haqiqiy umumiy flow bo'lsa chiqariladi.
- Bitta test ichidagi 1 qatorlik wrapper/helper yoki constant-getter funksiyalar yozilmasin; oddiy test data va `f"..."` kabi expressionlar test/run flow boshida local variable bo'lib tursin. Helper faqat takrorlanadigan UI harakati, conditional/retry, download/file validation yoki o'qishni aniq yengillashtiradigan blok uchun ishlatilsin.
- Download tekshiradigan testlar Windows, Linux va macOSda ishlashi kerak: contextlarda `accept_downloads=True` bo'lsin, fayl `download.save_as()` bilan `test-results/downloads/` ichiga OS-safe filename qilib saqlansin, va timeout bo'lsa Allurega URL/error/screenshot diagnostikasi yozilsin.
- Group test ichida cleanup yoki oldingi recordlarni cancel qilish faqat optional bo'lsin: data topilmasa no-op bo'lib, test yangi record yaratib davom etishi kerak.
- Yangi test yozishda u setup bosqichigami yoki qaysi mustaqil groupga tegishli ekanini aniq ajrat.
- `tests/smoke/test_setup/test_setup_runner.py` ichidagi mavjud barcha testlar user setup testlari hisoblanadi; runner setup testlari bilan bir papkada turadi va ular yozib bo'lingan.
- **user_setup yakunlangan**: `tests/smoke/test_setup/` ga YANGI test QO'SHILMAYDI. Yangi testlar `tests/smoke/test_life_cycle/` yoki yangi group (`tests/smoke/test_groups/test_<X>_grup/`) ichida yoziladi.
- **authorization har test boshida chaqirilmaydi**: login faqat sessiya boshida (setup `session_page` chain) yoki group boshida bir marta (`group_user_page`/group chain wrapperi) bajariladi; `run_*` biznes funksiyalari `page` ni allaqachon login qilingan deb qabul qiladi.
- **Yangi test ma'lumotlari `data_store.json` dan olinadi**: setup yaratgan entity nom/kodlari `load_data(...)` yoki `code` fixture orqali olinadi; test ichiga literal qiymat (`autotest`, `product-pw5963` kabi) hardcode qilinmaydi.
- Endi A-group testlari boshlanmoqda; A-groupning birinchi testi order uchun contract yaratish testi.
- A-group testlari `tests/smoke/test_groups/test_A_grup/` papkasiga yozib boriladi; masalan contract testi `tests/smoke/test_groups/test_A_grup/test_contract.py` ichida saqlanadi.
- A-group contract testida `a_group_contract_code` bilan birga `a_group_contract_name` ham `data_store.json` ga saqlanadi; order formasidagi `Договор` maydoni contract code emas, contract name bilan tanlanadi.
- Order testlari ko'p yozilishi kutiladi; yangi order case yozishda avval `tests/smoke/flows/flow_order/` ichidagi mavjud flowlardan foydalan, takrorlanadigan order harakatlari paydo bo'lsa ularni test ichida qoldirmay alohida order flowga ajrat.
- Test yozish, migratsiya yoki debug paytida xato testcase, noto'g'ri flow, ortiqcha murakkablik yoki dublikat kod ko'rinsa, foydalanuvchiga alohida xabar ber va tavsiya qilingan tuzatishni qisqa tushuntir.
- Contract add formasida contractni turli shartlar bilan yaratish mumkin; masalan `Типы оплат` sharti keyingi order testlarida alohida case sifatida tekshirilishi mumkin. Bunday holatlarda contract yaratish flowi parametrli bo'lsin va order test shu shart bilan yaratilgan contractni ishlatsin.
- Contract + `Типы оплат` case'ida `Тип оплаты` orderda auto-fill bo'lishini tekshir; user uni o'zgartirsa ham order ishlashi kerak, faqat contract sum limit tekshiriladi.
- Contract valyutasi order productlarini filterlaydi; boshqa valyutali contractga almashtirilsa, oldin tanlangan productlar o'chishi kutiladi.

## 6. Ish tartibi

1. Avval `$ARGUMENTS` bo'yicha kerakli fayllarni o'qi
2. Mavjud o'xshash testni o'rganib shablon chiqar
3. Yangi test yoz
4. Agar bu Selenium migratsiyasi bo'lsa, migrated kodni `for_migratsiya.py` davomiga yoz va runnerga avtomatik qo'shma
5. Oddiy yangi test bo'lsa, runner ga qo'sh
6. Foydalanuvchiga qaysi fayllarga nima qo'shilganini ko'rsat
