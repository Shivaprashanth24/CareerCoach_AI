"""
app.py
------
Main Flask application for CareerCoach AI.

Project flow:
Home -> Register -> Login -> Dashboard -> Upload Resume
     -> Resume Analysis -> Career Recommendation -> Chatbot -> Profile

Run with:  python app.py
"""

import os
import markdown
import re
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, Response
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import config
from modules import database as db
from modules import resume_parser
from modules import ai_analysis
from modules import career_tracker

# ---------------------------------------------------------------
# APP SETUP
# ---------------------------------------------------------------
app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

# Make sure the uploads folder exists
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)


def login_required(view):
    """Simple decorator: send guests to the login page."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def allowed_file(filename):
    """Only allow PDF and DOCX uploads."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )


# ---------------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------
# REGISTRATION
# ---------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # 1. Validate empty fields
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        # 2. Save user with a hashed password
        created = db.create_user(name, email, generate_password_hash(password))
        if not created:
            flash("This email is already registered.", "danger")
            return render_template("register.html")

        flash("Registration Successful", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------------------------------------------------------
# LOGIN / LOGOUT
# ---------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.get_user_by_email(email)
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    resume = db.get_latest_resume(session["user_id"])
    return render_template("dashboard.html", resume=resume)


# ---------------------------------------------------------------
# RESUME UPLOAD
# ---------------------------------------------------------------
@app.route("/upload-resume", methods=["GET", "POST"])
@login_required
def upload_resume():
    if request.method == "POST":
        file = request.files.get("resume")

        if not file or file.filename == "":
            flash("Please choose a file.", "danger")
            return render_template("upload_resume.html")

        if not allowed_file(file.filename):
            flash("Only PDF and DOCX files are allowed.", "danger")
            return render_template("upload_resume.html")

        # 1. Save the file inside the uploads folder
        filename = f"{session['user_id']}_{secure_filename(file.filename)}"
        filepath = os.path.join(config.UPLOAD_FOLDER, filename)
        file.save(filepath)

        # 2. Extract the text and store everything in MySQL
        text = resume_parser.extract_text(filepath)
        db.save_resume(session["user_id"], filename, text)

        flash("Resume Uploaded Successfully", "success")
        return redirect(url_for("analysis"))

    return render_template("upload_resume.html")


# ---------------------------------------------------------------
# RESUME ANALYSIS + CAREER RECOMMENDATION
# ---------------------------------------------------------------
@app.route("/analysis")
@login_required
def analysis():

    resume = db.get_latest_resume(session["user_id"])

    # -----------------------------------------------------------
    # No resume uploaded
    # -----------------------------------------------------------
    if not resume:
        return redirect(url_for("upload_resume"))

    # -----------------------------------------------------------
    # Get the stored filename
    #
    # Different database versions may use different names,
    # so we safely check all common possibilities.
    # -----------------------------------------------------------
    filename = (
        resume.get("filename")
        or resume.get("file_name")
        or resume.get("resume_filename")
        or resume.get("file")
        or resume.get("resume_file")
    )

    # -----------------------------------------------------------
    # If database already stores a full path, use it
    # -----------------------------------------------------------
    filepath = (
        resume.get("file_path")
        or resume.get("filepath")
        or resume.get("path")
    )

    # -----------------------------------------------------------
    # Otherwise rebuild the path from the stored filename
    # -----------------------------------------------------------
    if not filepath and filename:

        filepath = os.path.join(
            config.UPLOAD_FOLDER,
            filename
        )

    # -----------------------------------------------------------
    # Final safety check
    # -----------------------------------------------------------
    if not filepath:

        return """
        <h3>Resume file path could not be determined.</h3>
        <p>Please upload the resume again.</p>
        """

    # -----------------------------------------------------------
    # Make sure the file actually exists
    # -----------------------------------------------------------
    if not os.path.exists(filepath):

        return f"""
        <h3>Resume file not found.</h3>

        <p>
            The application knows about the resume,
            but the actual file could not be found.
        </p>

        <p>
            Please upload the resume again.
        </p>
        """

    # -----------------------------------------------------------
    # Analyze the resume
    # -----------------------------------------------------------
    resume_data = resume_parser.analyze_resume(
        filepath
    )

    text = resume_data.get(
        "text",
        ""
    )

    sections = resume_data.get(
        "sections",
        {}
    )

    personal = resume_data.get(
        "personal",
        {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
        }
    )

    skills = resume_data.get(
        "skills",
        []
    )

    projects = resume_data.get(
        "projects",
        []
    )

    experience = resume_data.get(
        "experience",
        []
    )

    education = resume_data.get(
        "education",
        []
    )

    certifications = resume_data.get(
        "certifications",
        []
    )

    extra_curricular = resume_data.get(
        "extra_curricular",
        []
    )

    # -----------------------------------------------------------
    # Render analysis page
    # -----------------------------------------------------------
    # Name -> role_key map for the existing Career Tracker roles, so
    # the recommendation text can link a mentioned role straight into
    # "Confirm & Start Tracking" there. Reuses the same role catalog —
    # no duplicate data.
    career_roles_map = {r["name"]: r["role_key"] for r in career_tracker.list_roles()}

    return render_template(
        "analysis.html",

        personal=personal,

        sections=sections,

        skills=skills,

        projects=projects,

        experience=experience,

        education=education,

        certifications=certifications,

        extra_curricular=extra_curricular,

        resume_text=text,

        career_roles_map=career_roles_map
    )

@app.route("/api/recommendation")
@login_required
def api_recommendation():

    resume = db.get_latest_resume(session["user_id"])

    if not resume:
        return jsonify({
            "reply": "No resume found. Please upload one first."
        })

    text = resume.get("resume_text") or ""

    if not text.strip():
        return jsonify({
            "reply": "No resume text was found."
        })

    skills = resume_parser.find_skills(text)

    recommendation = ai_analysis.career_recommendation(
        skills,
        text
    )

    recommendation_html = markdown.markdown(
        recommendation,
        extensions=["extra"]
    )

    return jsonify({
        "reply": recommendation_html
    })


# ---------------------------------------------------------------
# AI CHATBOT
# ---------------------------------------------------------------

# Cap how many past turns we keep in the session, so the conversation
# stays context-aware without letting the cookie-based session grow
# without bound. 16 entries = 8 student/bot exchanges.
CHAT_HISTORY_LIMIT = 16


@app.route("/chatbot")
@login_required
def chatbot():
    # Each fresh visit to the chat page starts a new conversation, since
    # the chat window itself only ever shows the greeting on load.
    session["chat_history"] = []

    resume = db.get_latest_resume(session["user_id"])
    resume_text = (resume.get("resume_text") if resume else "") or ""

    selected_role = db.get_selected_role(session["user_id"])
    target_role = selected_role.get("role_name") if selected_role else None
    career_interests = session.get("career_interests", "")
    user_name = (session.get("user_name") or "").split(" ")[0]

    if resume_text.strip():
        intro_message = (
            f"Hi{', ' + user_name if user_name else ''}! I've reviewed your resume. "
            "Ask me a career question, or say \"assess my skills\" and I'll test you "
            "one question at a time."
        )
    else:
        intro_message = (
            f"Hi{', ' + user_name if user_name else ''}! I am CareerCoach AI. "
            "Ask me something like \"What skills should I learn?\", or upload your "
            "resume first so I can personalize things."
        )

    return render_template(
        "chatbot.html",
        intro_message=intro_message,
        target_role=target_role,
        career_interests=career_interests,
    )


@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    """Receive a question from the chat page and reply using Gemini,
    keeping the reply grounded in the running conversation so far."""

    data = request.json or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"reply": "Please type a question."})

    # Career interests are optional free text the user can set once; keep
    # using the last value they gave for the rest of the session unless
    # they send a new one.
    interests = (data.get("interests") or "").strip()
    if interests:
        session["career_interests"] = interests[:300]
    interests = session.get("career_interests", "")

    resume = db.get_latest_resume(session["user_id"])
    resume_text = (resume.get("resume_text") if resume else "") or ""
    skills = resume_parser.find_skills(resume_text) if resume_text.strip() else []

    selected_role = db.get_selected_role(session["user_id"])
    target_role = selected_role.get("role_name") if selected_role else None

    history = session.get("chat_history", [])

    reply = ai_analysis.chatbot_reply(
        question,
        resume_text,
        skills=skills,
        target_role=target_role,
        history=history,
        interests=interests,
    )

    # Keep the running conversation in the session (plain text, not the
    # rendered HTML) so the next turn can build on it.
    history.append({"role": "user", "text": question[:1000]})
    history.append({"role": "assistant", "text": reply[:1500]})
    session["chat_history"] = history[-CHAT_HISTORY_LIMIT:]

    reply_html = markdown.markdown(reply, extensions=["extra"])

    return jsonify({"reply": reply_html})

# ---------------------------------------------------------------
# PROFILE
# ---------------------------------------------------------------
@app.route("/profile")
@login_required
def profile():
    user = db.get_user_by_id(session["user_id"])
    resume = db.get_latest_resume(session["user_id"])
    return render_template("profile.html", user=user, resume=resume)


# ---------------------------------------------------------------
# CAREER TRACKER DASHBOARD
# (New feature, added on top of the existing app. Does not modify
#  any route above this point.)
# ---------------------------------------------------------------

def _get_resume_text_for_user():
    """Small shared helper: latest resume text for the logged-in user, or ''."""
    resume = db.get_latest_resume(session["user_id"])
    return (resume.get("resume_text") if resume else "") or ""


@app.route("/career-dashboard")
@login_required
def career_dashboard():
    user_id = session["user_id"]
    resume_text = _get_resume_text_for_user()

    roles = career_tracker.list_roles()
    selected = db.get_selected_role(user_id)
    selected_role_key = selected["role_key"] if selected else None

    # Optional deep link from the Career Recommendation page
    # ("/career-dashboard?role=data_engineer"). This only pre-highlights
    # that role in the picker and enables "Confirm & Start Tracking" —
    # it never triggers gap analysis/roadmap generation on its own.
    # That only happens once the user explicitly confirms.
    valid_role_keys = {r["role_key"] for r in roles}
    requested_role_key = (request.args.get("role") or "").strip().lower()
    preselect_role_key = selected_role_key or (
        requested_role_key if requested_role_key in valid_role_keys else None
    )

    gap_analysis = None
    roadmap = None
    progress_map = {}
    quiz_history = []

    if selected_role_key:
        gap_analysis = career_tracker.analyze_role_fit(selected_role_key, resume_text, user_id)
        if gap_analysis:
            roadmap = career_tracker.get_or_generate_roadmap(
                user_id, selected_role_key, gap_analysis, resume_text
            )
            progress_map = career_tracker.get_roadmap_progress_map(user_id, selected_role_key)
        quiz_history = db.get_quiz_history(user_id)

    return render_template(
        "career_dashboard.html",
        roles=roles,
        selected_role_key=selected_role_key,
        preselect_role_key=preselect_role_key,
        gap_analysis=gap_analysis,
        roadmap=roadmap,
        progress_map=progress_map,
        quiz_history=quiz_history,
        has_resume=bool(resume_text.strip()),
        available_quiz_skills=career_tracker.quiz_bank.get_available_skill_keys(),
        skill_name_to_key={
            v: k for k, v in career_tracker.career_data.SKILL_DISPLAY_NAMES.items()
        },
    )


@app.route("/api/career/select-role", methods=["POST"])
@login_required
def api_career_select_role():
    data = request.json or {}
    role_key = (data.get("role_key") or "").strip()

    ok = career_tracker.select_role(session["user_id"], role_key)
    if not ok:
        return jsonify({"error": "Unknown role."}), 400

    resume_text = _get_resume_text_for_user()
    gap_analysis = career_tracker.analyze_role_fit(role_key, resume_text, session["user_id"])
    roadmap = career_tracker.get_or_generate_roadmap(
        session["user_id"], role_key, gap_analysis, resume_text
    )

    return jsonify({
        "gap_analysis": gap_analysis,
        "roadmap": roadmap,
    })


@app.route("/api/career/roadmap/regenerate", methods=["POST"])
@login_required
def api_career_regenerate_roadmap():
    data = request.json or {}
    role_key = (data.get("role_key") or "").strip()

    resume_text = _get_resume_text_for_user()
    gap_analysis = career_tracker.analyze_role_fit(role_key, resume_text, session["user_id"])
    if not gap_analysis:
        return jsonify({"error": "Unknown role."}), 400

    roadmap = career_tracker.get_or_generate_roadmap(
        session["user_id"], role_key, gap_analysis, resume_text, force_regenerate=True
    )

    return jsonify({"gap_analysis": gap_analysis, "roadmap": roadmap})


@app.route("/api/career/quiz/<skill_key>")
@login_required
def api_career_quiz(skill_key):
    questions = career_tracker.get_quiz_for_skill(skill_key)
    if not questions:
        return jsonify({"error": "No assessment available for this skill yet."}), 404
    return jsonify({
        "skill_key": skill_key,
        "skill_name": career_tracker.career_data.get_skill_display_name(skill_key),
        "questions": questions,
    })


@app.route("/api/career/quiz/<skill_key>/submit", methods=["POST"])
@login_required
def api_career_quiz_submit(skill_key):
    data = request.json or {}
    role_key = (data.get("role_key") or "").strip()
    answers = data.get("answers") or {}

    result = career_tracker.score_quiz(skill_key, answers)
    if result is None:
        return jsonify({"error": "No assessment available for this skill."}), 404

    score, total, percentage, feedback = result

    if role_key:
        career_tracker.record_quiz_result(
            session["user_id"], role_key, skill_key, score, total, percentage
        )

    return jsonify({
        "score": score,
        "total": total,
        "percentage": percentage,
        "feedback": feedback,
    })


@app.route("/api/career/refresh")
@login_required
def api_career_refresh():
    """
    Cheap re-read of the current gap analysis + roadmap progress for
    the user's already-selected role — used after a quiz submission
    or a status change so Skill Comparison / Career Readiness update
    immediately. Never touches the roadmap cache and never calls
    Gemini, so it's safe to call as often as the UI needs to.
    """
    selected = db.get_selected_role(session["user_id"])
    if not selected:
        return jsonify({"error": "No role selected."}), 400

    role_key = selected["role_key"]
    resume_text = _get_resume_text_for_user()
    gap_analysis = career_tracker.analyze_role_fit(role_key, resume_text, session["user_id"])
    progress_map = career_tracker.get_roadmap_progress_map(session["user_id"], role_key)

    return jsonify({"gap_analysis": gap_analysis, "progress_map": progress_map})


@app.route("/api/career/roadmap/status", methods=["POST"])
@login_required
def api_career_roadmap_status():
    data = request.json or {}
    role_key = (data.get("role_key") or "").strip()
    stage = (data.get("stage") or "").strip()
    skill_key = (data.get("skill_key") or "").strip()
    status = (data.get("status") or "").strip()

    ok = career_tracker.mark_roadmap_status(session["user_id"], role_key, stage, skill_key, status)
    if not ok:
        return jsonify({"error": "Invalid status."}), 400
    return jsonify({"ok": True})


@app.route("/api/career/progress")
@login_required
def api_career_progress():
    trend = career_tracker.get_readiness_trend(session["user_id"])
    return jsonify({"trend": trend})


# ---------------------------------------------------------------
# START THE SERVER
# ---------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
