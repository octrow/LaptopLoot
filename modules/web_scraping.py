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
CSS_SELECTOR_NEXT_PAGE = 'a.pagination__next'
CSS_SELECTOR_LISTING = 'li.s-item'

async def search_ebay(page, query, args):
    await page.goto("https://www.ebay.com/")  # Go to the main page first
    await page.wait_for_load_state('networkidle')  # Wait for main page to be fully interactive
    search_box = page.locator('#gh-ac')
    await search_box.fill(query, timeout=1000)
    await search_box.press('Enter')
    await page.wait_for_load_state('networkidle')
    if args:
        # choose filters
        more_filters_button = page.locator('.x-refine__main__list--more button')
        await more_filters_button.click()
        await page.wait_for_load_state('networkidle')

        # Apply RAM filter
        for ram in args.ram:
            ram_filter = page.locator(f'div#refineOverlay-subPanel-RAM%20Size li:has-text("{ram} GB") input')
            if await ram_filter.is_visible():
                await ram_filter.check()

        # Apply CPU filter
        cpu_filter = page.locator(f'div#refineOverlay-subPanel-Processor li:has-text("{args.cpu}") input')
        if await cpu_filter.is_visible():
            await cpu_filter.check()

        # Apply type filter (PC/Mac)
        type_filter = page.locator(f'div#refineOverlay-subPanel-Category li:has-text("{args.type}") input')
        if await type_filter.is_visible():
            await type_filter.check()

        # Apply the filter dialog
        apply_button = page.locator('x-overlay-footer__apply-btn btn btn--primary')
        await apply_button.click()
        await page.wait_for_load_state('networkidle')

    logger.info(f"Searching for {query}...")


async def navigate_to_next_page(page):
    try:
        next_page_link = page.locator(CSS_SELECTOR_NEXT_PAGE)
        if await next_page_link.is_visible():
            await next_page_link.click()
            await page.wait_for_load_state('networkidle', timeout=2000)
            await asyncio.sleep(randint(2, 5))
            return True
        else:
            print("No more pages found.")
            return False
    except PlaywrightTimeoutError:
        print("Timeout while waiting for the next page.")
        return False


async def scrape_page(page):
    logger.info("Scraping page...")
    laptops_data = []
    listings = await page.locator(CSS_SELECTOR_LISTING).all()  # Get all listings
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


async def scrape_ebay_listings(page, search_query, args):
    logger.info(f"Scraping {search_query}...")
    await search_ebay(page, search_query, args)
    all_laptops_data = []
    page_num = 1
    while True:
        if args.pages is not None and page_num > args.pages:
            break
        print(f"Scraping page {page_num}...")
        laptops_data = await scrape_page(page)
        all_laptops_data.extend(laptops_data)
        if not await navigate_to_next_page(page):
            break
        page_num += 1
        print(f"Scraped page {page_num}.")
    return all_laptops_data
