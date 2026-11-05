"""Findings #1, #2, #12 of docs/plans/2026-11-05-logic-map-fixes.md, with a fake page (no browser, no network)."""

import asyncio
from types import SimpleNamespace

import pytest

from modules import web_scraping
from modules.data_extraction import extract_prices, price_patterns


class FakeLocator:
    """Like a Playwright Locator: methods are coroutines, the object itself is not awaitable."""

    def __init__(self, page, key, visible=True):
        self.page, self.key, self.visible = page, key, visible

    async def click(self):
        self.page.calls.append(("click", self.key))

    async def check(self):
        self.page.calls.append(("check", self.key))

    async def fill(self, text):
        self.page.calls.append(("fill", self.key, text))

    async def press(self, key):
        self.page.calls.append(("press", self.key, key))

    async def is_visible(self):
        return self.visible


class FakePage:
    def __init__(self, hidden_labels=()):
        self.calls = []
        self.hidden_labels = set(hidden_labels)

    def get_by_role(self, role, name=None, exact=False):
        return FakeLocator(self, (role, name))

    def get_by_label(self, label, exact=False):
        return FakeLocator(self, ("label", label), visible=label not in self.hidden_labels)

    def locator(self, selector):
        return FakeLocator(self, ("css", selector))

    async def goto(self, url):
        self.calls.append(("goto", url))

    async def wait_for_load_state(self, *args, **kwargs):
        pass


class FakeExpect:
    async def to_be_visible(self):
        pass


@pytest.fixture
def no_browser_steps(monkeypatch):
    async def noop(*args, **kwargs):
        pass

    monkeypatch.setattr(web_scraping, "expect", lambda locator: FakeExpect())
    for step in ("change_language", "change_location", "choose_category"):
        monkeypatch.setattr(web_scraping, step, noop)


ARGS = SimpleNamespace(lang="en-US", country="United States", category="PC Laptops", ram=["16"],
                       screen_size=[], cpu=[], condition=[])


def test_apply_filter_clicks_the_tab_and_skips_values_without_a_label(no_browser_steps):
    page = FakePage(hidden_labels={"32 GB"})

    asyncio.run(web_scraping.apply_filter(page, "RAM Size", ["16", "32"], " GB"))

    assert ("click", ("tab", "RAM Size")) in page.calls
    checked = [call[1] for call in page.calls if call[0] == "check"]
    assert checked == [("label", "16 GB")]


def test_search_ebay_clicks_apply_and_types_the_query(no_browser_steps):
    page = FakePage()

    asyncio.run(web_scraping.search_ebay(page, "thinkpad x1", ARGS))

    assert ("click", ("label", "Apply")) in page.calls
    assert ("fill", ("css", web_scraping.CSS_SELECTOR_SEARCH_INPUT), "thinkpad x1") in page.calls
    assert ("press", ("css", web_scraping.CSS_SELECTOR_SEARCH_INPUT), "Enter") in page.calls


def test_search_ebay_types_the_query_before_the_filters(no_browser_steps):
    page = FakePage()

    asyncio.run(web_scraping.search_ebay(page, "thinkpad x1", ARGS))

    press = page.calls.index(("press", ("css", web_scraping.CSS_SELECTOR_SEARCH_INPUT), "Enter"))
    all_filters = page.calls.index(("click", ("label", "All Filters")))
    assert press < all_filters


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("$337.99", "$337.99"),
        ("$1,299.99", "$1,299.99"),
        ("$12,500", "$12,500"),
        ("$1,131.59 to $1,345.59", "$1,131.59, $1,345.59"),
        ("125 000 тенге", "125 000 тенге"),
        ("no price", "N/A"),
    ],
)
def test_extract_prices_keeps_thousands_separators(text, expected):
    assert asyncio.run(extract_prices([text], price_patterns)) == [expected]
