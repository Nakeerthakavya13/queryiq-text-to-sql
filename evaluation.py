
import time
import pandas as pd

from local_fallback import generate_local_sql
from sql_runner import run_query


TEST_CASES = [
    {
        "question": "Show all students",
        "expected_sql": """
            SELECT * FROM students ORDER BY name
        """,
    },
    {
        "question": "List students in Data Science",
        "expected_sql": """
            SELECT * FROM students
            WHERE LOWER(department) LIKE '%data science%'
               OR LOWER(department) LIKE '%datascience%'
               OR LOWER(department) = 'ds'
            ORDER BY name
        """,
    },
    {
        "question": "Show the top 5 students by marks",
        "expected_sql": """
            SELECT s.name, s.department, sc.subject, sc.marks, sc.grade
            FROM students s
            JOIN scores sc ON s.student_id = sc.student_id
            ORDER BY sc.marks DESC
            LIMIT 5
        """,
    },
    {
        "question": "What is the average mark for each subject?",
        "expected_sql": """
            SELECT subject, ROUND(AVG(marks), 2) AS average_marks
            FROM scores
            GROUP BY subject
            ORDER BY average_marks DESC
        """,
    },
    {
        "question": "Show students with attendance below 75%",
        "expected_sql": """
            SELECT s.name, s.department, a.subject,
                   a.present_days, a.total_days, a.percentage
            FROM students s
            JOIN attendance a ON s.student_id = a.student_id
            WHERE a.percentage < 75
            ORDER BY a.percentage
        """,
    },
    {
        "question": "List faculty with more than 8 years of experience",
        "expected_sql": """
            SELECT * FROM faculty
            WHERE experience_years > 8
            ORDER BY experience_years DESC
        """,
    },
    {
        "question": "Show students whose names start with A",
        "expected_sql": """
            SELECT * FROM students
            WHERE UPPER(name) LIKE 'A%'
            ORDER BY name
        """,
    },
]


def normalize_dataframe(df):
    """Normalize column and row order before comparing results."""
    if df is None:
        return None

    df = df.copy()
    df.columns = [str(col) for col in df.columns]
    df = df.reindex(sorted(df.columns), axis=1)

    if not df.empty:
        df = df.sort_values(
            by=list(df.columns),
            key=lambda col: col.astype(str),
            kind="stable",
        )

    return df.reset_index(drop=True)


def evaluate_local_fallback():
    results = []

    for case in TEST_CASES:
        question = case["question"]
        start = time.perf_counter()

        status = "Failed"
        correctness = "Not checked"
        row_count = 0
        details = ""

        try:
            generated_sql = generate_local_sql(question)

            if not generated_sql:
                status = "Unsupported"
                details = "Local fallback returned no SQL."

            else:
                actual = run_query(generated_sql)
                expected = run_query(case["expected_sql"])

                row_count = len(actual)
                status = "Success"

                actual_normalized = normalize_dataframe(actual)
                expected_normalized = normalize_dataframe(expected)

                if actual_normalized.equals(expected_normalized):
                    correctness = "Correct"
                else:
                    correctness = "Incorrect"
                    details = (
                        "Generated results differ from reference results."
                    )

        except Exception as error:
            details = f"{type(error).__name__}: {error}"

        elapsed_ms = round(
            (time.perf_counter() - start) * 1000, 2
        )

        results.append({
            "Question": question,
            "Status": status,
            "Correctness": correctness,
            "Rows": row_count,
            "Time (ms)": elapsed_ms,
            "Details": details,
        })

    return pd.DataFrame(results)
