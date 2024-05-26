import argparse
import json
import os
import asyncio
import traceback

from modules.google_sheets import save_to_google_sheet, load_settings
from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import async_playwright

import pandas as pd

from modules.web_scraping import scrape_ebay_listings

# --- Load Environment Variables ---
load_dotenv()

# --- Load settings from file ---
settings = load_settings()



# --- Main Function ---
async def main(args):
    # --- Google Sheets Configuration ---
    SPREADSHEET_ID = settings.get('SPREADSHEET_ID', os.getenv("SPREADSHEET_ID")) or None
    SHEET_NAME = settings.get('SHEET_NAME', os.getenv("SHEET_NAME")) or "eBay Laptops"
    search_query = os.getenv("SEARCH_QUERY") or input("Enter your eBay search query: ")
    try:
        logger.info(f"Search query: {search_query}")
        async with async_playwright() as p:
            browser = await setup_browser(p)
            context = await browser.new_context(locale=args.lang, timezone_id=args.timezone, geolocation=args.location, permissions=["geolocation"])
            page = await setup_page(browser)
            laptops_data = await scrape_ebay_listings(page, search_query, args)
            df = pd.DataFrame(laptops_data)
            logger.info("Dataframe:\n", df)

            # --- Google Sheets Integration (with new table handling) ---
            if args.new_table:
                await save_to_google_sheet(None, SHEET_NAME, laptops_data)
            else:
                await save_to_google_sheet(SPREADSHEET_ID, SHEET_NAME, laptops_data)
            await browser.close()
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
    finally:
        if 'browser' in locals():
            await browser.close()

async def setup_browser(p, without_browser=False):
    logger.info("Launching browser...")
    return await p.chromium.launch(headless=without_browser)

async def setup_page(browser):
    logger.info("Launching new page...")
    return await browser.new_page()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Web scraping parameters.')
    parser.add_argument('--pages', type=int, default=None, help='Number of pages to parse (default: all)')
    parser.add_argument('--type', choices=['pc', 'mac'], default='pc', help='Type of computer (default: pc)')
    parser.add_argument('--ram', nargs='+', type=int, choices=[16, 20, 24, 32, 64, 256],
                        default=[16, 20, 24, 32, 64, 256], help='RAM filter options (default: all)')
    parser.add_argument('--cpu', action='store_true', default=False, help='Turn on CPU filter (default: off)')
    parser.add_argument('--new-table', action='store_true', default=False,
                        help='Create a new Google Sheet and store its ID for future runs')
    parser.add_argument('--lang', choices=['en-EN', 'ru-RU', 'de-DE'], default='en-EN', help='Language of the search results (default: en-EN)')
    parser.add_argument('--zip_code', type=str, default='19706', help='Zip code for location (default: USA)')
    parser.add_argument('--timezone', type=str, default='US/Eastern', help='Timezone for location (default: US/Eastern)')
    parser.add_argument('--location', default={"longitude": 39.665810, "latitude": -75.598831}, help='Location for location (default: USA)')
    args = parser.parse_args()
    asyncio.run(main(args))

