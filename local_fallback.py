
import re

DEPARTMENTS = {
    "data science": (
        "LOWER(department) LIKE '%data science%' OR "
        "LOWER(department) LIKE '%datascience%' OR "
        "LOWER(department) = 'ds'",
        ["data science", "datascience", "data-science", "ds"]
    ),
    "cse": (
        "LOWER(department) LIKE '%cse%' OR "
        "LOWER(department) LIKE '%computer science%'",
        ["cse", "computer science"]
    ),
    "ece": (
        "LOWER(department) LIKE '%ece%' OR "
        "LOWER(department) LIKE '%electronics%'",
        ["ece", "electronics"]
    ),
    "eee": (
        "LOWER(department) LIKE '%eee%' OR "
        "LOWER(department) LIKE '%electrical%'",
        ["eee", "electrical"]
    ),
    "mechanical": (
        "LOWER(department) LIKE '%mechanical%'",
        ["mechanical", "mech"]
    ),
    "civil": (
        "LOWER(department) LIKE '%civil%'",
        ["civil"]
    ),
}


def generate_local_sql(question):
    if not isinstance(question, str) or not question.strip():
        return None

    q = re.sub(r"[?!.,]+", " ", question.lower().strip())
    q = re.sub(r"\s+", " ", q)

    def get_number(pattern):
        match = re.search(pattern, q)
        return match.group(1) if match else None

    student = "student" in q
    faculty = "faculty" in q or "faculties" in q
    count = any(x in q for x in [
        "count", "how many", "number of", "total number"
    ])

    # Identify department
    dept = None
    for key, (_, aliases) in DEPARTMENTS.items():
        if any(re.search(r"\b" + re.escape(a) + r"\b", q)
               for a in aliases):
            dept = key
            break

    dept_requested = (
        "department" in q
        or "students in " in q
        or "student in " in q
    )

    # Count students, including department filters
    if count and student:
        if dept_requested and dept is None:
            return None

        where = ""
        if dept:
            where = f" WHERE ({DEPARTMENTS[dept][0]})"

        return (
            "SELECT COUNT(*) AS total_students "
            f"FROM students{where}"
        )

    if count and faculty:
        return "SELECT COUNT(*) AS total_faculty FROM faculty"

    if count and any(x in q for x in ["score", "mark", "grade"]):
        return "SELECT COUNT(*) AS total_scores FROM scores"

    # Average age
    if student and "average" in q and "age" in q:
        return (
            "SELECT ROUND(AVG(age), 2) AS average_age "
            "FROM students"
        )

    # Average marks
    if "average" in q and any(
        x in q for x in ["mark", "marks", "score", "scores"]
    ):
        if "subject" in q or "each subject" in q or "per subject" in q:
            return """
                SELECT subject, ROUND(AVG(marks), 2) AS average_marks
                FROM scores
                GROUP BY subject
                ORDER BY average_marks DESC
            """
        return "SELECT ROUND(AVG(marks), 2) AS average_marks FROM scores"

    # Top or bottom students by age
    n = get_number(r"\b(?:top|first|bottom|lowest)\s+(\d+)\b")
    limit = max(1, min(int(n), 100)) if n else 10

    if student and "oldest" in q:
        return (
            "SELECT * FROM students "
            f"ORDER BY age DESC, name LIMIT {limit}"
        )

    if student and "youngest" in q:
        return (
            "SELECT * FROM students "
            f"ORDER BY age ASC, name LIMIT {limit}"
        )

    # Department filter; unknown departments are unsupported
    if student and dept_requested:
        if dept is None:
            return None

        return (
            "SELECT * FROM students "
            f"WHERE ({DEPARTMENTS[dept][0]}) ORDER BY name"
        )

    # Names starting with a letter
    if student and any(x in q for x in [
        "starting with", "beginning with", "start with",
        "names start", "name begins"
    ]):
        match = re.search(
            r"(?:starting with|beginning with|start with|"
            r"names? start(?:ing)? with|name begins with)\s+([a-z])\b",
            q
        )
        if not match:
            return None

        letter = match.group(1).upper()
        return (
            "SELECT * FROM students "
            f"WHERE UPPER(name) LIKE '{letter}%' ORDER BY name"
        )

    # Student age filters
    if student and (
        "age" in q
        or "older than" in q
        or "younger than" in q
    ):
        n = get_number(r"\b(\d+)\b")
        if not n:
            return None

        if any(x in q for x in ["older than", "above", "over", "greater than"]):
            op = ">"
        elif any(x in q for x in ["younger than", "below", "under", "less than"]):
            op = "<"
        else:
            op = "="

        return (
            "SELECT * FROM students "
            f"WHERE age {op} {int(n)} ORDER BY age DESC, name"
        )

    # Student year
    if student and "year" in q:
        words = {"first": 1, "second": 2, "third": 3, "fourth": 4}
        year = next(
            (v for word, v in words.items()
             if re.search(r"\b" + word + r"\b", q)),
            None
        )

        if year is None:
            n = get_number(r"\b([1-4])(?:st|nd|rd|th)?\s*year\b")
            year = int(n) if n else None

        if year:
            return (
                f"SELECT * FROM students WHERE year = {year} "
                "ORDER BY name"
            )
        return None

    # Top marks
    if any(x in q for x in ["top", "highest", "maximum", "best"]) and any(
        x in q for x in ["student", "mark", "marks", "score", "scores"]
    ):
        n = get_number(r"\btop\s+(\d+)\b")
        limit = max(1, min(int(n), 100)) if n else 10

        return f"""
            SELECT s.name, s.department, sc.subject, sc.marks, sc.grade
            FROM students s
            JOIN scores sc ON s.student_id = sc.student_id
            ORDER BY sc.marks DESC, s.name
            LIMIT {limit}
        """

    # Lowest marks
    if any(x in q for x in [
        "lowest marks", "minimum marks", "lowest score",
        "bottom students", "bottom marks"
    ]):
        n = get_number(r"\b(?:bottom|lowest)\s+(\d+)\b")
        limit = max(1, min(int(n), 100)) if n else 10

        return f"""
            SELECT s.name, s.department, sc.subject, sc.marks, sc.grade
            FROM students s
            JOIN scores sc ON s.student_id = sc.student_id
            ORDER BY sc.marks ASC, s.name
            LIMIT {limit}
        """

    # Marks thresholds
    if any(x in q for x in ["mark", "marks", "score", "scores", "grade"]):
        n = get_number(r"\b(\d+(?:\.\d+)?)\s*%?\b")

        if n and any(x in q for x in [
            "above", "greater than", "more than", "below", "less than", "under"
        ]):
            op = "<" if any(
                x in q for x in ["below", "less than", "under"]
            ) else ">"

            threshold = float(n)
            if 0 <= threshold <= 100:
                return f"""
                    SELECT s.name, s.department, sc.subject, sc.marks, sc.grade
                    FROM students s
                    JOIN scores sc ON s.student_id = sc.student_id
                    WHERE sc.marks {op} {threshold}
                    ORDER BY sc.marks DESC, s.name
                """

    # Attendance
    if "attendance" in q:
        n = get_number(r"\b(\d+(?:\.\d+)?)\s*%?")

        if n and any(x in q for x in [
            "below", "less than", "under", "above", "greater than", "more than"
        ]):
            op = "<" if any(
                x in q for x in ["below", "less than", "under"]
            ) else ">"

            threshold = max(0, min(float(n), 100))
            return f"""
                SELECT s.name, s.department, a.subject,
                       a.present_days, a.total_days, a.percentage
                FROM students s
                JOIN attendance a ON s.student_id = a.student_id
                WHERE a.percentage {op} {threshold}
                ORDER BY a.percentage, s.name
            """

        return """
            SELECT s.name, s.department, a.subject,
                   a.present_days, a.total_days, a.percentage
            FROM students s
            JOIN attendance a ON s.student_id = a.student_id
            ORDER BY a.percentage, s.name
        """

    # Faculty experience
    if faculty and "experience" in q:
        n = get_number(r"\b(\d+(?:\.\d+)?)\b")
        if not n:
            return None

        years = float(n)
        op = (
            ">" if any(x in q for x in ["more than", "above", "over", "greater than"])
            else "<" if any(x in q for x in ["less than", "below", "under"])
            else ">="
        )

        return f"""
            SELECT * FROM faculty
            WHERE experience_years {op} {years}
            ORDER BY experience_years DESC
        """

    if faculty:
        return "SELECT * FROM faculty ORDER BY name"

    # All students
    if student and any(x in q for x in ["show", "list", "all", "display"]):
        return "SELECT * FROM students ORDER BY name"

    # General marks listing
    if any(x in q for x in ["marks", "scores", "grades", "score"]):
        return """
            SELECT s.name, s.department, sc.subject,
                   sc.marks, sc.grade, sc.semester
            FROM students s
            JOIN scores sc ON s.student_id = sc.student_id
            ORDER BY s.name, sc.subject, sc.semester
        """

    return None


def explain_local_result(question, dataframe):
    if dataframe.empty:
        return (
            "The query ran successfully, but no matching records were found. "
            "Check your filters or the database values."
        )

    return (
        f"For your question, '{question}', the database returned "
        f"{len(dataframe)} row(s) and {len(dataframe.columns)} column(s). "
        "Review the table for the exact results."
    )
