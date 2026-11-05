# Plan: LaptopLoot

Entry point for open bugs, plans and ideas (2026-11-05). Rule: a closed item is deleted or marked ✅ with a commit link.

Source for logic findings: [docs/plans/2026-11-05-logic-map-fixes.md](docs/plans/2026-11-05-logic-map-fixes.md) (`#N` below = row number there).

## Bugs

- [ ] MEDIUM: all rows kept in memory and written once at the end; a crash, Sheets error or eBay block loses the whole scrape, exit 0 (`main.py:42-52`, `modules/google_sheets.py:107`) ([system-design.md](docs/system-design.md) Risks, related #8)
- [ ] MEDIUM #3: context (lang/timezone/geo) unused because the page comes from `browser.new_page()`; `--location` lon/lat swapped, no `type=` (`main.py:34-39,76`)
- [ ] MEDIUM #4: `--category`, `--price_order` unused; `--lang` handling broken; language loop has no limit
- [ ] MEDIUM #5: `extract_data_nlp` fallback fails on wrong types and aborts the run (`data_extraction.py:36`)
- [ ] MEDIUM #6: 2 s `networkidle` timeout ends pagination early, silently (`web_scraping.py:150`) (system-design Risks)
- [ ] MEDIUM #7: no header row, duplicates on every run, `--new-table` grants anyone-writer, `data[0]` fails on empty data (`google_sheets.py:77,91,107`) (system-design Risks: no dedup)
- [x] ✅ 2026-11-05 MEDIUM #8: failures now exit 1 (`main` returns 1, Sheets error re-raised; empty data skips Sheets, `data[0]` crash gone), test `tests/test_exit_codes.py`; не закоммичено
- [ ] MEDIUM #13: steps 3-6 catch only `PlaywrightTimeoutError`; AssertionError and strict-mode `Error` end the run (`web_scraping.py:49-128`)
- [ ] MEDIUM #14: placeholder "Shop on eBay" item may become a junk row per page; not confirmed live (`web_scraping.py:164-176`)
- [ ] MEDIUM: no backoff or retry on block/captcha pages, fixed 2-5 s sleeps (`web_scraping.py:155`) (system-design Risks)
- [ ] LOW #9-#11: selector typo `.s-item__selller`, unused cleaning module, headed browser by default (question); ✅ 2026-11-05 #11 `logger.info("Dataframe:\n", df)` prints no frame, fixed (f-string), не закоммичено
- [x] ✅ 2026-11-05 LOW: exit 0 on failure, same root as #8, fixed; не закоммичено

## Plans and features

- [ ] Finish the logic-map fixes in the order given in [Order of work](docs/plans/2026-11-05-logic-map-fixes.md): failure behaviour (#13, #5, #6, #8), then #7, #14, #4, #9-#11
- [ ] Confirm live that eBay keeps the category on the typed search query (fix of #1 is not confirmed live)
- [ ] Done when every finding has ✅ or a "keep as is" decision, and Known gaps in `docs/logic-map.md` lists every open HIGH and MEDIUM finding

## Ideas

- [ ] Next rung: SQLite file as source of truth plus sheet export; trigger: sheet near ~5M cells (~700 full runs) or first scheduled run ([system-design.md](docs/system-design.md) section 8)
- [ ] Item id from the URL as a key, so a re-run skips existing rows ([system-design.md](docs/system-design.md) section 5)
- [ ] Fewer CDP round trips per listing (~20 now); matters only at x10 volume (`data_extraction.py:51-67`)
- [ ] Unattended or scheduled runs need non-zero exit codes, retries, headless, dedup (system-design section 8)

## Detailed plans

- [docs/plans/2026-11-05-logic-map-fixes.md](docs/plans/2026-11-05-logic-map-fixes.md): logic-map findings
- [docs/logic-map.md](docs/logic-map.md): how a search becomes Sheet rows
- [docs/system-design.md](docs/system-design.md): system design review (2026-11-05), summary across repos in `~/dev/docs/system-design-report-2026-11-05.md`
