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





# --- Data Extraction Functions ---

# --- Web Scraping Functions ---


# --- Google Sheets Functions ---


# --- Main Function ---
async def main():
    search_query = os.getenv("SEARCH_QUERY") or input("Enter your eBay search query: ")
    try:
        logger.info(f"Search query: {search_query}")
        async with async_playwright() as p:
            logger.info("Launching browser...")
            browser = await p.chromium.launch(headless=False)
            logger.info("Launching new page...")
            page = await browser.new_page()
            logger.info("Navigating to eBay...")
            laptops_data = await scrape_ebay_listings(page, search_query)
            logger.info("Done scraping. Saving to Google Sheets...")
            df = pd.DataFrame(laptops_data)
            print(df)

            await save_to_google_sheet(SPREADSHEET_ID, SHEET_NAME, laptops_data)

            await browser.close()
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

