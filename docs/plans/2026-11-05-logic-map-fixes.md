# Plan: logic map findings

Findings from writing `docs/logic-map.md` on 2026-11-05. Independent review done the same day: #2, #3, #5, #7 corrected, #12-#14 added.
The map describes the code as it is; this file says what is wrong with it and what we propose. New findings are appended.
A fixed finding gets ✅ and the map is updated in the same commit.

Severity: HIGH: wrong result for the user. MEDIUM: worse result than it could be. LOW: noise, debt, docs.
"Question": not sure if bug or intent; owner decides. "Not confirmed": needs a live run.

## Findings

| # | Map step | What is wrong | We propose | Severity |
|---|---|---|---|---|
| ✅ 1 | 7 | `search_query` is only logged, never entered (`modules/web_scraping.py:142`, `main.py:29`). Every query scrapes the same category. | Type the query into the eBay search box, or drop the prompt. | HIGH |
| ✅ 2 | 6 | `apply_button = await page.get_by_label("Apply")` (`web_scraping.py:138`) raises `TypeError: object Locator can't be used in 'await' expression` on every run (reproduced with Playwright 1.64): the run ends before step 7, nothing is saved, exit 0. Also: tab `.click()` not awaited (`:101`), so the tab is never clicked; `filter_locator.is_visible()` not awaited (`:108`), so `check()` runs on every value and the first value without a label costs 30 s and drops the rest of that filter (`:109`, `:112`). | Drop the await on the Locator; await the click and `is_visible()`. | HIGH. Fixed: query typed into `#gh-ac` + Enter after step 5, before the filters (`web_scraping.py:127-133`); not confirmed live that eBay keeps the category on that search. |
| 3 | 2 | Context with lang/timezone/geolocation is created, page comes from `browser.new_page()` (`main.py:34-39`). `--location` lon/lat are swapped (`main.py:76`); `--location` has no `type=`, so a CLI value is a string. | `context.new_page()`; fix the dict; parse `--location`. | MEDIUM |
| 4 | 3, 5, Entry points | `--category` unused (`web_scraping.py:81`, path hard-coded); `--price_order` read nowhere; `--lang` never equals eBay's "en-US" and only Russian to English is handled (`:38-40`); the language loop has no limit. | Wire or remove the flags; cap the loop. | MEDIUM |
| 5 | 10 | `extract_data_nlp` first calls `listing.content()`, which a Locator does not have (`data_extraction.py:36`); past that it calls `.get_text()` on a str and `.ents` on a list (`natural_language_processor.py:44,33`, `data_extraction.py:37-40`). AttributeError aborts the run. | Remove the fallback or fix its types and catch errors. | MEDIUM |
| 6 | 8 | `wait_for_load_state('networkidle', timeout=2000)` timeout ends pagination early (`web_scraping.py:150`). | Longer timeout, or wait for the listing selector. | MEDIUM |
| 7 | 11 | No header row; every run appends duplicates (`google_sheets.py:107`); `--new-table` grants anyone-writer (`:77`); `data[0]` fails on empty data (`:91`). | Header on create, upsert by URL, restrict permission. | MEDIUM |
| 8 | 1, 11 | All exceptions are logged and the process exits 0 (`main.py:53`, `google_sheets.py:110`). | Re-raise or set a non-zero exit. | MEDIUM |
| 9 | 9 | Selector typo `.s-item__selller` (`web_scraping.py:174`); fields are lists, cleaning module (`natural_language_processor.py:57`) unused. | Fix typo; decide on scalar shape and wire cleaning or delete it. | LOW |
| 10 | 2 | Headed browser by default: `without_browser=False` goes to `headless=` (`main.py:60-62`). Question: intended? | Decide. | LOW |
| 11 | Output | `logger.info("Dataframe:\n", df)` prints no frame (`main.py:45`). | Add `{}`. | LOW |
| ✅ 12 | 9 | Price pattern 1 `\$\d+(?:\.\d{2})?` has no thousands separator (`data_extraction.py:12`): "$1,299.99" → "$1". Pattern 1 also matches ranges first, so pattern 2 (`:13`) is dead. | Allow commas (`\$[\d,]+(?:\.\d{2})?`); order range pattern first or drop it. | HIGH. Fixed: pattern 1 is `\$\d[\d,]*(?:\.\d{2})?`; the dead range pattern is dropped (a range still gives "$low, $high" from pattern 1). |
| 13 | 3-6 | Steps 3-6 catch only `PlaywrightTimeoutError`. `expect(...).to_be_visible()` raises AssertionError (`web_scraping.py:84,86,88,102,110`), strict-mode violations raise `Error` (e.g. `get_by_text(country)`, `:72`), the step-3 fallback (`:49-55`) and "All Filters" click (`:128`) have no handler: each ends the whole run. | Decide per step: catch `playwright Error` and `AssertionError` where "warn and continue" is meant, or fail loudly. | MEDIUM |
| 14 | 9 | Every `li.s-item` becomes a row (`web_scraping.py:164-176`). Not confirmed: eBay result pages are known to include a hidden placeholder item ("Shop on eBay"), which would add one junk row per page. | Live run; skip items without a real `.s-item__link` or with that title. | MEDIUM |

## Order of work

1. #2, #1, #3, #12: the run must reach the Sheet with the right query and prices (`web_scraping.py`, `data_extraction.py`, `main.py`).
2. #13, #5, #6, #8: failure behaviour.
3. #7, #14, #4, #9-#11.

## Done when

- [ ] every finding has ✅ or a "keep as is" decision with a reason;
- [ ] Known gaps in the map lists every open HIGH and MEDIUM finding.
