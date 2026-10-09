
import re


def generate_local_sql(question):
    q = question.lower().strip()
    q = re.sub(r"[?!.,]+", " ", q)
    q = re.sub(r"\s+", " ", q)

    def get_number(pattern):
        match = re.search(pattern, q)
        return match.group(1) if match else None

    # Count records
    if any(x in q for x in ["count", "how many", "number of"]):
        if "student" in q:
            return "SELECT COUNT(*) AS total_students FROM students"
        if "faculty" in q:
            return "SELECT COUNT(*) AS total_faculty FROM faculty"
        if "score" in q or "mark" in q:
            return "SELECT COUNT(*) AS total_scores FROM scores"

    # Student names starting with a letter
    if "student" in q and any(
        x in q for x in [
            "starting with", "beginning with", "start with",
            "names start", "name start", "name begins"
        ]
    ):
        match = re.search(
            r"(?:starting with|beginning with|start with|"
            r"names? start(?:ing)? with|name begins with)\s+([a-z])\b",
            q
        )
        if match:
            letter = match.group(1).upper()
            return (
                "SELECT * FROM students "
                f"WHERE UPPER(name) LIKE '{letter}%' ORDER BY name"
            )

    # Search by student name
    if "student" in q and any(
        x in q for x in ["named", "name is", "called"]
    ):
        match = re.search(
            r"(?:named|name is|called)\s+([a-z]+(?:\s+[a-z]+){0,2})",
            q
        )
        if match:
            name = match.group(1).strip().replace("'", "''")
            return (
                "SELECT * FROM students "
                f"WHERE LOWER(name) LIKE '%{name}%' ORDER BY name"
            )

    # Department filters
    departments = {
        "data science": ["data science", "datascience"],
        "cse": ["cse", "computer science"],
        "ece": ["ece", "electronics"],
        "eee": ["eee", "electrical"],
        "mechanical": ["mechanical", "mech"],
        "civil": ["civil"],
    }

    if "student" in q:
        for dept, terms in departments.items():
            if any(term in q for term in terms):
                if dept == "data science":
                    condition = (
                        "LOWER(department) LIKE '%data science%' "
                        "OR LOWER(department) LIKE '%datascience%' "
                        "OR LOWER(department) = 'ds'"
                    )
                elif dept == "cse":
                    condition = (
                        "LOWER(department) LIKE '%cse%' "
                        "OR LOWER(department) LIKE '%computer science%'"
                    )
                elif dept == "ece":
                    condition = (
                        "LOWER(department) LIKE '%ece%' "
                        "OR LOWER(department) LIKE '%electronics%'"
                    )
                elif dept == "eee":
                    condition = (
                        "LOWER(department) LIKE '%eee%' "
                        "OR LOWER(department) LIKE '%electrical%'"
                    )
                else:
                    condition = f"LOWER(department) LIKE '%{dept}%'"

                return (
                    f"SELECT * FROM students WHERE ({condition}) "
                    "ORDER BY name"
                )

    # Student age
    if "student" in q and "age" in q:
        n = get_number(r"\b(\d+)\b")
        if n:
            op = (
                ">" if any(x in q for x in ["older than", "above", "greater than"])
                else "<" if any(x in q for x in ["younger than", "below", "less than"])
                else "="
            )
            return f"SELECT * FROM students WHERE age {op} {int(n)}"

    # Student year
    if "student" in q and "year" in q:
        words = {"first": 1, "second": 2, "third": 3, "fourth": 4}
        year = next((v for word, v in words.items() if word in q), None)

        if year is None:
            n = get_number(r"\b([1-4])(?:st|nd|rd|th)?\s*year\b")
            year = int(n) if n else None

        if year:
            return f"SELECT * FROM students WHERE year = {year} ORDER BY name"

    # Average marks by subject
    if "average" in q and any(x in q for x in ["mark", "score", "grade"]):
        return """
            SELECT subject, ROUND(AVG(marks), 2) AS average_marks
            FROM scores
            GROUP BY subject
            ORDER BY average_marks DESC
        """

    # Top marks
    if "top" in q and any(x in q for x in ["student", "mark", "score"]):
        n = get_number(r"\btop\s+(\d+)\b")
        limit = max(1, min(int(n), 100)) if n else 10
        return f"""
            SELECT s.name, s.department, sc.subject, sc.marks, sc.grade
            FROM students s
            JOIN scores sc ON s.student_id = sc.student_id
            ORDER BY sc.marks DESC
            LIMIT {limit}
        """

    if any(x in q for x in [
        "highest marks", "maximum marks", "top marks", "highest score"
    ]):
        return """
            SELECT s.name, s.department, sc.subject, sc.marks, sc.grade
            FROM students s
            JOIN scores sc ON s.student_id = sc.student_id
            ORDER BY sc.marks DESC LIMIT 10
        """

    # Lowest marks
    if any(x in q for x in [
        "lowest marks", "minimum marks", "lowest score", "bottom students"
    ]):
        n = get_number(r"\b(?:bottom|lowest)\s+(\d+)\b")
        limit = max(1, min(int(n), 100)) if n else 10
        return f"""
            SELECT s.name, s.department, sc.subject, sc.marks, sc.grade
            FROM students s
            JOIN scores sc ON s.student_id = sc.student_id
            ORDER BY sc.marks ASC LIMIT {limit}
        """

    # Marks above or below a threshold
    if any(x in q for x in ["mark", "score", "grade"]):
        n = get_number(
            r"\b(\d+(?:\.\d+)?)\s*(?:marks?|scores?)?\b"
        )
        if n and any(x in q for x in [
            "above", "greater than", "more than", "below", "less than"
        ]):
            op = "<" if any(x in q for x in ["below", "less than"]) else ">"
            threshold = float(n)
            if 0 <= threshold <= 100:
                return f"""
                    SELECT s.name, s.department, sc.subject, sc.marks, sc.grade
                    FROM students s
                    JOIN scores sc ON s.student_id = sc.student_id
                    WHERE sc.marks {op} {threshold}
                    ORDER BY sc.marks DESC
                """

    # Attendance threshold
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
                ORDER BY a.percentage
            """

        return """
            SELECT s.name, s.department, a.subject,
                   a.present_days, a.total_days, a.percentage
            FROM students s
            JOIN attendance a ON s.student_id = a.student_id
            ORDER BY a.percentage
        """

    # Faculty experience
    if "faculty" in q and "experience" in q:
        n = get_number(r"\b(\d+(?:\.\d+)?)\b")
        years = float(n) if n else 8

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

    # Faculty listing
    if "faculty" in q:
        return "SELECT * FROM faculty ORDER BY name"

    # All students
    if "student" in q and any(
        x in q for x in ["show", "list", "all", "display"]
    ):
        return "SELECT * FROM students ORDER BY name"

    # General marks and grades
    if any(x in q for x in ["marks", "scores", "grades", "score"]):
        return """
            SELECT s.name, s.department, sc.subject,
                   sc.marks, sc.grade, sc.semester
            FROM students s
            JOIN scores sc ON s.student_id = sc.student_id
            ORDER BY s.name
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