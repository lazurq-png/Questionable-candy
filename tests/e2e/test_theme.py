"""The light and dark themes, and the parts of "professional" a test can measure.

Themes: with no stored choice the system setting decides (CSS alone); the
toggle stores an override that wins until toggled again. Playwright's colour-
scheme emulation stands in for the operating system.

Measured on every page, in both themes (night-run §9.4): no horizontal overflow
at phone width, controls at least 44x44, body text at 4.5:1 against the colour
actually painted behind it. None of this says the pages look good -- that still
needs a person (docs/ai/night-2026-09-16/progress.md, T5).
"""
from decimal import Decimal

import pytest
from playwright.sync_api import expect

from tests.factories.candy_factory import CandyFactory

LIGHT_BG = "rgb(250, 248, 251)"  # site.css --bg, light
DARK_BG = "rgb(20, 17, 24)"  # site.css --bg, dark
PHONE = {"width": 375, "height": 812}

# Every element that holds text directly, and the colour it is painted on.
# The background is found by compositing each ancestor's background colour
# until an opaque one is reached; an element with no opaque ancestor at all is
# reported, because a ratio against "transparent" would pass meaninglessly --
# the trap night-run §9.4 records.
CONTRAST_FAILURES = """
() => {
  const parse = (value) => {
    const m = value.match(/rgba?\\(([^)]+)\\)/);
    if (!m) return null;
    const p = m[1].split(/[\\s,\\/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const over = (top, bottom) => ({
    r: top.r * top.a + bottom.r * (1 - top.a),
    g: top.g * top.a + bottom.g * (1 - top.a),
    b: top.b * top.a + bottom.b * (1 - top.a),
    a: 1,
  });
  const painted = (element) => {
    const layers = [];
    for (let node = element; node; node = node.parentElement) {
      const colour = parse(getComputedStyle(node).backgroundColor);
      if (colour && colour.a > 0) {
        layers.push(colour);
        if (colour.a === 1) break;
      }
    }
    if (!layers.length || layers[layers.length - 1].a !== 1) return null;
    return layers.reduceRight((below, layer) => over(layer, below));
  };
  const luminance = ({ r, g, b }) => {
    const [R, G, B] = [r, g, b].map((v) => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * R + 0.7152 * G + 0.0722 * B;
  };
  const failures = [];
  for (const element of document.body.querySelectorAll("*")) {
    const hasText = [...element.childNodes].some(
      (n) => n.nodeType === Node.TEXT_NODE && n.textContent.trim()
    );
    if (!hasText || !element.getClientRects().length) continue;
    const style = getComputedStyle(element);
    if (style.visibility === "hidden" || element.closest(".visually-hidden")) continue;
    const background = painted(element);
    const label = `${element.tagName.toLowerCase()} "${element.textContent.trim().slice(0, 30)}"`;
    if (!background) {
      failures.push(`${label}: no opaque background behind it`);
      continue;
    }
    const text = over(parse(style.color), background);
    const [hi, lo] = [luminance(text), luminance(background)].sort((x, y) => y - x);
    const ratio = (hi + 0.05) / (lo + 0.05);
    if (ratio < 4.5) failures.push(`${label}: ${ratio.toFixed(2)}:1`);
  }
  return failures;
}
"""

# A field wrapped in a <label> is tapped through that label -- anywhere in it
# focuses the field -- so the label is the target to measure. The stepper's
# number box is drawn shorter than 44px inside a label that is not; every other
# input here has its label beside it rather than around it, and is measured as
# itself.
SMALL_TARGETS = """
() => [...document.querySelectorAll("button, input, .site-nav a, main a")]
  .filter((el) => el.getClientRects().length)
  .map((el) => [el, (el.tagName === "INPUT" && el.closest("label") ? el.closest("label") : el).getBoundingClientRect()])
  .filter(([, box]) => box.width < 44 || box.height < 44)
  .map(([el, box]) => `${el.tagName.toLowerCase()} "${(el.textContent || el.name).trim()}": ${Math.round(box.width)}x${Math.round(box.height)}`)
"""

OVERFLOW = "document.documentElement.scrollWidth - document.documentElement.clientWidth"

# Wrapping avoids overflow, so the overflow check alone passed a header whose
# links had broken onto two lines ("Cart (" / "0)"). One row, one line each.
HEADER_WRAPS = """
() => {
  const items = [...document.querySelectorAll(".site-nav > *")].filter((el) => el.getClientRects().length);
  const tops = items.map((el) => Math.round(el.getBoundingClientRect().top));
  const tall = items.filter((el) => el.getBoundingClientRect().height > 46).map((el) => el.textContent.trim());
  return { rows: new Set(tops).size, tall };
}
"""


def background(page):
    """The colour actually painted behind the page."""
    return page.evaluate("getComputedStyle(document.body).backgroundColor")


def check_page(page, name, assert_page_is_fully_rendered):
    """The four measurable properties, for whichever page is showing."""
    assert_page_is_fully_rendered(page)
    assert page.evaluate(OVERFLOW) == 0, f"{name}: scrolls sideways at {PHONE['width']}px"
    assert page.evaluate(HEADER_WRAPS) == {"rows": 1, "tall": []}, f"{name}: header wraps"
    assert page.evaluate(SMALL_TARGETS) == [], f"{name}: tap targets under 44x44"
    assert page.evaluate(CONTRAST_FAILURES) == [], f"{name}: text below 4.5:1"


@pytest.mark.parametrize("case", [
    # (system setting, stored toggle choice, theme expected on screen)
    ("light", None, "light"),
    ("dark", None, "dark"),
    # The dark and light values are written twice in site.css -- under the
    # media query and under [data-theme] -- so both copies are measured.
    ("light", "dark", "dark"),
    ("dark", "light", "light"),
], ids=lambda case: f"system-{case[0]}-stored-{case[1]}")
def test_every_page_meets_the_measurable_checks_in_both_themes(
    live_server, page, assert_page_is_fully_rendered, case
):
    """Phone width, each theme from the system and from the toggle, every page."""
    system, stored, shown = case
    page.set_viewport_size(PHONE)
    page.emulate_media(color_scheme=system)
    if stored:
        page.add_init_script(f"window.localStorage.setItem('theme', '{stored}')")
    expected = DARK_BG if shown == "dark" else LIGHT_BG

    page.goto(live_server.url)
    expect(page.get_by_test_id("catalog-empty")).to_be_visible()
    assert background(page) == expected
    check_page(page, "empty catalog", assert_page_is_fully_rendered)

    # A one-word name, because a long one wraps and makes its link tall enough
    # to pass the tap-target check by accident.
    CandyFactory(name="Taffy", price=Decimal("1.50"), stock=5)
    marshmallows = CandyFactory(name="Strawberry Cloud Marshmallows", price=Decimal("5.00"), stock=3)
    CandyFactory(name="Chili Mango Chews", price=Decimal("5.25"), stock=0)

    page.goto(f"{live_server.url}/shoppingcart/")
    expect(page.get_by_test_id("shoppingcart-empty")).to_be_visible()
    assert background(page) == expected
    check_page(page, "empty cart", assert_page_is_fully_rendered)

    page.goto(live_server.url)
    expect(page.get_by_test_id("theme-toggle")).to_be_visible()
    check_page(page, "catalog", assert_page_is_fully_rendered)

    # By card, not by position, so the test does not depend on catalog order.
    page.get_by_role("listitem").filter(has_text="Strawberry Cloud Marshmallows").get_by_role(
        "button", name="Add to cart"
    ).click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")
    check_page(page, "catalog after adding", assert_page_is_fully_rendered)

    page.get_by_role("listitem").filter(has_text="Taffy").get_by_role(
        "textbox", name="Number in cart"
    ).fill("2")
    expect(page.get_by_role("button", name="Ok")).to_be_visible()
    check_page(page, "catalog with a number waiting for Ok", assert_page_is_fully_rendered)
    page.reload()

    page.get_by_role("link", name="Strawberry Cloud Marshmallows").click()
    expect(page.get_by_test_id("candy-popup").get_by_test_id("candy-flaw")).to_be_visible()
    check_page(page, "detail popup", assert_page_is_fully_rendered)
    page.keyboard.press("Escape")

    page.goto(f"{live_server.url}/candy/{marshmallows.pk}/")
    check_page(page, "detail page", assert_page_is_fully_rendered)

    page.get_by_test_id("shoppingcart-link").click()
    expect(page.get_by_test_id("cart-panel-line")).to_have_count(1)
    check_page(page, "cart dropdown", assert_page_is_fully_rendered)

    page.get_by_test_id("checkout-button").click()
    page.wait_for_url("**/checkout/")
    expect(page.get_by_test_id("checkout-line")).to_have_count(1)
    check_page(page, "checkout", assert_page_is_fully_rendered)

    page.goto(f"{live_server.url}/shoppingcart/")
    page.get_by_label("Quantity of Strawberry Cloud Marshmallows", exact=True).fill("9")
    page.get_by_role("button", name="Update quantity of Strawberry Cloud Marshmallows").click()
    expect(page.get_by_test_id("shoppingcart-messages")).to_contain_text("Only 3")
    check_page(page, "cart with a notice", assert_page_is_fully_rendered)

    page.goto(f"{live_server.url}/candy/999999/")
    expect(page.get_by_test_id("candy-unavailable")).to_be_visible()
    check_page(page, "no longer available", assert_page_is_fully_rendered)


@pytest.mark.parametrize(("scheme", "expected", "pressed"), [
    ("dark", DARK_BG, "true"),
    ("light", LIGHT_BG, "false"),
])
def test_with_no_stored_choice_the_system_setting_decides(
    live_server, page, scheme, expected, pressed
):
    """No attribute is set, so the stylesheet's media query is what decides."""
    page.emulate_media(color_scheme=scheme)
    page.goto(live_server.url)

    toggle = page.get_by_test_id("theme-toggle")
    expect(toggle).to_be_visible()
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") is None
    assert background(page) == expected
    expect(toggle).to_have_attribute("aria-pressed", pressed)


def test_an_operating_system_switch_applies_live_without_a_stored_choice(live_server, page):
    """No reload: the media query flips the colours, the button's state follows."""
    page.emulate_media(color_scheme="light")
    page.goto(live_server.url)
    toggle = page.get_by_test_id("theme-toggle")
    expect(toggle).to_have_attribute("aria-pressed", "false")

    page.emulate_media(color_scheme="dark")

    expect(page.locator("body")).to_have_css("background-color", DARK_BG)
    expect(toggle).to_have_attribute("aria-pressed", "true")


def test_the_toggle_overrides_the_system_and_the_choice_survives_a_reload(live_server, page):
    """Both directions: dark on a light system, then light on a dark one."""
    page.emulate_media(color_scheme="light")
    page.goto(live_server.url)
    toggle = page.get_by_role("button", name="Dark theme")

    toggle.click()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    expect(page.locator("body")).to_have_css("background-color", DARK_BG)
    expect(toggle).to_have_attribute("aria-pressed", "true")

    page.reload()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    assert background(page) == DARK_BG

    page.emulate_media(color_scheme="dark")
    page.get_by_role("button", name="Dark theme").click()
    expect(page.locator("body")).to_have_css("background-color", LIGHT_BG)
    page.reload()
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    assert background(page) == LIGHT_BG  # light, although the system says dark


def test_a_stored_choice_is_applied_by_the_head_script_not_the_toggle(live_server, page):
    """The override must not wait for theme.js, or a dark choice flashes light.

    theme.js is blocked outright here, so only the inline script in <head> can
    have applied the stored theme.
    """
    page.route("**/static/shop/theme.js", lambda route: route.abort())
    page.add_init_script("window.localStorage.setItem('theme', 'dark')")
    page.emulate_media(color_scheme="light")

    page.goto(live_server.url)

    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "dark"
    assert background(page) == DARK_BG
    # And with its script missing, the toggle stays hidden rather than broken.
    expect(page.get_by_test_id("theme-toggle")).to_be_hidden()


def test_the_toggle_icon_is_not_part_of_its_name(live_server, page):
    """The sun/moon glyph is decoration; a screen reader should hear "Dark theme"."""
    page.goto(live_server.url)
    toggle = page.get_by_test_id("theme-toggle")
    expect(toggle).to_be_visible()

    expect(toggle).to_have_accessible_name("Dark theme")


def test_the_contrast_check_refuses_text_with_nothing_painted_behind_it(live_server, page):
    """The §9.4 trap: against "transparent" any ratio would pass meaninglessly.

    Guards the checker itself -- if it is ever loosened to treat transparent as
    white, this fails instead of every page silently passing.
    """
    page.goto(live_server.url)
    page.add_style_tag(content="html, body, .site-header, .empty-state { background: transparent !important; }")

    failures = page.evaluate(CONTRAST_FAILURES)

    assert any("no opaque background" in failure for failure in failures), failures
