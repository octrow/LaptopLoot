import os
import asyncio
import re
import traceback

import gspread
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
async def extract_laptop_name(listing):
    logger.info("Extracting laptop name...")
    try:
        name_element = listing.locator('.s-item__title')
        # logger.info(f"Extracted laptop name: name_element {name_element}")
        name = await name_element.text_content()
        logger.info(f"Extracted laptop name: {name}")
        return name.strip()
    except Exception as e:
        logger.error(f"Error extracting laptop name: {e}")
        return "N/A"


async def extract_price(listing):
    logger.info("Extracting price...")
    try:
        # Target the specific span element within .s-item__price
        price_element = listing.locator('.s-item__price')
        price_text = await price_element.text_content()
        # Remove non-numeric characters before converting
        price_text = re.sub(r"[^\d\.]", "", price_text)
        logger.info(f"Extracted price: {price_text}")
        return float(price_text)
    except Exception as e:
        logger.error(f"Error extracting price: {e}")
        return "N/A"


async def extract_shipping_cost(listing):
    logger.info("Extracting shipping cost...")
    try:
        shipping_element = listing.locator('.s-item__shipping')
        if await shipping_element.is_visible():
            shipping_text = await shipping_element.text_content()
            if 'Free' in shipping_text or 'Бесплатная' in shipping_text:
                logger.info(f"Extracted shipping cost: {0.00}")
                return 0.00
            else:
                # Extract only the numeric part of the shipping cost
                shipping_cost = re.findall(r"[\d\.]+", shipping_text)
                logger.info(f"Extracted shipping cost: {shipping_cost}")
                if shipping_cost:
                    return float(shipping_cost[0])
                else:
                    return "N/A"  # Or handle cases without a numeric cost differently
        else:
            return "N/A"
    except Exception as e:
        logger.error(f"Error extracting shipping cost: {e}")
        return "N/A"


async def extract_condition(listing):
    logger.info("Extracting condition...")
    try:
        # Target the specific span element with the condition information
        condition_element = listing.locator(".s-item__subtitle .SECONDARY_INFO")
        condition_text = await condition_element.text_content()
        logger.info(f"Extracted condition text: {condition_text}")
        return condition_text.strip()
    except Exception as e:
        logger.error(f"Error extracting condition: {e}")
        return "N/A"


async def extract_url(listing):
    logger.info("Extracting url...")
    try:
        logger.info("Extracted url: " + await listing.locator('.s-item__link').get_attribute('href'))
        return await listing.locator('.s-item__link').get_attribute('href')
    except Exception as e:
        logger.error(f"Error extracting url: {e}")
        return "N/A"


async def extract_time_left(listing):
    logger.info("Extracting time left...")
    try:
        time_left_element = listing.locator('.s-item__time-left')
        if await time_left_element.is_visible():
            time_left_text = await time_left_element.text_content()
            logger.info(f"Extracted time left: {time_left_text}")
            return time_left_text.strip()
        else:
            return "N/A"
    except Exception as e:
        logger.error(f"Error extracting time left: {e}")
        return "N/A"


# ... (Add other data extraction functions for: Bids, Seller Name, Seller Rating) ...

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
        laptop['Name'] = await extract_laptop_name(listing)
        laptop['Price'] = await extract_price(listing)
        laptop['Shipping Cost'] = await extract_shipping_cost(listing)
        laptop['Condition'] = await extract_condition(listing)
        laptop['URL'] = await extract_url(listing)
        laptop['Time Left'] = await extract_time_left(listing)
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
        # spreadsheet = await agc.open_by_key(spreadsheet_id)
        # logger.info(f"Spreadsheet ID: {spreadsheet.id}")
        # # Allow anyone with the URL to write to this spreadsheet.
        # await agc.insert_permission(spreadsheet.id, None, perm_type="anyone", role="writer")
        # # Create a new spreadsheet but also grab a reference to the default one.
        # ws = await ss.add_worksheet("My Test Worksheet", 10, 5)
        worksheet = await spreadsheet.get_worksheet(0)
        logger.info(f"Worksheet ID: {worksheet.id}")

        values = [[item[key] for key in item] for item in data]
        logger.info(f"Data: {values}")

        # Append the data to the sheet
        await worksheet.append_rows(values, value_input_option='RAW')
        logger.info(f"Data saved to Google Sheet: {sheet_name}")
    except gspread.exceptions.APIError as e:
        logger.error(f"APIError: {e}")
        # logger.error(traceback.format_exc())
    except gspread.exceptions.SpreadsheetNotFound as e:
        logger.error(f"SpreadsheetNotFound: {e}")
        # logger.error(traceback.format_exc())
    except gspread.exceptions.WorksheetNotFound as e:
        logger.error(f"WorksheetNotFound: {e}")
        # logger.error(traceback.format_exc())
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
    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
    # laptop_data ={"name": "test"}
    # async def main2():
    #     await save_to_google_sheet(SPREADSHEET_ID, SHEET_NAME, laptop_data)
    # asyncio.run(main2())
