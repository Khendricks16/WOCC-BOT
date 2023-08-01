import os

from logger_conf import bot_logger

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Google Sheets API vars
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'gserviceaccount_key.json'

creds = None
creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)


SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")


def gather_data() -> dict:
    """
    Returns a dict of the weekly training schedule data from the google sheet.
    
    If gathering the data was successful, the resulting dict should look like this:

    {
        "FOH": [
            # Rows of data for FOH sheet
            ...
        ],

        "BOH": [
            # Rows of data for BOH sheet
            ...
        ],
        ...
    }

    On a failed call to the API, an empty dict will be returned.
    """
    
    data = dict()

    try:
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        
        # Call the Sheets API
        result = sheet.values().batchGet(spreadsheetId=SPREADSHEET_ID,
                                    ranges=[f"{location}!A3:S15" for location in ("FOH", "BOH", "GTS")]).execute()
        # Load data into dict
        for range in result["valueRanges"]:
            data[range["range"]] = range.get("values", [])
        
        bot_logger.info("Successfuly gathered training schedule data")
        return data
    except HttpError:
        bot_logger.warning("Failed to gather training schedule data")
        return dict()


def clear() -> None:
    """Calls the google sheets API and clears all training schedule data within the training google sheet."""
    try:
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        
        batch_clear_values_request_body = {
            'ranges': [f"{location}!B3:S15" for location in ("FOH", "BOH", "GTS")]
        }
        
        # Call the Sheets API
        result = sheet.values().batchClear(spreadsheetId=SPREADSHEET_ID,
                                body=batch_clear_values_request_body).execute()

        bot_logger.info("Successfully cleared training schedule")
    except HttpError:
        bot_logger.warning("Failed to clear training schedule")
