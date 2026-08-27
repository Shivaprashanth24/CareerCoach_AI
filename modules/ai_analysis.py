"""
AI analysis and career guidance for CareerCoach AI.
Uses Google's Gemini API.
"""

from google import genai
import config
import time


# Create Gemini client
client = genai.Client(api_key=config.GEMINI_API_KEY)

def ask_gemini(prompt):
    """Send a prompt to Gemini and return the text response."""

    if not config.GEMINI_API_KEY:
        return "Gemini API key is not configured. Please add it in config.py."

    models_to_try = [
        config.GEMINI_MODEL,
        "gemini-3.5-flash"
    ]

    for model in models_to_try:

        for attempt in range(3):

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                return response.text

            except Exception as error:

                error_text = str(error)

                # Retry temporary Gemini server problems
                if "503" in error_text or "UNAVAILABLE" in error_text:

                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue

                    # After 3 attempts, try the fallback model
                    break

                # Other errors should not be retried
                return f"Could not reach the AI service: {error}"

    return (
        "Gemini is temporarily unavailable. "
        "Please try again in a few moments."
    )


def career_recommendation(skills, resume_text):
    prompt = f"""
You are CareerCoach AI, a professional and friendly career guidance assistant.

Analyze the student's resume and provide clear, practical career guidance.

Skills found in the resume:
{", ".join(skills) if skills else "Not detected"}

Resume text:
{resume_text[:2500]}

Give the response in the following exact structure:

🎯 RECOMMENDED CAREER
- Mention the most suitable career role based on the resume.
- Give one short reason.

💼 BEST CAREER ROLES
- Role 1
- Role 2
- Role 3

📚 MISSING SKILLS
- Skill 1
- Skill 2
- Skill 3
- Skill 4

🗺️ LEARNING ROADMAP

For each roadmap step, provide the following:

STEP 1: [Skill/Technology]
What to learn:
- Mention the important concepts the fresher should learn.

🌐 Recommended Learning Resources:

- Resource Name | Complete URL
- Resource Name | Complete URL

Rules:
- Recommend 2 useful resources for this step.
- Prefer official documentation or official learning websites.
- Also recommend one reliable learning platform when appropriate.
- The URL must be complete and valid.
- Match the resource to the skill being learned.

🛠️ Practice:
- Give one simple practical exercise or project.

STEP 2: [Skill/Technology]
What to learn:
- Mention the important concepts the fresher should learn.

📚 Recommended Learning Resources:
- Official documentation or official learning website
- One reliable learning platform

🛠️ Practice:
- Give one simple practical exercise or project.

STEP 3: [Skill/Technology]
What to learn:
- Mention the important concepts the fresher should learn.

📚 Recommended Learning Resources:
- Official documentation or official learning website
- One reliable learning platform

🛠️ Practice:
- Give one simple practical exercise or project.

STEP 4: [Skill/Technology]
What to learn:
- Mention the important concepts the fresher should learn.

📚 Recommended Learning Resources:
- Official documentation or official learning website
- One reliable learning platform

🛠️ Practice:
- Give one simple practical exercise or project.

STEP 5: [Skill/Technology]
What to learn:
- Mention the important concepts the fresher should learn.

📚 Recommended Learning Resources:
- Official documentation or official learning website
- One reliable learning platform

🛠️ Practice:
- Give one simple practical exercise or project.

🏆 CERTIFICATIONS

Recommend 4 relevant certifications for the student's target career.

Use this exact format:

- Certification Name | Complete Official URL
- Certification Name | Complete Official URL
- Certification Name | Complete Official URL
- Certification Name | Complete Official URL

Rules:
- Recommend exactly 4 certifications.
- Make them relevant to the recommended career.
- Prefer official certification pages.
- Include a mix of beginner-friendly and career-relevant certifications where appropriate.
- The URL must be complete and valid.
- Do not invent URLs.



🚀 PRACTICAL PROJECT
- Suggest one realistic project that combines the skills in the roadmap.
- Mention the main technologies to use.

💡 NEXT STEP
- Give one simple action the student should take next.

Rules:
- Keep the answer concise and easy to read.
- Use short bullet points.
- Do not write long paragraphs.
- Give practical advice suitable for a fresher.
- Do not invent skills that are not present in the resume.
- The roadmap must follow a logical learning order.
- Recommend well-known and reliable learning resources.
- Prefer official documentation when available.
- Do not provide fake URLs.
- Make the roadmap specific to the student's recommended career.
- Focus on skills that are actually useful for entry-level jobs.
"""

    return ask_gemini(prompt)

def _format_transcript(history):
    """Turn a list of {"role": "user"/"assistant", "text": ...} into a
    plain-text transcript the model can read as prior conversation turns."""

    if not history:
        return "This is the first message in the conversation."

    lines = []
    for turn in history:
        speaker = "Student" if turn.get("role") == "user" else "CareerCoachAI"
        text = (turn.get("text") or "").strip()
        if text:
            lines.append(f"{speaker}: {text}")
    return "\n".join(lines) if lines else "This is the first message in the conversation."


def chatbot_reply(question, resume_text="", skills=None, target_role=None, history=None, interests=None):
    """
    Answer a student's career-related question conversationally.

    Context-aware: uses the resume, detected skills, the student's chosen
    target role (if any), stated career interests/preferences (if any), and
    the running conversation history so far, so the reply follows naturally
    from what was already asked/answered instead of treating every message
    as a fresh, isolated question.
    """

    skills_text = ", ".join(skills) if skills else "Not detected yet"
    role_text = target_role or "Not chosen yet"
    interests_text = interests.strip() if interests and interests.strip() else "Not shared yet"
    transcript = _format_transcript(history)

    prompt = f"""
You are CareerCoach AI, a context-aware, conversational career guidance
chatbot embedded in a chat window. You remember and build on everything
said earlier in THIS conversation (given below as the transcript).

Student context (use this to personalize your reply, never invent facts
beyond it):
- Resume summary: {resume_text[:2000] if resume_text else "No resume has been uploaded yet."}
- Detected skills: {skills_text}
- Target career role: {role_text}
- Career interests / preferences: {interests_text}

Conversation so far:
{transcript}

Student's new message:
{question}

How to respond:
- Read the conversation so far first. If your previous message asked the
  student something, treat this new message as their answer to THAT
  question and react to it directly before doing anything else.
- If the student asks to be assessed/tested/quizzed on a skill (or the
  conversation is already in the middle of an assessment), run it
  conversationally:
    * Ask exactly ONE question per reply. Never ask two or more questions
      in the same message.
    * Start at Basic difficulty for that skill. If the student answers
      correctly, ask a slightly harder question next (Basic -> Intermediate
      -> Advanced). If they answer incorrectly or vaguely, gently correct
      them in one short line, then either ask an easier/clarifying question
      on the same topic or move on — do not just repeat the same question.
    * Never repeat a question (or a close variant of one) that already
      appears in the transcript above.
    * Base questions on the student's actual detected skills/resume/target
      role, not random topics.
    * Once you have asked enough questions to judge the skill (typically
      after a Basic, an Intermediate, and an Advanced question, or sooner
      if answers are consistently weak), stop asking and instead give a
      short final evaluation in this shape: state the assessed level
      (Basic / Intermediate / Advanced) and one short sentence of honest,
      specific justification based only on how they answered.
- Otherwise (general career/resume/skill questions), just answer directly
  and practically — one focused question back to the student only if you
  genuinely need clarification to help them.
- Keep the whole reply short: 2-5 sentences, or a few short bullet points.
  Never write long paragraphs or restate the transcript.
- Do not repeat advice, phrasing, or questions you already gave earlier in
  this conversation.
- Be encouraging but honest and realistic.
"""

    return ask_gemini(prompt)
