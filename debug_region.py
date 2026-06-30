from playwright.sync_api import sync_playwright
from flow_authorization import authorization

REGION_URL = "https://app3.greenwhite.uz/x24/a2/sb/sbr/moderator/region_list"


def log(msg):
    print(f"[DEBUG] {msg}", flush=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(no_viewport=True)
        context.set_default_timeout(15000)
        context.set_default_navigation_timeout(60000)
        page = context.new_page()
        try:
            authorization(page)
            page.goto(REGION_URL)
            page.wait_for_load_state("networkidle")
            page.get_by_role("button", name="Создать").click()
            page.locator(".bg-white.box-border.duration-100").first.wait_for(state="visible")
            page.locator(".bg-white.box-border.duration-100").click()
            page.locator("smt-input input").first.wait_for(state="visible")
            page.wait_for_timeout(800)

            # "Статус" yonidagi DOM strukturasini chiqaramiz
            html = page.get_by_text("Статус", exact=True).first.evaluate(
                "el => { let n = el.closest('smt-control') || el.parentElement.parentElement; return n ? n.outerHTML : 'none'; }"
            )
            log("STATUS BLOCK HTML:")
            print(html[:3000], flush=True)

            log("---- checkboxes ----")
            log(f"checkbox role count = {page.get_by_role('checkbox').count()}")
            log(f"switch role count = {page.get_by_role('switch').count()}")
            log(f"smt-checkbox count = {page.locator('smt-checkbox').count()}")
            log(f"smt-switch count = {page.locator('smt-switch').count()}")
            log(f"smt-radio count = {page.locator('smt-radio').count()}")
            log(f"smt-toggle count = {page.locator('smt-toggle').count()}")
        except Exception as e:
            log(f"EXCEPTION: {type(e).__name__}: {e}")
            page.screenshot(path="dbg_region_err.png", full_page=True)
        finally:
            page.wait_for_timeout(1000)
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
