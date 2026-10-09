
import re
import sqlite3
import time
import pandas as pd

from database import DB_PATH


# Query resource limits
MAX_SQL_LENGTH = 10_000
MAX_ROWS = 5_000
QUERY_TIMEOUT_SECONDS = 5
PROGRESS_CHECK_INTERVAL = 1_000


def validate_sql(sql):
    """Validate a single read-only SELECT or WITH query."""

    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("SQL query cannot be empty.")

    sql = sql.strip()

    if len(sql) > MAX_SQL_LENGTH:
        raise ValueError("SQL query is too long.")

    # Remove one optional trailing semicolon.
    if sql.endswith(";"):
        sql = sql[:-1].strip()

    # Reject multiple statements.
    if ";" in sql:
        raise ValueError("Only one SQL statement is allowed.")

    # Only SELECT and WITH statements are permitted.
    if not re.match(r"^(SELECT|WITH)\b", sql, re.I):
        raise ValueError("Only SELECT queries are allowed.")

    # Block unsafe operations and SQL comments.
    blocked = (
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|"
        r"ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|TRIGGER|"
        r"BEGIN|COMMIT|ROLLBACK|SAVEPOINT|RELEASE|"
        r"ANALYZE|RECURSIVE)\b"
    )

    if re.search(blocked, sql, re.I):
        raise ValueError("Unsafe SQL query blocked.")

    if "--" in sql or "/*" in sql or "*/" in sql:
        raise ValueError("SQL comments are not allowed.")

    return sql


def run_query(sql):
    """Execute a read-only query with time and row limits."""

    sql = validate_sql(sql)

    # Open the existing database in read-only mode.
    db_uri = f"{DB_PATH.resolve().as_uri()}?mode=ro"

    try:
        conn = sqlite3.connect(
            db_uri,
            uri=True,
            timeout=QUERY_TIMEOUT_SECONDS,
        )
    except sqlite3.Error as error:
        raise ValueError(
            f"Unable to open the database: {error}"
        ) from error

    start = time.monotonic()

    def stop_if_needed():
        return int(
            time.monotonic() - start >= QUERY_TIMEOUT_SECONDS
        )

    try:
        conn.execute("PRAGMA query_only = ON")

        # Interrupt long-running SQL queries.
        conn.set_progress_handler(
            stop_if_needed,
            PROGRESS_CHECK_INTERVAL,
        )

        cursor = conn.execute(sql)

        columns = [item[0] for item in cursor.description or []]

        # Fetch at most MAX_ROWS + 1 to detect truncation.
        rows = cursor.fetchmany(MAX_ROWS + 1)

        if time.monotonic() - start >= QUERY_TIMEOUT_SECONDS:
            raise ValueError(
                f"Query exceeded the {QUERY_TIMEOUT_SECONDS}-second limit."
            )

        truncated = len(rows) > MAX_ROWS
        rows = rows[:MAX_ROWS]

        result = pd.DataFrame(rows, columns=columns)

        if truncated:
            result.attrs["truncated"] = True
            result.attrs["row_limit"] = MAX_ROWS
        else:
            result.attrs["truncated"] = False

        return result

    except sqlite3.Error as error:
        if time.monotonic() - start >= QUERY_TIMEOUT_SECONDS:
            raise ValueError(
                f"Query exceeded the {QUERY_TIMEOUT_SECONDS}-second limit."
            ) from error

        raise ValueError(
            f"SQL execution failed: {error}"
        ) from error

    finally:
        conn.set_progress_handler(None, 0)
        conn.close()
