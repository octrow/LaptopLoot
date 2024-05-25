import argparse
import os
import asyncio
import traceback

from modules.google_sheets import SERVICE_ACCOUNT_FILE, save_to_google_sheet
from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import async_playwright

import pandas as pd

from modules.web_scraping import scrape_ebay_listings

# --- Load Environment Variables ---
load_dotenv()

# --- Google Sheets Configuration ---
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME") or "eBay Laptops"

# --- Main Function ---
async def main(args):
    search_query = os.getenv("SEARCH_QUERY") or input("Enter your eBay search query: ")
    try:
        logger.info(f"Search query: {search_query}")
        async with async_playwright() as p:
            browser = await setup_browser(p)
            page = await setup_page(browser)
            laptops_data = await scrape_ebay_listings(page, search_query, args)
            df = pd.DataFrame(laptops_data)
            logger.info("Dataframe:\n", df)
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
    args = parser.parse_args()
    asyncio.run(main(args))

