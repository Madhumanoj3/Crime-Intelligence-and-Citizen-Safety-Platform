# Crime Intelligence and Citizen Safety Platform

## About the Project

The Crime Intelligence and Citizen Safety Platform is a web-based application developed to make crime reporting and complaint management easier for citizens and police authorities.

The platform allows citizens to register complaints, track their status, access emergency SOS services, and view community alerts. It also provides crime intelligence features to identify duplicate complaints and analyze crime hotspots.

## Objectives

- Provide an easy way for citizens to report complaints.
- Improve transparency through complaint tracking.
- Help police authorities manage and monitor complaints.
- Identify duplicate complaints using text similarity techniques.
- Analyze crime locations to identify hotspot areas.
- Improve communication between citizens and police authorities.

## Technologies Used

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Django |
| Database | PostgreSQL |
| Machine Learning | Python |
| Duplicate Detection | TF-IDF and Cosine Similarity |
| Hotspot Analysis | K-Means Clustering |
| Map Visualization | Leaflet |
| Development Tool | Visual Studio Code |

## Main Modules

### 1. Citizen Module
- User registration and login.
- Complaint registration and tracking.
- Emergency SOS feature.
- Viewing community alerts.
- Providing feedback.

### 2. Inspector Module
- Reviewing submitted complaints.
- Identifying duplicate complaints.
- Assigning complaints to police officers.
- Monitoring investigation progress.

### 3. Police Officer Module
- Viewing assigned complaints.
- Managing case details.
- Updating investigation progress.
- Maintaining evidence and accused details.

### 4. Admin Module
- Managing users and police officers.
- Managing police station details.
- Managing community alerts.
- Maintaining system information.

### 5. Crime Intelligence Module
- Identifies potentially duplicate complaints using TF-IDF and Cosine Similarity.
- Analyzes crime location data using K-Means Clustering.
- Displays geographical complaint patterns through map visualization.

## System Requirements

- Python
- PostgreSQL
- Visual Studio Code
- Modern Web Browser
- Required Python packages

## Installation and Execution

1. Clone the repository:

   ```bash
   git clone https://github.com/Madhumanoj3/REPOSITORY-NAME.git
   ```

2. Navigate to the project directory:

   ```bash
   cd REPOSITORY-NAME
   ```

3. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure the PostgreSQL database connection in the Django settings.

5. Apply database migrations:

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Start the Django development server:

   ```bash
   python manage.py runserver
   ```

7. Open the application in your browser:

   ```text
   http://127.0.0.1:8000/
   ```

## Project Outcomes

- Simplifies the complaint registration process for citizens.
- Provides a centralized platform for complaint management.
- Helps identify potentially duplicate complaints.
- Supports geographical analysis of reported crime locations.
- Improves coordination between inspectors and police officers.

## Future Enhancements

- Integration with official crime databases.
- Real-time crime data analysis.
- Improved emergency notification services.
- Advanced crime prediction techniques.
- Mobile application support.

## Project Team

**Crime Intelligence and Citizen Safety Platform**

Developed by:

- Madhumanoj A (24BCS048)
- Mana Kabesvaran S (24BCS049)

**Department of Computer Science and Engineering**  
Mepco Schlenk Engineering College (Autonomous), Sivakasi.

---

*This project is developed as part of the academic mini-project.*
