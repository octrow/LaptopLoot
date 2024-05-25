import asyncio
from random import randint

from loguru import logger
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from modules.data_extraction import extract_element

# --- Selectors ---
CSS_SELECTOR_LAPTOP_NAME = '.s-item__title'
CSS_SELECTOR_PRICE = '.s-item__price'
CSS_SELECTOR_SHIPPING_COST = '.s-item__shipping'
CSS_SELECTOR_CONDITION = '.s-item__subtitle .SECONDARY_INFO'
CSS_SELECTOR_URL = '.s-item__link'
CSS_SELECTOR_TIME_LEFT = '.s-item__time-left'

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
        laptop['Name'] = await extract_element(listing, CSS_SELECTOR_LAPTOP_NAME, 'laptop name')
        laptop['Price'] = await extract_element(listing, CSS_SELECTOR_PRICE, 'price')
        laptop['Shipping Cost'] = await extract_element(listing, CSS_SELECTOR_SHIPPING_COST, 'shipping cost')
        laptop['Condition'] = await extract_element(listing, CSS_SELECTOR_CONDITION, 'condition')
        laptop['URL'] = await extract_element(listing, CSS_SELECTOR_URL, 'url')
        laptop['Time Left'] = await extract_element(listing, CSS_SELECTOR_TIME_LEFT, 'time left')
        laptop['Seller Name'] = await extract_element(listing, '.s-item__selller', 'seller name') # TODO: dev
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
