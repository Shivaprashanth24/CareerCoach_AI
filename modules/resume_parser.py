"""
modules/resume_parser.py
------------------------

Robust resume parser for PDF and DOCX resumes.

Supports:
- Single-page resumes
- Two-page resumes
- PDF and DOCX
- Skills
- Education
- Projects
- Experience
- Certifications
- Extra-curricular activities
- Basic project and experience detection
- Two-column PDF text extraction
"""

import os
import re

import pdfplumber
import docx


# ===============================================================
# SECTION DEFINITIONS
# ===============================================================

SECTION_ALIASES = {
    "Skills": {
        "skills",
        "technical skills",
        "key skills",
        "core skills",
        "professional skills",
    },

    "Education": {
        "education",
        "academic",
        "academic qualifications",
        "educational background",
        "qualification",
        "qualifications",
    },

    "Projects": {
        "projects",
        "project",
        "academic projects",
        "personal projects",
        "key projects",
    },

    "Experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "work history",
        "internship",
        "internships",
    },

    "Certifications": {
        "certifications",
        "certification",
        "certificates",
        "certificate",
        "courses",
        "courses and certifications",
    },

    "Extra Curricular": {
        "extra curricular",
        "extracurricular",
        "co curricular",
        "cocurricular",
        "activities",
    },

    # Non-target sections are still detected so they can stop the
    # previous target section (for example ACHIEVEMENTS must not become
    # part of PROJECTS).
    "_Other": {
        "summary",
        "objective",
        "profile",
        "career objective",
        "achievements",
        "achievement",
        "achievements",
        "acheivement",
        "acheivements",
        "awards",
        "honors",
        "declaration",
        "references",
        "contact",
        "personal details",
        "volunteering",
        "volunteering and leadership",
        "leadership",
    },
}


# ===============================================================
# COMMON SKILLS
# ===============================================================

COMMON_SKILLS = [
    "python",
    "java",
    "c",
    "c++",
    "c#",
    "javascript",
    "typescript",
    "html",
    "html5",
    "css",
    "css3",
    "tailwind",
    "tailwind css",
    "bootstrap",
    "react",
    "angular",
    "node",
    "node.js",
    "flask",
    "django",
    "spring",
    "spring boot",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "oracle",
    "git",
    "github",
    "docker",
    "linux",
    "aws",
    "azure",
    "power bi",
    "tableau",
    "excel",
    "machine learning",
    "deep learning",
    "data analysis",
    "data science",
    "tensorflow",
    "pytorch",
    "keras",
    "numpy",
    "pandas",
    "communication",
    "teamwork",
    "problem solving",
]


# ===============================================================
# TEXT CLEANING
# ===============================================================

def clean_text(text):
    """Clean extracted PDF/DOCX text without destroying useful content."""

    if not text:
        return ""

    text = text.replace("\xa0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")

    # Normalize different dash characters
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("−", "-")

    # Normalize spaces
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def remove_bullet(text):
    """Remove common bullet characters from a line."""

    if not text:
        return ""

    return re.sub(
        r"^\s*(?:[-•●○▪◦►▸»*]\s*)+",
        "",
        text
    ).strip()


def normalize_heading(text):
    """Normalize a possible section heading."""

    if not text:
        return ""

    text = clean_text(text)

    text = re.sub(
        r"^[^A-Za-z]+",
        "",
        text
    )

    text = re.sub(
        r"[^A-Za-z0-9 ]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.lower().strip()


# ===============================================================
# PDF EXTRACTION
# ===============================================================

def _cluster_lines(words):
    """
    Group a set of words into reading-order lines.

    Words are grouped by vertical position (top) and, within a
    line, ordered left-to-right. This is used per-column so it
    naturally supports both single and multi-column resumes.
    """

    if not words:
        return []

    sorted_words = sorted(words, key=lambda w: (round(w["top"]), w["x0"]))

    lines = []
    current_line = []
    current_top = None

    for word in sorted_words:

        if current_top is None or abs(word["top"] - current_top) <= 3:
            current_line.append(word)
            current_top = word["top"] if current_top is None else current_top
        else:
            lines.append(current_line)
            current_line = [word]
            current_top = word["top"]

    if current_line:
        lines.append(current_line)

    text_lines = []

    for line in lines:
        line_sorted = sorted(line, key=lambda w: w["x0"])
        text_lines.append(" ".join(w["text"] for w in line_sorted))

    return text_lines


def _detect_column_split(words, page_width):
    """
    Detect whether a page uses a two-column layout, and if so,
    return the x-coordinate of the gutter between the columns.

    Works row-by-row: for every row of words, look at the widest
    horizontal gap between two consecutive words. If a wide gap
    shows up at roughly the same x-position across many different
    rows, that's a real column gutter (as opposed to an incidental
    wide space within a single line of single-column text).

    Returns None for single-column pages.
    """

    if not words:
        return None

    rows = {}

    for word in words:
        row_key = round(word["top"] / 3)
        rows.setdefault(row_key, []).append(word)

    candidates = []

    for row_words in rows.values():

        if len(row_words) < 2:
            continue

        row_sorted = sorted(row_words, key=lambda w: w["x0"])

        for left_word, right_word in zip(row_sorted, row_sorted[1:]):

            gap = right_word["x0"] - left_word["x1"]

            if gap < 20:
                continue

            mid = (left_word["x1"] + right_word["x0"]) / 2

            # Only consider gaps roughly in the middle of the page -
            # margins near the far left/right are not column gutters.
            if page_width * 0.25 <= mid <= page_width * 0.75:
                candidates.append(mid)

    if not candidates:
        return None

    # Cluster nearby candidate positions together so that small
    # jitter (different rows' gaps not being pixel-perfect aligned)
    # still counts as "the same" gutter.
    candidates.sort()

    clusters = []

    for x in candidates:
        if clusters and x - clusters[-1][-1] <= 15:
            clusters[-1].append(x)
        else:
            clusters.append([x])

    clusters.sort(key=len, reverse=True)
    best_cluster = clusters[0]

    # Require the gap to recur across several distinct rows before
    # trusting it as a genuine column gutter, not a one-off wide
    # space in an otherwise single-column line.
    if len(best_cluster) < 4:
        return None

    return sum(best_cluster) / len(best_cluster)


def _extract_page_text(page):
    """
    Extract a single page's text, automatically handling both
    single-column and two-column resume layouts.
    """

    words = page.extract_words(x_tolerance=2, y_tolerance=3)

    if not words:
        return ""

    split_x = _detect_column_split(words, page.width)

    if split_x is None:
        # Single-column layout: simple top-to-bottom reading order.
        return "\n".join(_cluster_lines(words))

    # Two-column layout: read the left column fully (top to bottom),
    # then the right column fully (top to bottom). This keeps each
    # column's section headings and content together instead of
    # interleaving unrelated columns on the same line.
    left_words = [w for w in words if (w["x0"] + w["x1"]) / 2 < split_x]
    right_words = [w for w in words if (w["x0"] + w["x1"]) / 2 >= split_x]

    left_lines = _cluster_lines(left_words)
    right_lines = _cluster_lines(right_words)

    return "\n".join(left_lines + right_lines)


def _extract_from_pdf(filepath):
    """
    Extract text from every PDF page.

    Automatically detects single-column vs two-column (or more)
    layouts per page and reads each column in proper top-to-bottom
    order, so section headings are never merged with unrelated
    text from another column.
    """

    pages = []

    with pdfplumber.open(filepath) as pdf:

        for page in pdf.pages:

            text = ""

            try:
                text = _extract_page_text(page)
            except Exception:
                text = ""

            # Fallback 1: legacy layout-preserving extraction
            if not text.strip():
                try:
                    text = page.extract_text(
                        x_tolerance=2,
                        y_tolerance=3,
                        layout=True
                    ) or ""
                except Exception:
                    text = ""

            # Fallback 2: plain extraction
            if not text.strip():
                try:
                    text = page.extract_text() or ""
                except Exception:
                    text = ""

            if text.strip():
                pages.append(text)

    return "\n".join(pages)


# ===============================================================
# DOCX EXTRACTION
# ===============================================================

def _extract_from_docx(filepath):
    """Extract DOCX paragraphs and tables in their original document order.

    Borderless tables are frequently used for two-column resume templates.
    Preserving body order prevents sections from being scrambled.
    """
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    document = docx.Document(filepath)
    parts = []

    for child in document.element.body.iterchildren():
        if child.tag.endswith('}p'):
            paragraph = Paragraph(child, document)
            text = clean_text(paragraph.text)
            if text:
                parts.append(text)
        elif child.tag.endswith('}tbl'):
            table = Table(child, document)
            for row in table.rows:
                row_parts = []
                for cell in row.cells:
                    cell_text = clean_text(cell.text)
                    if cell_text:
                        row_parts.append(cell_text)
                if row_parts:
                    parts.append(" ".join(row_parts))

    return "\n".join(parts)


# ===============================================================
# MAIN TEXT EXTRACTION
# ===============================================================

def extract_text(filepath):
    """Return all text from a PDF or DOCX resume."""

    if not filepath:
        return ""

    if not os.path.exists(filepath):
        return ""

    extension = os.path.splitext(filepath)[1].lower()

    if extension == ".pdf":
        return _extract_from_pdf(filepath)

    if extension == ".docx":
        return _extract_from_docx(filepath)

    return ""


# ===============================================================
# SECTION DETECTION
# ===============================================================

def _match_heading(line):
    """
    Detect a section heading.

    Handles both:

        EDUCATION

    and:

        EDUCATION SETHU INSTITUTE OF TECHNOLOGY
    """

    if not line:
        return None

    normalized = normalize_heading(line)

    # Exact heading
    for section, aliases in SECTION_ALIASES.items():

        if normalized in aliases:
            return section

    upper = clean_text(line).upper()

    # A lowercase line beginning with a section word is usually normal prose,
    # e.g. "projects while fostering professional growth". Exact aliases
    # were already handled above, so reject lowercase prose here.
    if line and line[0].islower():
        return None

    # Only treat a section keyword as a heading when it starts the line.
    # Matching arbitrary occurrences (e.g. "experience", "skills", or
    # "projects" inside prose) causes section leakage.
    patterns = {
        "Skills": [
            r"^(?:TECHNICAL\s+|KEY\s+|CORE\s+)?SKILLS(?:\s*[:|-].*)?$",
            r"^(?:TECHNICAL\s+|KEY\s+|CORE\s+)?SKILLS\b",
        ],
        "Education": [
            r"^(?:ACADEMIC\s+QUALIFICATIONS?|EDUCATIONAL\s+BACKGROUND|EDUCATION|QUALIFICATIONS?)\b",
        ],
        "Projects": [
            r"^(?:ACADEMIC\s+|PERSONAL\s+|KEY\s+)?PROJECTS?\b",
        ],
        "Experience": [
            r"^(?:PROFESSIONAL\s+|WORK\s+|EMPLOYMENT\s+)?EXPERIENCE\b",
            r"^(?:INTERNSHIPS?)\b",
            r"^(?:INTERN\s+EXPERIENCE|INTERNSHIP\s+EXPERIENCE)\b",
        ],
        "Certifications": [
            r"^(?:COURSES\s+AND\s+)?CERTIFICATIONS?\b",
            r"^CERTIFICATES?\b",
        ],
        "Extra Curricular": [
            r"^(?:EXTRA[-\s]?CURRICULAR|CO[-\s]?CURRICULAR|ACTIVITIES)\b",
        ],
        "_Other": [
            r"^(?:SUMMARY|OBJECTIVE|PROFILE|CAREER\s+OBJECTIVE)\b",
            r"^(?:ACHIEVEMENTS?|AWARDS?|HONORS?|HONOURS?)\b",
            r"^(?:DECLARATION|REFERENCES?|CONTACT|PERSONAL\s+DETAILS?)\b",
            r"^(?:VOLUNTEERING(?:\s+AND\s+LEADERSHIP)?|LEADERSHIP)\b",
            r"^NPTEL\s+AWARDS?\b",
        ],
    }

    for section, regexes in patterns.items():

        for pattern in regexes:

            if re.match(pattern, upper):
                return section

    return None


# ===============================================================
# SECTION HEADING + CONTENT SPLIT
# ===============================================================

def _split_heading_and_content(line, section):
    """
    If PDF extraction gives:

        EDUCATION SETHU INSTITUTE...

    split it into:

        heading = EDUCATION
        content = SETHU INSTITUTE...
    """

    if not line or not section:
        return False, ""

    patterns = {

        "Skills": (
            r"^(?:TECHNICAL\s+|KEY\s+|CORE\s+)?SKILLS\b"
        ),

        "Education": (
            r"^(?:ACADEMIC\s+QUALIFICATIONS?|"
            r"EDUCATIONAL\s+BACKGROUND|"
            r"EDUCATION|QUALIFICATIONS?)\b"
        ),

        "Projects": (
            r"^(?:ACADEMIC\s+|PERSONAL\s+|KEY\s+)?PROJECTS?\b"
        ),

        "Experience": (
            r"^(?:PROFESSIONAL\s+|WORK\s+|"
            r"EMPLOYMENT\s+)?EXPERIENCE\b"
        ),

        "Certifications": (
            r"^(?:COURSES\s+AND\s+)?"
            r"CERTIFICATIONS?|CERTIFICATES?\b"
        ),

        "Extra Curricular": (
            r"^(?:EXTRA[-\s]?CURRICULAR|"
            r"CO[-\s]?CURRICULAR|ACTIVITIES)\b"
        ),
    }

    pattern = patterns.get(section)

    if not pattern:
        return False, ""

    match = re.match(
        pattern,
        line,
        flags=re.IGNORECASE
    )

    if not match:
        return False, ""

    remaining = line[match.end():].strip()

    return True, remaining


# ===============================================================
# SECTION LINE CLEANING
# ===============================================================

def clean_section_lines(lines):
    """
    Clean lines but preserve useful resume information.
    """

    result = []

    for line in lines:

        line = clean_text(line)
        line = remove_bullet(line)

        if not line:
            continue

        # Remove obvious page numbering
        if re.fullmatch(
            r"(page\s*)?\d+\s*(of\s*\d+)?",
            line,
            flags=re.IGNORECASE
        ):
            continue

        result.append(line)

    return result


# ===============================================================
# PARSE SECTIONS
# ===============================================================

def parse_sections(text):
    """Split resume text into logical sections while preventing content
    from one section (e.g. achievements) from leaking into another.

    Headings are matched case-insensitively and may appear on the same
    line as their first piece of content.
    """

    sections = {
        "Skills": [],
        "Education": [],
        "Projects": [],
        "Experience": [],
        "Certifications": [],
        "Extra Curricular": [],
    }

    if not text:
        return sections

    lines = [clean_text(x) for x in text.splitlines() if clean_text(x)]
    current_section = None

    for line in lines:
        detected = _match_heading(line)

        if detected:
            # Non-target heading: stop the current target section.
            if detected == "_Other":
                current_section = None
                continue

            normalized = normalize_heading(line)

            if normalized in SECTION_ALIASES.get(detected, set()):
                current_section = detected
                continue

            matched, remaining = _split_heading_and_content(line, detected)
            if matched:
                current_section = detected
                if remaining:
                    sections[current_section].append(remove_bullet(remaining))
                continue

            # The line is still a valid heading even when it is a custom
            # alias such as "Intern Experience" that has no split pattern.
            current_section = detected
            continue

        if current_section:
            sections[current_section].append(remove_bullet(line))

    for section in sections:
        sections[section] = clean_section_lines(sections[section])

    return sections


# ===============================================================
# SKILL FINDER
# ===============================================================

def find_skills(text):
    """Return known skills found in the resume."""

    if not text:
        return []

    lower = text.lower()

    found = []

    for skill in COMMON_SKILLS:

        # Special handling for short skills
        if skill in {"c", "c++", "c#"}:

            pattern = r"(?<![a-z])" + re.escape(skill) + r"(?![a-z])"

            if re.search(pattern, lower):
                found.append(skill.title())

        else:

            if skill.lower() in lower:
                found.append(skill.title())

    # Remove duplicates while preserving order
    return list(dict.fromkeys(found))


# ===============================================================
# PERSONAL DETAILS EXTRACTION
# ===============================================================

def extract_personal_details(text):
    """
    Extract name, email, phone, and location from resume text.
    
    Returns a dictionary with:
    - name: extracted name or empty string
    - email: extracted email or empty string
    - phone: extracted phone number or empty string
    - location: extracted location or empty string
    """
    
    if not text:
        return {
            "name": "",
            "email": "",
            "phone": "",
            "location": ""
        }
    
    details = {
        "name": "",
        "email": "",
        "phone": "",
        "location": ""
    }
    
    lines = text.split("\n")
    
    # Email extraction - look for email pattern
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    email_matches = re.findall(email_pattern, text)
    if email_matches:
        details["email"] = email_matches[0]
    
    # Phone extraction - look for phone patterns
    phone_patterns = [
        r"\+?1?\s*[\(\-\s]?[0-9]{3}[\)\-\s]?[0-9]{3}[\-\s]?[0-9]{4}",  # US format
        r"\+?91\s*[\-\s]?[0-9]{5}[\-\s]?[0-9]{5}",  # India format
        r"[0-9]{10}",  # Simple 10 digit
    ]
    
    for pattern in phone_patterns:
        phone_matches = re.findall(pattern, text)
        if phone_matches:
            details["phone"] = phone_matches[0].strip()
            break
    
    # Name extraction - usually first few lines before any section headers
    for line in lines[:10]:  # Check first 10 lines
        line = clean_text(line)
        normalized = normalize_heading(line)
        
        if not line or len(line) > 100:
            continue
        
        # Skip if it's a section header
        is_header = False
        for section_aliases in SECTION_ALIASES.values():
            if normalized in section_aliases:
                is_header = True
                break
        
        if is_header or "@" in line or any(char.isdigit() for char in line):
            continue
        
        # Check if it looks like a name (2-5 words, all alphabetic or dash)
        words = line.split()
        if 1 <= len(words) <= 5 and all(
            all(c.isalpha() or c in ['-', '.'] for c in word)
            for word in words
        ):
            details["name"] = line
            break
    
    # Location extraction - look for common location indicators
    location_keywords = [
        "location", "based in", "based at", "city", "country",
        "from", "currently in", "located in"
    ]
    
    for i, line in enumerate(lines[:20]):
        line_lower = line.lower()
        for keyword in location_keywords:
            if keyword in line_lower:
                # Extract location from this line
                location = re.sub(rf".*{keyword}\s*:?\s*", "", line_lower, flags=re.IGNORECASE)
                location = location.split("\n")[0].strip()
                if location and len(location) < 100:
                    details["location"] = clean_text(location)
                    break
        if details["location"]:
            break
    
    return details


# ===============================================================
# PROJECT PARSER
# ===============================================================

def _looks_like_project_title(line):
    """Detect a project title without relying on one fixed resume template.

    Resume project descriptions are often bullet points, so bullet characters
    cannot be used as project boundaries. Instead, title-like lines are
    detected using capitalization, sentence structure, and common prose
    signals. This handles titles such as:
      - Blockchain-Based Rancher Product Selling System
      - Messaging Automation System using OpenClaw
      - Matrimonial Website using JSP, Servlets, JDBC, and MySQL
    while keeping normal description bullets attached to the current project.
    """
    line = clean_text(remove_bullet(line))
    if not line or len(line) > 140:
        return False

    low = line.lower().strip()
    words = re.findall(r"[A-Za-z][A-Za-z0-9+.#'/-]*", line)
    if not words or len(words) > 14:
        return False

    # Strong description/prose starters. These should remain attached to the
    # preceding project even when the first word is capitalized.
    prose_starts = (
        "built", "developed", "designed", "implemented", "created",
        "applied", "installed", "configured", "integrated", "deployed",
        "automated", "contributed", "assisted", "won", "selected",
        "gaining", "gained", "worked", "managed", "maintained",
        "optimized", "trained", "classified", "segmented", "detected",
        "used", "utilized", "leveraged", "tracking", "transmitted",
        "ensured", "provided", "responsible", "currently", "completed",
        "experience", "actively", "participated", "coordinated",
    )
    if low.startswith(prose_starts):
        return False

    if re.match(r"^(technologies|technology|tech stack|tools?)\s*:", low):
        return False

    # Continuation lines and technology/detail lists can look title-cased
    # because product/framework names are capitalized. They are not project
    # boundaries.
    if line.lstrip().startswith(("+", "&")):
        return False

    detail_terms = (
        "algorithm", "pipeline", "detection", "classification",
        "segmentation", "dashboard", "responsive web", "cart management",
        "checkout workflow", "smooth navigation", "real-time",
        "real time", "data transmission", "transmitted", "modules",
        "sensor", "cloud dashboard", "implemented", "developed",
        "application enabling", "database-driven",
    )
    if any(term in low for term in detail_terms):
        return False

    # A technology-heavy comma list is normally a continuation of the
    # current project, not a new title. Keep legitimate titles such as
    # "Matrimonial Website using JSP, Servlets, JDBC, and MySQL" by only
    # applying this rule when the line is clearly a tool/module list.
    if line.count(",") >= 2 and (
        re.match(
            r"^(?:arduino|esp8266|esp32|gsm|gps|python|java|javascript|html5|css3|mysql|mqtt|modules|sensor|resnet|efficientnet|cnn)\b",
            low,
        )
        or re.search(r"\b(?:modules|sensors?)\s*[,;]", low)
    ):
        return False

    # A sentence ending in punctuation is almost always a description.
    if line.endswith((".", ";", ":")):
        return False

    # Very long lines are normally descriptions, not project names.
    if len(line.split()) > 12:
        return False

    # Strong title signal: all-uppercase headings.
    alpha = [c for c in line if c.isalpha()]
    if alpha and sum(c.isupper() for c in alpha) / len(alpha) >= 0.72:
        return True

    # Strong title signal: title case. Count words that begin with an
    # uppercase letter, while allowing connector words such as "using",
    # "and", "of", "for", "with", "in", "to".
    connectors = {
        "a", "an", "and", "as", "at", "by", "for", "from", "in",
        "of", "on", "or", "the", "to", "using", "via", "with", "&"
    }
    meaningful = [w for w in words if w.lower() not in connectors]
    if meaningful:
        title_words = sum(1 for w in meaningful if w[0].isupper())
        title_ratio = title_words / len(meaningful)

        # At least two title-cased words makes a useful boundary. This is
        # intentionally permissive for technology-heavy project names.
        if len(meaningful) >= 2 and title_ratio >= 0.70:
            return True

    # Short noun-phrase headings containing an obvious project noun.
    if len(words) <= 7 and re.search(
        r"\b(?:project|application|website|system|platform|dashboard|portal|app)\b",
        low,
    ):
        # Reject obvious sentence-like phrases.
        if not re.search(r"\b(?:is|are|was|were|has|have|this|that)\b", low):
            return True

    return False


def parse_projects(lines):
    """Group wrapped project titles and all following descriptions.

    Project titles are detected conservatively. Wrapped title lines are
    joined when the previous line clearly continues (e.g. ends in "of"
    or "&"), preventing one project from becoming several projects.
    """
    if not lines:
        return []

    projects = []
    current = None

    for raw in lines:
        line = clean_text(remove_bullet(raw))
        if not line:
            continue

        # Join wrapped title lines such as:
        # "Automated Detection of Retinopathy of"
        # "Prematurity (ROP) Using Deep Learning"
        if current is not None and len(current) == 1:
            previous = current[0]
            if re.search(
                r"(?:\b(?:of|and|for|with|using|in|on|based)|&|[(/-])\s*$",
                previous,
                re.I,
            ):
                # A wrapped title may contain words like "using" that
                # would normally look like description text.
                if (
                    len(line.split()) <= 10
                    and not re.match(
                        r"^(built|developed|designed|implemented|created|applied|automated|contributed|assisted|won|selected)\b",
                        line,
                        re.I,
                    )
                ):
                    current[0] = f"{previous} {line}".strip()
                    continue

        if current is None:
            current = [line]
            continue

        if _looks_like_project_title(line) and len(current) >= 1:
            projects.append(current)
            current = [line]
        else:
            current.append(line)

    if current:
        projects.append(current)

    return projects


# ===============================================================
# EXPERIENCE PARSER
# ===============================================================

def _looks_like_experience_start(line):
    """Detect a job/role line from common role vocabulary."""
    line = clean_text(remove_bullet(line))
    if not line or len(line) > 120:
        return False

    low = line.lower()
    role_words = [
        "intern", "developer", "engineer", "analyst", "designer",
        "associate", "trainee", "manager", "consultant", "specialist",
        "coordinator", "executive", "officer", "architect", "administrator",
        "programmer", "tester", "lead", "scientist", "accountant",
    ]

    return any(
        re.search(r"\b" + re.escape(word) + r"\b", low)
        for word in role_words
    )


def parse_experience(lines):
    """Group each role with its company/date and bullet descriptions."""
    if not lines:
        return []

    experience = []
    current = None

    for raw in lines:
        line = clean_text(remove_bullet(raw))
        if not line:
            continue

        if current is not None and _looks_like_experience_start(line):
            # A second role starts a new entry.
            experience.append(current)
            current = [line]
        elif current is None:
            current = [line]
        else:
            current.append(line)

    if current:
        experience.append(current)

    return experience


# ===============================================================
# EDUCATION PARSER
# ===============================================================

def parse_education(lines):
    """
    Convert education section lines into readable education items.
    
    Maintains all education details on a single line for consistency
    with the existing template display format.
    """

    if not lines:
        return []

    education = []
    current_entry = []

    degree_keywords = [
        "bachelor",
        "master",
        "phd",
        "diploma",
        "associate",
        "b.a.",
        "b.s.",
        "b.sc.",
        "b.tech",
        "m.a.",
        "m.s.",
        "m.sc.",
        "m.tech",
        "mba",
        "bca",
        "mca",
        "b.com",
        "m.com",
        "degree",
        "graduation",
    ]

    for line in lines:

        line = clean_text(line)

        if not line:
            continue

        lower = line.lower()

        # A line is education if it contains degree keywords or is a university/institute name
        is_education_header = (
            any(keyword in lower for keyword in degree_keywords)
            or "university" in lower
            or "institute" in lower
            or "college" in lower
            or "school" in lower
        )

        if is_education_header:

            # Save previous entry if exists
            if current_entry:
                education.append(" | ".join(current_entry))
                current_entry = []

            current_entry.append(line)

        else:

            # Add detail to current entry
            if current_entry or line:
                current_entry.append(line)

    # Add final entry
    if current_entry:
        education.append(" | ".join(current_entry))

    return education


# ===============================================================
# CERTIFICATION PARSER
# ===============================================================

def _is_certification_heading_or_line(line):
    """Return True when a line has a strong certification signal."""
    low = clean_text(line).lower()
    if not low:
        return False

    patterns = [
        r"\bcertified\b",
        r"\bcertification\b",
        r"\bcertificate\b",
        r"\blicen[cs]e\b",
        r"\bcredential\b",
        r"\bprofessional certificate\b",
        r"\bcompletion certificate\b",
    ]
    return any(re.search(p, low, re.I) for p in patterns)


def _split_certification_entries(lines):
    """Split certification-section content without losing wrapped entries.

    Resume templates use bullets, dates, issuer lines, or one credential per
    line.  A new bullet is always a safe boundary; otherwise a new line with
    a strong credential signal starts a new entry when the previous entry is
    already complete.
    """
    entries = []
    current = []

    for raw in lines or []:
        if not raw:
            continue
        original = clean_text(raw)
        if not original:
            continue

        had_bullet = bool(re.match(r"^\s*[-•●○▪◦►▸»*]\s+", original))
        line = remove_bullet(original)

        if had_bullet and current:
            entries.append(" ".join(current))
            current = []

        # Numbered certification lists are also common.
        numbered = bool(re.match(r"^\s*\d+[.)]\s+", original))
        if numbered and current:
            entries.append(" ".join(current))
            current = []
            line = re.sub(r"^\s*\d+[.)]\s+", "", line)

        issuer_only = re.fullmatch(
            r"(?:Infosys|NPTEL|Coursera|Udemy|Google|Microsoft|Amazon Web Services|AWS|Oracle|Cisco|IBM|KLOG Foundation Institute|IMARTICUS Private Limited|Great Learning)\.?,?",
            line,
            flags=re.I,
        )
        if issuer_only and current:
            current.append(line)
            entries.append(" ".join(current))
            current = []
            continue

        # A common format is one credential per line as "Title - Issuer".
        # If both the current and incoming lines have that structure, the
        # incoming line is a new credential even when its title lacks the
        # literal word certificate.
        if current and " - " in line and any(" - " in part for part in current):
            entries.append(" ".join(current))
            current = []

        if current and _is_certification_heading_or_line(line):
            # If the current entry already contains a credential signal,
            # another credential-signal line is usually the next certificate.
            if _is_certification_heading_or_line(" ".join(current)) and len(line.split()) <= 18:
                entries.append(" ".join(current))
                current = []

        # Some PDF templates place several credentials on one visual line.
        # Split after a known issuer when another credential starts immediately
        # after it. This is safer than splitting at every capitalized word.
        issuer_pattern = r"\b(?:Infosys|NPTEL|Coursera|Udemy|Google|Microsoft|Amazon Web Services|AWS|Oracle|Cisco|IBM|KLOG Foundation Institute|IMARTICUS Private Limited|Great Learning)\b"
        marked = re.sub(
            r"(" + issuer_pattern + r")\s+(?=[A-Z])",
            r"\1|||",
            line,
            flags=re.I,
        )
        parts = marked.split("|||")

        if len(parts) > 1:
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if current:
                    entries.append(" ".join(current))
                    current = []
                current.append(part)
            continue

        current.append(line)

    if current:
        entries.append(" ".join(current))

    return [re.sub(r"\s+", " ", x).strip() for x in entries if x.strip()]


def _looks_like_certificate_entry(line):
    """Detect common certificate names even when the word certificate is absent."""
    low = clean_text(line).lower()
    if not low or len(low) > 180:
        return False

    if _is_certification_heading_or_line(low):
        return True

    # Common issuers/platforms. These are deliberately broad and are only
    # used outside an explicit Certifications section as a fallback.
    issuer_terms = [
        "coursera", "udemy", "edx", "nptel", "swayam", "google",
        "microsoft", "aws", "amazon web services", "oracle", "cisco",
        "ibm", "infosys", "tcs", "accenture", "linkedin learning",
        "great learning", "simplilearn", "skill india", "hackerrank",
        "freecodecamp", "meta", "salesforce", "red hat",
    ]
    if any(term in low for term in issuer_terms):
        cert_words = ["course", "training", "credential", "professional", "developer", "associate", "exam", "masterclass"]
        return any(w in low for w in cert_words)

    return False


def parse_certifications(lines, full_text=""):
    """Extract ALL certification entries from varied resume layouts.

    Handles explicit Certifications/Certificates sections, bullet and
    numbered lists, wrapped lines, issuer/date lines, and certificates
    placed under Achievements/Awards or elsewhere when no heading exists.
    """
    results = []

    # 1) Explicit section: preserve bullet/number boundaries and wrapped text.
    results.extend(_split_certification_entries(lines))

    # 2) Global fallback: collect every certification-looking entry from the
    # entire resume. This is important when a column extractor fails to keep
    # the Certifications heading attached to its content.
    if full_text:
        all_lines = [clean_text(x) for x in full_text.splitlines() if clean_text(x)]
        i = 0
        while i < len(all_lines):
            line = all_lines[i]
            if _match_heading(line) in {"Skills", "Education", "Projects", "Experience", "Certifications", "Extra Curricular", "_Other"}:
                i += 1
                continue

            if _looks_like_certificate_entry(line) and not re.search(r"\b(?:award|awards|prize|achievement|achievements|honor|honours)\b", line, re.I):
                block = [remove_bullet(line)]
                # Only attach short continuation lines. Stop at headings,
                # bullets, dates, or another obvious certificate.
                j = i + 1
                while j < len(all_lines) and j <= i + 3:
                    nxt = all_lines[j]
                    if _match_heading(nxt):
                        break
                    if re.match(r"^\s*(?:[-•●○▪◦►▸»*]|\d+[.)])\s+", nxt):
                        break
                    if re.search(r"\b(?:award|awards|prize|achievement|achievements|honor|honours)\b", nxt, re.I):
                        break
                    if _looks_like_certificate_entry(nxt):
                        break
                    if re.search(r"\b(19|20)\d{2}\b", nxt) or re.search(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b", nxt, re.I):
                        block.append(nxt)
                        j += 1
                        break
                    # Short issuer/detail line can belong to this credential.
                    if len(nxt.split()) <= 12:
                        block.append(nxt)
                        j += 1
                    else:
                        break
                results.append(" ".join(block))
                i = max(i + 1, j)
                continue
            i += 1

    # 3) De-duplicate exact and near-duplicate entries. Keep every distinct
    # credential instead of collapsing the whole section into one string.
    cleaned = []
    seen = set()
    for item in results:
        item = re.sub(r"\s+", " ", item).strip(" -|•")
        if not item:
            continue
        key = re.sub(r"[^a-z0-9]+", " ", item.lower()).strip()
        if key and key not in seen:
            seen.add(key)
            cleaned.append(item)

    return cleaned


# ===============================================================
# ANALYZE RESUME
# ===============================================================

def analyze_resume(filepath):
    """
    Complete resume analysis with personal details extraction.

    Returns everything required by the Flask application:
    - text: full extracted text
    - sections: raw sections
    - personal: name, email, phone, location
    - skills: list of detected skills
    - projects: list of [title, detail1, detail2, ...]
    - experience: list of [title, detail1, detail2, ...]
    - education: list of [degree, detail1, detail2, ...]
    - certifications: list of certification strings
    - extra_curricular: list of activity strings
    """

    text = extract_text(filepath)

    if not text:
        return {
            "text": "",
            "sections": {
                "Skills": [],
                "Education": [],
                "Projects": [],
                "Experience": [],
                "Certifications": [],
                "Extra Curricular": [],
            },
            "personal": {
                "name": "",
                "email": "",
                "phone": "",
                "location": "",
            },
            "skills": [],
            "projects": [],
            "experience": [],
            "education": [],
            "certifications": [],
            "extra_curricular": [],
        }

    sections = parse_sections(text)

    certifications = parse_certifications(
        sections.get("Certifications", []),
        text
    )

    # Extract personal details
    personal = extract_personal_details(text)

    skills = find_skills(text)

    projects = parse_projects(
        sections.get("Projects", [])
    )

    experience = parse_experience(
        sections.get("Experience", [])
    )

    education = parse_education(
        sections.get("Education", [])
    )

    return {
        "text": text,

        "sections": sections,

        "personal": personal,

        "skills": skills,

        "projects": projects,

        "experience": experience,

        "education": education,

        "certifications": certifications,

        "extra_curricular": sections.get(
            "Extra Curricular",
            []
        ),
    }