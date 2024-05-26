import asyncio
from random import randint

import playwright.sync_api
from loguru import logger
from playwright.async_api import expect
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
CSS_SELECTOR_LANGUAGE_BUTTON = '#gh-eb-Geo'
CSS_SELECTOR_LANGUAGE_DROPDOWN = '#gh-eb-Geo-o'
CSS_SELECTOR_ENGLISH_LANGUAGE = '#gh-eb-Geo-a-en'
CSS_SELECTOR_SHIP_TO_BUTTON = '#gh-shipto-click button[title="Ship to"]'
CSS_SELECTOR_SHIP_TO_MODAL = '#gh-shipto-click-modal'
CSS_SELECTOR_COUNTRY_DROPDOWN = '#nid-v8v-0-content'


async def change_language(page, target_language='en-US'):
    """Changes the language on eBay if it doesn't match the target language.

    Args:
        page (Page): The Playwright page object.
        target_language (str, optional): The desired language (e.g., 'en-US').
                                          Defaults to 'en-US'.
    """
    current_language = await page.evaluate('() => document.documentElement.lang')
    logger.info(f"Current language: {current_language}, Target language: {target_language}")
    if current_language != target_language:
        logger.info(f"Changing language to {target_language}...")
        while await page.get_by_role("button", name="Выбран язык: Русский").is_visible():
            try:
                # Open language dropdown
                await page.get_by_role("button", name="Выбран язык: Русский").click()
                await page.get_by_role("link", name="English").click()
                # Optionally wait for the page to reload or update after language change
                await page.wait_for_load_state('networkidle')  # You might need to adjust this
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout while trying to change the language to {target_language}")
                await page.locator(CSS_SELECTOR_LANGUAGE_BUTTON).click()
                await page.wait_for_selector(CSS_SELECTOR_LANGUAGE_DROPDOWN, state='visible', timeout=1000)
                logger.info("Language dropdown opened")
                # Click on the target language
                await page.locator(CSS_SELECTOR_ENGLISH_LANGUAGE).click()
                logger.info(f"Language changed to {target_language}")
                await page.wait_for_load_state('networkidle')  # You might need to adjust this


async def change_location(page, country="United States"):
    """Changes the location/country on eBay using the shipping address modal.

    Args:
        page (Page): The Playwright page object.
        country_code (str, optional): The desired country code (e.g., 'United States').
                                      Defaults to 'United States'.
    """
    try:
        # Click on "Ship to" button
        await page.get_by_role("button", name="Ship to").click()
        logger.info("Ship to button clicked")
        await page.get_by_role("button", name="Ship to:").click()
        logger.info("Ship to: button clicked")
        await page.get_by_text(country).click()
        logger.info(f"Country: {country} selected")
        await page.get_by_role("button", name="Done").click()
        logger.info("Done button clicked")

        await page.wait_for_load_state('networkidle')  # Wait for potential page update
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while trying to change the location to {country}")

async def choose_category(page, category):
    try:
        await page.get_by_role("button", name="Shop by category").click()
        await expect(page.get_by_role("link", name="Computers & tablets")).to_be_visible()
        await page.get_by_role("link", name="Computers & tablets").click()
        await expect(page.get_by_role("link", name="Laptops & Netbooks")).to_be_visible()
        await page.get_by_role("link", name="Laptops & Netbooks").click()
        await expect(page.get_by_role("link", name="PC Laptops & Netbooks")).to_be_visible()
        await page.get_by_role("link", name="PC Laptops & Netbooks").click()
        await page.wait_for_load_state('networkidle')
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while trying to choose the category {category}")


# Helper function to apply filters
async def apply_filter(page, filter_name, filter_values, suffix=""):
    if filter_values:
        try:
            logger.info(f"Applying filter '{filter_name}' with values: {filter_values}")
            # Open the filter tab
            page.get_by_role("tab", name=filter_name, exact=True).click()
            await expect(page.get_by_role("tab", name=filter_name, exact=True)).to_be_visible()

            # Apply each filter value
            for value in filter_values:
                filter_locator = page.get_by_label(f"{value}{suffix}", exact=True)
                logger.info(f"Applying filter '{filter_name}' with value: {value}")
                if filter_locator.is_visible():
                    await filter_locator.check()
                    await expect(filter_locator).to_be_visible()
            await page.wait_for_load_state('networkidle')
        except PlaywrightTimeoutError:
            logger.warning(f"Timeout or error applying filter '{filter_name}' with values: {filter_values}")


async def search_ebay(page, query, args):
    await page.goto("https://www.ebay.com/")  # Go to the main page first
    await page.wait_for_load_state('networkidle')  # Wait for main page to be fully interactive

    await change_language(page, args.lang)  # Ensure English language
    await change_location(page, args.country)  # Set location to United States
    await page.wait_for_load_state('networkidle')
    await choose_category(page, args.category) # Set category to PC Laptops
    await page.wait_for_load_state('networkidle')
    if args:
        pass
    # --- Choose filters ---
    await page.get_by_label("All Filters").click()  # Updated selector
    await page.wait_for_load_state('networkidle')

    # --- Apply Filters ---
    await apply_filter(page, 'RAM Size', args.ram, ' GB')
    await apply_filter(page, 'Screen Size', args.screen_size)
    await apply_filter(page, 'Processor', args.cpu)
    await apply_filter(page, 'Condition', args.condition)

    # --- Apply the filter dialog ---
    apply_button = await page.get_by_label("Apply")  # Use more robust selector
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
