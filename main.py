import os
import asyncio

import gspread
from dotenv import load_dotenv
from random import randint
from loguru import logger
from playwright.async_api import async_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

import pandas as pd
from google.oauth2.service_account import Credentials
import gspread_asyncio

# --- Google Sheets Configuration ---
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME") or "eBay Laptops"
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")


# --- Data Extraction Functions ---
async def extract_laptop_name(listing):
    try:
        return (await listing.locator('.s-item__title').text_content()).strip()
    except:
        return "N/A"


async def extract_price(listing):
    try:
        price_text = await (listing.locator('.s-item__price span').text_content()).strip()
        return float(price_text.replace('$', '').replace(',', ''))
    except:
        return "N/A"


async def extract_shipping_cost(listing):
    try:
        shipping_element = await listing.locator('.s-item__shipping')
        if shipping_element.is_visible():
            shipping_text = shipping_element.text_content().strip()
            if 'Free' in shipping_text:
                return 0.00
            else:
                return float(shipping_text.replace('shipping', '').replace('$', '').replace(',', ''))
        else:
            return "N/A"
    except:
        return "N/A"


async def extract_condition(listing):
    try:
        condition_element = await listing.locator('.s-item__subtitle')
        if condition_element.is_visible():
            return condition_element.text_content().strip()
        else:
            return "N/A"
    except:
        return "N/A"


async def extract_url(listing):
    try:
        return await listing.locator('.s-item__link').get_attribute('href')
    except:
        return "N/A"


async def extract_time_left(listing):
    try:
        time_left_element = await listing.locator('.s-item__time-left')
        if time_left_element.is_visible():
            return time_left_element.text_content().strip()
        else:
            return "N/A"
    except:
        return "N/A"


# ... (Add other data extraction functions for: Bids, Seller Name, Seller Rating) ...

# --- Web Scraping Functions ---
async def search_ebay(page, query):
    await page.goto("https://www.ebay.com/")  # Go to the main page first
    await page.wait_for_load_state('networkidle')  # Wait for main page to be fully interactive
    search_box = page.locator('#gh-ac')
    await search_box.fill(query, timeout=60000)
    await search_box.press('Enter')
    await page.wait_for_load_state('networkidle')


async def scrape_page(page):
    # Awaiting 'all()' before iterating
    laptops_data = []
    for listing in await page.locator('li.s-item').all():
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
    await search_ebay(page, search_query)
    all_laptops_data = []
    page_num = 1
    while True:
        print(f"Scraping page {page_num}...")
        # Awaiting 'scrape_page' before extending
        all_laptops_data.extend(await scrape_page(page))
        try:
            next_page_link = page.locator('a.pagination__next')
            if await next_page_link.is_visible():
                await next_page_link.click()
                page_num += 1
                await page.wait_for_load_state('networkidle', timeout=10000)
                await asyncio.sleep(randint(2, 5))
                print(f"Scraped page {page_num}.")
                break # DEVNOTE: For testing purposes
            else:
                print("No more pages found.")
                break
        except PlaywrightTimeoutError:
            print("Timeout while waiting for the next page.")
            break
    return all_laptops_data


# --- Google Sheets Functions ---
async def save_to_google_sheet(spreadsheet_id, sheet_name, data):
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    )
    # logger.info(f'Creds: {creds}')

    agcm = gspread_asyncio.AsyncioGspreadClientManager(lambda: creds)  # Create the manager
    # logger.info(f'AGCM: {agcm}')
    async with agcm.authorize() as client:  # Get authorized client
        spreadsheet = await client.open_by_key(spreadsheet_id)
        # logger.info(f'Spreadsheet: {spreadsheet}')
        try:
            worksheet = await spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = await spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)

        if data:
            await worksheet.append_rows(data, value_input_option="USER_ENTERED")
        else:
            print("No data to save to Google Sheets.")


# --- Main Function ---
async def main():
    load_dotenv()
    search_query = os.getenv("SEARCH_QUERY") or input("Enter your eBay search query: ")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        laptops_data = await scrape_ebay_listings(page, search_query)

        df = pd.DataFrame(laptops_data)
        print(df)

        await save_to_google_sheet(SPREADSHEET_ID, SHEET_NAME, laptops_data)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())