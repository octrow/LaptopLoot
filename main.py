import os
import asyncio

import gspread
from dotenv import load_dotenv
from random import randint
import time

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
def extract_laptop_name(listing):
    try:
        return listing.locator('.s-item__title').text_content().strip()
    except:
        return "N/A"


def extract_price(listing):
    try:
        price_text = listing.locator('.s-item__price').text_content().strip()
        return float(price_text.replace('$', '').replace(',', ''))
    except:
        return "N/A"


def extract_shipping_cost(listing):
    try:
        shipping_element = listing.locator('.s-item__shipping')
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


def extract_condition(listing):
    try:
        condition_element = listing.locator('.s-item__subtitle')
        if condition_element.is_visible():
            return condition_element.text_content().strip()
        else:
            return "N/A"
    except:
        return "N/A"


def extract_url(listing):
    try:
        return listing.locator('.s-item__link').get_attribute('href')
    except:
        return "N/A"


def extract_time_left(listing):
    try:
        time_left_element = listing.locator('.s-item__time-left')
        if time_left_element.is_visible():
            return time_left_element.text_content().strip()
        else:
            return "N/A"
    except:
        return "N/A"


# ... (Add other data extraction functions for: Bids, Seller Name, Seller Rating) ...

# --- Web Scraping Functions ---
def search_ebay(page, query):
    search_box = page.locator('#gh-ac')
    search_box.fill(query)
    search_box.press('Enter')
    page.wait_for_load_state('networkidle')


def scrape_page(page):
    laptops_data = []
    for listing in page.locator('li.s-item').all():
        laptop = {}
        laptop['Name'] = extract_laptop_name(listing)
        laptop['Price'] = extract_price(listing)
        laptop['Shipping Cost'] = extract_shipping_cost(listing)
        laptop['Condition'] = extract_condition(listing)
        laptop['URL'] = extract_url(listing)
        laptop['Time Left'] = extract_time_left(listing)
        # ... (Call other data extraction functions) ...
        laptops_data.append(laptop)
    return laptops_data


async def scrape_ebay_listings(page, search_query):
    search_ebay(page, search_query)
    all_laptops_data = []
    page_num = 1
    while True:
        print(f"Scraping page {page_num}...")
        all_laptops_data.extend(scrape_page(page))
        try:
            next_page_link = page.locator('a.pagination__next')
            if next_page_link.is_visible():
                next_page_link.click()
                page_num += 1
                page.wait_for_load_state('networkidle', timeout=10000)
                time.sleep(randint(2, 5))
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

    agcm = gspread_asyncio.AsyncioGspreadClientManager(lambda: creds)  # Create the manager
    async with agcm.authorize() as client:  # Get authorized client
        spreadsheet = await client.open_by_key(spreadsheet_id)
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

    async with async_playwright() as p: # Use async_playwright
        browser = await p.chromium.launch(headless=True) # TODO: Class 'Browser' does not define '__await__', so the 'await' operator cannot be used on its instances
        page = await browser.new_page()

        laptops_data = await scrape_ebay_listings(page, search_query)  # No await needed here

        df = pd.DataFrame(laptops_data)
        print(df)

        await save_to_google_sheet(SPREADSHEET_ID, SHEET_NAME, laptops_data)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())