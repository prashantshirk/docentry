import os
import json
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__, static_folder="static", template_folder="static")
CORS(app)

# --- Google Sheets Setup ---
sheet = None

try:
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)

        # Replace with your actual Google Sheet name
        SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "ClinicPatients")
        sheet = client.open(SHEET_NAME).sheet1
        print("✅ Connected to Google Sheet:", SHEET_NAME)
    else:
        print("❌ GOOGLE_CREDENTIALS_JSON not found in environment variables.")
except Exception as e:
    print("❌ Error connecting to Google Sheets:", e)

# --- API route to add patient ---
@app.route("/api/add_patient", methods=["POST"])
def add_patient():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        patient_id = str(uuid.uuid4())[:8]  # short unique ID
        name = data.get("name")
        contact = data.get("contact")
        address = data.get("address")
        test_name = data.get("test_name")
        test_result = data.get("test_result")
        problem = data.get("problem")
        visit_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if sheet:
            sheet.append_row([
                patient_id, name, contact, address, test_name, test_result,
                problem, visit_date
            ])
            return jsonify({"message": "✅ Patient data saved successfully!", "patient_id": patient_id})
        else:
            return jsonify({"error": "Google Sheets not configured."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- API route to get patient history ---
@app.route("/api/get_patient/<patient_id>", methods=["GET"])
def get_patient(patient_id):
    try:
        if sheet:
            records = sheet.get_all_records()
            patient_history = [
                row for row in records if row.get("Patient ID") == patient_id
            ]
            return jsonify({"history": patient_history})
        else:
            return jsonify({"error": "Google Sheets not configured."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Serve Frontend ---
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(debug=True)
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")
