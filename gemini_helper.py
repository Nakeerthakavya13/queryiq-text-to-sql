
import os
import re
from google import genai
from database import get_schema

MODEL = "gemini-2.5-flash"


def call_gemini(prompt):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Set it in the VS Code terminal."
        )

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        return response.text.strip()

    finally:
        client.close()


def generate_sql(question):
    prompt = f"""
You are a Text-to-SQL assistant using SQLite.

Database schema:
{get_schema()}

User question:
{question}

Rules:
1. Return only one SQLite SELECT query.
2. Use only tables and columns in the schema.
3. Use JOINs when needed.
4. Never generate INSERT, UPDATE, DELETE, DROP, ALTER,
   CREATE, PRAGMA, ATTACH, or DETACH statements.
5. Do not include Markdown code fences.
6. Return SQL only.
"""

    sql = call_gemini(prompt)

    sql = re.sub(
        r"^```(?:sql)?\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )
    sql = re.sub(r"\s*```$", "", sql).strip()

    return sql.rstrip(";").strip()


def explain_result(question, sql, dataframe):
    preview = dataframe.head(10).to_string(index=False)

    prompt = f"""
Explain the database result in simple English.

User question: {question}
SQL executed: {sql}
Number of rows: {len(dataframe)}

Result preview:
{preview}

Explain only what the provided results support.
Do not invent facts. Keep the explanation concise.
"""

    return call_gemini(prompt)


def confidence_warning(question, dataframe):
    if dataframe.empty:
        return (
            "No matching records found. "
            "Try rephrasing your question."
        )

    if len(question.split()) < 3:
        return (
            "Warning: The question may be ambiguous. "
            "Check the generated SQL."
        )

    return (
        "Query executed successfully. "
        "Review the SQL and results to confirm they match your question."
    )

