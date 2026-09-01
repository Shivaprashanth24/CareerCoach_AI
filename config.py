""" 
config.py
---------
All configuration values for CareerCoach AI live here.
Set the required configuration values in the local .env file. Never commit .env to GitHub.
"""

import os

from dotenv import load_dotenv

load_dotenv()
# ---------------- Flask ----------------
SECRET_KEY = os.getenv("SECRET_KEY", "")

# ---------------- MySQL ----------------
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "careercoach_ai")

# ---------------- Gemini AI ----------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.6-flash"

# ---------------- File uploads ----------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB limit
