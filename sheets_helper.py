import gspread
from oauth2client.service_account import ServiceAccountCredentials

# إعداد الاتصال
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("api/credentials.json", scope)
client = gspread.authorize(creds)

# معرف الشيت الرئيسي
MASTER_SPREADSHEET_ID = "1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY"

def open_main_sheet():
    return client.open_by_key(MASTER_SPREADSHEET_ID).worksheet("admin")

def open_by_url(url):
    sheet_id = url.split("/d/")[1].split("/")[0]
    return client.open_by_key(sheet_id).sheet1
