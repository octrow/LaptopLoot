# google_sheets.py
import json
import os
import traceback

import gspread
import gspread_asyncio
from google.oauth2.service_account import Credentials
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# --- Settings File Path ---
SETTINGS_FILE = 'settings.json'

# --- Function to load settings from JSON ---
def load_settings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        return settings
    except FileNotFoundError:
        # Create an empty settings file if it doesn't exist
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({}, f)
        return {}

# --- Function to save settings to JSON ---
def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)



SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
if SERVICE_ACCOUNT_FILE is None:
    raise ValueError("SERVICE_ACCOUNT_FILE is not set! Check your .env file.")

settings = load_settings()

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


async def save_to_google_sheet(spreadsheet_id: str | None, sheet_name: str, data):
    """Saves the scraped data to a Google Sheet.

    Args:
        spreadsheet_id (str): The ID of the Google Spreadsheet. If None, a new one is created.
        sheet_name (str): The name of the sheet within the Spreadsheet.
        data (list): The scraped data as a list of dictionaries.

    Returns:
        str or None: The Spreadsheet ID if a new spreadsheet was created, otherwise None.
    """
    agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
    try:
        agc = await agcm.authorize()
        logger.info(f"Connected to Google Sheets: {agc}")

        if spreadsheet_id is None:
            spreadsheet = await agc.create("Laptop Loot Data")
            spreadsheet_id = spreadsheet.id # Get ID of the newly created spreadsheet
            logger.info(f"New Spreadsheet ID: {spreadsheet.id}")
            logger.info("Spreadsheet URL: https://docs.google.com/spreadsheets/d/{0}".format(spreadsheet.id))
            logger.info("Open the URL in your browser to see gspread_asyncio in action!")
            # Allow anyone with the URL to write to this spreadsheet.
            await agc.insert_permission(spreadsheet.id, None, perm_type="anyone", role="writer")
            settings['SPREADSHEET_ID'] = spreadsheet_id
            save_settings(settings)
        else:
            spreadsheet = await agc.open_by_key(spreadsheet_id)
            logger.info(f"Opened existing Spreadsheet: {spreadsheet.title}")
        try:
            worksheet = await spreadsheet.worksheet(sheet_name)
            logger.info(f"Found existing worksheet: {sheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = await spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)
            logger.info(f"Created new worksheet: {sheet_name}")

        # --- Resize worksheet if necessary ---
        await resize_worksheet(worksheet, len(data), len(data[0]))
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

async def resize_worksheet(worksheet, rows_needed, cols_needed):
    """Resizes the worksheet if there are not enough rows or columns."""
    try:
        # Get current worksheet dimensions
        current_rows = len(await worksheet.get_all_values())
        current_cols = len(await worksheet.row_values(1))

        # Resize if needed
        if current_rows < rows_needed:
            await worksheet.add_rows(rows_needed - current_rows)
            logger.info(f"Added {rows_needed - current_rows} rows to worksheet.")
        if current_cols < cols_needed:
            await worksheet.add_cols(cols_needed - current_cols)
            logger.info(f"Added {cols_needed - current_cols} columns to worksheet.")

    except Exception as e:
        logger.error(f"Error resizing worksheet: {e}")
        logger.error(traceback.format_exc())