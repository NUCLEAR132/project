# ============================================================================
# Tenx Plus System - Main Application
# ============================================================================
# Project Name : Tenx Plus System
# Description  : School Management System
# Database     : PostgreSQL (Render)
# Framework    : Flask
# Author       : Tenx Plus Team
# Version      : 2.0.0 - PostgreSQL Edition
# ============================================================================
# Change Log:
# ----------
# v1.0.0 : SQLite Version - school.db
# v2.0.0 : Migrated to PostgreSQL - Render Database
#          - Replaced sqlite3 with psycopg2
#          - Replaced ? with %s
#          - Replaced conn.execute with cur.execute
#          - Replaced lastrowid with RETURNING id
#          - Fixed COUNT(*) handling for RealDictCursor
# ============================================================================

# ============================================================================
# 1. IMPORTS
# ============================================================================

from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from flask import redirect
from flask import url_for
from flask import send_file

from database import get_db
from database import init_db

from auth import is_authenticated
from auth import login as auth_login
from auth import logout as auth_logout

import csv
import io
import time

# ============================================================================
# 2. APP INITIALIZATION
# ============================================================================

app = Flask(__name__)
@app.before_request
def block_bots():
    user_agent = request.headers.get('User-Agent', '').lower()

    # لو اللي داخل مش متصفح حقيقي، اديله صفحة وهمية
    bad_agents = ['python-requests', 'curl', 'wget', 'httpclient', 'scrapy', 'bot']

    for bad in bad_agents:
        if bad in user_agent:
            return """
            <html>
            <head><title>Tenx Plus</title></head>
            <body style="background:black;color:red;text-align:center;margin-top:200px;font-family:Arial">
            <h1>Dont Try kid</h1>
            <p>This site is protected by Tenx Plus Security</p>
            </body>
            </html>
            """, 403
# Initialize Database
# This will create all tables if not exists
# Tables: students, teachers, classes, grades, attendance
init_db()

# SFR_044

# ============================================================================
# 3. HELPER FUNCTIONS
# ============================================================================

def require_auth():
    """
    Check if user is authenticated.

    Returns:
        bool: True if authenticated, False otherwise
    """
    return is_authenticated()

def unauthorized():
    """
    Return unauthorized response.

    Returns:
        tuple: JSON response with 401 status
    """
    return jsonify(
        {
            "success": False,
            "error": "Unauthorized"
        }
    ), 401

def render_page(template, **kwargs):
    """
    Render page with default logos.

    Args:
        template (str): Template name
        **kwargs: Additional template variables

    Returns:
        str: Rendered HTML
    """
    kwargs.setdefault(
        'logo_light',
        url_for('static', filename='1.jpg')
    )

    kwargs.setdefault(
        'logo_dark',
        url_for('static', filename='2.jpg')
    )

    return render_template(
        template,
        **kwargs
    )

# ============================================================================
# 4. PAGE ROUTES - HTML PAGES
# ============================================================================

@app.route("/")
@app.route("/home")
def home():
    """
    Home Page - Main Dashboard.
    """
    if not require_auth():
        return redirect(
            url_for("login_page")
        )

    return render_page(
        "index.html",
        title="الرئيسية",
        page="home"
    )

@app.route("/students")
def students_page():
    """
    Students Page.
    """
    if not require_auth():
        return redirect(
            url_for("login_page")
        )

    return render_page(
        "index.html",
        title="الطلاب",
        page="students"
    )

@app.route("/teachers")
def teachers_page():
    """
    Teachers Page.
    """
    if not require_auth():
        return redirect(
            url_for("login_page")
        )

    return render_page(
        "index.html",
        title="المعلمون",
        page="teachers"
    )

@app.route("/schedule")
def schedule_page():
    """
    Schedule Page.
    """
    if not require_auth():
        return redirect(
            url_for("login_page")
        )

    return render_page(
        "index.html",
        title="الجدول",
        page="schedule"
    )

@app.route("/grades")
def grades_page():
    """
    Grades Page.
    """
    if not require_auth():
        return redirect(
            url_for("login_page")
        )

    return render_page(
        "index.html",
        title="الدرجات",
        page="grades"
    )

@app.route("/attendance")
def attendance_page():
    """
    Attendance Page.
    """
    if not require_auth():
        return redirect(
            url_for("login_page")
        )

    return render_page(
        "index.html",
        title="الحضور",
        page="attendance"
    )

@app.route("/reports")
def reports_page():
    """
    Reports Page.
    """
    if not require_auth():
        return redirect(
            url_for("login_page")
        )

    return render_page(
        "index.html",
        title="التقارير",
        page="reports"
    )

@app.route("/login")
def login_page():
    """
    Login Page.
    """
    return render_page(
        "login.html"
    )

# ============================================================================
# 5. AUTH API
# ============================================================================

@app.route("/api/login", methods=["POST"])
def api_login():
    """
    API: Login.
    """
    data = request.get_json() or {}

    password = data.get(
        "password",
        ""
    )

    if auth_login(password):
        return jsonify(
            {
                "success": True
            }
        )

    return jsonify(
        {
            "success": False,
            "error": "كلمة المرور غير صحيحة"
        }
    ), 401

@app.route("/api/logout", methods=["POST"])
def api_logout():
    """
    API: Logout.
    """
    auth_logout()

    return jsonify(
        {
            "success": True
        }
    )

# ============================================================================
# 6. STATS API
# ============================================================================

@app.route("/api/stats")
def api_stats():
    """
    API: Get Dashboard Statistics.
    """
    if not require_auth():
        return unauthorized()

    conn = get_db()
    cur = conn.cursor()

    # Students Count
    cur.execute(
        "SELECT COUNT(*) as cnt FROM students"
    )
    students_count = cur.fetchone()["cnt"]

    # Teachers Count
    cur.execute(
        "SELECT COUNT(*) as cnt FROM teachers"
    )
    teachers_count = cur.fetchone()["cnt"]

    # Classes Count
    cur.execute(
        "SELECT COUNT(*) as cnt FROM classes"
    )
    classes_count = cur.fetchone()["cnt"]

    # Grades Count
    cur.execute(
        "SELECT COUNT(*) as cnt FROM grades"
    )
    grades_count = cur.fetchone()["cnt"]

    # Today Date
    today = time.strftime("%Y-%m-%d")

    # Present Today
    cur.execute(
        "SELECT COUNT(*) as cnt FROM attendance WHERE date = %s AND status = 'present'",
        (today,)
    )
    present_today = cur.fetchone()["cnt"]

    # Absent Today
    cur.execute(
        "SELECT COUNT(*) as cnt FROM attendance WHERE date = %s AND status = 'absent'",
        (today,)
    )
    absent_today = cur.fetchone()["cnt"]

    # Students By Grade
    cur.execute(
        "SELECT grade, COUNT(*) as cnt FROM students GROUP BY grade"
    )
    grade_rows = cur.fetchall()

    by_grade = [
        {
            "grade": r["grade"],
            "count": r["cnt"]
        }
        for r in grade_rows
    ]

    conn.close()

    return jsonify(
        {
            "success": True,
            "students": students_count,
            "teachers": teachers_count,
            "classes": classes_count,
            "grades": grades_count,
            "present_today": present_today,
            "absent_today": absent_today,
            "by_grade": by_grade,
        }
    )

# ============================================================================
# 7. STUDENTS API
# ============================================================================

@app.route("/api/students", methods=["GET"])
def api_students_list():
    """
    API: Get All Students.
    Supports search and grade filter.
    """
    if not require_auth():
        return unauthorized()

    search = request.args.get(
        "q",
        ""
    ).strip()

    grade_filter = request.args.get(
        "grade",
        ""
    ).strip()

    conn = get_db()
    cur = conn.cursor()

    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if search:
        query += " AND (name ILIKE %s OR guardian_phone ILIKE %s)"
        params.extend(
            [
                f"%{search}%",
                f"%{search}%"
            ]
        )

    if grade_filter:
        query += " AND grade = %s"
        params.append(
            grade_filter
        )

    query += " ORDER BY grade, name"

    cur.execute(
        query,
        params
    )

    rows = cur.fetchall()

    conn.close()

    return jsonify(
        {
            "success": True,
            "students": [dict(r) for r in rows]
        }
    )

@app.route("/api/students", methods=["POST"])
def api_students_add():
    """
    API: Add New Student.
    """
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}

    name = (data.get("name") or "").strip()
    grade = (data.get("grade") or "").strip()

    if not name or not grade:
        return jsonify(
            {
                "success": False,
                "error": "الاسم والصف مطلوبان"
            }
        ), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO students (name, grade, birth_date, guardian_phone, address) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (
            name,
            grade,
            data.get("birth_date", ""),
            data.get("guardian_phone", ""),
            data.get("address", "")
        )
    )

    new_id = cur.fetchone()["id"]

    conn.commit()
    conn.close()

    return jsonify(
        {
            "success": True,
            "id": new_id
        }
    )

@app.route("/api/students/<int:sid>", methods=["PUT"])
def api_students_update(sid):
    """
    API: Update Student.
    """
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}

    name = (data.get("name") or "").strip()
    grade = (data.get("grade") or "").strip()

    if not name or not grade:
        return jsonify(
            {
                "success": False,
                "error": "الاسم والصف مطلوبان"
            }
        ), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE students SET name=%s, grade=%s, birth_date=%s, guardian_phone=%s, address=%s WHERE id=%s",
        (
            name,
            grade,
            data.get("birth_date", ""),
            data.get("guardian_phone", ""),
            data.get("address", ""),
            sid
        )
    )

    conn.commit()
    conn.close()

    return jsonify(
        {
            "success": True
        }
    )

@app.route("/api/students/<int:sid>", methods=["DELETE"])
def api_students_delete(sid):
    """
    API: Delete Student.
    """
    if not require_auth():
        return unauthorized()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM students WHERE id=%s",
        (sid,)
    )

    conn.commit()
    conn.close()

    return jsonify(
        {
            "success": True
        }
    )

# ============================================================================
# 8. TEACHERS API
# ============================================================================

@app.route("/api/teachers", methods=["GET"])
def api_teachers_list():
    """
    API: Get All Teachers.
    """
    if not require_auth():
        return unauthorized()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM teachers ORDER BY name"
    )

    rows = cur.fetchall()

    conn.close()

    return jsonify(
        {
            "success": True,
            "teachers": [dict(r) for r in rows]
        }
    )

@app.route("/api/teachers", methods=["POST"])
def api_teachers_add():
    """
    API: Add New Teacher.
    """
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}

    name = (data.get("name") or "").strip()
    subject = (data.get("subject") or "").strip()

    if not name or not subject:
        return jsonify(
            {
                "success": False,
                "error": "الاسم والمادة مطلوبان"
            }
        ), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO teachers (name, subject, phone, email, hire_date) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (
            name,
            subject,
            data.get("phone", ""),
            data.get("email", ""),
            data.get("hire_date", "")
        )
    )

    new_id = cur.fetchone()["id"]

    conn.commit()
    conn.close()

    return jsonify(
        {
            "success": True,
            "id": new_id
        }
    )

@app.route("/api/teachers/<int:tid>", methods=["PUT"])
def api_teachers_update(tid):
    """
    API: Update Teacher.
    """
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}

    name = (data.get("name") or "").strip()
    subject = (data.get("subject") or "").strip()

    if not name or not subject:
        return jsonify(
            {
                "success": False,
                "error": "الاسم والمادة مطلوبان"
            }
        ), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE teachers SET name=%s, subject=%s, phone=%s, email=%s, hire_date=%s WHERE id=%s",
        (
            name,
            subject,
            data.get("phone", ""),
            data.get("email", ""),
            data.get("hire_date", ""),
            tid
        )
    )

    conn.commit()
    conn.close()

    return jsonify(
        {
            "success": True
        }
    )

@app.route("/api/teachers/<int:tid>", methods=["DELETE"])
def api_teachers_delete(tid):
    """
    API: Delete Teacher.
    """
    if not require_auth():
        return unauthorized()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM teachers WHERE id=%s",
        (tid,)
    )

    conn.commit()
    conn.close()

    return jsonify(
        {
            "success": True
        }
    )

# ============================================================================
# 9. SCHEDULE API
# ============================================================================

@app.route("/api/schedule", methods=["GET"])
def api_schedule_list():
    """
    API: Get Schedule.
    """
    if not require_auth():
        return unauthorized()

    grade = request.args.get(
        "grade",
        ""
    ).strip()

    conn = get_db()
    cur = conn.cursor()

    if grade:
        cur.execute(
            """
            SELECT c.*, t.name as teacher_name
            FROM classes c
            LEFT JOIN teachers t ON c.teacher_id = t.id
            WHERE c.grade = %s
            ORDER BY c.day, c.period
            """,
            (grade,)
        )
    else:
        cur.execute(
            """
            SELECT c.*, t.name as teacher_name
            FROM classes c
            LEFT JOIN teachers t ON c.teacher_id = t.id
            ORDER BY c.grade, c.day, c.period
            """
        )

    rows = cur.fetchall()

    conn.close()

    return jsonify(
        {
            "success": True,
            "classes": [dict(r) for r in rows]
        }
    )

@app.route("/api/schedule", methods=["POST"])
def api_schedule_add():
    """
    API: Add New Class Schedule.
    """
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}

    grade = (data.get("grade") or "").strip()
    day = (data.get("day") or "").strip()
    subject = (data.get("subject") or "").strip()

    if not grade or not day or not subject:
        return jsonify(
            {
                "success": False,
                "error": "الصف واليوم والمادة مطلوبة"
            }
        ), 400

    try:
        period = int(data.get("period", 1))
    except (ValueError, TypeError):
        return jsonify(
            {
                "success": False,
                "error": "رقم الحصة غير صحيح"
            }
        ), 400

    teacher_id = data.get("teacher_id")

    if teacher_id in ("", None):
        teacher_id = None
    else:
        try:
            teacher_id = int(teacher_id)
        except (ValueError, TypeError):
            teacher_id = None

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO classes (grade, day, period, subject, teacher_id) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (
            grade,
            day,
            period,
            subject,
            teacher_id
        )
    )

    new_id = cur.fetchone()["id"]

    conn.commit()
    conn.close()

    return jsonify(
        {
            "success": True,
            "id": new_id
        }
    )

@app.route("/api/schedule/<int:cid>", methods=["DELETE"])
def api_schedule_delete(cid):
    """
    API: Delete Schedule.
    """
    if not require_auth():
        return unauthorized()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM classes WHERE id=%s",
        (cid,)
    )

    conn.commit()
    conn.close()

    return jsonify(
        {
            "success": True
        }
    )

# ============================================================================
# 10. GRADES API
# ============================================================================

@app.route("/api/grades", methods=["GET"])
def api_grades_list():
    """
    API: Get Grades.
    """
    if not require_auth():
        return unauthorized()

    student_id = request.args.get(
        "student_id",
        ""
    ).strip()

    subject = request.args.get(
        "subject",
        ""
    ).strip()

    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT g.*, s.name as student_name, s.grade as student_grade
        FROM grades g
        JOIN students s ON g.student_id = s.id
        WHERE 1=1
    """

    params = []

    if student_id:
        query += " AND g.student_id = %s"
        params.append(student_id)

    if subject:
        query += " AND g.subject = %s"
        params.append(subject)

    query += " ORDER BY g.exam_date DESC, g.id DESC"

    cur.execute(
        query,
        params
    )

    rows = cur.fetchall()

    conn.close()

    return jsonify(
        {
            "success": True,
            "grades": [dict(r) for r in rows]
        }
    )

@app.route("/api/grades", methods=["POST"])
def api_grades_add():
    """
    API: Add New Grade.
    """
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}

    try:
        student_id = int(data.get("student_id"))
        score = float(data.get("score"))
        max_score = float(data.get("max_score", 100))
    except (ValueError, TypeError):
        return jsonify(
            {
                "success": False,
                "error": "بيانات غير صحيحة"
            }
        ), 400

    subject = (data.get("subject") or "").strip()

    if not subject:
        return jsonify(
            {
                "success": False,
                "error": "المادة مطلوبة"
            }
        ), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO grades (student_id, subject, score, max_score, exam_date, notes) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (
            student_id,
            subject,
            score,
            max_score,
            data.get("exam_date", ""),
            data.get("notes", "")
        )
    )

    new_id = cur.fetchone()["id"]

    conn.commit()
    conn.close()

    return jsonify(
        {
            "success": True,
            "id": new_id
        }
    )

@app.route("/api/grades/<int:gid>", methods=["DELETE"])
def api_grades_delete(gid):
    """
    API: Delete Grade.
    """
    if not require_auth():
        return unauthorized()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM grades WHERE id=%s",
        (gid,)
    )

    conn.commit()
    conn.close()

    return jsonify(
        {
            "success": True
        }
    )

# ============================================================================
# 11. ATTENDANCE API
# ============================================================================

@app.route("/api/attendance", methods=["GET"])
def api_attendance_list():
    """
    API: Get Attendance.
    """
    if not require_auth():
        return unauthorized()

    date = request.args.get(
        "date",
        ""
    ).strip()

    grade = request.args.get(
        "grade",
        ""
    ).strip()

    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT a.*, s.name as student_name, s.grade as student_grade
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE 1=1
    """

    params = []

    if date:
        query += " AND a.date = %s"
        params.append(date)

    if grade:
        query += " AND s.grade = %s"
        params.append(grade)

    query += " ORDER BY a.date DESC, s.name"

    cur.execute(
        query,
        params
    )

    rows = cur.fetchall()

    conn.close()

    return jsonify(
        {
            "success": True,
            "attendance": [dict(r) for r in rows]
        }
    )

@app.route("/api/attendance", methods=["POST"])
def api_attendance_add():
    """
    API: Add / Update Attendance.
    """
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}

    try:
        student_id = int(data.get("student_id"))
    except (ValueError, TypeError):
        return jsonify(
            {
                "success": False,
                "error": "الطالب غير صحيح"
            }
        ), 400

    date = (data.get("date") or "").strip()
    status = (data.get("status") or "").strip()

    if not date or status not in ("present", "absent", "late"):
        return jsonify(
            {
                "success": False,
                "error": "البيانات غير صحيحة"
            }
        ), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM attendance WHERE student_id=%s AND date=%s",
        (student_id, date)
    )

    existing = cur.fetchone()

    if existing:
        cur.execute(
            "UPDATE attendance SET status=%s, notes=%s WHERE id=%s",
            (
                status,
                data.get("notes", ""),
                existing["id"]
            )
        )
    else:
        cur.execute(
            "INSERT INTO attendance (student_id, date, status, notes) VALUES (%s, %s, %s, %s)",
            (
                student_id,
                date,
                status,
                data.get("notes", "")
            )
        )

    conn.commit()
    conn.close()

    return jsonify(
        {
            "success": True
        }
    )

# ============================================================================
# 12. REPORT API
# ============================================================================

@app.route("/api/report/student/<int:sid>")
def api_report_student(sid):
    """
    API: Student Report.
    """
    if not require_auth():
        return unauthorized()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM students WHERE id=%s",
        (sid,)
    )

    student = cur.fetchone()

    if not student:
        conn.close()
        return jsonify(
            {
                "success": False,
                "error": "الطالب غير موجود"
            }
        ), 404

    cur.execute(
        "SELECT subject, score, max_score, exam_date FROM grades WHERE student_id=%s ORDER BY exam_date DESC",
        (sid,)
    )

    grades = cur.fetchall()

    cur.execute(
        "SELECT status, COUNT(*) as cnt FROM attendance WHERE student_id=%s GROUP BY status",
        (sid,)
    )

    attendance = cur.fetchall()

    conn.close()

    grades_list = [dict(g) for g in grades]

    total_score = sum(g["score"] for g in grades_list)
    total_max = sum(g["max_score"] for g in grades_list)

    average = round(
        (total_score / total_max * 100) if total_max > 0 else 0,
        1
    )

    attendance_dict = {
        a["status"]: a["cnt"]
        for a in attendance
    }

    return jsonify(
        {
            "success": True,
            "student": dict(student),
            "grades": grades_list,
            "attendance": attendance_dict,
            "average": average,
            "total_grades": len(grades_list),
        }
    )

# ============================================================================
# 13. EXPORT API
# ============================================================================

@app.route("/api/export/<string:kind>")
def api_export(kind):
    """
    API: Export Data to CSV.
    """
    if not require_auth():
        return unauthorized()

    conn = get_db()
    cur = conn.cursor()

    output = io.StringIO()
    writer = csv.writer(output)

    if kind == "students":
        writer.writerow(
            [
                "ID",
                "الاسم",
                "الصف",
                "تاريخ الميلاد",
                "هاتف ولي الأمر",
                "العنوان"
            ]
        )

        cur.execute(
            "SELECT * FROM students ORDER BY grade, name"
        )

        rows = cur.fetchall()

        for r in rows:
            writer.writerow(
                [
                    r["id"],
                    r["name"],
                    r["grade"],
                    r["birth_date"],
                    r["guardian_phone"],
                    r["address"]
                ]
            )

    elif kind == "teachers":
        writer.writerow(
            [
                "ID",
                "الاسم",
                "المادة",
                "الهاتف",
                "البريد",
                "تاريخ التعيين"
            ]
        )

        cur.execute(
            "SELECT * FROM teachers ORDER BY name"
        )

        rows = cur.fetchall()

        for r in rows:
            writer.writerow(
                [
                    r["id"],
                    r["name"],
                    r["subject"],
                    r["phone"],
                    r["email"],
                    r["hire_date"]
                ]
            )

    elif kind == "grades":
        writer.writerow(
            [
                "ID",
                "الطالب",
                "الصف",
                "المادة",
                "الدرجة",
                "من",
                "التاريخ",
                "ملاحظات"
            ]
        )

        cur.execute(
            """
            SELECT g.*, s.name as sname, s.grade as sgrade
            FROM grades g JOIN students s ON g.student_id = s.id
            ORDER BY s.grade, s.name
            """
        )

        rows = cur.fetchall()

        for r in rows:
            writer.writerow(
                [
                    r["id"],
                    r["sname"],
                    r["sgrade"],
                    r["subject"],
                    r["score"],
                    r["max_score"],
                    r["exam_date"],
                    r["notes"]
                ]
            )

    elif kind == "attendance":
        writer.writerow(
            [
                "ID",
                "الطالب",
                "الصف",
                "التاريخ",
                "الحالة",
                "ملاحظات"
            ]
        )

        cur.execute(
            """
            SELECT a.*, s.name as sname, s.grade as sgrade
            FROM attendance a JOIN students s ON a.student_id = s.id
            ORDER BY a.date DESC
            """
        )

        rows = cur.fetchall()

        for r in rows:
            writer.writerow(
                [
                    r["id"],
                    r["sname"],
                    r["sgrade"],
                    r["date"],
                    r["status"],
                    r["notes"]
                ]
            )

    else:
        conn.close()
        return jsonify(
            {
                "success": False,
                "error": "نوع التصدير غير معروف"
            }
        ), 400

    conn.close()

    csv_bytes = io.BytesIO(
        output.getvalue().encode("utf-8-sig")
    )

    csv_bytes.seek(0)

    return send_file(
        csv_bytes,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"{kind}_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    )

# ============================================================================
# 14. RUN APP
# ============================================================================

if __name__ == "__main__":
    app.run(
        debug=False,
        host="0.0.0.0",
        port=5000,
        threaded=True
    )

#    Hh = 1
#    while attempts > 0:
#        try:
#            user_pass = input("Enter Password: ")
#            if auth_login(user_pass):
#                print("\nConnected. Open http://127.0.0.1:5000\n")
#                app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
# SFR_044
#
#
#                break
#            else:
#                attempts -= 1
#                print(f"Wrong password. {attempts} attempts left.")
#        except KeyboardInterrupt:
#            print("\nExiting.")
#            break

#    if attempts == 0:
#        print("Exiting.")