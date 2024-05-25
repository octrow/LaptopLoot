# google_sheets.py
import os
import traceback

import gspread_asyncio
from google.oauth2.service_account import Credentials
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
if SERVICE_ACCOUNT_FILE is None:
    raise ValueError("SERVICE_ACCOUNT_FILE is not set! Check your .env file.")

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
        worksheet = await spreadsheet.get_worksheet(0)
        logger.info(f"Worksheet ID: {worksheet.id}")
        values = [[item[key] for key in item] for item in data]
        logger.info(f"Values: {values}")
        # Append the data to the sheet
        flat_values = []
        for value in values:
            flat_row = []
            for item in value:
                if isinstance(item, list):
                    flat_row.append(', '.join(map(str, item)))
                else:
                    flat_row.append(item)
            flat_values.append(flat_row)
        # Append the data to the sheet
        logger.info(f'Flat values: {flat_values}')
        await worksheet.append_rows(flat_values, value_input_option='RAW')
        logger.info(f"Data saved to Google Sheet: {sheet_name}")
        logger.info("Spreadsheet URL: https://docs.google.com/spreadsheets/d/{0}".format(spreadsheet.id))
    except Exception as e:
        logger.error(f"Error saving data to Google Sheet: {e}")
        logger.error(traceback.format_exc())
