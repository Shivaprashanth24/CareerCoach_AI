"""
modules/career_ai.py
----------------------
AI-powered roadmap generation for the Career Tracker dashboard.

This is intentionally kept separate from modules/ai_analysis.py so
the existing resume career-recommendation feature and chatbot are
never touched. It reuses the same Gemini client setup/pattern.
"""

import json
import re
import time

from google import genai

import config

# Separate client instance from ai_analysis.py, same configuration.
_client = genai.Client(api_key=config.GEMINI_API_KEY)


def _ask_gemini(prompt):
    """Send a prompt to Gemini and return the raw text response."""

    if not config.GEMINI_API_KEY:
        return None

    models_to_try = [config.GEMINI_MODEL, "gemini-3.5-flash"]

    for model in models_to_try:
        for attempt in range(3):
            try:
                response = _client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                return response.text
            except Exception as error:
                error_text = str(error)
                is_quota_error = (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                    or "quota" in error_text.lower()
                )
                if is_quota_error:
                    # Quota exceeded — retrying the same model won't
                    # help right now. Skip straight to the next model
                    # (if any) instead of burning more of the quota,
                    # and fall back to the deterministic roadmap if
                    # every model is exhausted.
                    break
                if "503" in error_text or "UNAVAILABLE" in error_text:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    break
                # Unknown error — don't keep hammering this model either.
                break
    return None


def _extract_json(text):
    """Pull the first {...} JSON object out of a model response."""
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return None


def generate_roadmap(role_name, strengths, gaps, improve, resume_text):
    """
    Ask Gemini for a Beginner -> Intermediate -> Advanced roadmap
    focused on closing the given skill gaps for the target role.

    Returns a dict:
    {
        "beginner":     [{"skill": str, "focus": str, "practice": str}, ...],
        "intermediate": [...],
        "advanced":     [...]
    }
    Falls back to a deterministic structure (built only from the real
    gap list, no invented skills) if the AI call or JSON parsing fails.
    """

    strengths_text = ", ".join(strengths) if strengths else "None detected yet"
    gaps_text = ", ".join(gaps) if gaps else "None — all core skills detected"
    improve_text = ", ".join(improve) if improve else "None"

    prompt = f"""
You are CareerCoach AI, generating a personalized learning roadmap.

Target role: {role_name}

Candidate's current strengths (skills already present): {strengths_text}
Candidate's missing skills (skill gaps to close): {gaps_text}
Skills the candidate has but scored low on in assessments: {improve_text}

Resume summary:
{resume_text[:1500]}

Return ONLY a single valid JSON object (no markdown, no commentary) in
exactly this shape:

{{
  "beginner": [
    {{"skill": "skill name", "focus": "what to learn and why, 1-2 sentences", "practice": "one small practical exercise"}}
  ],
  "intermediate": [
    {{"skill": "skill name", "focus": "...", "practice": "..."}}
  ],
  "advanced": [
    {{"skill": "skill name", "focus": "...", "practice": "..."}}
  ]
}}

Rules:
- Only include skills from the candidate's missing skills or low-scoring skills listed above — do not invent unrelated skills.
- Order beginner -> intermediate -> advanced by logical learning progression.
- Keep each "focus" and "practice" to one short sentence.
- If there are very few gaps, it is fine for a stage to have 1 item or be an empty list.
- Output must be valid JSON only.
"""

    raw = _ask_gemini(prompt)
    parsed = _extract_json(raw)

    if parsed and all(k in parsed for k in ("beginner", "intermediate", "advanced")):
        return parsed

    # ---- Deterministic fallback (no AI call succeeded) -------------
    # Split the real gap list evenly across the three stages so the
    # roadmap still reflects only the user's actual missing skills.
    ordered_gaps = gaps if gaps else improve
    stages = {"beginner": [], "intermediate": [], "advanced": []}
    stage_names = ["beginner", "intermediate", "advanced"]

    for index, skill_name in enumerate(ordered_gaps):
        stage = stage_names[min(index // max(1, -(-len(ordered_gaps) // 3)), 2)]
        stages[stage].append({
            "skill": skill_name,
            "focus": f"Build a working understanding of {skill_name}.",
            "practice": f"Complete one small hands-on exercise using {skill_name}.",
        })

    return stages
