import asyncio
import gspread_asyncio
from google.oauth2.service_account import Credentials

class GSheetsHandler:
    """Handles interaction with Google Sheets."""

    def __init__(self, service_account_file):
        self.service_account_file = service_account_file

    async def save_to_google_sheet(self, spreadsheet_id, sheet_name, data):
        """Authenticates and saves data to the specified Google Sheet."""

        creds = Credentials.from_service_account_file(
            self.service_account_file,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
            ],
        )

        async with gspread_asyncio.AsyncAuthorize(creds) as client:
            spreadsheet = await client.open_by_key(spreadsheet_id)
            try:
                worksheet = await spreadsheet.worksheet(sheet_name)
            except gspread_asyncio.exceptions.WorksheetNotFound:
                worksheet = await spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)

            if data: # Check if data is not empty
                # Append data (assuming data is a list of dictionaries)
                await worksheet.append_rows(data, value_input_option="USER_ENTERED")
            else:
                print("No data to save to Google Sheets.")