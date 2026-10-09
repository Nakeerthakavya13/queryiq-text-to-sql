
import sqlite3
import random
from pathlib import Path

DB_PATH = Path(__file__).parent / "college.db"


def create_database():
    random.seed(42)
    conn = sqlite3.connect(DB_PATH)

    conn.executescript("""
    DROP TABLE IF EXISTS attendance;
    DROP TABLE IF EXISTS scores;
    DROP TABLE IF EXISTS students;
    DROP TABLE IF EXISTS faculty;

    CREATE TABLE students (
        student_id INTEGER PRIMARY KEY,
        name TEXT, age INTEGER, gender TEXT,
        department TEXT, year INTEGER
    );

    CREATE TABLE scores (
        score_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER, subject TEXT,
        marks REAL, grade TEXT, semester INTEGER
    );

    CREATE TABLE attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER, subject TEXT,
        present_days INTEGER, total_days INTEGER,
        percentage REAL
    );

    CREATE TABLE faculty (
        faculty_id INTEGER PRIMARY KEY,
        name TEXT, department TEXT,
        subject TEXT, experience_years INTEGER
    );
    """)

    departments = ["CSE", "Data Science", "ECE", "EEE"]
    subjects = ["Python", "DBMS", "Statistics", "Machine Learning"]

    names = [
        ("Aarav Sharma", "Male"), ("Ananya Reddy", "Female"),
        ("Arjun Kumar", "Male"), ("Aadhya Rao", "Female"),
        ("Aditya Singh", "Male"), ("Akshara Patel", "Female"),
        ("Abhinav Gupta", "Male"), ("Amrutha Reddy", "Female"),
        ("Akhil Varma", "Male"), ("Avani Sharma", "Female"),
        ("Bhavana Rao", "Female"), ("Bharath Kumar", "Male"),
        ("Charan Reddy", "Male"), ("Chandana Das", "Female"),
        ("Deepak Singh", "Male"), ("Divya Sharma", "Female"),
        ("Eswar Rao", "Male"), ("Farah Khan", "Female"),
        ("Gautham Reddy", "Male"), ("Harika Patel", "Female"),
        ("Ishaan Kumar", "Male"), ("Jahnavi Rao", "Female"),
        ("Karthik Varma", "Male"), ("Kavya Reddy", "Female"),
        ("Lokesh Kumar", "Male"), ("Meghana Das", "Female"),
        ("Nikhil Sharma", "Male"), ("Navya Reddy", "Female"),
        ("Pavan Kumar", "Male"), ("Priya Singh", "Female"),
        ("Rahul Rao", "Male"), ("Sravya Patel", "Female"),
        ("Sai Teja", "Male"), ("Sneha Sharma", "Female"),
        ("Tarun Kumar", "Male"), ("Vaishnavi Rao", "Female"),
        ("Varun Reddy", "Male"), ("Yamini Das", "Female"),
        ("Rohit Kumar", "Male"), ("Zoya Khan", "Female")
    ]

    students = []
    for i, (name, gender) in enumerate(names, start=1):
        students.append((
            i, name, random.randint(18, 22), gender,
            departments[(i - 1) % len(departments)],
            random.randint(1, 4)
        ))

    conn.executemany(
        "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?)",
        students
    )

    scores, attendance = [], []

    for student in students:
        sid = student[0]

        for semester in range(1, 5):
            for subject in subjects:
                marks = random.randint(35, 100)
                grade = (
                    "A" if marks >= 80 else
                    "B" if marks >= 65 else
                    "C" if marks >= 50 else "F"
                )
                scores.append(
                    (sid, subject, marks, grade, semester)
                )

        for subject in subjects:
            present = random.randint(55, 100)
            attendance.append(
                (sid, subject, present, 100, float(present))
            )

    conn.executemany("""
        INSERT INTO scores
        (student_id, subject, marks, grade, semester)
        VALUES (?, ?, ?, ?, ?)
    """, scores)

    conn.executemany("""
        INSERT INTO attendance
        (student_id, subject, present_days, total_days, percentage)
        VALUES (?, ?, ?, ?, ?)
    """, attendance)

    faculty = [
        (1, "Ramesh Rao", "CSE", "DBMS", 12),
        (2, "Anitha Sharma", "Data Science", "Machine Learning", 10),
        (3, "Suresh Kumar", "ECE", "Python", 8),
        (4, "Meena Reddy", "EEE", "Statistics", 14),
        (5, "Priya Singh", "CSE", "Python", 7),
        (6, "Arjun Patel", "Data Science", "DBMS", 9),
        (7, "Kavitha Rao", "CSE", "Machine Learning", 11),
        (8, "Naveen Nayak", "Data Science", "Statistics", 6)
    ]

    conn.executemany(
        "INSERT INTO faculty VALUES (?, ?, ?, ?, ?)",
        faculty
    )

    conn.commit()
    conn.close()
    print("Database created successfully!")


def get_schema():
    return """
    students(student_id, name, age, gender, department, year)
    scores(score_id, student_id, subject, marks, grade, semester)
    attendance(attendance_id, student_id, subject,
               present_days, total_days, percentage)
    faculty(faculty_id, name, department, subject, experience_years)
    """


if __name__ == "__main__":
    create_database()
