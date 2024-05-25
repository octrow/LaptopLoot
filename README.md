# LaptopLoot

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

LaptopLoot automates the process of scraping laptop data from eBay and saving it to a Google Sheet for analysis. 
It leverages asynchronous programming with `Playwright` for efficient web scraping and `gspread` for seamless Google Sheets integration. 

## Features:

- **Fast and Efficient:** Utilizes asynchronous programming to scrape data from eBay quickly and efficiently.
- **Pagination Handling:** Automatically navigates through multiple pages of search results.
- **Customizable Data Extraction:** Easily configure the script to target and extract specific laptop attributes (name, price, condition, etc.).
- **Google Sheets Integration:**  Saves the scraped data directly to a Google Sheet, making it accessible for analysis or visualization.
- **Rate Limiting:** Implements delays to avoid overwhelming eBay and reduce the risk of being blocked.
- **Robust Error Handling:** Designed to handle unexpected errors during scraping, ensuring the script runs smoothly.

## Requirements:

- **Python 3.7+** 
- **Libraries:** Install the necessary libraries using `pip install -r requirements.txt` 
- **Google Cloud Platform Project:** 
    - Create a new GCP project.
    - Enable the Google Sheets API.
    - Create a service account with read/write access to Google Sheets and download its JSON key file.

## Setup and Configuration:

1. **Clone the Repository:** `git clone https://github.com/octrow/LaptopLoot.git`
2. **Install Dependencies:** `pip install -r requirements.txt`
3. **Environment Variables:**
    - Create a `.env` file in the project's root directory.
    - Add the following lines, replacing the placeholders with your actual values: 
    ```
    SEARCH_QUERY="your eBay search query"
    SPREADSHEET_ID="your_spreadsheet_id"
    SHEET_NAME="your_sheet_name"
    SERVICE_ACCOUNT_FILE="path/to/your_service_account_credentials.json" 
    ```
    - `SPREADSHEET_ID`: The ID of your Google Spreadsheet.
    - `SHEET_NAME`: The name of the sheet within the spreadsheet (defaults to 'eBay Laptops').
    - `SERVICE_ACCOUNT_FILE`:  Path to your Google Cloud service account JSON file for authentication.
    - `SEARCH_QUERY`: (Optional) The eBay search query. If not set, the script will prompt for input.

## Usage:

1. **Run the Scraper:** `python main.py`
2. **View Data:** Open your Google Sheet to access the scraped laptop data.

### Data Extraction Functions

#### `extract_laptop_name(listing)`

- Extracts the laptop's name from an eBay listing element.
- Returns "N/A" if extraction fails.

#### `extract_price(listing)`

- Extracts the laptop's price, cleans it (removes '$', ','), and converts it to a float.
- Returns "N/A" if extraction fails.

#### `extract_shipping_cost(listing)`

- Extracts shipping cost, handling cases for free shipping and various formats.
- Returns "N/A" if extraction fails.

#### `extract_condition(listing)`

- Extracts the condition of the laptop (e.g., New, Used).
- Returns "N/A" if extraction fails.

#### `extract_url(listing)`

- Extracts the URL of the eBay listing.
- Returns "N/A" if extraction fails.

#### `extract_time_left(listing)`

- Extracts the remaining time for the listing.
- Returns "N/A" if extraction fails.

### Web Scraping Functions

#### `search_ebay(page, query)`

- Navigates to eBay, enters the search query, and waits for results to load.

#### `scrape_page(page)`

- Iterates through listings on a single search results page, extracts data using the data extraction functions, and returns a list of laptop data dictionaries.

#### `scrape_ebay_listings(page, search_query)`

- Performs the main scraping logic:
    - Calls `search_ebay` to initiate the search.
    - Loops through search result pages, scraping each page with `scrape_page`.
    - Handles pagination and implements random delays to avoid overloading eBay.
    - Returns a list of laptop data dictionaries from all pages.

### Google Sheets Functions

#### `save_to_google_sheet(spreadsheet_id, sheet_name, data)`

- Authenticates with Google Sheets using the service account credentials.
- Opens the specified spreadsheet and worksheet (or creates a new one if it doesn't exist).
- Appends the scraped laptop data to the Google Sheet.

### Main Function

#### `async def main()`

- Loads environment variables.
- Gets the search query (either from environment variable or user input).
- Launches a Playwright browser instance.
- Scrapes eBay listings using the provided query.
- Converts the scraped data to a Pandas DataFrame.
- Saves the data to the Google Sheet.
- Closes the browser.

### Execution

The `if __name__ == "__main__":` block ensures that the `main()` function is called when the script is run directly. 

## Workflow

Here's the workflow of the eBay scraper code:

1. **Initialization (`main.py`)**:
   - Load environment variables from the `.env` file using `load_dotenv()`.
   - Get Google Sheets configuration (spreadsheet ID, sheet name).
   - Parse command-line arguments using `argparse`.

2. **Web Scraping (`modules/web_scraping.py`):**
   - **`search_ebay(page, query, args)`:**
     - Navigates to the eBay homepage and waits for the page to load.
     - Enters the `query` in the search box.
     - Applies filters based on the provided `args` (page number, laptop type, RAM, CPU).
     - Waits for the search results page to load.
   - **`scrape_ebay_listings(page, search_query, args)`:**
     - Calls `search_ebay()` to initiate the search.
     - Loops through the specified number of pages (`args.pages`) or until there are no more pages.
     - Calls `scrape_page()` for each page to extract data from individual listings. 
     - Navigates to the next page using `navigate_to_next_page()`.
     - Returns a list of dictionaries (`all_laptops_data`), where each dictionary represents a laptop listing. 

3. **Data Extraction (`modules/data_extraction.py`):**
   - **`extract_element(listing, css_selector, element_name)`:**
     - Tries to extract the desired element using the provided `css_selector`.
     - If the element is not found using the selector, it falls back to using NLP-based extraction with `extract_data_nlp()`.
     - Handles special cases for specific elements (e.g., price, shipping cost).
   - **`extract_data_nlp(listing, element_name)`:**
     - Uses NLP (with spaCy and NLTK) to extract data from the HTML content of the listing.
     - Cleans the HTML content, processes the text, and attempts to find the desired element based on the provided `element_name`.

4. **Data Processing and Storage (`main.py`):**
   - The scraped data (list of dictionaries) is converted to a Pandas DataFrame for easier handling. 
   - The DataFrame is printed to the console. 
   - The data is saved to a Google Sheet using `save_to_google_sheet()`

**Error Handling:**

- The code uses `try-except` blocks throughout to handle potential errors during web scraping, data extraction, and saving to Google Sheets.
- `traceback.format_exc()` is used to log detailed error messages and stack traces.

**Additional Tips:**

- **Rate Limiting:**  Be mindful of eBay's rate limits. Avoid sending too many requests in a short period.  
The random delays in the code help with this, but further adjustments might be needed.
- **IP Blocking:** Scraping websites aggressively can lead to your IP address being blocked. 
Consider using proxy servers or rotating IP addresses to mitigate this risk.
- **Website Changes:**  Websites change frequently. 
If eBay's structure changes, the scraper may break and require updates to the selectors used in `page.locator()`.

### File Structure

- `main.py`: Main script to run the scraper.
- `modules/`: Directory for custom modules.
    - `web_scraping.py`: Contains functions for web scraping logic.
    - `data_extraction.py`: Contains functions for extracting specific data from listings.
    - `natural_language_processor.py`: Contains a class for natural language processing tasks. 
    - `google_sheets.py`: Contains functions to interact with Google Sheets.

## Disclaimer:

- This project is for educational purposes and personal use only. 
- Always respect eBay's terms of service and `robots.txt` guidelines.
- Avoid scraping excessively to prevent putting unnecessary load on eBay's servers.

## License:

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.