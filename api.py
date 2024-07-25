from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# إعداد الاتصال بـ Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# معرف الشيت الرئيسي
MASTER_SPREADSHEET_ID = "1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY"

def open_sheet_by_url(url):
    sheet_id = url.split("/d/")[1].split("/")[0]
    return client.open_by_key(sheet_id).sheet1

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    sheet = client.open_by_key(MASTER_SPREADSHEET_ID).worksheet("admin")
    users = sheet.get_all_values()[1:]

    for row in users:
        if row[0] == username and row[1] == password:
            return jsonify({
                "status": "success",
                "sheetUrl": row[2],
                "permissions": row[3]
            })
    return jsonify({"status": "error", "message": "بيانات الدخول غير صحيحة."})

@app.route("/get-headers", methods=["POST"])
def get_headers():
    sheet_url = request.json.get("sheetUrl")
    try:
        sheet = open_sheet_by_url(sheet_url)
        headers = sheet.row_values(1)
        return jsonify(headers)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/submit-rating", methods=["POST"])
def submit_rating():
    data = request.json
    sheet_url = data["sheetUrl"]
    date_str = data["date"]
    activity = data["activity"]
    rating = data["rating"]

    try:
        sheet = open_sheet_by_url(sheet_url)
        headers = sheet.row_values(1)
        col_index = headers.index(activity) + 1
        all_dates = sheet.col_values(1)[1:]

        row_index = None
        for idx, d in enumerate(all_dates):
            try:
                if datetime.strptime(d, "%Y-%m-%d").strftime("%Y-%m-%d") == date_str:
                    row_index = idx + 2
                    break
            except:
                continue

        if not row_index:
            row_index = len(all_dates) + 2
            sheet.update_cell(row_index, 1, date_str)

        sheet.update_cell(row_index, col_index, rating)
        return jsonify({"status": "success", "message": "تم حفظ التقييم."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# نقطة البداية
if __name__ == "__main__":
    app.run(debug=True)
