"""
modules/quiz_bank.py
----------------------
Static skill-assessment question bank used by the Career Tracker
dashboard. Each skill maps to a list of multiple-choice questions.
Kept as plain Python data (same style as resume_parser.COMMON_SKILLS)
so the assessment feature has no extra external dependency.

Question shape:
{
    "question": str,
    "options": [str, str, str, str],
    "correct_index": int   # index into "options"
}
"""

QUESTION_BANK = {

    "python": [
        {
            "question": "Which keyword is used to define a function in Python?",
            "options": ["func", "def", "function", "lambda"],
            "correct_index": 1,
        },
        {
            "question": "What does the following return? len([1, 2, 3])",
            "options": ["2", "3", "1", "Error"],
            "correct_index": 1,
        },
        {
            "question": "Which data type is immutable in Python?",
            "options": ["list", "dict", "tuple", "set"],
            "correct_index": 2,
        },
        {
            "question": "What is the output of 3 // 2 in Python?",
            "options": ["1.5", "1", "2", "1.0"],
            "correct_index": 1,
        },
        {
            "question": "Which module is commonly used for DataFrame operations?",
            "options": ["numpy", "pandas", "requests", "os"],
            "correct_index": 1,
        },
    ],

    "sql": [
        {
            "question": "Which SQL clause is used to filter rows before grouping?",
            "options": ["HAVING", "WHERE", "GROUP BY", "ORDER BY"],
            "correct_index": 1,
        },
        {
            "question": "Which SQL clause filters groups after aggregation?",
            "options": ["WHERE", "GROUP BY", "HAVING", "LIMIT"],
            "correct_index": 2,
        },
        {
            "question": "Which JOIN returns only matching rows from both tables?",
            "options": ["LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "FULL OUTER JOIN"],
            "correct_index": 2,
        },
        {
            "question": "Which keyword removes duplicate rows from a result set?",
            "options": ["UNIQUE", "DISTINCT", "FILTER", "GROUP"],
            "correct_index": 1,
        },
        {
            "question": "Which command permanently removes a table and its data?",
            "options": ["DELETE TABLE", "REMOVE TABLE", "DROP TABLE", "TRUNCATE ROW"],
            "correct_index": 2,
        },
    ],

    "etl": [
        {
            "question": "What does ETL stand for?",
            "options": [
                "Extract, Transform, Load",
                "Evaluate, Test, Launch",
                "Export, Transfer, Log",
                "Encode, Translate, Link",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which stage typically cleans and reshapes raw data?",
            "options": ["Extract", "Transform", "Load", "Archive"],
            "correct_index": 1,
        },
        {
            "question": "What is a common reason to schedule ETL jobs incrementally?",
            "options": [
                "To avoid reprocessing the entire dataset every run",
                "To make queries slower",
                "To skip data validation",
                "To reduce table columns",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which of these is a common orchestration tool for ETL pipelines?",
            "options": ["Photoshop", "Airflow", "Figma", "Excel"],
            "correct_index": 1,
        },
        {
            "question": "What is a 'data pipeline'?",
            "options": [
                "A physical network cable",
                "A series of steps that move and transform data from source to destination",
                "A type of database index",
                "A user interface component",
            ],
            "correct_index": 1,
        },
    ],

    "spark": [
        {
            "question": "What is Apache Spark primarily used for?",
            "options": [
                "Distributed large-scale data processing",
                "Front-end web design",
                "Mobile app development",
                "Image editing",
            ],
            "correct_index": 0,
        },
        {
            "question": "What is an RDD in Spark?",
            "options": [
                "A Resilient Distributed Dataset",
                "A relational database driver",
                "A rendering data device",
                "A REST data descriptor",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which Spark component is used for SQL-style queries on structured data?",
            "options": ["Spark Streaming", "Spark SQL", "MLlib", "GraphX"],
            "correct_index": 1,
        },
        {
            "question": "What does 'lazy evaluation' mean in Spark?",
            "options": [
                "Transformations are not executed until an action is called",
                "Spark runs slower than other engines",
                "Code errors are ignored",
                "Data is never actually processed",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which language is Spark's PySpark API primarily for?",
            "options": ["Python", "PHP", "Ruby", "Swift"],
            "correct_index": 0,
        },
    ],

    "cloud": [
        {
            "question": "Which of these is a major cloud service provider?",
            "options": ["AWS", "MySQL", "Postman", "VS Code"],
            "correct_index": 0,
        },
        {
            "question": "What does 'IaaS' stand for in cloud computing?",
            "options": [
                "Infrastructure as a Service",
                "Internet as a Server",
                "Information as a Storage",
                "Interface as a System",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which AWS service is primarily used for object storage?",
            "options": ["EC2", "S3", "RDS", "Lambda"],
            "correct_index": 1,
        },
        {
            "question": "What is 'auto-scaling' in cloud environments?",
            "options": [
                "Automatically adjusting compute resources based on demand",
                "Automatically deleting unused files",
                "Manually resizing a database",
                "Automatically writing code",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which of these is a serverless compute service?",
            "options": ["AWS Lambda", "AWS S3", "AWS RDS", "AWS VPC"],
            "correct_index": 0,
        },
    ],

    "machine_learning": [
        {
            "question": "Which of these is a supervised learning algorithm?",
            "options": ["K-Means", "Linear Regression", "PCA", "Apriori"],
            "correct_index": 1,
        },
        {
            "question": "What is 'overfitting' in machine learning?",
            "options": [
                "The model performs well on training data but poorly on new data",
                "The model is too simple to learn patterns",
                "The dataset is too small to train on",
                "The model trains too quickly",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which metric is commonly used to evaluate classification models?",
            "options": ["RMSE", "F1-Score", "R-squared", "MAE"],
            "correct_index": 1,
        },
        {
            "question": "What is the purpose of splitting data into train/test sets?",
            "options": [
                "To evaluate how well the model generalizes to unseen data",
                "To make the dataset smaller",
                "To remove missing values",
                "To speed up data loading",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which technique helps reduce overfitting?",
            "options": ["Regularization", "Adding more layers only", "Ignoring validation data", "Removing all features"],
            "correct_index": 0,
        },
    ],

    "git": [
        {
            "question": "Which command creates a new local branch?",
            "options": ["git branch <name>", "git new <name>", "git create <name>", "git init <name>"],
            "correct_index": 0,
        },
        {
            "question": "Which command stages changes for commit?",
            "options": ["git add", "git commit", "git push", "git stage-only"],
            "correct_index": 0,
        },
        {
            "question": "What does 'git clone' do?",
            "options": [
                "Creates a local copy of a remote repository",
                "Deletes a repository",
                "Merges two branches",
                "Creates a new file",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which command uploads local commits to a remote repository?",
            "options": ["git pull", "git fetch", "git push", "git merge"],
            "correct_index": 2,
        },
        {
            "question": "What is a 'merge conflict'?",
            "options": [
                "When Git cannot automatically combine changes from two branches",
                "When a repository has no commits",
                "When a branch is deleted",
                "When Git is not installed",
            ],
            "correct_index": 0,
        },
    ],

    "javascript": [
        {
            "question": "Which keyword declares a block-scoped variable in modern JavaScript?",
            "options": ["var", "let", "define", "int"],
            "correct_index": 1,
        },
        {
            "question": "What does '===' check in JavaScript?",
            "options": [
                "Value and type equality",
                "Value equality only",
                "Reference equality only",
                "Nothing, it's invalid syntax",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which method converts a JSON string into a JavaScript object?",
            "options": ["JSON.stringify()", "JSON.parse()", "JSON.toObject()", "Object.fromJSON()"],
            "correct_index": 1,
        },
        {
            "question": "What is a Promise used for in JavaScript?",
            "options": [
                "Handling asynchronous operations",
                "Declaring variables",
                "Styling HTML elements",
                "Defining CSS classes",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which array method creates a new array with transformed elements?",
            "options": ["forEach", "map", "filter only", "reduce only"],
            "correct_index": 1,
        },
    ],

    "docker": [
        {
            "question": "What is a Docker image?",
            "options": [
                "A read-only template used to create containers",
                "A running instance of an application",
                "A virtual machine hypervisor",
                "A cloud storage bucket",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which file defines how a Docker image is built?",
            "options": ["docker.yml", "Dockerfile", "image.json", "build.docker"],
            "correct_index": 1,
        },
        {
            "question": "Which command lists running containers?",
            "options": ["docker ls", "docker ps", "docker list", "docker show"],
            "correct_index": 1,
        },
        {
            "question": "What is the benefit of containerization?",
            "options": [
                "Consistent environments across development and production",
                "Automatically writing application code",
                "Replacing the need for version control",
                "Eliminating the need for a database",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which command builds a Docker image from a Dockerfile?",
            "options": ["docker run", "docker build", "docker start", "docker compile"],
            "correct_index": 1,
        },
    ],

    "linux": [
        {
            "question": "Which command lists files in a directory?",
            "options": ["ls", "dir-list", "show", "list-files"],
            "correct_index": 0,
        },
        {
            "question": "Which command changes file permissions?",
            "options": ["chperm", "chmod", "permit", "setperm"],
            "correct_index": 1,
        },
        {
            "question": "Which command shows currently running processes?",
            "options": ["ps", "proc", "tasks", "jobs-all"],
            "correct_index": 0,
        },
        {
            "question": "What does 'grep' do?",
            "options": [
                "Searches text using patterns",
                "Compresses files",
                "Changes file ownership",
                "Schedules cron jobs",
            ],
            "correct_index": 0,
        },
        {
            "question": "Which symbol redirects command output to a file, overwriting it?",
            "options": ["|", ">>", ">", "<"],
            "correct_index": 2,
        },
    ],

}


def get_quiz(skill_key):
    """Return the question list for a skill key, or an empty list."""
    return QUESTION_BANK.get(skill_key, [])


def has_quiz(skill_key):
    """True if an assessment exists for this skill."""
    return skill_key in QUESTION_BANK and len(QUESTION_BANK[skill_key]) > 0


def get_available_skill_keys():
    """All skill keys that currently have an assessment available."""
    return list(QUESTION_BANK.keys())
