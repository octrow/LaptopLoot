import os # Used for interacting with the operating system
import asyncio # Imports the asyncio library for asynchronous programming.

import gspread # Imports the gspread library for interacting with Google Sheets.
from dotenv import load_dotenv # Imports the load_dotenv function from the dotenv library.
from random import randint # Imports the randint function for generating random integers.
from loguru import logger # Imports the logger object for logging messages.
from playwright.async_api import async_playwright # Imports the async_playwright function from Playwright.
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError # For handling timeouts during web scraping.

import pandas as pd # Imports the pandas library for data manipulation, aliased as 'pd'.
from google.oauth2.service_account import Credentials # Imports the Credentials class from the google.oauth2.service_account module.
import gspread_asyncio # Imports the gspread_asyncio library for asynchronous interaction with Google Sheets.

# --- Google Sheets Configuration ---
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID") # Retrieves the 'SPREADSHEET_ID' environment variable.
SHEET_NAME = os.getenv("SHEET_NAME") or "eBay Laptops" #  Retrieves 'SHEET_NAME' or defaults to 'eBay Laptops'.
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE") #  Retrieves the 'SERVICE_ACCOUNT_FILE' environment variable.


# --- Data Extraction Functions ---
async def extract_laptop_name(listing): # Defines an asynchronous function to extract laptop names from eBay listings.
    try: # Start of a try-except block to handle potential errors during extraction.
        return (await listing.locator('.s-item__title').text_content()).strip() # Attempts to locate the laptop title element, extract its text content, and strip any leading/trailing whitespace.
    except: # Catches any exceptions raised during the process.
        return "N/A" # Returns "N/A" if an error occurs during extraction.


async def extract_price(listing): # Defines an asynchronous function to extract prices from eBay listings.
    try:
        price_text = await (listing.locator('.s-item__price span').text_content()).strip() # Locates the price element, extracts its text content, and removes leading/trailing whitespace.
        return float(price_text.replace('$', '').replace(',', '')) # Cleans the price text by removing '$' and ',' characters, then converts it to a float.
    except:
        return "N/A" # Returns "N/A" if an error occurs during extraction.


async def extract_shipping_cost(listing): # Defines an asynchronous function to extract shipping costs.
    try:
        shipping_element = await listing.locator('.s-item__shipping') # Locates the shipping element on the page.
        if shipping_element.is_visible(): # Checks if the shipping element is visible on the page.
            shipping_text = shipping_element.text_content().strip() # Extracts shipping text, removes extra spaces.
            if 'Free' in shipping_text: # Checks if shipping is free.
                return 0.00 # Returns 0.00 for free shipping.
            else: # If shipping is not free
                return float(shipping_text.replace('shipping', '').replace('$', '').replace(',', '')) #  Extracts the numerical shipping cost from the text.
        else: #  If the shipping element is not visible
            return "N/A" # Returns "N/A", indicating shipping cost is not found
    except: # Handles any errors during the process
        return "N/A" # Returns "N/A" if any error occurs.


async def extract_condition(listing): # Defines an asynchronous function to extract the condition of the laptop.
    try:
        condition_element = await listing.locator('.s-item__subtitle') # Locates the element containing the laptop's condition.
        if condition_element.is_visible(): # Checks if the condition element is visible.
            return condition_element.text_content().strip() # Extracts the text content of the condition and removes leading/trailing whitespace.
        else: # If the condition element is not visible.
            return "N/A" # Returns "N/A" if the condition is not found.
    except: # Handles any errors during the condition extraction process.
        return "N/A" # Returns "N/A" if any error occurs during extraction.


async def extract_url(listing): # Defines an asynchronous function to extract the URL of the eBay listing.
    try:
        return await listing.locator('.s-item__link').get_attribute('href') # Attempts to retrieve the 'href' attribute (URL) of the listing link element.
    except: # Handles any errors during the URL extraction.
        return "N/A" # Returns "N/A" if the URL cannot be extracted.


async def extract_time_left(listing): # Defines an asynchronous function to extract the remaining time for the eBay listing.
    try:
        time_left_element = await listing.locator('.s-item__time-left') # Locates the element displaying the time left.
        if time_left_element.is_visible(): # Checks if the time left element is actually visible on the page.
            return time_left_element.text_content().strip() # Extracts the time left text from the element and removes any extra spaces.
        else:
            return "N/A" # Returns "N/A" if the time left is not found or visible.
    except: # Handles any errors during the time left extraction.
        return "N/A" # Returns "N/A" if there's any error while getting the time left information.


# ... (Add other data extraction functions for: Bids, Seller Name, Seller Rating) ...

# --- Web Scraping Functions ---
async def search_ebay(page, query): #  Defines an asynchronous function to perform a search on eBay.
    await page.goto("https://www.ebay.com/")  # Navigates to the eBay homepage.
    await page.wait_for_load_state('networkidle')  # Waits for the page to finish loading and become idle.
    search_box = page.locator('#gh-ac') # Locates the eBay search bar using its ID.
    await search_box.fill(query, timeout=60000) # Enters the provided search query into the search bar, setting a timeout.
    await search_box.press('Enter') # Simulates pressing the Enter key to initiate the search.
    await page.wait_for_load_state('networkidle') # Waits for the search results page to load.


async def scrape_page(page): # Defines an asynchronous function to scrape laptop data from a single eBay search results page.
    # Awaiting 'all()' before iterating
    laptops_data = [] # Initializes an empty list to store the scraped laptop data.
    for listing in await page.locator('li.s-item').all(): # Iterates through each eBay listing on the page.
        laptop = {} # Creates an empty dictionary to store data for the current laptop.
        laptop['Name'] = await extract_laptop_name(listing) # Extracts and stores the laptop's name.
        laptop['Price'] = await extract_price(listing) # Extracts and stores the laptop's price.
        laptop['Shipping Cost'] = await extract_shipping_cost(listing) # Extracts and stores the shipping cost.
        laptop['Condition'] = await extract_condition(listing) # Extracts and stores the laptop's condition.
        laptop['URL'] = await extract_url(listing) # Extracts and stores the URL of the listing.
        laptop['Time Left'] = await extract_time_left(listing) # Extracts and stores the time left for the listing.
        # ... (Call other data extraction functions) ...
        laptops_data.append(laptop) # Adds the laptop data dictionary to the list.
    return laptops_data # Returns the list of laptop data dictionaries.


async def scrape_ebay_listings(page, search_query): # Defines an asynchronous function to scrape multiple pages of eBay listings.
    await search_ebay(page, search_query) # Performs an initial search based on the provided search query.
    all_laptops_data = [] # Initializes an empty list to store laptop data from all pages.
    page_num = 1 # Initializes a page counter variable.
    while True: # Enters an infinite loop to keep scraping until a condition breaks it.
        print(f"Scraping page {page_num}...") # Prints the current page number being scraped.
        # Awaiting 'scrape_page' before extending
        all_laptops_data.extend(await scrape_page(page)) # Scrapes the current page and extends the all_laptops_data list.
        try: # Start of a try-except block to handle potential errors.
            next_page_link = page.locator('a.pagination__next') #  Locates the 'Next' page link.
            if await next_page_link.is_visible(): # Checks if the 'Next' page link is visible, indicating more pages.
                await next_page_link.click() #  Clicks the 'Next' page link.
                page_num += 1 #  Increments the page counter.
                await page.wait_for_load_state('networkidle', timeout=10000) # Waits for the next page to load completely, up to a timeout.
                await asyncio.sleep(randint(2, 5)) # Pauses execution for a random interval to avoid overloading eBay's servers.
                print(f"Scraped page {page_num}.")
                break # DEVNOTE: For testing purposes
            else:
                print("No more pages found.") # Prints a message if the 'Next' page link is not visible (no more pages).
                break # Exits the loop if there are no more pages.
        except PlaywrightTimeoutError: # Handles the PlaywrightTimeoutError exception (occurs if a page takes too long to load).
            print("Timeout while waiting for the next page.") # Prints an error message.
            break # Exits the loop if a timeout occurs.
    return all_laptops_data # Returns the scraped data from all pages.


# --- Google Sheets Functions ---
async def save_to_google_sheet(spreadsheet_id, sheet_name, data): # Defines an async function to save data to Google Sheets
    creds = Credentials.from_service_account_file( # Loads credentials for a service account from a JSON file.
        SERVICE_ACCOUNT_FILE, # File path to the service account key file.
        scopes=[ # List of scopes the service account should have access to.
            "https://www.googleapis.com/auth/spreadsheets", # Scope for reading and writing to Google Sheets.
        ],
    )
    # logger.info(f'Creds: {creds}')

    agcm = gspread_asyncio.AsyncioGspreadClientManager(lambda: creds)  # Create the manager
    # logger.info(f'AGCM: {agcm}')
    async with agcm.authorize() as client:  # Get authorized client
        spreadsheet = await client.open_by_key(spreadsheet_id) # Opens a specific Google Spreadsheet by its ID.
        # logger.info(f'Spreadsheet: {spreadsheet}')
        try: # Attempts to find a worksheet by its name.
            worksheet = await spreadsheet.worksheet(sheet_name) # Tries to get the worksheet with the given name.
        except gspread.exceptions.WorksheetNotFound: # If a worksheet with that name is not found.
            worksheet = await spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20) # Adds a new worksheet with the specified title and dimensions.

        if data: #  Checks if there's data to save.
            await worksheet.append_rows(data, value_input_option="USER_ENTERED") # Appends the scraped data to the Google Sheet.
        else:
            print("No data to save to Google Sheets.") # Prints a message if there is no data to save.


# --- Main Function ---
async def main(): #  Defines the main asynchronous function where the program logic starts.
    load_dotenv() #  Loads environment variables from a .env file.
    search_query = os.getenv("SEARCH_QUERY") or input("Enter your eBay search query: ") # Gets the search query either from env variable or user input.

    async with async_playwright() as p: # Launches a new instance of the Playwright browser context.
        browser = await p.chromium.launch(headless=False) #  Starts a new Chromium browser instance.
        page = await browser.new_page() #  Opens a new browser tab (page).

        laptops_data = await scrape_ebay_listings(page, search_query) # Starts scraping eBay listings using the provided query.

        df = pd.DataFrame(laptops_data) # Converts the scraped data to a Pandas DataFrame for easier handling.
        print(df) # Prints the DataFrame, showing the scraped data in a structured format.

        await save_to_google_sheet(SPREADSHEET_ID, SHEET_NAME, laptops_data) # Saves the scraped data to the specified Google Sheet.

        await browser.close() # Closes the browser.


if __name__ == "__main__":
    asyncio.run(main()) # Runs the main asynchronous function.