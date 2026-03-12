# Hospital Patient Management System

## Overview

The Hospital Patient Management System is a web application designed to manage patient records efficiently. It allows users to add new patients, search for existing patients, and download patient records in CSV format. The application is built using Flask for the backend and HTML/CSS/JavaScript for the frontend.

## Features

- **Add New Patient**: Users can add new patient records by providing the patient's name, age, and problems.
- **Search Patient**: Users can search for a patient by their ID to view detailed information.
- **Download Patient Records**: Users can download the entire patient database as a CSV file.

## Setup Instructions

### Prerequisites

- Python 3.x
- Flask
- Pandas
- A web browser

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/prashantshirk/doc-entery.git
   cd doc-entery
   ```

2. **Install Dependencies**:
   Ensure you have `pip` installed, then run:
   ```bash
   pip install flask pandas
   ```

3. **Run the Application**:
   Start the Flask server by executing:
   ```bash
   python app.py
   ```
   The application will be accessible at `http://127.0.0.1:5000`.

### File Structure

- `app.py`: The main Flask application file handling routes and logic.
- `index.html`: The frontend HTML file for the user interface.
- `patients.csv`: The CSV file storing patient data.

## API Endpoints

- **`GET /`**: Renders the homepage of the application. Response: HTML page.
- **`POST /add_patient`**: Adds a new patient to the database. Request Body: JSON object containing `name`, `age`, and `problems`. Response: JSON object indicating success or failure.
- **`GET /get_patient/<int:patient_id>`**: Retrieves information for a specific patient by ID. Response: JSON object with patient details or an error message.
- **`GET /download_csv`**: Downloads the patient records as a CSV file. Response: CSV file download.

## Usage

1. **Add a New Patient**: Navigate to the "Add New Patient" section. Fill in the patient's name, age, and problems. Click "Add Patient" to save the record.
2. **Search for a Patient**: Navigate to the "Search Patient" section. Enter the patient ID and click "Search" to view details.
3. **Download Patient Records**: Click the "Download Patient Records" button to download the CSV file.

## Troubleshooting

- **Server Errors**: Check the console output for error messages.
- **CSV File Issues**: Ensure the `patients.csv` file is not open in another program when running the application.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License.
 remember to add me on insta hehe hehe 
