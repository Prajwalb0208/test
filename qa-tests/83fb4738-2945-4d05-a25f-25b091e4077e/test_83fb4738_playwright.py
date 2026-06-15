import re
import os
from playwright.sync_api import Page, expect


def _try_intent(page, selectors, action="click", value=None, timeout=5000):
    """Try multiple selectors in order, performing action on the first visible match."""
    errors = []
    
    log_path = os.environ.get("QA_ACTIONS_LOG")
    test_name = os.environ.get("PYTEST_CURRENT_TEST", "test").split(":")[-1].split(" ")[0]

    def _log(msg):
        # Print for stdout log
        print(f"\n> {msg}")
        if log_path:
            try:
                with open(log_path, "a") as f:
                    f.write(f"[{test_name}] [ACTION] {msg}\n")
            except Exception:
                pass

    import time
    start_time = time.time()
    while time.time() - start_time < timeout / 1000.0:
        for sel in selectors:
            try:
                if isinstance(sel, str):
                    loc = page.locator(sel).first
                else:
                    loc = sel.first
                if loc.is_visible():
                    if action == "click":
                        loc.click(timeout=timeout)
                        _log(f"Clicked element matching '{sel}'")
                    elif action == "fill":
                        loc.fill(value or "", timeout=timeout)
                        _log(f"Filled '{value}' into '{sel}'")
                    return loc
            except Exception as e:
                errors.append(f"{sel}: {e}")
        page.wait_for_timeout(200)
    raise Exception(f"Could not find element with any selector. Tried: {selectors}. Errors: {errors}")


def test_attempt_to_provision_tenant_with_missing_required_field(page: Page):
    page.goto("http://localhost:8080/dev")
    page.wait_for_load_state("networkidle")
    _try_intent(page, ["button:has-text('Provision New Tenant')", "a:has-text('Provision New Tenant')", "*:has-text('Provision New Tenant')"], action="click", value=None)
    page.fill('input[aria-label*="Tenant Name"], input[placeholder*="Tenant Name"]', "")
    page.fill("input[type='email']", ""); page.fill("input[type='password']", ""); _try_intent(page, ["button:has-text('Secure Session Initiation')"], action="click"); assert "required" in page.locator("body").text_content() or "missing" in page.locator("body").text_content(), f"Expected validation error message for missing fields, but found: {page.locator('body').text_content()}"
    page.fill("div[aria-label='CORPORATE EMAIL'] input[type='email'], input[placeholder*='user@organization.com'], input[type='email']", "")
    page.fill("div[aria-label='IDENTITY SECRET'] input[type='password'], input[placeholder*='\u2022\u2022\u2022\u2022\u2022\u2022'], input[type='password']", "")
    _try_intent(page, ["button:has-text('Secure Session Initiation')"], action="click")
    expect(page.locator("body")).to_contain_text("required") or expect(page.locator("body")).to_contain_text("Please enter")
    # WARNING: 4 step(s) could not be automated:
    # - Step 2: Click the 'Provision New Tenant' button.
    # - Step 3: Fill the required field (e.g., Tenant Name) with an empty string or leav
    # - Step 4: Attempt to submit the form/provision the tenant.
    # - Step 5: Assert that a validation error message appears next to the missing field