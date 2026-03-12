# Hospital Patient Management System

## Overview

The Hospital Patient Management System is a comprehensive web application designed to manage patient records, appointments, visits, and messaging efficiently. It uses **Google Sheets** as a backend database and provides both admin and patient portals. The application is built using Flask for the backend and HTML/CSS/JavaScript for the frontend.

## Features

### Admin Features
- **Patient Management**: Add, search, update, and delete patient records
- **Appointment Management**: View and manage patient appointments
- **Visit Records**: Track patient visits with diagnosis, prescriptions, and notes
- **Messaging**: Communicate with patients through the portal
- **Dashboard**: View statistics and analytics
- **Access Logs**: Track all system access and activities

### Patient Features
- **Patient Portal**: Secure login with patient ID and password
- **Self-Service**: View personal medical records, appointments, and visit history
- **Book Appointments**: Schedule appointments with doctors
- **Messaging**: Communicate with healthcare staff
- **Profile Management**: Update personal information

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher**
- **pip** (Python package installer)
- **Google Account** (for Google Sheets API)
- **Web Browser** (Chrome, Firefox, Safari, or Edge)

---

## Complete Setup Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/prashantshirk/docentry.git
cd docentry
```

### Step 2: Set Up Python Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask==3.0.0
- gspread==6.0.0
- google-auth==2.22.0
- werkzeug==3.0.0
- fpdf==1.7.2
- Flask-Limiter==3.5.0
- requests==2.31.0

---

## Google Sheets API Setup

### Step 4: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on **"Select a Project"** → **"New Project"**
3. Enter a project name (e.g., "Hospital Patient System")
4. Click **"Create"**

### Step 5: Enable Google Sheets API

1. In your Google Cloud Console, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Sheets API"**
3. Click on it and press **"Enable"**
4. Also search for and enable **"Google Drive API"**

### Step 6: Create Service Account Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"Service Account"**
3. Enter a service account name (e.g., "patient-app-service")
4. Click **"Create and Continue"**
5. For role, select **"Editor"** (or **"Basic" → "Editor"**)
6. Click **"Continue"** → **"Done"**

### Step 7: Generate JSON Key File

1. In the **"Credentials"** page, find your newly created service account
2. Click on the service account email
3. Go to the **"Keys"** tab
4. Click **"Add Key"** → **"Create New Key"**
5. Choose **"JSON"** format
6. Click **"Create"**
7. The JSON file will be downloaded automatically
8. **Rename the file** to `patient-app-backend-b56334f48a1b.json` and place it in your project root directory

### Step 8: Create Google Spreadsheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Name it **"Hospital Patient Data"** (or any name you prefer)
4. Copy the **Spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID_HERE/edit
   ```
5. Share the spreadsheet with your service account email:
   - Click **"Share"** button
   - Paste the service account email (found in the JSON file as `client_email`)
   - Give **"Editor"** permissions
   - Uncheck **"Notify people"**
   - Click **"Share"**

---

## Application Configuration

### Step 9: Set Environment Variables

Create a `.env` file in your project root (or set these as environment variables):

```bash
# Secret key for Flask sessions (change this to a random string)
SECRET_KEY=your_super_secret_random_key_here_change_this

# Google Spreadsheet ID from Step 8
SPREADSHEET_ID=your_spreadsheet_id_here

# Optional: Google Credentials as JSON string (for deployment)
# GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"..."}'
```

**Generating a Secret Key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Alternative: Using JSON Credentials File

If you don't want to use environment variables for Google credentials, the app will automatically look for `patient-app-backend-b56334f48a1b.json` in the project root directory.

---

## Running the Application

### Step 10: Start the Flask Server

```bash
python app.py
```

The application will start on `http://127.0.0.1:5000`

You should see output similar to:
```
INFO - Connected to Spreadsheet: Hospital Patient Data
* Running on http://127.0.0.1:5000
```

### Step 11: Access the Application

Open your web browser and navigate to:
- **Admin Portal**: `http://127.0.0.1:5000/login`
- **Patient Portal**: `http://127.0.0.1:5000/patient/login`

---

## Default Login Credentials

### Admin Login
- **Username**: `admin`
- **Password**: `admin123`

**⚠️ IMPORTANT**: Change the default admin password immediately after first login!

### Patient Login
Patients need to:
1. Be registered by an admin first
2. Sign up at `/patient/signup` using their Patient ID
3. Create their own password during signup

---

## File Structure

```
docentry/
├── app.py                                    # Main Flask application
├── add_user.py                              # Utility script to add users
├── requirements.txt                         # Python dependencies
├── patient-app-backend-b56334f48a1b.json   # Google Service Account credentials
├── .env                                     # Environment variables (create this)
├── static/                                  # CSS, JS, images
│   └── styles.css
├── templates/                               # HTML templates
│   ├── login.html                          # Admin login page
│   ├── patient_login.html                  # Patient login page
│   ├── patient_signup.html                 # Patient registration
│   ├── patient_dashboard.html              # Patient dashboard
│   └── index.html                          # Admin dashboard
└── README.md                               # This file
```

---

## Google Sheets Structure

The application automatically creates the following sheets in your spreadsheet:

### 1. Patients
Columns: `id`, `name`, `age`, `phone`, `address`, `problems`, `last_visit`, `password_hash`

### 2. Users
Columns: `username`, `password_hash`, `role`

### 3. Visits_v2
Columns: `visit_id`, `patient_id`, `date`, `diagnosis`, `prescription`, `notes`, `doctor_name`

### 4. Appointments_v2
Columns: `appt_id`, `patient_id`, `patient_name`, `date`, `time`, `status`, `notes`, `doctor`, `issue`

### 5. Messages
Columns: `msg_id`, `patient_id`, `sender`, `content`, `timestamp`

### 6. AccessLogs
Columns: `log_id`, `timestamp`, `ip_address`, `action`, `username`, `user_agent`, `location`, `isp`

---

## API Endpoints

### Admin Routes
- **`GET /`**: Admin dashboard (requires login)
- **`POST /login`**: Admin login
- **`GET /logout`**: Logout
- **`POST /add_patient`**: Add a new patient
- **`GET /get_all_patients`**: Retrieve all patients
- **`DELETE /delete_patient/<pid>`**: Delete a patient
- **`GET /dashboard_stats`**: Get dashboard statistics
- **`POST /book_appointment`**: Book an appointment
- **`GET /get_appointments`**: Get all appointments
- **`DELETE /delete_appointment/<appt_id>`**: Delete an appointment
- **`POST /add_visit`**: Add a visit record
- **`GET /get_visits/<pid>`**: Get visits for a patient
- **`POST /admin/send_message`**: Send message to patient

### Patient Routes
- **`GET /patient/login`**: Patient login page
- **`POST /patient/login`**: Patient login
- **`GET /patient/signup`**: Patient signup page
- **`POST /patient/signup`**: Patient registration
- **`GET /patient/dashboard`**: Patient dashboard (requires login)
- **`GET /patient/get_data`**: Get patient's personal data
- **`POST /patient/book_appointment`**: Book appointment
- **`POST /patient/send_message`**: Send message to admin

### Utility Routes
- **`GET /health`**: Health check endpoint
- **`GET /test_log`**: Test logging functionality

---

## Usage Guide

### For Administrators

1. **Login**: Navigate to `/login` and use admin credentials
2. **Add Patients**: Click "Add New Patient" and fill in the form with:
   - Patient name
   - Age
   - Phone number
   - Address
   - Medical problems/conditions
3. **Search Patients**: Use the search bar to find patients by ID or name
4. **Book Appointments**: Schedule appointments with date, time, and doctor information
5. **Add Visit Records**: Record patient visits with diagnosis, prescriptions, and notes
6. **View Messages**: Check and respond to patient messages
7. **Monitor Logs**: Review access logs for security monitoring

### For Patients

1. **First-Time Setup**:
   - Ask an admin to register you in the system
   - Go to `/patient/signup`
   - Enter your Patient ID (provided by admin)
   - Create a password
   
2. **Login**: Use your Patient ID and password at `/patient/login`

3. **View Records**: See your medical history, appointments, and prescriptions

4. **Book Appointments**: Schedule appointments with doctors

5. **Send Messages**: Communicate with healthcare staff

---

## Security Features

- **Password Hashing**: All passwords are hashed using Werkzeug's security functions
- **Session Management**: Secure session-based authentication
- **Rate Limiting**: Protection against brute force attacks (10 login attempts per minute)
- **Access Logs**: Comprehensive logging of all system access
- **IP Tracking**: Monitor access by IP address and location
- **Role-Based Access**: Separate admin and patient permissions

---

## Troubleshooting

### Google Sheets Connection Issues

**Problem**: `Google Sheets Connection Failed`

**Solutions**:
1. Verify that `patient-app-backend-b56334f48a1b.json` exists in the project root
2. Check that the service account email has Editor access to the spreadsheet
3. Ensure Google Sheets API and Google Drive API are enabled in Google Cloud Console
4. Verify the `SPREADSHEET_ID` environment variable is correct

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
```bash
pip install -r requirements.txt
```

### Port Already in Use

**Problem**: `Address already in use`

**Solution**:
```bash
# Find and kill the process using port 5000
# On Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# On macOS/Linux:
lsof -ti:5000 | xargs kill -9
```

### Environment Variables Not Loading

**Problem**: App can't find environment variables

**Solution**:
1. Install python-dotenv: `pip install python-dotenv`
2. Add to `app.py` at the top:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

### Session Errors

**Problem**: `RuntimeError: The session is unavailable because no secret key was set`

**Solution**: Set the `SECRET_KEY` environment variable

---

## Deployment

### Deploying to Heroku

1. **Create `Procfile`**:
   ```
   web: gunicorn app:app
   ```

2. **Add gunicorn to requirements.txt**:
   ```bash
   pip install gunicorn
   pip freeze > requirements.txt
   ```

3. **Set environment variables in Heroku**:
   ```bash
   heroku config:set SECRET_KEY=your_secret_key
   heroku config:set SPREADSHEET_ID=your_spreadsheet_id
   heroku config:set GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
   ```

### Deploying to Render/Railway

1. Connect your GitHub repository
2. Set environment variables in the dashboard
3. Deploy from main branch

---

## Additional Configuration

### Adding New Admin Users

Use the `add_user.py` script:
```bash
python add_user.py
```

Or manually add to the Google Sheet "Users" tab:
- Column A: username
- Column B: password_hash (use Werkzeug's `generate_password_hash`)
- Column C: role (e.g., "admin", "staff", "doctor")

### Customizing Rate Limits

Edit in `app.py`:
```python
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2000 per day", "500 per hour"],  # Modify these values
    storage_uri="memory://"
)
```

---

## Maintenance

### Regular Backups

1. **Download Google Sheet**: File → Download → Excel or CSV
2. **Automated Backups**: Use Google Sheets API to schedule backups
3. **Version History**: Google Sheets maintains version history automatically

### Monitoring

1. Check the **AccessLogs** sheet regularly for suspicious activity
2. Monitor the `/health` endpoint for application status
3. Review error logs in the console output

### Updates

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Support & Contact

- **Issues**: [GitHub Issues](https://github.com/prashantshirk/docentry/issues)
- **Documentation**: This README
- **Author**: prashantshirk

Remember to add me on insta hehe hehe 😄

---

## Changelog

### Version 2.0
- Added patient portal
- Implemented appointments and visits tracking
- Added messaging system
- Enhanced security with rate limiting
- Added access logs and monitoring

### Version 1.0
- Initial release
- Basic patient management
- Admin dashboard
- CSV export functionality

---

## FAQ

**Q: Can I use a different database instead of Google Sheets?**
A: Yes, you can modify the `SheetsClient` class to use PostgreSQL, MySQL, or MongoDB.

**Q: How many patients can the system handle?**
A: Google Sheets can handle up to 10 million cells. For larger deployments, consider migrating to a traditional database.

**Q: Is this HIPAA compliant?**
A: This is a basic implementation. For HIPAA compliance, additional security measures, encryption, and audit trails are required.

**Q: Can I customize the UI?**
A: Yes! Edit the HTML files in the `templates/` folder and CSS in `static/` folder.

---

## Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Repository cloned
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Google Cloud Project created
- [ ] Google Sheets API enabled
- [ ] Google Drive API enabled
- [ ] Service account created
- [ ] JSON credentials downloaded and renamed
- [ ] Google Spreadsheet created and named
- [ ] Spreadsheet shared with service account
- [ ] `.env` file created with SECRET_KEY and SPREADSHEET_ID
- [ ] Application started (`python app.py`)
- [ ] Accessed admin portal and logged in
- [ ] Changed default admin password

**Congratulations! Your Hospital Patient Management System is now ready to use! 🎉**
