import os
import asyncio
from dotenv import load_dotenv
from random import randint

from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeout

from modules.ebay_scraper import EbayScraper
from modules.gsheets_handler import GSheetsHandler


async def main():
    """Main function to orchestrate the scraping and data saving process."""

    load_dotenv()  # Load environment variables from .env

    # --- Project Configuration (Get from .env or user input) ---
    search_query = os.getenv("SEARCH_QUERY") or input("Enter your eBay search query: ")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    sheet_name = os.getenv("SHEET_NAME") or "eBay Laptops" 
    service_account_file = os.getenv(
        "SERVICE_ACCOUNT_FILE"
    )  

    # --- Data Points to Extract ---
    data_fields = [
        {"name": "Laptop Name", "selector": ".s-item__title"},  
        {"name": "Price", "selector": ".s-item__price"},
        {"name": "Condition", "selector": ".SECONDARY_INFO"}, 
        {"name": "URL", "selector": ".s-item__link", "attribute": "href"},
        # ... add more data fields as needed ...
    ]

    async with async_playwright() as p:
        # --- Initialize Components ---
        browser = await p.chromium.launch(headless=False)  # Headless=False for debugging
        scraper = EbayScraper(browser, data_fields)
        gsheets = GSheetsHandler(service_account_file)

        # --- 1. Scrape Data from eBay ---
        laptops_data = await scraper.scrape_ebay_listings(search_query)

        # --- 2. Save Data to Google Sheets --- 
        await gsheets.save_to_google_sheet(spreadsheet_id, sheet_name, laptops_data)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())