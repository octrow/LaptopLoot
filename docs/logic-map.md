# Logic map

How one eBay search query becomes rows in a Google Sheet.
The map describes the code as it is today, step by step.
Each step says what it decides, where the flow branches, and which module does it.

There is no glossary file; `README.md` is the user-facing description and is not trusted by this map.
Known gaps and fixes in progress are in `docs/plans/2026-11-05-logic-map-fixes.md`.

Rule: if you change a step or a branch, update this file in the same commit.
`tests/test_logic_map.py` checks that every `Module:` line points to a real module (paths start at the repo root).

## The flow at a glance

```
CLI args + env + settings.json
  │
  ├─ 1  Entry ............... which query, which sheet, which filters
  ├─ 2  Browser ............. launch Chromium, context, page
  ├─ 3  Language ............ switch eBay UI to English
  ├─ 4  Location ............ pick "Ship to" country
  ├─ 5  Category ............ walk the category menu
  ├─ 7  Query ............... typed into the eBay search box (runs before step 6)
  ├─ 6  Filters ............. RAM, screen, CPU, condition in "All Filters"
  ├─ 8  Pagination .......... scrape page, click next, until stop
  ├─ 9  Listing fields ...... CSS selectors per field
  ├─ 10 NLP fallback ........ only when a selector call raises
  └─ 11 Save ................ append rows to a worksheet
  │
Google Sheet rows (and a DataFrame that is only logged)
```

`modules/natural_language_processor` cleaning functions (`clean_laptop_data`) are never called by the flow. See Side flows.

## Where the flow splits by kind

Splits are decided in a few independent places: CLI flags, hard-coded field names in `handle_special_cases`, hard-coded Russian/English button labels.

| Kind / variant | Switched on by | Steps it changes | What changes |
|---|---|---|---|
| Field `url` | element_name == "url" | 9 | reads `href` of the first element |
| Field `price` | element_name == "price" | 9 | regex list `price_patterns` (dollars with optional thousands commas, then tenge), first pattern that matches, one result per visible element |
| Field `shipping cost` | element_name == "shipping cost" | 9 | regex list `shipping_patterns`: "Free" / "Local" / number / "No shipping info" |
| Other fields | default | 9 | list of stripped texts |
| Russian UI | button "Выбран язык: Русский" visible | 3 | the only case where the language is changed |
| New sheet | `--new-table` | 11 | spreadsheet id None → create |

Examples:
- `--lang ru-RU` → step 3 still clicks "English" when the Russian button is visible; the flag never selects Russian.
- Listing with no `.s-item__time-left` → field is the string "N/A", not a list.
- Price "$1,299.99" → "$1,299.99".
- Price "$131.59 to $345.59" → "$131.59, $345.59": pattern 1 finds both ends; there is no separate range pattern.

Module: `modules/data_extraction`, `modules/web_scraping`

## Entry points

One entry point: `python main.py [flags]`. No API, GUI or worker.

| Flag / input | Default | Read by | Notes |
|---|---|---|---|
| `SEARCH_QUERY` env, else `input()` | none | step 7 | prompt blocks when unset; empty → no search, category only |
| `SPREADSHEET_ID` | `settings.json` wins over env | step 11 | `settings.get(key, env)`: env used only when the key is absent from settings.json |
| `SHEET_NAME` | `settings.json`, else env, else "eBay Laptops" | step 11 | same `settings.get(key, env)` precedence (`main.py:28`) |
| `--pages` | None = all | step 8 | |
| `--new-table` | False | step 11 | creates "Laptop Loot Data", writes its id to `settings.json` |
| `--lang` | en-EN (choices en-EN, ru-RU, de-DE) | steps 2, 3 | |
| `--country` | United States | step 4 | |
| `--timezone`, `--location` | US/Eastern, dict lon 39.66 / lat -75.60 | step 2 | passed to a context that is not used; `--location` from the CLI is a plain string (no `type=`) |
| `--category` | PC Laptops & Netbooks | step 5 | read, not used |
| `--ram`, `--screen_size`, `--cpu`, `--condition` | all listed values | step 6 | |
| `--price_order` | Price + Shipping: lowest first | none | no code reads it |
| `SERVICE_ACCOUNT_FILE` env | none, required | import of `modules/google_sheets` | missing → ValueError at import, before any scraping |

Side effects at import, before any flag is used:
- `load_settings` creates an empty `settings.json` in the current directory when it is missing (`modules/google_sheets` import, then again in `main`);
- spaCy `en_core_web_sm` is loaded twice: by `NaturalLanguageProcessor()` in `modules/data_extraction` and at module level in `modules/natural_language_processor`;
- `clean_laptop_data([])` runs once (see Side flows).

Module: `main`, `modules/google_sheets`

## Steps

### 1. Entry

Decides: query, sheet target, filter lists.
In: argv, env, `settings.json`. Out: `args`, `search_query`.
Branches:
- `SEARCH_QUERY` unset → `input()` (runs before the `try`; EOF on a non-interactive stdin ends the run with a traceback).
Fails: any exception in steps 2-11 is caught in `main`, logged with traceback, process exits 1.
Notes: `browser.close()` runs twice (inside the `async with` and in `finally`, after Playwright stopped); the second call does not raise.
Module: `main`

### 2. Browser

Decides: how the page is created.
Out: `page`.
Branches:
- headless parameter is named `without_browser` and defaults to False, passed as `headless=` → the browser is visible.
Notes: a context is created with `args.lang`, `args.timezone`, `args.location`, but the page comes from `browser.new_page()`, a different default context. Lang, timezone and geolocation are never applied.
Fails: exception → caught in `main`.
Module: `main`

### 3. Language

Decides: whether to switch eBay to English.
In: `page`, `args.lang`. 
Branches:
- `document.documentElement.lang == args.lang` → nothing. The flag choices ("en-EN", "ru-RU", "de-DE") are not the usual page lang values ("en", "en-US"; not confirmed for eBay), so in practice the next check always runs;
- button "Выбран язык: Русский" not visible → nothing;
- visible → click it, click "English", wait networkidle; loops while the button stays visible;
- PlaywrightTimeoutError → falls back to `#gh-eb-Geo` selectors.
Fails: loop has no attempt limit. A failure inside the fallback (dropdown wait is 1000 ms) is not caught here → run ends in `main` (#13).
Module: `modules/web_scraping`

### 4. Location

Decides: "Ship to" country.
Branches:
- clicks "Ship to", "Ship to:", text of `args.country`, "Done";
- PlaywrightTimeoutError → warning, continues with the old location.
Fails: silent continue on timeout only. Other Playwright errors (e.g. strict-mode violation when a name or `get_by_text(country)` matches several elements) end the run (#13).
Module: `modules/web_scraping`

### 5. Category

Decides: category page.
Branches:
- always clicks Computers & tablets → Laptops & Netbooks → PC Laptops & Netbooks; `args.category` is only logged on timeout.
Fails: a click timeout (30 s) → warning, continues on the current page. A menu link that is not visible fails `expect(...).to_be_visible()` after 5 s with AssertionError, which is not caught → run ends (#13).
Module: `modules/web_scraping`

### 6. Filters

Decides: which filter checkboxes are ticked.
Out: filtered result list.
Branches:
- opens "All Filters", calls `apply_filter` for RAM Size (suffix " GB"), Screen Size, Processor, Condition, then clicks the "Apply" label;
- an empty list skips that filter;
- runs on the search results of step 7 (step 7 comes first);
- per filter: click its tab; per value: `get_by_label(value+suffix)`, `check()` only when that label is visible.
Branches inside a filter:
- value has no visible label → skipped, the other values of that filter still run.
Fails: a click or `check()` timeout (30 s) → PlaywrightTimeoutError → warning; the remaining values of that filter are skipped.
Also: the "All Filters" and "Apply" clicks have no handler; `expect(...)` failures raise AssertionError; both end the run (#13).
Module: `modules/web_scraping`

### 7. Query

Runs after step 5 and before step 6, inside `search_ebay`.
Decides: what is searched within the category page.
Branches:
- query non-empty → fill `#gh-ac` (eBay search box), press Enter, wait networkidle;
- query empty → no search, the category page is filtered as is.
Notes: not confirmed live that eBay keeps the category from step 5 on this search; if it does not, the search runs in all categories.
Fails: a missing search box → PlaywrightTimeoutError, not caught here → run ends in `main`.
Module: `modules/web_scraping`

### 8. Pagination

Decides: when to stop.
Branches:
- `args.pages` set and `page_num > pages` → stop; checked before scraping, so `--pages 0` scrapes nothing;
- no visible `a.pagination__next` → stop;
- click, wait networkidle with 2000 ms timeout, sleep 2-5 s; timeout → returns False and stops; the page already moved on, so the clicked page is not scraped.
Out: all rows concatenated into one list.
Notes: uses `print` for progress, not the logger.
Module: `modules/web_scraping`

### 9. Listing fields

Decides: the row of one `li.s-item`.
Out: dict with Name, Price, Shipping Cost, Condition, URL, Time Left, Seller Name.
Branches:
- no element for a selector → "N/A" (string);
- else visible elements only → special-case by field name (see split table);
- `Seller Name` selector is `.s-item__selller` (three l), always no match → "N/A".
Notes: values are lists of strings, not scalars. Price may be a list of "$337.99" / "$1,299.99" strings.
Notes: every `li.s-item` becomes a row; there is no filter for placeholder items (#14).
Module: `modules/data_extraction`, `modules/web_scraping`

### 10. NLP fallback

Decides: what to do when a selector call raises.
Branches:
- exception in step 9 → `extract_data_nlp`: intended to clean HTML to text, spaCy-tag it, look for an entity labelled with the field name, return its tag source.
Notes: the first call, `listing.content()`, does not exist on a Locator → AttributeError. Past it, `clean_html` returns a str, `extract_relevant_text` calls `.get_text()` on that str, and `find_element` reads `.ents` on a list. The AttributeError is not caught here and stops the whole run in `main`.
Fails: stops the run.
Module: `modules/data_extraction`, `modules/natural_language_processor`

### 11. Save

Decides: which spreadsheet and worksheet receive the rows.
In: list of dict rows. Out: appended rows; return value unused.
Branches:
- `--new-table` → id None → create "Laptop Loot Data", grant "anyone with the link: writer", write id to `settings.json`;
- else open by id (from settings.json, env, or None → creates a new sheet too, same branch);
- worksheet missing → created with 100 rows, 20 cols;
- `resize_worksheet` compares `len(data)` and `len(data[0])` with the filled rows (`get_all_values`) and filled cells of row 1, not the grid size, and adds the difference; its errors are logged and skipped;
- lists are joined with ", ", then `append_rows(RAW)`.
Notes: no header row is written; rows are appended on every run, with no dedup. Empty `data` → warning and return, Sheets is not contacted.
Fails: any exception is logged and re-raised; `main` turns it into exit 1.
Module: `modules/google_sheets`

### Output

Google Sheet rows. Also a pandas DataFrame logged with `logger.info(f"Dataframe:\n{df}")`.
Module: `main`

## Side flows

### Data cleaning (not wired)

`clean_laptop_data` and its helpers (price to float, shipping to 0.0, spaCy name filter) are defined and executed at import on an empty list. Nothing in the flow calls them. They expect scalars, the scraper produces lists.
Module: `modules/natural_language_processor`

### settings.json

Holds `SPREADSHEET_ID`. Created empty at import when missing; the id is written by the create branch of step 11 (`--new-table`, or no id anywhere). Committed file contains an id.
Module: `modules/google_sheets`

## Known gaps

Details in the plan.
- Only Playwright timeouts are handled in steps 3-6; AssertionError from `expect` and other errors end the run (#13).
- Placeholder `li.s-item` items may become junk rows (#14, not confirmed).
- Context settings (lang, timezone, location) never reach the page (#3).
- Category, price order, language flags are ignored or only partly honoured (#4).
- NLP fallback raises and aborts the run (#5).
- Pagination stops on a 2 s networkidle timeout (#6).
- Sheet gets no header, duplicates on every run, new sheet is world-writable (#7).
- ✅ #8 fixed: failure exits 1 (still no retry).
