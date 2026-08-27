# CareerCoach AI

A simple full-stack AI career guidance web app (capstone project).

**Stack:** Flask · MySQL · Bootstrap 5 · Chart.js · Google Gemini API · pdfplumber

## Features
1. Home page (landing)
2. Registration (stored in MySQL, hashed passwords)
3. Login / Logout (session based, no JWT)
4. Dashboard with Bootstrap cards
5. Resume upload (PDF / DOCX -> `uploads/`)
6. Resume analysis (Skills, Education, Projects, Experience, Certifications + chart)
7. Career recommendation using Gemini
8. AI career chatbot
9. Profile page

## Setup (5 steps)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create the database
mysql -u root -p < database/schema.sql

# 3. Edit config.py
#    MYSQL_PASSWORD = "your mysql password"
#    GEMINI_API_KEY = "your gemini api key"   (https://aistudio.google.com/apikey)

# 4. Run the app
python app.py

# 5. Open http://127.0.0.1:5000
```

## Folder structure
```
CareerCoach_AI/
├── app.py               # all Flask routes
├── config.py            # settings (MySQL + Gemini key)
├── requirements.txt
├── database/schema.sql  # MySQL tables
├── modules/
│   ├── database.py      # MySQL queries
│   ├── resume_parser.py # PDF/DOCX text + section extraction
│   └── ai_analysis.py   # Gemini API calls
├── templates/           # Jinja2 HTML pages
├── static/css|js|images
└── uploads/             # uploaded resumes
```

## Flow
Home → Register → Login → Dashboard → Upload Resume → Analysis → Career Recommendation → Chatbot → Profile
