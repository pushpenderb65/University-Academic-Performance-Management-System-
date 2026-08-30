import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# -------------------------------------------------------------
# Page Configuration
# -------------------------------------------------------------
st.set_page_config(
    page_title="University Analytics Portal",
    page_icon="🎓",
    layout="wide"
)

# -------------------------------------------------------------
# Safe Database Path Detection (Works both locally & Cloud)
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "university.db")
DB_URI = f"sqlite:///{DB_PATH}"


@st.cache_resource
def get_db_engine():
    return create_engine(DB_URI)


engine = get_db_engine()


# Helper function to run queries safely
def run_query(query, params=None):
    with engine.connect() as conn:
        if params:
            return pd.read_sql(text(query), conn, params=params)
        return pd.read_sql(text(query), conn)


# -------------------------------------------------------------
# ===================  LOGIN CONFIG  ===========================
# -------------------------------------------------------------
# NOTE: For a real deployment, move these into st.secrets instead
# of hardcoding them here.
ADMIN_CREDENTIALS = {
    "admin": "admin123",
}


def check_student_login(student_id: int, student_name: str) -> bool:
    """Validate a student by ID + Name against the Students table."""
    query = """
        SELECT student_id, student_name
        FROM Students
        WHERE student_id = :sid;
    """
    df = run_query(query, params={"sid": student_id})
    if df.empty:
        return False
    db_name = str(df.iloc[0]["student_name"]).strip().lower()
    return db_name == student_name.strip().lower()


def init_session_state():
    defaults = {
        "logged_in": False,
        "role": None,          # "Admin" or "Student"
        "student_id": None,
        "student_name": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def logout():
    for key in ["logged_in", "role", "student_id", "student_name"]:
        st.session_state[key] = False if key == "logged_in" else None
    st.rerun()


# -------------------------------------------------------------
# ===================  LOGIN PAGE  =============================
# -------------------------------------------------------------
def show_login_page():
    st.title("🎓 University Academic & Performance Portal")
    st.caption("Please login to continue")

    left, mid, right = st.columns([1, 2, 1])
    with mid:
        role_choice = st.radio(
            "Login as:",
            ["Admin", "Student"],
            horizontal=True,
        )
        st.divider()

        if role_choice == "Admin":
            with st.form("admin_login_form"):
                st.subheader("🔑 Admin Login")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)

                if submitted:
                    if ADMIN_CREDENTIALS.get(username) == password:
                        st.session_state.logged_in = True
                        st.session_state.role = "Admin"
                        st.success("Login successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("Invalid admin username or password.")

        else:  # Student
            with st.form("student_login_form"):
                st.subheader("🎓 Student Login")
                sid = st.number_input("Student ID", min_value=1, step=1)
                sname = st.text_input("Full Name (as per university records)")
                submitted = st.form_submit_button("Login", use_container_width=True)

                if submitted:
                    if check_student_login(int(sid), sname):
                        st.session_state.logged_in = True
                        st.session_state.role = "Student"
                        st.session_state.student_id = int(sid)
                        st.session_state.student_name = sname
                        st.success("Login successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("Student ID / Name not found. Please check and try again.")


# -------------------------------------------------------------
# ===================  ADMIN DASHBOARD  ========================
# (Original full dashboard — all students, all tabs)
# -------------------------------------------------------------
def show_admin_dashboard():
    with st.sidebar:
        st.header("📌 Project Details")
        st.markdown("""
        **University Academic & Performance System**

        *A full-stack relational database analytics pipeline built with SQL & Python.*
        """)
        st.divider()
        st.markdown("### 👨‍💻 Developer")
        st.markdown("**Pushpender**")
        st.markdown("[🔗 Connect on LinkedIn](https://www.linkedin.com/in/push2003)")
        st.caption("Data Science & Database Project Portfolio")
        st.divider()
        st.markdown(f"**Logged in as:** Admin")
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    st.title("🎓 University Academic & Performance Dashboard")
    st.markdown("Real-time reporting and query portal powered by **SQL & Streamlit**.")
    st.divider()

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    total_students_df = run_query("SELECT COUNT(*) AS total FROM Students;")
    total_courses_df = run_query("SELECT COUNT(*) AS total FROM Courses;")
    total_faculty_df = run_query("SELECT COUNT(*) AS total FROM Instructors;")
    avg_gpa_df = run_query("SELECT ROUND(AVG(cgpa), 2) AS avg_cgpa FROM student_gpa_report;")

    col_m1.metric("Total Students", int(total_students_df['total'][0]))
    col_m2.metric("Active Courses", int(total_courses_df['total'][0]))
    col_m3.metric("Faculty Members", int(total_faculty_df['total'][0]))
    col_m4.metric("University Avg CGPA", float(avg_gpa_df['avg_cgpa'][0]))

    st.divider()

    tab1, tab2, tab3 = st.tabs(
        ["📊 Department Leaderboard", "🔍 Student Transcript Lookup", "⚠️ Attendance Alerts (<75%)"]
    )

    # TAB 1: Department-wise Top Rankers
    with tab1:
        st.subheader("Department Rankings & CGPA Leaders")
        dept_list_df = run_query("SELECT DISTINCT dept_name FROM Departments;")
        dept_options = ["All Departments"] + dept_list_df['dept_name'].tolist()
        selected_dept = st.selectbox("Select Department:", dept_options)

        if selected_dept == "All Departments":
            leaderboard_query = """
                SELECT student_id, student_name, dept_name, cgpa, avg_attendance, dept_rank
                FROM student_gpa_report
                ORDER BY dept_name, dept_rank ASC;
            """
            df_leaderboard = run_query(leaderboard_query)
        else:
            leaderboard_query = """
                SELECT student_id, student_name, dept_name, cgpa, avg_attendance, dept_rank
                FROM student_gpa_report
                WHERE dept_name = :dept
                ORDER BY dept_rank ASC;
            """
            df_leaderboard = run_query(leaderboard_query, params={"dept": selected_dept})

        st.dataframe(df_leaderboard, use_container_width=True, hide_index=True)

    # TAB 2: Student Transcript Lookup (Admin can look up ANY student)
    with tab2:
        st.subheader("Student Academic Profile & Coursework")
        col_search1, col_search2 = st.columns([1, 3])
        with col_search1:
            search_id = st.number_input("Enter Student ID:", min_value=1, step=1, value=1)
            search_btn = st.button("Fetch Academic Record", use_container_width=True)

        if search_btn or search_id:
            render_student_transcript(int(search_id))

    # TAB 3: Defaulter / Attendance Warning List
    with tab3:
        st.subheader("Attendance Shortage Alerts (< 75%)")
        st.markdown("Students requiring attendance counseling or exam disqualification warnings:")

        defaulter_query = """
            SELECT
                student_id AS 'Student ID',
                student_name AS 'Name',
                dept_name AS 'Department',
                cgpa AS 'Current CGPA',
                (avg_attendance || '%') AS 'Average Attendance'
            FROM student_gpa_report
            WHERE avg_attendance < 75.0
            ORDER BY avg_attendance ASC;
        """
        defaulter_df = run_query(defaulter_query)

        if not defaulter_df.empty:
            st.dataframe(defaulter_df, use_container_width=True, hide_index=True)
        else:
            st.success("All students currently meet the minimum 75% attendance criteria.")

    show_footer()


# -------------------------------------------------------------
# ===================  STUDENT DASHBOARD  ======================
# (Restricted — only their own record)
# -------------------------------------------------------------
def show_student_dashboard():
    with st.sidebar:
        st.header("📌 Project Details")
        st.markdown("""
        **University Academic & Performance System**

        *A full-stack relational database analytics pipeline built with SQL & Python.*
        """)
        st.divider()
        st.markdown(f"**Logged in as:** {st.session_state.student_name} (ID: {st.session_state.student_id})")
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    st.title("🎓 My Academic Profile")
    st.markdown("View your CGPA, department rank, attendance and enrolled courses.")
    st.divider()

    render_student_transcript(st.session_state.student_id)
    show_footer()


# -------------------------------------------------------------
# Shared: render a single student's transcript
# -------------------------------------------------------------
def render_student_transcript(sid: int):
    profile_query = """
        SELECT student_id, student_name, dept_name, cgpa, avg_attendance, dept_rank
        FROM student_gpa_report
        WHERE student_id = :sid;
    """
    profile_df = run_query(profile_query, params={"sid": sid})

    if not profile_df.empty:
        student_data = profile_df.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.info(f"**Name:** {student_data['student_name']}")
        c2.metric("Department", student_data['dept_name'])
        c3.metric("CGPA", student_data['cgpa'])
        c4.metric("Dept Rank", f"#{student_data['dept_rank']}")

        st.markdown("#### Enrolled Courses & Grades")

        courses_query = """
            SELECT
                c.course_code AS 'Course Code',
                c.course_title AS 'Course Title',
                c.credits AS 'Credits',
                e.grade AS 'Grade',
                (e.attendance_percentage || '%') AS 'Attendance'
            FROM Enrollments e
            JOIN Sections sec ON e.section_id = sec.section_id
            JOIN Courses c ON sec.course_id = c.course_id
            WHERE e.student_id = :sid;
        """
        student_courses_df = run_query(courses_query, params={"sid": sid})
        st.table(student_courses_df)
    else:
        st.warning(f"No records found for Student ID: {sid}")


# -------------------------------------------------------------
# Footer
# -------------------------------------------------------------
def show_footer():
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray; font-size: 14px;'>"
        "Developed by <b>Pushpender</b> | "
        "<a href='https://www.linkedin.com/in/push2003' target='_blank' "
        "style='text-decoration: none; color: #0077B5; font-weight: bold;'>LinkedIn Profile</a>"
        "</div>",
        unsafe_allow_html=True
    )


# -------------------------------------------------------------
# ===================  MAIN ROUTER  =============================
# -------------------------------------------------------------
init_session_state()

if not st.session_state.logged_in:
    show_login_page()
elif st.session_state.role == "Admin":
    show_admin_dashboard()
elif st.session_state.role == "Student":
    show_student_dashboard()
