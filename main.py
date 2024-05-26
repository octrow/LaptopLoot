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
            context = await browser.new_context(
                locale=args.lang,
                timezone_id=args.timezone,
                geolocation=args.location,
                permissions=["geolocation"])
            page = await setup_page(browser)

            # await context.clear_cookies() # Clear cookies before
            laptops_data = await scrape_ebay_listings(page, search_query, args)
            # await context.clear_cookies() # Clear cookies after
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
    parser.add_argument('--new-table', action='store_true', default=False,
                        help='Create a new Google Sheet and store its ID for future runs')
    parser.add_argument('--lang', choices=['en-EN', 'ru-RU', 'de-DE'], default='en-EN', help='Language of the search results (default: en-EN)')
    parser.add_argument('--country', type=str, default='United States', help='Country for location (default: United States)')
    parser.add_argument('--timezone', type=str, default='US/Eastern', help='Timezone for location (default: US/Eastern)')
    parser.add_argument('--location', default={"longitude": 39.665810, "latitude": -75.598831}, help='Location for location (default: USA)')
    # Category (default: PC Laptops & Netbooks)
    parser.add_argument('--category', type=str, default='PC Laptops & Netbooks',
                        help='eBay category to search within (default: PC Laptops & Netbooks)')
    # Filters
    parser.add_argument('--ram', nargs='+', type=int, choices=[4, 8, 12, 16, 20, 24, 32, 64, 128],
                        default=[4, 8, 12, 16, 20, 24, 32, 64, 128], help='RAM filter options (default: all)')
    parser.add_argument('--screen_size', nargs='+', type=str,
                        default=['13-13.9 in', '14-14.9 in', '15-15.9 in', '16-16.9 in'],
                        help='Screen size filter options (default: all common sizes)')
    parser.add_argument('--cpu', nargs='+', type=str,
                        default=['Intel Core i9 13th Gen.', 'Intel Core i9 12th Gen.', 'Intel Core i9 11th Gen',
                                 'Intel Core i9 10th Gen.', "Intel Core i7 13th Gen.", "Intel Core i7 12th Gen.",
                                 "Intel Core i7 11th Gen.", "Intel Core i5 12th Gen.", "Intel Core i5 13th Gen.",
                                 "Intel Core i5 11th Gen.", "Intel Core i3 13th Gen.", "Intel Core i3 12th Gen.",
                                 "AMD Ryzen 9 7000 Series", "AMD Ryzen 9 5000 Series",'AMD Ryzen 5', 'AMD Ryzen 7',
                                 'AMD Ryzen 9'],
                        help='CPU filter options (default: common Intel and AMD processors)')
    parser.add_argument('--condition', nargs='+', type=str,
                        default=['New', 'Open box', "Certified - Refurbished", "Excellent - Refurbished",
                                 "Very Good - Refurbished", "Good - Refurbished",'Used'],
                        help='Condition filter options (default: common conditions)')
    # Price Order (default: Price + Shipping: lowest first)
    parser.add_argument('--price_order', type=str, default='Price + Shipping: lowest first',
                        choices=['Price + Shipping: lowest first', 'Price + Shipping: highest first',
                                 'Price: lowest first', 'Price: highest first', 'Ending soonest', 'Newly listed'],
                        help='Sorting order for price (default: Price + Shipping: lowest first)')
    args = parser.parse_args()
    asyncio.run(main(args))

