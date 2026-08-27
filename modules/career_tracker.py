"""
modules/career_tracker.py
---------------------------
Business logic for the Career Tracker dashboard: skill-gap analysis,
readiness scoring, roadmap generation/caching, and quiz scoring.

Reuses the existing `database.py` connection helpers and the resume
text already stored via the existing resume upload flow. Does not
modify or call into modules/resume_parser.py's internal state, and
does not touch modules/ai_analysis.py.
"""

import json

from modules import database as db
from modules import career_data
from modules import career_ai
from modules import quiz_bank


def list_roles():
    """Return the full role catalog for the role picker UI."""
    return career_data.get_all_roles()


# Assessment-score classification bands used for the visible
# "Skill Comparison" panel (Career Tracker requirement #4). This is
# the single source of truth for those thresholds — change them here
# only.
def _classify_percentage(percentage):
    """80-100 -> strength, 60-79 -> needs_improvement, 0-59 -> skill_gap."""
    if percentage >= 80:
        return "strength"
    if percentage >= 60:
        return "needs_improvement"
    return "skill_gap"


def analyze_role_fit(role_key, resume_text, user_id):
    """
    Compare a user's resume/assessment record against a target role's
    required skills.

    Returns None if the role_key is unknown, otherwise:
    {
        "role": {...},
        "strengths": [ {key, name, weight}, ... ],   # present in resume (roadmap input)
        "gaps":      [ {key, name, weight}, ... ],   # missing entirely (roadmap input)
        "improve":   [ {key, name, weight, percentage}, ... ],  # roadmap input
        "readiness_pct": int,          # driven ONLY by actual assessment results
        "skill_coverage_pct": int,     # informational: resume keyword coverage
        "skill_status": {              # the live "Skill Comparison" panel data
            "strength":          [ {key, name, weight, percentage}, ... ],  # 80-100%
            "needs_improvement": [ {key, name, weight, percentage}, ... ],  # 60-79%
            "skill_gap":         [ {key, name, weight, percentage}, ... ],  # 0-59%
            "not_assessed":      [ {key, name, weight, percentage: None}, ... ],
        },
    }

    `strengths` / `gaps` / `improve` above are resume-keyword based and
    exist only to seed the initial AI roadmap content (so a brand-new
    role selection still gets a useful roadmap before any assessment
    has been taken). `skill_status` is assessment-score based only,
    per the exact 80/60/0 thresholds, and is what the Skill Comparison
    UI renders — it updates live as assessments are submitted.
    """
    role = career_data.get_role(role_key)
    if not role:
        return None

    detected = career_data.detect_skills_in_text(resume_text or "")
    latest_scores = db.get_latest_quiz_scores(user_id) if user_id else {}

    strengths, gaps, improve = [], [], []
    matched_weight = 0
    total_weight = 0

    skill_status = {
        "strength": [],
        "needs_improvement": [],
        "skill_gap": [],
        "not_assessed": [],
    }
    assessed_weight_score = 0  # sum(weight * percentage/100) for readiness

    for skill in role["skills"]:
        key = skill["key"]
        weight = skill["weight"]
        total_weight += weight
        display_name = career_data.get_skill_display_name(key)

        is_present = key in detected
        attempt = latest_scores.get(key)

        # ---- Resume-based buckets (roadmap-generation input only) ----
        if is_present:
            matched_weight += weight
            if attempt is not None:
                percentage = float(attempt["percentage"])
                if percentage >= 70:
                    strengths.append({"key": key, "name": display_name, "weight": weight, "percentage": percentage})
                else:
                    improve.append({"key": key, "name": display_name, "weight": weight, "percentage": percentage})
            else:
                # Mentioned in the resume, but never verified with an
                # assessment — don't assume it's a strength until the
                # user is actually tested on it.
                improve.append({
                    "key": key, "name": display_name, "weight": weight,
                    "percentage": None, "needs_assessment": True,
                })
        else:
            gaps.append({"key": key, "name": display_name, "weight": weight})

        # ---- Assessment-based skill_status (Skill Comparison panel) ----
        if attempt is not None:
            percentage = float(attempt["percentage"])
            bucket = _classify_percentage(percentage)
            skill_status[bucket].append({
                "key": key, "name": display_name, "weight": weight, "percentage": percentage,
            })
            assessed_weight_score += weight * (percentage / 100.0)
        else:
            skill_status["not_assessed"].append({
                "key": key, "name": display_name, "weight": weight, "percentage": None,
            })

    # Sort every bucket by weight (highest priority first)
    strengths.sort(key=lambda s: -s["weight"])
    gaps.sort(key=lambda s: -s["weight"])
    improve.sort(key=lambda s: -s["weight"])
    for bucket in skill_status.values():
        bucket.sort(key=lambda s: -s["weight"])

    skill_coverage_pct = round((matched_weight / total_weight) * 100) if total_weight else 0

    # Career Readiness reflects ACTUAL assessment results only (per
    # requirement #6): a skill with no assessment contributes 0 toward
    # readiness until the user proves it, weighted by the skill's
    # importance to the role. This is intentionally independent of the
    # resume-keyword coverage above.
    readiness_pct = round((assessed_weight_score / total_weight) * 100) if total_weight else 0

    return {
        "role": role,
        "strengths": strengths,
        "gaps": gaps,
        "improve": improve,
        "readiness_pct": readiness_pct,
        "skill_coverage_pct": skill_coverage_pct,
        "skill_status": skill_status,
    }


def select_role(user_id, role_key):
    """Persist the user's chosen target role."""
    role = career_data.get_role(role_key)
    if not role:
        return False
    db.save_selected_role(user_id, role_key, role["name"])
    return True


def _key_by_display_name():
    """Reverse lookup: display name -> skill key."""
    return {
        career_data.get_skill_display_name(k): k for k in career_data.SKILL_DISPLAY_NAMES
    }


def _attach_resources(roadmap):
    """
    Add up to 3 curated, verified learning resources to each roadmap
    item (matched by skill name -> skill key). Applied at read-time
    so it also enriches roadmaps that were cached before resources
    existed, without needing to regenerate them.
    """
    key_by_name = _key_by_display_name()
    for stage_name in ("beginner", "intermediate", "advanced"):
        for item in roadmap.get(stage_name, []):
            skill_key = key_by_name.get(item.get("skill"))
            item["resources"] = career_data.get_skill_resources(skill_key) if skill_key else []
    return roadmap


def get_or_generate_roadmap(user_id, role_key, gap_analysis, resume_text, force_regenerate=False):
    """
    Return the roadmap dict for a user/role, using the cached version
    unless force_regenerate is True (used on "Reassess" after a user
    completes learning stages).
    """
    if not force_regenerate:
        cached = db.get_roadmap_cache(user_id, role_key)
        if cached and cached.get("roadmap_json"):
            try:
                return _attach_resources(json.loads(cached["roadmap_json"]))
            except (ValueError, TypeError):
                pass  # fall through and regenerate

    strengths = [s["name"] for s in gap_analysis["strengths"]]
    gaps = [g["name"] for g in gap_analysis["gaps"]]
    improve = [i["name"] for i in gap_analysis["improve"]]

    roadmap = career_ai.generate_roadmap(
        gap_analysis["role"]["name"], strengths, gaps, improve, resume_text or ""
    )

    db.save_roadmap_cache(user_id, role_key, json.dumps(roadmap))

    # Seed roadmap progress rows (pending) for any new skills so the
    # progress tracker has something to show immediately.
    existing_progress = {
        row["skill_key"] for row in db.get_roadmap_progress(user_id, role_key)
    }
    key_by_name = _key_by_display_name()
    for stage_name in ("beginner", "intermediate", "advanced"):
        for item in roadmap.get(stage_name, []):
            skill_key = key_by_name.get(item.get("skill"), item.get("skill", "")[:100])
            if skill_key not in existing_progress:
                db.upsert_roadmap_progress(user_id, role_key, stage_name, skill_key, "pending")

    return _attach_resources(roadmap)


def get_roadmap_progress_map(user_id, role_key):
    """Return {skill_key: status} for a user/role."""
    rows = db.get_roadmap_progress(user_id, role_key)
    return {row["skill_key"]: row["status"] for row in rows}


def mark_roadmap_status(user_id, role_key, stage, skill_key, status):
    """Manually mark a roadmap item's status (pending/in_progress/completed)."""
    if status not in ("pending", "in_progress", "completed"):
        return False
    db.upsert_roadmap_progress(user_id, role_key, stage, skill_key, status)
    return True


def get_quiz_for_skill(skill_key):
    """Return quiz questions for a skill, with correct answers stripped."""
    questions = quiz_bank.get_quiz(skill_key)
    safe_questions = []
    for i, q in enumerate(questions):
        safe_questions.append({
            "index": i,
            "question": q["question"],
            "options": q["options"],
        })
    return safe_questions


def score_quiz(skill_key, answers):
    """
    Score a submitted quiz.
    `answers` is a dict/list mapping question index -> selected option index.
    Returns (score, total, percentage, feedback_list) or None if no quiz exists.
    """
    questions = quiz_bank.get_quiz(skill_key)
    if not questions:
        return None

    score = 0
    feedback = []

    for i, q in enumerate(questions):
        selected = answers.get(str(i), answers.get(i, None)) if isinstance(answers, dict) else None
        correct = q["correct_index"]
        is_correct = (selected == correct)
        if is_correct:
            score += 1
        feedback.append({
            "question": q["question"],
            "selected_index": selected,
            "correct_index": correct,
            "correct_option": q["options"][correct],
            "is_correct": is_correct,
        })

    total = len(questions)
    percentage = round((score / total) * 100, 2) if total else 0
    return score, total, percentage, feedback


def record_quiz_result(user_id, role_key, skill_key, score, total, percentage):
    """Persist a quiz attempt and auto-update roadmap progress."""
    skill_name = career_data.get_skill_display_name(skill_key)
    db.save_quiz_attempt(user_id, role_key, skill_key, skill_name, score, total, percentage)

    # A "Strength"-level score (>=80%, matching the Skill Comparison
    # threshold) marks the related roadmap item complete; anything
    # lower marks it in-progress so it stays visible as a focus area.
    progress_rows = db.get_roadmap_progress(user_id, role_key)
    for row in progress_rows:
        if row["skill_key"] == skill_key:
            new_status = "completed" if percentage >= 80 else "in_progress"
            db.upsert_roadmap_progress(user_id, role_key, row["stage"], skill_key, new_status)


def get_readiness_trend(user_id):
    """
    Return a simple time-ordered list of quiz attempts
    [{taken_at, skill_name, percentage}, ...] for the progress chart.
    """
    rows = db.get_quiz_history(user_id)
    return [
        {
            "taken_at": row["taken_at"].isoformat() if hasattr(row["taken_at"], "isoformat") else str(row["taken_at"]),
            "skill_name": row["skill_name"],
            "percentage": float(row["percentage"]),
        }
        for row in rows
    ]
