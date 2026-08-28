import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Page Configuration
st.set_page_config(
    page_title="University Analytics Portal",
    page_icon="🎓",
    layout="wide"
)

# -------------------------------------------------------------
# Database Connection Setup
# -------------------------------------------------------------
DB_URI = "mysql+pymysql://root:2003@localhost:3306/university_db"

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
# Sidebar: Developer Branding & Navigation
# -------------------------------------------------------------
with st.sidebar:
    st.header("📌 Project Details")
    st.markdown("""
    **University Academic & Performance System**  
    *A full-stack relational database analytics pipeline built with MySQL & Python.*
    """)
    st.divider()
    
    # Developer Attribution
    st.markdown("### 👨‍💻 Developer")
    st.markdown("**Pushpender**")
    st.markdown("[🔗 Connect on LinkedIn](https://www.linkedin.com/in/push2003)")
    st.caption("Data Science & Database Project Portfolio")

# -------------------------------------------------------------
# UI Header & Key Metrics
# -------------------------------------------------------------
st.title("🎓 University Academic & Performance Dashboard")
st.markdown("Real-time reporting and query portal powered by **MySQL & Streamlit**.")
st.divider()

# High-Level Metric Cards
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

total_students_df = run_query("SELECT COUNT(*) AS total FROM Students;")
total_courses_df = run_query("SELECT COUNT(*) AS total FROM Courses;")
total_faculty_df = run_query("SELECT COUNT(*) AS total FROM Instructors;")
avg_gpa_df = run_query("SELECT ROUND(AVG(cgpa), 2) AS avg_cgpa FROM student_gpa_report;")

col_m1.metric("Total Students", total_students_df['total'][0])
col_m2.metric("Active Courses", total_courses_df['total'][0])
col_m3.metric("Faculty Members", total_faculty_df['total'][0])
col_m4.metric("University Avg CGPA", avg_gpa_df['avg_cgpa'][0])

st.divider()

# -------------------------------------------------------------
# Main Tabs: Dashboard, Search, and Low Attendance Alert
# -------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Department Leaderboard", "🔍 Student Transcript Lookup", "⚠️ Attendance Alerts (<75%)"])

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

# TAB 2: Student Transcript & Profile Lookup
with tab2:
    st.subheader("Student Academic Profile & Coursework")
    
    col_search1, col_search2 = st.columns([1, 3])
    
    with col_search1:
        search_id = st.number_input("Enter Student ID:", min_value=1, step=1, value=1)
        search_btn = st.button("Fetch Academic Record", use_container_width=True)
    
    if search_btn or search_id:
        profile_query = """
            SELECT student_id, student_name, dept_name, cgpa, avg_attendance, dept_rank
            FROM student_gpa_report
            WHERE student_id = :sid;
        """
        profile_df = run_query(profile_query, params={"sid": search_id})
        
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
                    CONCAT(e.attendance_percentage, '%') AS 'Attendance'
                FROM Enrollments e
                JOIN Sections sec ON e.section_id = sec.section_id
                JOIN Courses c ON sec.course_id = c.course_id
                WHERE e.student_id = :sid;
            """
            student_courses_df = run_query(courses_query, params={"sid": search_id})
            st.table(student_courses_df)
        else:
            st.warning(f"No records found for Student ID: {search_id}")

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
            CONCAT(avg_attendance, '%') AS 'Average Attendance'
        FROM student_gpa_report
        WHERE avg_attendance < 75.0
        ORDER BY avg_attendance ASC;
    """
    defaulter_df = run_query(defaulter_query)
    
    if not defaulter_df.empty:
        st.dataframe(defaulter_df, use_container_width=True, hide_index=True)
    else:
        st.success("All students currently meet the minimum 75% attendance criteria.")

# -------------------------------------------------------------
# Bottom Footer: Attribution
# -------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 14px;'>"
    "Developed by <b>Pushpender</b> | "
    "<a href='https://www.linkedin.com/in/push2003' target='_blank' style='text-decoration: none; color: #0077B5; font-weight: bold;'>LinkedIn Profile</a>"
    "</div>", 
    unsafe_allow_html=True
)