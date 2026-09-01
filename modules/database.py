"""
modules/database.py
-------------------
All MySQL logic is kept here so that app.py stays clean and simple.
Each function opens a connection, does one job, and closes the connection.
"""

import mysql.connector
import config


def get_connection():
    """Create and return a new MySQL connection."""
    return mysql.connector.connect(
    host=config.MYSQL_HOST,
    port=config.MYSQL_PORT,
    user=config.MYSQL_USER,
    password=config.MYSQL_PASSWORD,
    database=config.MYSQL_DB,
    ssl_disabled=False,
)


# ---------------------------------------------------------------
# USER FUNCTIONS
# ---------------------------------------------------------------
def create_user(name, email, password_hash):
    """Insert a new user. Returns True on success, False if email exists."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password_hash),
        )
        conn.commit()
        return True
    except mysql.connector.IntegrityError:
        # Duplicate email
        return False
    finally:
        cursor.close()
        conn.close()


def get_user_by_email(email):
    """Return a user row (dict) or None."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def get_user_by_id(user_id):
    """Return a user row (dict) by id or None."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


# ---------------------------------------------------------------
# RESUME FUNCTIONS
# ---------------------------------------------------------------
def save_resume(user_id, filename, resume_text):
    """Save an uploaded resume and its extracted text."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO resumes (user_id, filename, resume_text) VALUES (%s, %s, %s)",
        (user_id, filename, resume_text),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_latest_resume(user_id):
    """Return the most recently uploaded resume of a user, or None."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM resumes WHERE user_id = %s ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    resume = cursor.fetchone()
    cursor.close()
    conn.close()
    return resume


# ---------------------------------------------------------------
# CAREER TRACKER FUNCTIONS
# (Additive only — added for the Career Tracker dashboard feature.
#  Nothing above this line was changed.)
# ---------------------------------------------------------------

def save_selected_role(user_id, role_key, role_name):
    """Record the career role a user has chosen to track."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_career_role (user_id, role_key, role_name) VALUES (%s, %s, %s)",
        (user_id, role_key, role_name),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_selected_role(user_id):
    """Return the most recently selected role for a user, or None."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM user_career_role WHERE user_id = %s ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    role = cursor.fetchone()
    cursor.close()
    conn.close()
    return role


def save_quiz_attempt(user_id, role_key, skill_key, skill_name, score, total_questions, percentage):
    """Store one completed skill-assessment attempt."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO user_quiz_attempts
           (user_id, role_key, skill_key, skill_name, score, total_questions, percentage)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (user_id, role_key, skill_key, skill_name, score, total_questions, percentage),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_quiz_history(user_id, skill_key=None):
    """Return quiz attempts for a user, optionally filtered by skill, newest first."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if skill_key:
        cursor.execute(
            """SELECT * FROM user_quiz_attempts
               WHERE user_id = %s AND skill_key = %s
               ORDER BY taken_at DESC""",
            (user_id, skill_key),
        )
    else:
        cursor.execute(
            "SELECT * FROM user_quiz_attempts WHERE user_id = %s ORDER BY taken_at ASC",
            (user_id,),
        )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_latest_quiz_scores(user_id):
    """
    Return a dict {skill_key: latest attempt row} — the most recent
    attempt per skill for this user.
    """
    rows = get_quiz_history(user_id)
    latest = {}
    for row in rows:
        latest[row["skill_key"]] = row  # rows are ASC, so later ones overwrite
    return latest


def upsert_roadmap_progress(user_id, role_key, stage, skill_key, status):
    """Create or update the completion status of one roadmap skill item."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO user_roadmap_progress (user_id, role_key, stage, skill_key, status)
           VALUES (%s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE status = VALUES(status), stage = VALUES(stage)""",
        (user_id, role_key, stage, skill_key, status),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_roadmap_progress(user_id, role_key):
    """Return all roadmap progress rows for a user/role as a list of dicts."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM user_roadmap_progress WHERE user_id = %s AND role_key = %s",
        (user_id, role_key),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def save_roadmap_cache(user_id, role_key, roadmap_json):
    """Store (replace) the cached AI-generated roadmap for a user/role."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM user_roadmap_cache WHERE user_id = %s AND role_key = %s",
        (user_id, role_key),
    )
    cursor.execute(
        "INSERT INTO user_roadmap_cache (user_id, role_key, roadmap_json) VALUES (%s, %s, %s)",
        (user_id, role_key, roadmap_json),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_roadmap_cache(user_id, role_key):
    """Return the cached roadmap row for a user/role, or None."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT * FROM user_roadmap_cache
           WHERE user_id = %s AND role_key = %s
           ORDER BY id DESC LIMIT 1""",
        (user_id, role_key),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row
