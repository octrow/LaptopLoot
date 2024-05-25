import os
import asyncio
import re
import traceback

from modules import robust_extract
from modules.natural_language_processor import NaturalLanguageProcessor
# from modules.robust_extract import extract_price
from dotenv import load_dotenv
from random import randint
from loguru import logger
from playwright.async_api import async_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

import pandas as pd
from google.oauth2.service_account import Credentials
import gspread_asyncio

# --- Load Environment Variables ---
load_dotenv()

# --- Google Sheets Configuration ---
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME") or "eBay Laptops"
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
if SERVICE_ACCOUNT_FILE is None:
    raise ValueError("SERVICE_ACCOUNT_FILE is not set! Check your .env file.")


# --- Data Extraction Functions ---
nlp = NaturalLanguageProcessor()

async def extract_data_nlp(listing, element_name):
    html_content = await listing.content()
    soup = nlp.parse_html(html_content)
    text = nlp.extract_text(soup)
    tokens = nlp.process_text(text)
    element = nlp.find_element(element_name, tokens)
    if element:
        element_code = nlp.get_element_code(soup, element)
        return element_code
    else:
        return "N/A"

async def extract_element(listing, css_selector, element_name):
    logger.info(f"Extracting {element_name}...")
    try:
        elements = await listing.locator(css_selector).all()
        if not elements:
            return "N/A"
        texts = []
        for element in elements:
            if await element.is_visible():
                text = await element.text_content()
                texts.append(text)
        logger.info(f"Extracted {element_name}: {texts}")
        if element_name in ["url"]:
            url = await elements[0].get_attribute('href')
            logger.info(f"Extracted {element_name}: {url}")
            return url
        if element_name in ["price"]:
            # Remove non-numeric characters before converting
            price_texts = [re.sub(r"[^\d\.]", "", text) for text in texts]
            texts = price_texts
        if element_name in ["shipping cost"]:
            if any('Free' in text or 'Бесплатная' in text for text in texts):
                logger.info(f"Extracted shipping cost: {0.00}")
                return 0.00
            else:
                shipping_costs = [re.findall(r"[\d\.]+", text) for text in texts]
                logger.info(f"Extracted shipping cost: {shipping_costs}")
                if shipping_costs:
                    return [str(cost[0]) for cost in shipping_costs if cost]
                else:
                    return "N/A"
        if element_name in ["time left"]:
            logger.info(f"Extracted time left: {texts}")
            return [text.strip() for text in texts]
        return [text.strip() for text in texts]
    except Exception as e:
        logger.error(f"Error extracting {element_name}: {e}")
        logger.error(traceback.format_exc())
        return await extract_data_nlp(listing, element_name)


# --- Web Scraping Functions ---
async def search_ebay(page, query):
    await page.goto("https://www.ebay.com/")  # Go to the main page first
    await page.wait_for_load_state('networkidle')  # Wait for main page to be fully interactive
    search_box = page.locator('#gh-ac')
    await search_box.fill(query, timeout=1000)
    await search_box.press('Enter')
    await page.wait_for_load_state('networkidle')
    logger.info(f"Searching for {query}...")


async def scrape_page(page):
    logger.info("Scraping page...")
    laptops_data = []
    listings = await page.locator('li.s-item').all()  # Get all listings
    for listing in listings:
        logger.info(f"Scraping listing: {listing}")
        laptop = {}
        # laptop['Name'] = await extract_laptop_name(listing)
        laptop['Name'] = await extract_element(listing, '.s-item__title', 'laptop name')
        laptop['Price'] = await extract_element(listing, '.s-item__price', 'price')
        laptop['Shipping Cost'] = await extract_element(listing, '.s-item__shipping', 'shipping cost')
        laptop['Condition'] = await extract_element(listing, '.s-item__subtitle .SECONDARY_INFO', 'condition')
        laptop['URL'] = await extract_element(listing, '.s-item__link', 'url')
        laptop['Time Left'] = await extract_element(listing, '.s-item__time-left', 'time left')
        # ... (Call other data extraction functions) ...
        laptops_data.append(laptop)
    return laptops_data


async def scrape_ebay_listings(page, search_query):
    logger.info(f"Scraping {search_query}...")
    await search_ebay(page, search_query)
    all_laptops_data = []
    page_num = 1
    while True:
        print(f"Scraping page {page_num}...")
        all_laptops_data.extend(await scrape_page(page))
        try:
            next_page_link = page.locator('a.pagination__next')
            if await next_page_link.is_visible():
                await next_page_link.click()
                page_num += 1
                await page.wait_for_load_state('networkidle', timeout=2000)
                await asyncio.sleep(randint(2, 5))
                print(f"Scraped page {page_num}.")
            else:
                print("No more pages found.")
                break
        except PlaywrightTimeoutError:
            print("Timeout while waiting for the next page.")
            break
    return all_laptops_data


# --- Google Sheets Functions ---
def get_creds():
    # To obtain a service account JSON file, follow these steps:
    # https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    scoped = creds.with_scopes([
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    return scoped
async def save_to_google_sheet(spreadsheet_id, sheet_name, data):
    """Saves the scraped data to a Google Sheet.

    Args:
        spreadsheet_id (str): The ID of the Google Spreadsheet.
        sheet_name (str): The name of the sheet within the Spreadsheet.
        data (list): The scraped data as a list of dictionaries.
    """
    agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
    try:
        agc = await agcm.authorize()
        logger.info(f"Connected to Google Sheets: {agc}")
        spreadsheet = await agc.create("Laptop Loot Data")
        logger.info(f"spreadsheet_id is None. New Spreadsheet ID: {spreadsheet.id}")
        logger.info("Spreadsheet URL: https://docs.google.com/spreadsheets/d/{0}".format(spreadsheet.id))
        logger.info("Open the URL in your browser to see gspread_asyncio in action!")
        # Allow anyone with the URL to write to this spreadsheet.
        await agc.insert_permission(spreadsheet.id, None, perm_type="anyone", role="writer")
        worksheet = await spreadsheet.get_worksheet(0)
        logger.info(f"Worksheet ID: {worksheet.id}")

        values = [[item[key] for key in item] for item in data]
        # logger.info(f"Data: {values}")
        # Append the data to the sheet
        flat_values = []
        for value in values:
            flat_row = []
            for item in value:
                if isinstance(item, list):
                    flat_row.append(', '.join(map(str, item)))
                else:
                    flat_row.append(item)
            flat_values.append(flat_row)
        # logger.info(f"Flat values: {flat_values}")
        # Append the data to the sheet
        await worksheet.append_rows(flat_values, value_input_option='RAW')
        logger.info(f"Data saved to Google Sheet: {sheet_name}")
    except Exception as e:
        logger.error(f"Error saving data to Google Sheet: {e}")
        # logger.error(traceback.format_exc())


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

