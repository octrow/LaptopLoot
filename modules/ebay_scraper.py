import asyncio
from random import randint
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class EbayScraper:
    """Handles the web scraping logic for eBay."""

    def __init__(self, browser, data_fields):
        self.browser = browser
        self.data_fields = data_fields

    async def _navigate_to_laptops(self, page):
        """Navigates from eBay's homepage to the laptops category page."""

        # 1. Open eBay homepage
        await page.goto("https://www.ebay.com/")

        # 2. Click "Shop by category"
        await page.click("#gh-shop-a")
        await asyncio.sleep(randint(1, 3))

        # 3. Click "Computers, Tablets & Network Hardware"
        await page.click('a.scnd[href*="Computers-Tablets-Network-Hardware"]')
        await asyncio.sleep(randint(1, 3))

        # 4. Click "PC Laptops"
        await page.click('a[href*="PC-Laptops-Netbooks"]')
        await asyncio.sleep(randint(1, 3))

    async def _apply_filters(self, page):
        """Applies filters on the laptops category page."""

        # 5. Click the "Filter" button
        await page.click(".srp-controls__control--link-enabled >> svg")
        await asyncio.sleep(randint(1, 3))

        # 6 & 7. Sort by "Price + Shipping: lowest first"
        await page.click('div[data-refine-item="sort"]')  # Open sort options
        await asyncio.sleep(randint(1, 3))
        await page.click('div[role="radio"][aria-label="Price + Shipping: lowest first"]')
        await asyncio.sleep(randint(1, 3))

        # 8. Click "Done" to apply filters
        await page.click('button[aria-label="Done"]')
        await asyncio.sleep(randint(1, 3))

    async def scrape_ebay_listings(self, search_query):
        """Scrapes eBay listings based on the search query."""
        page = await self.browser.new_page()
        await self._navigate_to_laptops(page)

        # --- Search ---
        await page.fill("#gh-ac", search_query)
        await page.press("#gh-ac", "Enter")

        # --- Filters ---
        await asyncio.sleep(randint(1, 3))
        await self._apply_filters(page)

        # --- Pagination and Data Extraction ---
        all_laptops_data = []
        page_num = 1
        while True:  # Loop through pages
            await page.wait_for_selector(
                ".s-item__wrapper", timeout=5000
            )  # Wait for listings to load
            print(f"Scraping page {page_num}...")

            # --- Extract Data ---
            laptops_data = await self._extract_listing_data(page)
            all_laptops_data.extend(laptops_data)

            # --- Pagination ---
            try:
                # Adapt the selector to target the "Next" page link
                next_page_link = await page.wait_for_selector(
                    'a.pagination__next', timeout=2000
                )
                await next_page_link.click()
                page_num += 1
                await asyncio.sleep(
                    randint(2, 5)
                )  # Introduce a random delay between page loads
            except PlaywrightTimeoutError:
                print("No more pages found.")
                break

        return all_laptops_data

    async def _extract_listing_data(self, page):
        """Extracts data from eBay listing elements on a single page."""
        laptops_data = []
        listings = await page.query_selector_all(".s-item__wrapper")
        for listing in listings:
            laptop_data = {}
            for field in self.data_fields:
                try:
                    locator = listing.locator(field["selector"])
                    if "attribute" in field:
                        laptop_data[field["name"]] = await locator.get_attribute(
                            field["attribute"]
                        )
                    else:
                        text_content = await locator.text_content()
                        if text_content:
                            laptop_data[field["name"]] = text_content.strip()
                        else:
                            laptop_data[field["name"]] = "N/A"  # Handle empty data
                except Exception as e:
                    print(f"Error extracting {field['name']}: {e}")
                    laptop_data[field["name"]] = "N/A"
            laptops_data.append(laptop_data)
        return laptops_data