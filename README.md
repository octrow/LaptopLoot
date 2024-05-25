# LaptopLoot

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

LaptopLoot automates the process of scraping laptop data from eBay and saving it to a Google Sheet for analysis. It leverages asynchronous programming with `Playwright` for efficient web scraping and `gspread` for seamless Google Sheets integration. 

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

## Usage:

1. **Run the Scraper:** `python main.py`
2. **View Data:** Open your Google Sheet to access the scraped laptop data.

## Disclaimer:

- This project is for educational purposes and personal use only. 
- Always respect eBay's terms of service and `robots.txt` guidelines.
- Avoid scraping excessively to prevent putting unnecessary load on eBay's servers.

## License:

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.