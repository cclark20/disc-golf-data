import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
import pandas as pd
import numpy as np

def authenticate():
    # Set the path to the credentials file for your Google API project
    credentials_file = "./client_secret.json"
    # define scope
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    # Authenticate with Google Sheets using the credentials file
    creds = None
    if os.path.exists(credentials_file):
        creds = service_account.Credentials.from_service_account_file(credentials_file, scopes=scope)

    # Create the Google Sheets API client
    sheets_service = build('sheets', 'v4', credentials=creds)

    return sheets_service

def append_to_sheet(service, csv_data:str):
    # Set the ID of the Google Sheet you want to append data to
    sheet_id = "1Q5oZvtzbnVL_xggy4N6hNkssXbaEXiVtr91mZSO0MRc"

    # Append the CSV data to the Google Sheet
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range='event_results',  # Update the sheet and range as needed
        valueInputOption='USER_ENTERED',
        body={'values': csv_data}
    ).execute()
    print(f"Data appended to sheet {sheet_id}")



# gspread

def auth_gspread():
    # Set the path to the credentials file for your Google API project
    credentials_file = "./client_secret.json"
    # define scope
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    # Authenticate with Google Sheets using the credentials file
    creds = None
    if os.path.exists(credentials_file):
        creds = service_account.Credentials.from_service_account_file(credentials_file, scopes=scope)

    client = gspread.authorize(creds)
    return client

def get_sheet_df(gspread_client, sheet:str, worksheet:str) -> pd.DataFrame:
    sheet = gspread_client.open(sheet)
    worksheet = sheet.worksheet(worksheet)
    return pd.DataFrame(worksheet.get_all_records())

def replace_sheet(gspread_client, sheet:str, worksheet:str, data:pd.DataFrame):
    sheet = gspread_client.open(sheet)
    worksheet = sheet.worksheet(worksheet)

    # typing
    values = data.values.tolist()
    values = [ [int(val) if isinstance(val, np.int64) else val for val in row] for row in values]
    values = [ [round(val,2) if isinstance(val, float) else val for val in row] for row in values]

    worksheet.clear()
    worksheet.update([data.columns.values.tolist()] + values)
