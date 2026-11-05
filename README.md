# LaptopLoot

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Scrapes eBay laptop listings into a Google Sheet.

This is a small learning project. It is not finished and has bugs.

## Known issues

- All rows stay in memory and go to the sheet in one append at the end. A crash, a Sheets error or an eBay block midway loses the whole run, and the exit code is still 0.

Details: [docs/logic-map.md](docs/logic-map.md) and [docs/plans/2026-11-05-logic-map-fixes.md](docs/plans/2026-11-05-logic-map-fixes.md).

## What it does

- Opens eBay with `Playwright` and walks through the result pages.
- Reads name, price, shipping, condition, URL and time left.
- Waits a random time between pages.
- Appends the rows to a Google Sheet with `gspread`.

The old feature list is in [docs/readme-details.md](docs/readme-details.md).

## Requirements

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- A Google Cloud project with the Google Sheets API enabled
- A service account with access to Google Sheets, and its JSON key file

## Setup

```bash
git clone https://github.com/octrow/LaptopLoot.git
cd LaptopLoot
uv sync
uv run playwright install chromium
```

`uv sync` also installs the spaCy `en_core_web_sm` model.

Create a `.env` file in the project root:

```
SEARCH_QUERY="your eBay search query"
SPREADSHEET_ID="your_spreadsheet_id"
SHEET_NAME="your_sheet_name"
SERVICE_ACCOUNT_FILE="path/to/your_service_account_credentials.json"
```

- `SPREADSHEET_ID`: the ID of your Google Spreadsheet.
- `SHEET_NAME`: the sheet to write to. Default: `eBay Laptops`.
- `SERVICE_ACCOUNT_FILE`: path to the service account JSON file.
- `SEARCH_QUERY`: optional. If not set, the script asks for it.

## Run

```bash
uv run main.py
```

Then open your Google Sheet. Run `uv run main.py --help` for the filter options (RAM, CPU, condition, pages).

## How it works

1. `main.py` reads the `.env` file and the command-line options.
2. `modules/web_scraping.py` opens eBay, applies filters and goes page by page.
3. `modules/data_extraction.py` reads each listing with CSS selectors. A text-based fallback uses spaCy and NLTK.
4. `main.py` puts the rows in a Pandas DataFrame and saves them with `modules/google_sheets.py`.

The full step list, function notes and tips are in [docs/readme-details.md](docs/readme-details.md).

## Limits

- eBay changes its pages. If the selectors stop matching, the scraper breaks.
- Many requests can get your IP blocked. The random delays help a little.

## Disclaimer

This project is for learning and personal use only.
Follow eBay's terms of service and `robots.txt`, and do not scrape heavily.

## License

MIT. See [LICENSE](LICENSE).
