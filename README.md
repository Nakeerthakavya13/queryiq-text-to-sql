
# Text-to-SQL Natural Language Interface

## Project Overview
The Text-to-SQL Natural Language Interface allows users to query college database information using plain English questions. The application converts supported questions into SQL queries, executes them on an SQLite database, and displays results in a Streamlit interface.

## Technologies Used
- Python
- Streamlit
- SQLite
- Pandas
- Google Gemini API (when API access is available)

## Features
- Natural-language question input
- SQL query generation for supported questions
- SQLite query execution
- Student, score, attendance, and faculty data
- Query results displayed in a table
- CSV download
- Query history
- Basic SQL safety validation
- Local rule-based fallback when Gemini is unavailable
- Result explanations

## Database Tables
- `students`: student ID, name, age, gender, department, year
- `scores`: score ID, student ID, subject, marks, grade, semester
- `attendance`: attendance ID, student ID, subject, present days, total days, percentage
- `faculty`: faculty ID, name, department, subject, experience years

## Project Structure
```text
text_to_sql_project/
├── app.py
├── database.py
├── gemini_helper.py
├── local_fallback.py
├── sql_runner.py
├── college.db
├── requirements.txt
└── README.md
```

## Setup
1. Install Python.
2. Open a terminal in the project directory.
3. Create a virtual environment:

   `py -m venv .venv`

4. Activate it in PowerShell:

   `.\.venv\Scripts\Activate.ps1`

5. Install dependencies:

   `py -m pip install streamlit pandas google-genai`

## Run the Application
Run:

`py -m streamlit run app.py`

Open the local URL shown in the terminal, usually `http://localhost:8501`.

## Gemini API
Gemini SQL generation and explanations require a valid API key and internet access. Set `GEMINI_API_KEY` in the terminal before launching the app if using Gemini.

The local fallback supports only the question patterns implemented in `local_fallback.py`. Unsupported questions will need Gemini access or additional fallback rules.

## Safety
The application permits read-only SQL queries and uses SQLite query-only mode during execution. The SQL validation is a basic safeguard and should not be treated as a complete security boundary.

## Sample Questions
- Show all students
- List students in Data Science
- Show the top 10 students by marks
- What is the average mark for each subject?
- Show students with attendance below 75%
- List faculty with more than 8 years of experience

## Limitations
- Local fallback supports predefined question patterns.
- Sample database records are synthetic.
- Gemini functionality depends on API authentication and availability.

## Future Enhancements
- Broader natural-language query support
- Voice-based queries
- Improved query confidence estimation
- Deployment to a public hosting platform
