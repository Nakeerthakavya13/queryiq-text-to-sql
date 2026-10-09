
import streamlit as st
import pandas as pd

from database import DB_PATH, create_database, get_schema
from gemini_helper import generate_sql, explain_result, confidence_warning
from sql_runner import run_query
from local_fallback import generate_local_sql, explain_local_result
from evaluation import evaluate_local_fallback


# ==================================================
# PAGE CONFIGURATION
# ==================================================
st.set_page_config(
    page_title="QueryIQ | Text-to-SQL",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not DB_PATH.exists():
    create_database()


# ==================================================
# SESSION STATE
# ==================================================
defaults = {
    "history": [],
    "question_input": "",
    "last_result": None,
    "last_sql": "",
    "last_question": "",
    "last_mode": "",
    "last_explanation": "",
    "evaluation_results": None,
    "navigate_to_ask": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# CUSTOM STYLING
# ==================================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .hero {
        padding: 1.6rem;
        border-radius: 16px;
        background: linear-gradient(120deg, #17365D, #2878A5);
        color: white;
        margin-bottom: 1.2rem;
    }

    .hero h1 {
        color: white;
        margin-bottom: 0.4rem;
    }

    .hero p {
        color: #E6F2FF;
        margin-bottom: 0;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,0.25);
        padding: 14px;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# HELPER: DISPLAY RESULTS SAFELY
# ==================================================
def display_results(result, key_prefix="results"):
    """Display query results, truncation warning, and CSV download."""

    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True,
    )

    if result.attrs.get("truncated", False):
        st.warning(
            "Only the first 5,000 rows are displayed. "
            "Refine your query to retrieve a smaller result."
        )

    st.download_button(
        "⬇️ Download Results as CSV",
        data=result.to_csv(index=False).encode("utf-8"),
        file_name="query_results.csv",
        mime="text/csv",
        key=f"{key_prefix}_download",
    )


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================
with st.sidebar:
    st.title("🎓 QueryIQ")
    st.caption("Natural Language Database Assistant")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "🏠 Dashboard",
            "💬 Ask Database",
            "📊 Explore Results",
            "🕘 Query History",
            "🗂️ Database Schema",
            "🧪 Evaluation",
        ],
    )

    st.divider()
    st.subheader("Technology Stack")
    st.caption("Python · Streamlit · SQLite")
    st.caption("Gemini + Local Fallback")
    st.caption("Read-only SQL execution")


# ==================================================
# DASHBOARD
# ==================================================
if page == "🏠 Dashboard":

    st.markdown(
        """
        <div class="hero">
            <h1>Welcome to QueryIQ 👋</h1>
            <p>
                Explore your college database using plain English.
                No manual SQL writing required.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    history = st.session_state.history
    result = st.session_state.last_result

    c1, c2, c3 = st.columns(3)

    c1.metric("Queries Executed", len(history))
    c2.metric(
        "Latest Result Rows",
        len(result) if result is not None else 0,
    )
    c3.metric(
        "Last Query Mode",
        st.session_state.last_mode or "Not started",
    )

    st.subheader("✨ Features")

    col1, col2 = st.columns(2)

    with col1:
        st.info(
            "**💬 Natural Language Queries**\n\n"
            "Ask questions about students, marks, attendance, and faculty."
        )
        st.info(
            "**📊 Interactive Charts**\n\n"
            "Search results and visualize numeric data."
        )

    with col2:
        st.info(
            "**🧾 SQL Transparency**\n\n"
            "Inspect the SQL generated for your question."
        )
        st.info(
            "**📥 Export and Evaluation**\n\n"
            "Download results and evaluate fallback performance."
        )

    st.subheader("🚀 Example Questions")

    examples = [
        "Show all students",
        "List students in Data Science",
        "Show the top 10 students by marks",
        "What is the average mark for each subject?",
        "Show students with attendance below 75%",
        "List faculty with more than 8 years of experience",
    ]

    for example in examples:
        if st.button(
            example,
            key=f"dashboard_{example}",
            use_container_width=True,
        ):
            st.session_state.question_input = example
            st.session_state.navigate_to_ask = True
            st.rerun()


# ==================================================
# ASK DATABASE
# ==================================================
elif page == "💬 Ask Database" or st.session_state.pop(
    "navigate_to_ask", False
):

    st.title("💬 Ask Your Database")
    st.write(
        "Enter a question in English to generate SQL and display results."
    )

    with st.expander("💡 Example Questions"):
        examples = [
            "Show all students",
            "List students in Data Science",
            "Show the top 10 students by marks",
            "What is the average mark for each subject?",
            "Show students with attendance below 75%",
            "List faculty with more than 8 years of experience",
        ]

        for example in examples:
            if st.button(example, key=f"ask_example_{example}"):
                st.session_state.question_input = example
                st.rerun()

    with st.form("query_form"):
        question = st.text_area(
            "Your question",
            key="question_input",
            placeholder="Example: Show the average marks for each subject",
            height=110,
        )

        submitted = st.form_submit_button(
            "🚀 Generate SQL and Run",
            type="primary",
            use_container_width=True,
        )

    if submitted:

        if not question.strip():
            st.warning("Please enter a question.")

        else:
            sql = None
            result = None
            mode = "Gemini"

            try:
                # Try Gemini first; use local fallback if unavailable.
                try:
                    with st.spinner("Generating SQL..."):
                        sql = generate_sql(question)

                    if not sql:
                        raise ValueError("Gemini returned no SQL.")

                except Exception:
                    mode = "Local fallback"
                    sql = generate_local_sql(question)

                if not sql:
                    st.warning(
                        "The AI service is unavailable and the local "
                        "fallback does not support this question yet. "
                        "Try one of the example questions."
                    )

                else:
                    with st.spinner("Executing query..."):
                        result = run_query(sql)

                    try:
                        if mode == "Gemini":
                            explanation = explain_result(
                                question, sql, result
                            )
                        else:
                            explanation = explain_local_result(
                                question, result
                            )
                    except Exception:
                        explanation = explain_local_result(
                            question, result
                        )

                    st.session_state.last_result = result
                    st.session_state.last_sql = sql
                    st.session_state.last_question = question
                    st.session_state.last_mode = mode
                    st.session_state.last_explanation = explanation

                    st.session_state.history.insert(
                        0,
                        {
                            "question": question,
                            "sql": sql,
                            "rows": len(result),
                            "status": "Success",
                            "mode": mode,
                        },
                    )

                    st.success("Query executed successfully!")

            except Exception as error:
                st.error(f"Unable to process the query: {error}")
                st.caption(
                    "Check the database connection, generated SQL, "
                    "and SQL safety validation."
                )

    result = st.session_state.last_result

    if result is not None:
        st.divider()
        st.subheader("📊 Query Results")

        c1, c2, c3 = st.columns(3)
        c1.metric("Rows Returned", len(result))
        c2.metric("Columns", len(result.columns))
        c3.metric("Query Mode", st.session_state.last_mode)

        with st.expander("🧾 Generated SQL"):
            st.code(st.session_state.last_sql, language="sql")

        display_results(result, "ask")

        st.subheader("💬 Result Explanation")
        st.write(st.session_state.last_explanation)

        warning = confidence_warning(
            st.session_state.last_question,
            result,
        )

        if result.empty:
            st.warning(warning)
        else:
            st.caption(warning)


# ==================================================
# EXPLORE RESULTS
# ==================================================
elif page == "📊 Explore Results":

    st.title("📊 Results Explorer")

    result = st.session_state.last_result

    if result is None:
        st.info("Run a query first to explore its results.")

    elif result.empty:
        st.warning("The latest query returned no records.")

    else:
        st.caption(f"{len(result)} rows · {len(result.columns)} columns")

        search = st.text_input("🔎 Search within results")
        filtered = result.copy()

        if search.strip():
            mask = filtered.astype(str).apply(
                lambda column: column.str.contains(
                    search,
                    case=False,
                    na=False,
                    regex=False,
                )
            ).any(axis=1)

            filtered = filtered[mask]

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
        )

        if result.attrs.get("truncated", False):
            st.warning(
                "The query result was limited to the first 5,000 rows. "
                "Refine your question for a more specific result."
            )

        st.caption(f"{len(filtered)} matching row(s)")

        st.download_button(
            "⬇️ Download Filtered CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="filtered_results.csv",
            mime="text/csv",
            key="explorer_download",
        )

        st.divider()
        st.subheader("📈 Visualize Results")

        numeric_cols = filtered.select_dtypes(
            include="number"
        ).columns.tolist()

        category_cols = [
            col for col in filtered.columns
            if col not in numeric_cols
        ]

        if not numeric_cols:
            st.info(
                "No numeric columns are available. Try a query involving "
                "marks, attendance, or experience."
            )

        else:
            chart_type = st.selectbox(
                "Chart type",
                ["Bar chart", "Line chart", "Area chart"],
            )

            value_col = st.selectbox(
                "Numeric column",
                numeric_cols,
            )

            if category_cols:
                category_col = st.selectbox(
                    "Category / X-axis",
                    category_cols,
                )

                chart_data = filtered[
                    [category_col, value_col]
                ].dropna()

                if not chart_data.empty:
                    chart_data = chart_data.groupby(
                        category_col,
                        dropna=False,
                    )[value_col].mean().to_frame()

                    if chart_type == "Bar chart":
                        st.bar_chart(chart_data)
                    elif chart_type == "Line chart":
                        st.line_chart(chart_data)
                    else:
                        st.area_chart(chart_data)

                else:
                    st.info("No usable values are available to chart.")

            else:
                chart_data = filtered[
                    [value_col]
                ].reset_index(drop=True)

                if chart_type == "Bar chart":
                    st.bar_chart(chart_data)
                elif chart_type == "Line chart":
                    st.line_chart(chart_data)
                else:
                    st.area_chart(chart_data)


# ==================================================
# QUERY HISTORY
# ==================================================
elif page == "🕘 Query History":

    st.title("🕘 Query History")

    history = st.session_state.history

    if not history:
        st.info("Your executed queries will appear here.")

    else:
        history_df = pd.DataFrame(history)

        search = st.text_input("🔎 Search query history")

        if search.strip():
            history_df = history_df[
                history_df["question"].str.contains(
                    search,
                    case=False,
                    na=False,
                    regex=False,
                )
            ]

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
        )

        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()

        st.download_button(
            "⬇️ Export Query History",
            data=pd.DataFrame(history).to_csv(
                index=False
            ).encode("utf-8"),
            file_name="query_history.csv",
            mime="text/csv",
            key="history_download",
        )


# ==================================================
# DATABASE SCHEMA
# ==================================================
elif page == "🗂️ Database Schema":

    st.title("🗂️ Database Explorer")
    st.write("Review the schema supplied to the query generator.")

    st.code(get_schema(), language="text")

    st.caption("Database engine: SQLite")
    st.caption(f"Database file: {DB_PATH.name}")

    st.info(
        "Keep SQL execution read-only. Do not expose private student "
        "records in a public deployment."
    )


# ==================================================
# EVALUATION
# ==================================================
elif page == "🧪 Evaluation":

    st.title("🧪 Query Evaluation")

    st.write(
        "Measure local fallback coverage, execution success, "
        "result correctness, and response time."
    )

    st.info(
        "Correctness is compared against reference SQL results on the "
        "current database. This fixed test suite does not measure "
        "general AI accuracy."
    )

    if st.button("▶️ Run Evaluation", type="primary"):

        with st.spinner("Running evaluation tests..."):
            st.session_state.evaluation_results = (
                evaluate_local_fallback()
            )

    df = st.session_state.evaluation_results

    if df is not None and not df.empty:

        total = len(df)
        successful = int(
            (df["Status"] == "Success").sum()
        )
        correct = int(
            (df["Correctness"] == "Correct").sum()
        )
        incorrect = int(
            (df["Correctness"] == "Incorrect").sum()
        )
        unsupported = int(
            (df["Status"] == "Unsupported").sum()
        )
        failed = int(
            (df["Status"] == "Failed").sum()
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Test Cases", total)
        c2.metric(
            "Execution Success",
            f"{successful / total * 100:.1f}%",
        )
        c3.metric(
            "Result Correctness",
            f"{correct / total * 100:.1f}%",
        )
        c4.metric("Unsupported", unsupported)

        st.subheader("📋 Detailed Test Results")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("📊 Evaluation Summary")

        summary = pd.DataFrame({
            "Metric": [
                "Execution success",
                "Correct results",
                "Incorrect results",
                "Unsupported questions",
                "Failed queries",
            ],
            "Count": [
                successful,
                correct,
                incorrect,
                unsupported,
                failed,
            ],
        })

        st.bar_chart(summary.set_index("Metric"))

        st.subheader("⏱️ Response Time")

        st.bar_chart(
            df.set_index("Question")[["Time (ms)"]]
        )

        st.download_button(
            "⬇️ Download Evaluation Report",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="evaluation_report.csv",
            mime="text/csv",
            key="evaluation_download",
        )


# ==================================================
# FOOTER
# ==================================================
st.divider()

st.caption(
    "QueryIQ | Text-to-SQL College Database Assistant | "
    "Python · Streamlit · SQLite"
)
