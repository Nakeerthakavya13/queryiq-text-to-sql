
import time
import pandas as pd

from local_fallback import generate_local_sql
from sql_runner import run_query


TEST_CASES = [
    {
        "question": "Show all students",
        "expected": "SELECT * FROM students ORDER BY name",
    },
    {
        "question": "Count students",
        "expected": "SELECT COUNT(*) AS total_students FROM students",
    },
    {
        "question": "Count students in CSE",
        "expected": (
            "SELECT COUNT(*) AS total_students FROM students "
            "WHERE (LOWER(department) LIKE '%cse%' OR "
            "LOWER(department) LIKE '%computer science%')"
        ),
    },
    {
        "question": "Show average age of students",
        "expected": (
            "SELECT ROUND(AVG(age), 2) AS average_age FROM students"
        ),
    },
    {
        "question": "Show the top 5 oldest students",
        "expected": (
            "SELECT * FROM students ORDER BY age DESC, name LIMIT 5"
        ),
    },
    {
        "question": "Show students older than 20",
        "expected": (
            "SELECT * FROM students "
            "WHERE age > 20 ORDER BY age DESC, name"
        ),
    },
    {
        "question": "Show students in XYZ department",
        "expected": None,
    },
]


def normalize_sql(sql):
    if sql is None:
        return None
    return " ".join(sql.lower().split()).rstrip(";")


def evaluate_local_fallback():
    results = []

    for case in TEST_CASES:
        start = time.perf_counter()
        question = case["question"]
        expected_sql = case["expected"]

        try:
            generated_sql = generate_local_sql(question)

            if generated_sql is None:
                status = (
                    "Correctly unsupported"
                    if expected_sql is None
                    else "Unsupported"
                )
                correct = expected_sql is None
                rows = 0

            elif expected_sql is None:
                status = "Incorrectly supported"
                correct = False
                rows = 0

            else:
                actual = run_query(generated_sql)
                expected = run_query(expected_sql)

                correct = (
                    normalize_sql(generated_sql)
                    == normalize_sql(expected_sql)
                    and actual.equals(expected)
                )
                status = "Success" if correct else "Incorrect"
                rows = len(actual)

        except Exception as error:
            status = "Failed"
            correct = False
            rows = 0
            error_message = str(error)
        else:
            error_message = ""

        results.append({
            "Question": question,
            "Status": status,
            "Correctness": "Correct" if correct else "Incorrect",
            "Rows": rows,
            "Time (ms)": round(
                (time.perf_counter() - start) * 1000, 2
            ),
            "Details": error_message,
        })

    return pd.DataFrame(results)
