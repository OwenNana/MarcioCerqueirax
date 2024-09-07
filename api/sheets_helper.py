from flask import Flask, request, jsonify
from sheets_helper import client, open_main_sheet, open_by_url
from datetime import datetime

app = Flask(__name__)

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    sheet = open_main_sheet()
    rows = sheet.get_all_values()[1:]

    for row in rows:
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
    sheet = open_by_url(sheet_url)
    headers = sheet.row_values(1)
    return jsonify(headers)

@app.route("/submit-rating", methods=["POST"])
def submit_rating():
    data = request.json
    sheet_url = data["sheetUrl"]
    date_str = data["date"]
    activity = data["activity"]
    rating = data["rating"]

    sheet = open_by_url(sheet_url)
    headers = sheet.row_values(1)
    col_index = headers.index(activity) + 1

    all_dates = sheet.col_values(1)[1:]
    row_index = None
    for i, d in enumerate(all_dates):
        if d == date_str:
            row_index = i + 2
            break

    if not row_index:
        row_index = len(all_dates) + 2
        sheet.update_cell(row_index, 1, date_str)

    sheet.update_cell(row_index, col_index, rating)
    return jsonify({"status": "success", "message": "تم حفظ التقييم."})

@app.route("/users", methods=["GET"])
def users():
    sheet = open_main_sheet()
    data = sheet.get_all_values()[1:]
    users = [{
        "username": r[0],
        "password": r[1],
        "sheetUrl": r[2],
        "permissions": r[3]
    } for r in data]
    return jsonify(users)

@app.route("/create-user", methods=["POST"])
def create_user():
    data = request.json
    username = data["username"]
    password = data["password"]

    new_sheet = client.create(f"Sheet - {username}")
    new_sheet.share(username, perm_type='user', role='writer')
    url = new_sheet.url

    sheet = open_main_sheet()
    sheet.append_row([username, password, url, "user"])

    return jsonify({"status": "success", "message": "تم إنشاء المستخدم بنجاح", "sheetUrl": url})

if __name__ == "__main__":
    app.run(debug=True)
