"""
modules/career_data.py
-----------------------
Static reference data for the Career Tracker dashboard: the role
catalog (target roles and the skills each one requires) and the
keyword patterns used to detect those skills inside resume text.

This module does not read or write the database and does not touch
the existing resume parser — it only defines reference data used by
modules/career_tracker.py to compare a user's resume against a role.
"""

import re

# ===============================================================
# SKILL KEYWORD DETECTION
# ---------------------------------------------------------------
# Broader than resume_parser.COMMON_SKILLS on purpose: the career
# tracker needs to recognize role-specific tools (Spark, Airflow,
# Kubernetes, etc.) that the general resume analyzer does not look
# for. Kept completely separate so the existing resume analyzer is
# never touched.
# ===============================================================

SKILL_KEYWORDS = {
    "python": ["python"],
    "sql": [r"\bsql\b"],
    "java": [r"\bjava\b(?!script)"],
    "javascript": ["javascript", r"\bjs\b", "node.js", "nodejs"],
    "r_lang": [r"\br programming\b", r"\br language\b"],
    "etl": ["etl", "extract transform load", "data pipeline", "data pipelines"],
    "spark": ["spark", "pyspark", "apache spark"],
    "hadoop": ["hadoop", "hdfs", "mapreduce"],
    "kafka": ["kafka"],
    "airflow": ["airflow"],
    "cloud": ["aws", "azure", "gcp", "google cloud", "amazon web services"],
    "data_warehousing": ["data warehouse", "data warehousing", "redshift", "snowflake", "bigquery"],
    "docker": ["docker", "container"],
    "kubernetes": ["kubernetes", "k8s"],
    "terraform": ["terraform", "infrastructure as code", "iac"],
    "cicd": ["ci/cd", "continuous integration", "continuous deployment", "jenkins", "github actions"],
    "linux": ["linux", "unix", "shell scripting", "bash"],
    "git": ["git", "github", "gitlab", "version control"],
    "machine_learning": ["machine learning", "scikit-learn", "sklearn"],
    "deep_learning": ["deep learning", "neural network", "tensorflow", "pytorch", "keras"],
    "statistics": ["statistics", "statistical analysis", "hypothesis testing"],
    "data_analysis": ["data analysis", "data analytics", "exploratory data analysis", "eda"],
    "nlp": ["nlp", "natural language processing"],
    "computer_vision": ["computer vision", "opencv", "image processing"],
    "data_visualization": ["tableau", "power bi", "matplotlib", "seaborn", "data visualization"],
    "excel": ["excel", "spreadsheet"],
    "react": ["react", "react.js", "reactjs"],
    "angular": ["angular"],
    "vue": ["vue", "vue.js"],
    "html_css": ["html", "css", "html5", "css3"],
    "rest_api": ["rest api", "restful", "api development"],
    "flask": ["flask"],
    "django": ["django"],
    "spring_boot": ["spring boot", "spring framework", "spring mvc"],
    "mongodb": ["mongodb", "nosql"],
    "mysql": ["mysql", "postgresql", "relational database"],
    "system_design": ["system design", "microservices", "distributed systems"],
    "communication": ["communication"],
    "problem_solving": ["problem solving", "problem-solving"],
}


def get_skill_display_name(skill_key):
    """Human-friendly label for a skill key (used across the UI)."""
    return SKILL_DISPLAY_NAMES.get(skill_key, skill_key.replace("_", " ").title())


SKILL_DISPLAY_NAMES = {
    "python": "Python",
    "sql": "SQL",
    "java": "Java",
    "javascript": "JavaScript",
    "r_lang": "R Programming",
    "etl": "ETL / Data Pipelines",
    "spark": "Apache Spark",
    "hadoop": "Hadoop",
    "kafka": "Apache Kafka",
    "airflow": "Apache Airflow",
    "cloud": "Cloud Platforms (AWS/Azure/GCP)",
    "data_warehousing": "Data Warehousing",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform / IaC",
    "cicd": "CI/CD",
    "linux": "Linux / Shell Scripting",
    "git": "Git & Version Control",
    "machine_learning": "Machine Learning",
    "deep_learning": "Deep Learning",
    "statistics": "Statistics",
    "data_analysis": "Data Analysis",
    "nlp": "Natural Language Processing",
    "computer_vision": "Computer Vision",
    "data_visualization": "Data Visualization",
    "excel": "Excel",
    "react": "React",
    "angular": "Angular",
    "vue": "Vue.js",
    "html_css": "HTML/CSS",
    "rest_api": "REST APIs",
    "flask": "Flask",
    "django": "Django",
    "spring_boot": "Spring Boot",
    "mongodb": "MongoDB",
    "mysql": "SQL Databases",
    "system_design": "System Design",
    "communication": "Communication",
    "problem_solving": "Problem Solving",
}


# ===============================================================
# CURATED LEARNING RESOURCES
# ---------------------------------------------------------------
# Deliberately static and hand-picked (not AI-generated) so the
# Career Tracker roadmap can show real, verified links without ever
# risking an invented/broken URL. Only official documentation and
# well-known, reputable learning platforms. Up to 3 per skill —
# fewer is fine, we never pad with a weak link just to reach 3.
# ===============================================================

SKILL_RESOURCES = {
    "python": [
        {"name": "Python Official Docs", "url": "https://docs.python.org/3/"},
        {"name": "Microsoft Learn: Python", "url": "https://learn.microsoft.com/en-us/training/paths/beginner-python/"},
    ],
    "sql": [
        {"name": "Microsoft Learn: SQL", "url": "https://learn.microsoft.com/en-us/training/paths/get-started-querying-with-transact-sql/"},
        {"name": "Mode SQL Tutorial", "url": "https://mode.com/sql-tutorial/"},
    ],
    "java": [
        {"name": "Oracle Java Documentation", "url": "https://docs.oracle.com/en/java/"},
    ],
    "javascript": [
        {"name": "MDN: JavaScript Guide", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript"},
        {"name": "GitHub Skills: JavaScript", "url": "https://skills.github.com/"},
    ],
    "etl": [
        {"name": "AWS Skill Builder: Data Engineering", "url": "https://skillbuilder.aws/"},
        {"name": "Databricks Academy", "url": "https://www.databricks.com/learn/training/home"},
    ],
    "spark": [
        {"name": "Apache Spark Documentation", "url": "https://spark.apache.org/docs/latest/"},
        {"name": "Databricks Academy: Apache Spark", "url": "https://www.databricks.com/learn/training/home"},
    ],
    "hadoop": [
        {"name": "Apache Hadoop Documentation", "url": "https://hadoop.apache.org/docs/stable/"},
    ],
    "kafka": [
        {"name": "Apache Kafka Documentation", "url": "https://kafka.apache.org/documentation/"},
    ],
    "airflow": [
        {"name": "Apache Airflow Documentation", "url": "https://airflow.apache.org/docs/"},
    ],
    "cloud": [
        {"name": "AWS Skill Builder", "url": "https://skillbuilder.aws/"},
        {"name": "Microsoft Learn: Azure Fundamentals", "url": "https://learn.microsoft.com/en-us/training/paths/azure-fundamentals/"},
        {"name": "Google Cloud Skills Boost", "url": "https://www.cloudskillsboost.google/"},
    ],
    "data_warehousing": [
        {"name": "Google Cloud Skills Boost: BigQuery", "url": "https://www.cloudskillsboost.google/"},
        {"name": "AWS Skill Builder", "url": "https://skillbuilder.aws/"},
    ],
    "docker": [
        {"name": "Docker Official Docs", "url": "https://docs.docker.com/"},
    ],
    "kubernetes": [
        {"name": "Kubernetes Official Docs", "url": "https://kubernetes.io/docs/home/"},
    ],
    "terraform": [
        {"name": "HashiCorp Terraform Docs", "url": "https://developer.hashicorp.com/terraform/docs"},
    ],
    "cicd": [
        {"name": "GitHub Skills", "url": "https://skills.github.com/"},
    ],
    "linux": [
        {"name": "Linux Foundation Training", "url": "https://training.linuxfoundation.org/"},
    ],
    "git": [
        {"name": "GitHub Skills", "url": "https://skills.github.com/"},
        {"name": "Git Official Documentation", "url": "https://git-scm.com/doc"},
    ],
    "machine_learning": [
        {"name": "Google Cloud Skills Boost: ML", "url": "https://www.cloudskillsboost.google/"},
        {"name": "Kaggle Learn", "url": "https://www.kaggle.com/learn"},
    ],
    "deep_learning": [
        {"name": "Kaggle Learn: Deep Learning", "url": "https://www.kaggle.com/learn/intro-to-deep-learning"},
    ],
    "statistics": [
        {"name": "Kaggle Learn", "url": "https://www.kaggle.com/learn"},
    ],
    "data_analysis": [
        {"name": "Kaggle Learn: Data Analysis", "url": "https://www.kaggle.com/learn/pandas"},
        {"name": "Microsoft Learn: Data Analytics", "url": "https://learn.microsoft.com/en-us/training/paths/analyze-data-power-bi/"},
    ],
    "nlp": [
        {"name": "Kaggle Learn: NLP", "url": "https://www.kaggle.com/learn/natural-language-processing"},
    ],
    "computer_vision": [
        {"name": "Kaggle Learn: Computer Vision", "url": "https://www.kaggle.com/learn/computer-vision"},
    ],
    "data_visualization": [
        {"name": "Microsoft Learn: Power BI", "url": "https://learn.microsoft.com/en-us/training/powerplatform/power-bi"},
    ],
    "excel": [
        {"name": "Microsoft Learn: Excel", "url": "https://learn.microsoft.com/en-us/training/browse/?products=excel"},
    ],
    "react": [
        {"name": "React Official Docs", "url": "https://react.dev/learn"},
        {"name": "GitHub Skills", "url": "https://skills.github.com/"},
    ],
    "angular": [
        {"name": "Angular Official Docs", "url": "https://angular.dev/overview"},
    ],
    "vue": [
        {"name": "Vue.js Official Docs", "url": "https://vuejs.org/guide/introduction.html"},
    ],
    "html_css": [
        {"name": "MDN: HTML", "url": "https://developer.mozilla.org/en-US/docs/Web/HTML"},
        {"name": "MDN: CSS", "url": "https://developer.mozilla.org/en-US/docs/Web/CSS"},
    ],
    "rest_api": [
        {"name": "MDN: HTTP", "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP"},
    ],
    "flask": [
        {"name": "Flask Official Docs", "url": "https://flask.palletsprojects.com/"},
    ],
    "django": [
        {"name": "Django Official Docs", "url": "https://docs.djangoproject.com/"},
    ],
    "spring_boot": [
        {"name": "Spring Boot Official Docs", "url": "https://spring.io/projects/spring-boot"},
        {"name": "Spring Guides", "url": "https://spring.io/guides"},
    ],
    "mongodb": [
        {"name": "MongoDB Official Docs", "url": "https://www.mongodb.com/docs/"},
    ],
    "mysql": [
        {"name": "MySQL Official Docs", "url": "https://dev.mysql.com/doc/"},
        {"name": "Oracle Database Documentation", "url": "https://docs.oracle.com/en/database/"},
    ],
    "system_design": [
        {"name": "GitHub Skills", "url": "https://skills.github.com/"},
    ],
}


def get_skill_resources(skill_key):
    """Up to 3 curated, verified resources for a skill (never AI-generated)."""
    return SKILL_RESOURCES.get(skill_key, [])[:3]


def detect_skills_in_text(text):
    """
    Scan resume text for every skill key in SKILL_KEYWORDS.
    Returns a set of matched skill keys. Case-insensitive,
    word-boundary aware where useful.
    """
    if not text:
        return set()

    lower = text.lower()
    matched = set()

    for skill_key, patterns in SKILL_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, lower):
                matched.add(skill_key)
                break

    return matched


# ===============================================================
# ROLE CATALOG
# ---------------------------------------------------------------
# Each skill entry has a "weight": 3 = core/must-have, 2 = important,
# 1 = nice-to-have. Used to prioritize gaps and compute readiness.
# ===============================================================

CAREER_ROLES = {
    "data_engineer": {
        "name": "Data Engineer",
        "icon": "bi-hdd-network",
        "description": "Builds and maintains the data pipelines and infrastructure that move and transform data at scale.",
        "skills": [
            {"key": "python", "weight": 3},
            {"key": "sql", "weight": 3},
            {"key": "etl", "weight": 3},
            {"key": "spark", "weight": 3},
            {"key": "cloud", "weight": 3},
            {"key": "data_warehousing", "weight": 2},
            {"key": "airflow", "weight": 2},
            {"key": "kafka", "weight": 1},
            {"key": "hadoop", "weight": 1},
            {"key": "docker", "weight": 1},
            {"key": "git", "weight": 1},
        ],
    },
    "data_scientist": {
        "name": "Data Scientist",
        "icon": "bi-graph-up",
        "description": "Analyzes data and builds statistical/ML models to generate insights and predictions.",
        "skills": [
            {"key": "python", "weight": 3},
            {"key": "sql", "weight": 3},
            {"key": "statistics", "weight": 3},
            {"key": "machine_learning", "weight": 3},
            {"key": "data_analysis", "weight": 2},
            {"key": "data_visualization", "weight": 2},
            {"key": "deep_learning", "weight": 1},
            {"key": "nlp", "weight": 1},
            {"key": "cloud", "weight": 1},
            {"key": "git", "weight": 1},
        ],
    },
    "ml_engineer": {
        "name": "Machine Learning Engineer",
        "icon": "bi-cpu",
        "description": "Designs, trains, and deploys machine learning models into production systems.",
        "skills": [
            {"key": "python", "weight": 3},
            {"key": "machine_learning", "weight": 3},
            {"key": "deep_learning", "weight": 3},
            {"key": "sql", "weight": 2},
            {"key": "cloud", "weight": 2},
            {"key": "docker", "weight": 2},
            {"key": "cicd", "weight": 1},
            {"key": "kubernetes", "weight": 1},
            {"key": "computer_vision", "weight": 1},
            {"key": "nlp", "weight": 1},
        ],
    },
    "full_stack_developer": {
        "name": "Full Stack Developer",
        "icon": "bi-layers",
        "description": "Builds both the frontend and backend of web applications end to end.",
        "skills": [
            {"key": "javascript", "weight": 3},
            {"key": "html_css", "weight": 3},
            {"key": "react", "weight": 2},
            {"key": "rest_api", "weight": 3},
            {"key": "mysql", "weight": 2},
            {"key": "mongodb", "weight": 1},
            {"key": "git", "weight": 2},
            {"key": "docker", "weight": 1},
            {"key": "django", "weight": 1},
            {"key": "flask", "weight": 1},
        ],
    },
    "backend_developer": {
        "name": "Backend Developer",
        "icon": "bi-server",
        "description": "Builds the server-side logic, APIs and databases that power applications.",
        "skills": [
            {"key": "python", "weight": 2},
            {"key": "java", "weight": 2},
            {"key": "sql", "weight": 3},
            {"key": "rest_api", "weight": 3},
            {"key": "spring_boot", "weight": 2},
            {"key": "flask", "weight": 1},
            {"key": "django", "weight": 1},
            {"key": "system_design", "weight": 2},
            {"key": "git", "weight": 2},
            {"key": "docker", "weight": 1},
        ],
    },
    "devops_engineer": {
        "name": "DevOps Engineer",
        "icon": "bi-diagram-3",
        "description": "Automates deployment pipelines and manages the infrastructure applications run on.",
        "skills": [
            {"key": "linux", "weight": 3},
            {"key": "cloud", "weight": 3},
            {"key": "docker", "weight": 3},
            {"key": "kubernetes", "weight": 3},
            {"key": "cicd", "weight": 3},
            {"key": "terraform", "weight": 2},
            {"key": "git", "weight": 2},
            {"key": "python", "weight": 1},
        ],
    },
}


def get_all_roles():
    """Return the role catalog as a list of dicts (role_key included)."""
    roles = []
    for key, data in CAREER_ROLES.items():
        roles.append({
            "role_key": key,
            "name": data["name"],
            "icon": data["icon"],
            "description": data["description"],
            "skill_count": len(data["skills"]),
        })
    return roles


def get_role(role_key):
    """Return one role's full definition (including skills), or None."""
    data = CAREER_ROLES.get(role_key)
    if not data:
        return None
    return {
        "role_key": role_key,
        "name": data["name"],
        "icon": data["icon"],
        "description": data["description"],
        "skills": data["skills"],
    }
