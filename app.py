import logging
import os
import json
import uuid
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from functools import wraps

# Required for tracking
import requests 

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2.service_account import Credentials
import gspread
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --------- 1. Logging Setup ---------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PatientApp")

# --------- 2. App & Rate Limiting Config ---------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super_secret_key_change_this")

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://" 
)

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]

CACHE_TTL_SECONDS = 5

# --------- 3. Utilities ---------
def json_ok(data=None):
    return jsonify({"success": True, **(data or {})})

def json_err(message, code=400):
    logger.error(f"Response Error {code}: {message}")
    return jsonify({"success": False, "message": message}), code

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return wrapper

def patient_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'patient_id' not in session:
            return redirect(url_for('patient_login_page'))
        return f(*args, **kwargs)
    return wrapper

# --------- 4. Sheets Client ---------
class SheetsClient:
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self._worksheets = {}
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._last_fetch = {}
        self._init_client()

    def _init_client(self):
        try:
            creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
            if creds_json:
                creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPE)
            else:
                local_file = "patient-app-backend-b56334f48a1b.json"
                if os.path.exists(local_file):
                    creds = Credentials.from_service_account_file(local_file, scopes=SCOPE)
                else:
                    logger.warning("No Google Credentials found.")
                    return

            self.client = gspread.authorize(creds)
            ss_id = os.getenv("SPREADSHEET_ID")
            
            if ss_id:
                self.spreadsheet = self.client.open_by_key(ss_id)
            else:
                self.spreadsheet = self.client.open("Hospital Patient Data")
            
            logger.info(f"Connected to Spreadsheet: {self.spreadsheet.title}")

        except Exception as e:
            logger.critical(f"Google Sheets Connection Failed: {e}")
            self.client = None

    def _get_ws(self, title: str, force_refresh=False):
        if not self.spreadsheet:
            raise RuntimeError("Spreadsheet not connected")
        
        # If we need fresh data or title isn't cached
        if force_refresh and title in self._worksheets:
            del self._worksheets[title]

        if title in self._worksheets:
            return self._worksheets[title]
            
        try:
            ws = self.spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            ws = self.spreadsheet.add_worksheet(title=title, rows=100, cols=20)
        self._worksheets[title] = ws
        return ws

    def get_all_values_cached(self, title: str) -> List[List[str]]:
        now = time.time()
        with self._cache_lock:
            last = self._last_fetch.get(title, 0)
            if title in self._cache and (now - last) < CACHE_TTL_SECONDS:
                return self._cache[title]
            
            ws = self._get_ws(title)
            vals = ws.get_all_values() or []
            self._cache[title] = vals
            self._last_fetch[title] = now
            return vals

    def get_all_records_cached(self, title: str) -> List[Dict[str, Any]]:
        vals = self.get_all_values_cached(title)
        if not vals or len(vals) < 1: return []
        headers = vals[0]
        records = []
        for row in vals[1:]:
            rec = {headers[i]: (row[i] if i < len(row) else "") for i in range(len(headers))}
            records.append(rec)
        return records

    def append_row(self, title: str, row: List[Any]):
        try:
            # Try normal append
            ws = self._get_ws(title)
            res = ws.append_row(row, value_input_option='USER_ENTERED')
        except Exception:
            # If it fails (e.g. deleted tab), force refresh worksheet and try once more
            logger.warning(f"Append failed for {title}, retrying with fresh worksheet ref...")
            ws = self._get_ws(title, force_refresh=True)
            res = ws.append_row(row, value_input_option='USER_ENTERED')
            
        with self._cache_lock:
            self._last_fetch[title] = 0
        return res

    def delete_row_by_index(self, title: str, index_1based: int):
        ws = self._get_ws(title)
        ws.delete_rows(index_1based)
        with self._cache_lock:
            self._last_fetch[title] = 0

    def update_cell(self, title: str, row: int, col: int, value: Any):
        ws = self._get_ws(title)
        ws.update_cell(row, col, value)
        with self._cache_lock:
            self._last_fetch[title] = 0

    def find_row_index(self, title: str, col_index_zero_based: int, value: str) -> Optional[int]:
        vals = self.get_all_values_cached(title)
        for i, row in enumerate(vals):
            if len(row) > col_index_zero_based and str(row[col_index_zero_based]) == str(value):
                return i + 1
        return None

sheets = SheetsClient()

# Schemas
DEFAULT_SCHEMAS = {
    "Patients": ["id", "name", "age", "phone", "address", "problems", "last_visit", "password_hash"],
    "Users": ["username", "password_hash", "role"],
    "Visits_v2": ["visit_id", "patient_id", "date", "diagnosis", "prescription", "notes", "doctor_name"],
    "Appointments_v2": ["appt_id", "patient_id", "patient_name", "date", "time", "status", "notes", "doctor", "issue"],
    "Messages": ["msg_id", "patient_id", "sender", "content", "timestamp"],
    "AccessLogs": ["log_id", "timestamp", "ip_address", "action", "username", "user_agent", "location", "isp"]
}

def ensure_sheets_and_headers():
    if not sheets.spreadsheet: return
    for title, headers in DEFAULT_SCHEMAS.items():
        try:
            ws = sheets._get_ws(title)
            # FIX: Only append headers if A1 is totally empty
            val_a1 = ws.acell('A1').value
            if not val_a1: 
                ws.append_row(headers)
        except Exception as e:
            logger.error(f"Schema check error {title}: {e}")

# Startup
try:
    ensure_sheets_and_headers()
    try:
        users = sheets.get_all_records_cached("Users")
        if not any(u.get("username") == "admin" for u in users):
            sheets.append_row("Users", ["admin", generate_password_hash("admin123"), "admin"])
    except Exception: pass
except Exception as e:
    logger.critical(f"Startup error: {e}")

# --------- 5. Services ---------

class LogService:
    sheet = "AccessLogs"

    @staticmethod
    def get_ip():
        if request.headers.getlist("X-Forwarded-For"):
            return request.headers.getlist("X-Forwarded-For")[0]
        return request.remote_addr

    @staticmethod
    def get_ip_info(ip):
        try:
            # 2s timeout. If it fails, we catch it.
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        "location": f"{data.get('city', '?')}, {data.get('country', '?')}",
                        "isp": data.get('isp', 'Unknown')
                    }
        except Exception as e:
            logger.error(f"IP API Error: {e}")
        return {"location": "Unknown", "isp": "Unknown"}

    @classmethod
    def log_event(cls, action, username="Guest"):
        # Synchronous logging with error catching
        try:
            ip = cls.get_ip()
            user_agent = request.headers.get('User-Agent')
            
            # Try to get info, default to unknown if fails
            info = cls.get_ip_info(ip)
            
            new_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            row = [
                new_id, 
                timestamp, 
                ip, 
                action, 
                username, 
                user_agent, 
                info['location'], 
                info['isp']
            ]
            
            sheets.append_row(cls.sheet, row)
            logger.info(f"TRACKED: {action} | IP: {ip}")
            return True
        except Exception as e:
            logger.error(f"Tracking failed CRITICAL: {e}")
            return False

class AuthService:
    @staticmethod
    def verify_user(username, password):
        users = sheets.get_all_records_cached("Users")
        user = next((u for u in users if u.get("username") == username), None)
        if user and check_password_hash(user.get("password_hash", ""), password):
            return user
        return None

class PatientService:
    sheet = "Patients"
    
    @classmethod
    def create_patient(cls, payload):
        if not all(k in payload for k in ["name", "age", "problems"]):
            raise ValueError("Name, Age, and Problems required")
        
        # --- FIX: SEQUENTIAL ID LOGIC ---
        all_data = sheets.get_all_values_cached(cls.sheet)
        # Length includes header. If len=1 (header), next is 1.
        next_id_num = len(all_data) 
        
        # Format 0001, 0002...
        new_id = str(next_id_num).zfill(4)
        
        row = [
            new_id, 
            payload["name"], 
            payload["age"], 
            payload.get("phone", ""), 
            payload.get("address", ""), 
            payload["problems"], 
            datetime.now().strftime("%Y-%m-%d"), 
            "" 
        ]
        sheets.append_row(cls.sheet, row)
        return new_id

    @classmethod
    def list_patients(cls):
        vals = sheets.get_all_values_cached(cls.sheet)
        if not vals or len(vals)<2: return []
        res = []
        for row in vals[1:]:
            while len(row) < 7: row.append("")
            res.append({
                "id": row[0], "name": row[1], "age": row[2], "phone": row[3],
                "address": row[4], "problems": row[5], "last_visit": row[6]
            })
        return res

    @classmethod
    def update_patient(cls, pid, payload):
        r_idx = sheets.find_row_index(cls.sheet, 0, str(pid))
        if not r_idx: raise KeyError("Patient not found")
        row_vals = sheets._get_ws(cls.sheet).row_values(r_idx)
        
        exist = row_vals[5] if len(row_vals)>5 else ""
        new_p = payload.get("problems", "")
        updated = (exist + ", " + new_p).strip(", ") if new_p else exist
        
        if "phone" in payload: sheets.update_cell(cls.sheet, r_idx, 4, payload["phone"])
        if "address" in payload: sheets.update_cell(cls.sheet, r_idx, 5, payload["address"])
        sheets.update_cell(cls.sheet, r_idx, 6, updated)
        sheets.update_cell(cls.sheet, r_idx, 7, datetime.now().strftime("%Y-%m-%d"))

    @classmethod
    def delete_patient(cls, pid):
        r_idx = sheets.find_row_index(cls.sheet, 0, str(pid))
        if not r_idx: raise KeyError("Patient not found")
        sheets.delete_row_by_index(cls.sheet, r_idx)

    @classmethod
    def find_profile(cls, pid):
        idx = sheets.find_row_index(cls.sheet, 0, str(pid))
        if not idx: raise KeyError("Patient not found")
        row = sheets._get_ws(cls.sheet).row_values(idx)
        return {
            "id": row[0], "name": row[1] if len(row)>1 else "", 
            "age": row[2] if len(row)>2 else "", "phone": row[3] if len(row)>3 else "",
            "address": row[4] if len(row)>4 else "", "problems": row[5] if len(row)>5 else "",
            "last_visit": row[6] if len(row)>6 else ""
        }

class AppointmentService:
    sheet = "Appointments_v2"
    @classmethod
    def create_appointment(cls, payload):
        if not all(k in payload for k in ["patient_id", "date", "time"]): raise ValueError("Missing fields")
        # UUID for appts is fine
        new_id = str(uuid.uuid4())[:8]
        row = [new_id, payload["patient_id"], payload.get("patient_name", "Unknown"),
               payload["date"], payload["time"], "Scheduled", 
               payload.get("notes", ""), payload.get("doctor", ""), payload.get("issue", "")]
        sheets.append_row(cls.sheet, row)

    @classmethod
    def list_appointments(cls):
        vals = sheets.get_all_values_cached(cls.sheet)
        res = []
        for row in vals[1:]:
            if len(row)<5: continue
            res.append({
                "appt_id": row[0], "patient_id": row[1], "patient_name": row[2],
                "date": row[3], "time": row[4], "status": row[5] if len(row)>5 else "",
                "notes": row[6] if len(row)>6 else "", "doctor": row[7] if len(row)>7 else "",
                "issue": row[8] if len(row)>8 else ""
            })
        return res

    @classmethod
    def delete_appointment(cls, appt_id, requester_id=None):
        vals = sheets.get_all_values_cached(cls.sheet)
        for i, row in enumerate(vals):
            if i==0: continue
            if len(row)>0 and str(row[0]) == str(appt_id):
                if requester_id and (len(row)<2 or str(row[1]) != str(requester_id)):
                    raise PermissionError("Unauthorized")
                sheets.delete_row_by_index(cls.sheet, i+1)
                return
        raise KeyError("Appointment not found")

class VisitService:
    sheet = "Visits_v2"
    @classmethod
    def add_visit(cls, payload):
        if not all(k in payload for k in ["patient_id", "date"]): raise ValueError("ID/Date required")
        row = [str(uuid.uuid4())[:8], payload["patient_id"], payload["date"],
               payload.get("diagnosis", ""), payload.get("prescription", ""),
               payload.get("notes", ""), payload.get("doctor_name", "")]
        sheets.append_row(cls.sheet, row)
        try:
            r = sheets.find_row_index("Patients", 0, str(payload["patient_id"]))
            if r: sheets.update_cell("Patients", r, 7, payload["date"])
        except: pass

    @classmethod
    def list_visits_for_patient(cls, pid):
        vals = sheets.get_all_values_cached(cls.sheet)
        return [{
            "visit_id": r[0], "date": r[2] if len(r)>2 else "",
            "diagnosis": r[3] if len(r)>3 else "", "prescription": r[4] if len(r)>4 else "",
            "notes": r[5] if len(r)>5 else "", "doctor_name": r[6] if len(r)>6 else ""
        } for r in vals[1:] if len(r)>1 and str(r[1]) == str(pid)]

class MessageService:
    sheet = "Messages"
    @classmethod
    def send_message(cls, pid, sender, content):
        if not content: raise ValueError("Empty message")
        sheets.append_row(cls.sheet, [str(uuid.uuid4())[:8], pid, sender, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    @classmethod
    def list_threads(cls):
        msgs = sheets.get_all_records_cached(cls.sheet)
        p_vals = sheets.get_all_values_cached("Patients")
        pmap = {str(r[0]): r[1] for r in p_vals[1:] if r}
        threads = {}
        for m in msgs:
            pid = str(m.get("patient_id"))
            if pid not in threads:
                threads[pid] = {"patient_id": pid, "patient_name": pmap.get(pid, f"ID {pid}"), "last_message": "", "timestamp": "", "unread": False}
            threads[pid]["last_message"] = m.get("content", "")
            threads[pid]["timestamp"] = m.get("timestamp", "")
            if m.get("sender") == "patient": threads[pid]["unread"] = True
        return sorted(threads.values(), key=lambda x: x["timestamp"], reverse=True)

    @classmethod
    def get_messages_for_patient(cls, pid):
        msgs = sheets.get_all_records_cached(cls.sheet)
        return [m for m in msgs if str(m.get("patient_id")) == str(pid)]

# --------- 6. Routes ---------

# DEBUG ROUTE (NEW): Use this to see why logging might be failing
@app.route('/test_log')
def test_log():
    try:
        success = LogService.log_event("Test Event", "Tester")
        return jsonify({"success": success, "message": "Check AccessLogs sheet now."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login_page():
    if request.method == 'GET':
        return render_template('login.html')
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        LogService.log_event("Admin Login Failed - Missing Data", "Unknown")
        return json_err("Missing credentials", 400)

    user = AuthService.verify_user(username, password)
    if user:
        session['user'] = username
        session['role'] = user.get("role")
        LogService.log_event("Admin Login Success", username)
        return json_ok()
    
    LogService.log_event("Admin Login Failed - Bad Creds", username)
    return json_err("Invalid credentials", 401)

@app.route('/patient/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def patient_login_page():
    if request.method == 'GET':
        return render_template('patient_login.html')
    data = request.get_json() or {}
    pid = data.get("patient_id")
    password = data.get("password")
    
    try:
        idx = sheets.find_row_index("Patients", 0, str(pid))
        if not idx:
            LogService.log_event("Patient Login Failed - ID Not Found", pid or "?")
            return json_err("ID not found", 404)
            
        row = sheets._get_ws("Patients").row_values(idx)
        if len(row)>7 and row[7] and check_password_hash(row[7], password):
            session["patient_id"] = str(pid)
            session["patient_name"] = row[1]
            LogService.log_event("Patient Login Success", pid)
            return json_ok()
            
        LogService.log_event("Patient Login Failed - Bad Password", pid)
        return json_err("Invalid credentials", 401)
    except Exception as e:
        logger.error(f"Login error: {e}")
        return json_err("Login failed", 500)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/add_patient', methods=['POST'])
@login_required
def add_patient():
    data = request.get_json() or {}
    try:
        pid = data.get("patient_id")
        if pid:
            PatientService.update_patient(pid, data)
            return json_ok({"message": f"Updated {pid}"})
        
        # New Patient (Sequential ID)
        new_id = PatientService.create_patient(data)
        LogService.log_event("Admin Created Patient", new_id)
        return json_ok({"message": "Created", "patient_id": new_id})
    except Exception as e:
        logger.error(f"Add patient error: {e}")
        return json_err(str(e), 500)

@app.route('/get_all_patients')
@login_required
def get_all_patients():
    try: return json_ok({"patients": PatientService.list_patients()})
    except Exception as e: return json_err(str(e), 500)

@app.route('/delete_patient/<pid>', methods=['DELETE'])
@login_required
def delete_patient(pid):
    try:
        PatientService.delete_patient(pid)
        return json_ok({"message": "Deleted"})
    except KeyError: return json_err("Not found", 404)
    except Exception as e: return json_err(str(e), 500)

@app.route('/dashboard_stats')
@login_required
def dashboard_stats():
    try:
        patients = PatientService.list_patients()
        visits = sheets.get_all_values_cached("Visits_v2")
        today = datetime.now().strftime("%Y-%m-%d")
        patients_today = sum(1 for p in patients if p.get("last_visit") == today)
        
        counts = {}
        for v in visits[1:]:
            if len(v)>2 and v[2]:
                d = v[2].split(" ")[0]
                counts[d] = counts.get(d, 0) + 1
        dates, chart_counts = [], []
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            dates.append(d)
            chart_counts.append(counts.get(d, 0))
        return json_ok({"total_patients": len(patients), "patients_today": patients_today, "chart_dates": dates, "chart_counts": chart_counts})
    except Exception as e: return json_err(str(e), 500)

# --- Appointments & Visits & Messages ---
@app.route('/book_appointment', methods=['POST'])
@login_required
def book_appointment():
    try:
        AppointmentService.create_appointment(request.get_json() or {})
        return json_ok({"message": "Booked"})
    except Exception as e: return json_err(str(e), 500)

@app.route('/delete_appointment/<appt_id>', methods=['DELETE'])
def delete_appointment(appt_id):
    try:
        AppointmentService.delete_appointment(appt_id, session.get("patient_id"))
        return json_ok({"message": "Deleted"})
    except PermissionError: return json_err("Unauthorized", 403)
    except Exception as e: return json_err(str(e), 500)

@app.route('/get_appointments')
@login_required
def get_appointments():
    try: return json_ok({"appointments": AppointmentService.list_appointments()})
    except Exception as e: return json_err(str(e), 500)

@app.route('/add_visit', methods=['POST'])
@login_required
def add_visit():
    try:
        VisitService.add_visit(request.get_json() or {})
        return json_ok({"message": "Added"})
    except Exception as e: return json_err(str(e), 500)

@app.route('/get_visits/<pid>')
@login_required
def get_visits(pid):
    try: return json_ok({"visits": VisitService.list_visits_for_patient(pid)})
    except Exception as e: return json_err(str(e), 500)

@app.route('/patient/get_data')
@patient_login_required
def get_patient_data():
    pid = session.get("patient_id")
    try:
        return json_ok({
            "profile": PatientService.find_profile(pid),
            "appointments": [a for a in AppointmentService.list_appointments() if str(a["patient_id"]) == str(pid)],
            "messages": MessageService.get_messages_for_patient(pid)
        })
    except Exception as e: return json_err(str(e), 500)

@app.route('/patient/book_appointment', methods=['POST'])
@patient_login_required
def patient_book_appointment():
    data = request.get_json() or {}
    data["patient_id"] = session["patient_id"]
    try:
        AppointmentService.create_appointment(data)
        return json_ok({"message": "Booked"})
    except Exception as e: return json_err(str(e), 500)

@app.route('/patient/send_message', methods=['POST'])
@patient_login_required
def patient_send_message():
    data = request.get_json() or {}
    try:
        MessageService.send_message(session["patient_id"], "patient", data.get("content"))
        return json_ok()
    except Exception as e: return json_err(str(e), 500)

@app.route('/patient/signup', methods=['GET', 'POST'])
def patient_signup_page():
    if request.method == 'GET': return render_template('patient_signup.html')
    data = request.get_json() or {}
    pid, password = data.get("patient_id"), data.get("password")
    try:
        idx = sheets.find_row_index("Patients", 0, str(pid))
        if not idx: return json_err("ID not found", 404)
        row = sheets._get_ws("Patients").row_values(idx)
        if len(row)>7 and row[7]: return json_err("Account exists", 400)
        
        sheets.update_cell("Patients", idx, 8, generate_password_hash(password))
        LogService.log_event("Patient Account Activated", pid)
        return json_ok({"message": "Created"})
    except Exception as e: return json_err(str(e), 500)

@app.route('/patient/dashboard')
@patient_login_required
def patient_dashboard(): return render_template('patient_dashboard.html')

@app.route('/search_patient')
@login_required
def search_patient():
    q = request.args.get("query", "").lower()
    if not q: return json_ok({"results": []})
    try:
        res = [p for p in PatientService.list_patients() if q in str(p["id"]).lower() or q in str(p["name"]).lower()]
        return json_ok({"results": res})
    except Exception as e: return json_err(str(e), 500)

@app.route('/admin/get_chat_threads')
@login_required
def get_chat_threads():
    try: return json_ok({"threads": MessageService.list_threads()})
    except Exception as e: return json_err(str(e), 500)

@app.route('/admin/get_messages/<pid>')
@login_required
def admin_get_messages(pid):
    try: return json_ok({"messages": MessageService.get_messages_for_patient(pid)})
    except Exception as e: return json_err(str(e), 500)

@app.route('/admin/send_message', methods=['POST'])
@login_required
def admin_send_message():
    data = request.get_json() or {}
    try:
        MessageService.send_message(data.get("patient_id"), "admin", data.get("content"))
        return json_ok()
    except Exception as e: return json_err(str(e), 500)

@app.route('/health')
def health_check(): return json_ok({"status": "ok"})

# Error handler for rate limits
@app.errorhandler(429)
def ratelimit_handler(e):
    return json_err("Rate limit exceeded. Try again later.", 429)

if __name__ == "__main__":
    app.run(debug=True)