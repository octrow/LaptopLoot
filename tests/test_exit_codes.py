"""Finding #8: a failed run must exit non-zero; empty data must not touch Sheets."""

import asyncio
import os
from types import SimpleNamespace

os.environ.setdefault("SERVICE_ACCOUNT_FILE", "dummy.json")  # import-time check only; no Sheets call is made

import main as main_mod  # noqa: E402
from modules import google_sheets  # noqa: E402


class _FakePW:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def _run_main(monkeypatch):
    monkeypatch.setenv("SEARCH_QUERY", "thinkpad")

    async def boom(*a, **k):
        raise RuntimeError("blocked")

    async def fake_browser(p):
        raise RuntimeError("no browser")

    monkeypatch.setattr(main_mod, "async_playwright", lambda: _FakePW())
    monkeypatch.setattr(main_mod, "setup_browser", fake_browser)
    return asyncio.run(main_mod.main(SimpleNamespace(new_table=False)))


def test_main_returns_nonzero_on_failure(monkeypatch):
    assert _run_main(monkeypatch) == 1


def test_save_reraises_sheets_errors(monkeypatch):
    class BadManager:
        def __init__(self, *a, **k):
            pass

        async def authorize(self):
            raise RuntimeError("quota")

    monkeypatch.setattr(google_sheets.gspread_asyncio, "AsyncioGspreadClientManager", BadManager)
    try:
        asyncio.run(google_sheets.save_to_google_sheet("id", "s", [{"a": 1}]))
    except RuntimeError:
        return
    raise AssertionError("error was swallowed")


def test_save_skips_empty_data(monkeypatch):
    def fail(*a, **k):
        raise AssertionError("Sheets must not be contacted")

    monkeypatch.setattr(google_sheets.gspread_asyncio, "AsyncioGspreadClientManager", fail)
    asyncio.run(google_sheets.save_to_google_sheet("id", "s", []))
