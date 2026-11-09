from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from database import get_db, init_db
from auth import is_authenticated, login as auth_login, logout as auth_logout
import csv
import io
import time


app = Flask(__name__)
init_db()

# SFR_044

def require_auth():
    return is_authenticated()

def unauthorized():
    return jsonify({"success": False, "error": "Unauthorized"}), 401

def render_page(template, **kwargs):
    kwargs.setdefault('logo_light', url_for('static', filename='1.jpg'))
    kwargs.setdefault('logo_dark', url_for('static', filename='2.jpg'))
    return render_template(template, **kwargs)


@app.route("/")
@app.route("/home")
def home():
    if not require_auth():
        return redirect(url_for("login_page"))
    return render_page("index.html", title="الرئيسية", page="home")

@app.route("/students")
def students_page():
    if not require_auth():
        return redirect(url_for("login_page"))
    return render_page("index.html", title="الطلاب", page="students")

@app.route("/teachers")
def teachers_page():
    if not require_auth():
        return redirect(url_for("login_page"))
    return render_page("index.html", title="المعلمون", page="teachers")

@app.route("/schedule")
def schedule_page():
    if not require_auth():
        return redirect(url_for("login_page"))
    return render_page("index.html", title="الجدول", page="schedule")

@app.route("/grades")
def grades_page():
    if not require_auth():
        return redirect(url_for("login_page"))
    return render_page("index.html", title="الدرجات", page="grades")

@app.route("/attendance")
def attendance_page():
    if not require_auth():
        return redirect(url_for("login_page"))
    return render_page("index.html", title="الحضور", page="attendance")

@app.route("/reports")
def reports_page():
    if not require_auth():
        return redirect(url_for("login_page"))
    return render_page("index.html", title="التقارير", page="reports")

@app.route("/login")
def login_page():
    return render_page("login.html")

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    if auth_login(data.get("password", "")):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "كلمة المرور غير صحيحة"}), 401

@app.route("/api/logout", methods=["POST"])
def api_logout():
    auth_logout()
    return jsonify({"success": True})

@app.route("/api/stats")
def api_stats():
    if not require_auth():
        return unauthorized()

    conn = get_db()
    cur = conn.cursor()

    students_count = cur.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    teachers_count = cur.execute("SELECT COUNT(*) FROM teachers").fetchone()[0]
    classes_count = cur.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
    grades_count = cur.execute("SELECT COUNT(*) FROM grades").fetchone()[0]

    today = time.strftime("%Y-%m-%d")
    present_today = cur.execute(
        "SELECT COUNT(*) FROM attendance WHERE date = ? AND status = 'present'",
        (today,)
    ).fetchone()[0]
    absent_today = cur.execute(
        "SELECT COUNT(*) FROM attendance WHERE date = ? AND status = 'absent'",
        (today,)
    ).fetchone()[0]

    grade_rows = cur.execute("SELECT grade, COUNT(*) as cnt FROM students GROUP BY grade").fetchall()
    by_grade = [{"grade": r["grade"], "count": r["cnt"]} for r in grade_rows]

    conn.close()

    return jsonify({
        "success": True,
        "students": students_count,
        "teachers": teachers_count,
        "classes": classes_count,
        "grades": grades_count,
        "present_today": present_today,
        "absent_today": absent_today,
        "by_grade": by_grade,
    })


@app.route("/api/students", methods=["GET"])
def api_students_list():
    if not require_auth():
        return unauthorized()

    search = request.args.get("q", "").strip()
    grade_filter = request.args.get("grade", "").strip()

    conn = get_db()
    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR guardian_phone LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if grade_filter:
        query += " AND grade = ?"
        params.append(grade_filter)

    query += " ORDER BY grade, name"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify({"success": True, "students": [dict(r) for r in rows]})


@app.route("/api/students", methods=["POST"])
def api_students_add():
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    grade = (data.get("grade") or "").strip()

    if not name or not grade:
        return jsonify({"success": False, "error": "الاسم والصف مطلوبان"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO students (name, grade, birth_date, guardian_phone, address) VALUES (?, ?, ?, ?, ?)",
        (name, grade, data.get("birth_date", ""), data.get("guardian_phone", ""), data.get("address", ""))
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({"success": True, "id": new_id})


@app.route("/api/students/<int:sid>", methods=["PUT"])
def api_students_update(sid):
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    grade = (data.get("grade") or "").strip()

    if not name or not grade:
        return jsonify({"success": False, "error": "الاسم والصف مطلوبان"}), 400

    conn = get_db()
    conn.execute(
        "UPDATE students SET name=?, grade=?, birth_date=?, guardian_phone=?, address=? WHERE id=?",
        (name, grade, data.get("birth_date", ""), data.get("guardian_phone", ""), data.get("address", ""), sid)
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/students/<int:sid>", methods=["DELETE"])
def api_students_delete(sid):
    if not require_auth():
        return unauthorized()

    conn = get_db()
    conn.execute("DELETE FROM students WHERE id=?", (sid,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/teachers", methods=["GET"])
def api_teachers_list():
    if not require_auth():
        return unauthorized()

    conn = get_db()
    rows = conn.execute("SELECT * FROM teachers ORDER BY name").fetchall()
    conn.close()

    return jsonify({"success": True, "teachers": [dict(r) for r in rows]})


@app.route("/api/teachers", methods=["POST"])
def api_teachers_add():
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    subject = (data.get("subject") or "").strip()

    if not name or not subject:
        return jsonify({"success": False, "error": "الاسم والمادة مطلوبان"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO teachers (name, subject, phone, email, hire_date) VALUES (?, ?, ?, ?, ?)",
        (name, subject, data.get("phone", ""), data.get("email", ""), data.get("hire_date", ""))
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({"success": True, "id": new_id})


@app.route("/api/teachers/<int:tid>", methods=["PUT"])
def api_teachers_update(tid):
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    subject = (data.get("subject") or "").strip()

    if not name or not subject:
        return jsonify({"success": False, "error": "الاسم والمادة مطلوبان"}), 400

    conn = get_db()
    conn.execute(
        "UPDATE teachers SET name=?, subject=?, phone=?, email=?, hire_date=? WHERE id=?",
        (name, subject, data.get("phone", ""), data.get("email", ""), data.get("hire_date", ""), tid)
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/teachers/<int:tid>", methods=["DELETE"])
def api_teachers_delete(tid):
    if not require_auth():
        return unauthorized()

    conn = get_db()
    conn.execute("DELETE FROM teachers WHERE id=?", (tid,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/schedule", methods=["GET"])
def api_schedule_list():
    if not require_auth():
        return unauthorized()

    grade = request.args.get("grade", "").strip()

    conn = get_db()
    if grade:
        rows = conn.execute("""
            SELECT c.*, t.name as teacher_name
            FROM classes c
            LEFT JOIN teachers t ON c.teacher_id = t.id
            WHERE c.grade = ?
            ORDER BY c.day, c.period
        """, (grade,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT c.*, t.name as teacher_name
            FROM classes c
            LEFT JOIN teachers t ON c.teacher_id = t.id
            ORDER BY c.grade, c.day, c.period
        """).fetchall()

    conn.close()
    return jsonify({"success": True, "classes": [dict(r) for r in rows]})


@app.route("/api/schedule", methods=["POST"])
def api_schedule_add():
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}
    grade = (data.get("grade") or "").strip()
    day = (data.get("day") or "").strip()
    subject = (data.get("subject") or "").strip()

    if not grade or not day or not subject:
        return jsonify({"success": False, "error": "الصف واليوم والمادة مطلوبة"}), 400

    try:
        period = int(data.get("period", 1))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "رقم الحصة غير صحيح"}), 400

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
        "INSERT INTO classes (grade, day, period, subject, teacher_id) VALUES (?, ?, ?, ?, ?)",
        (grade, day, period, subject, teacher_id)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({"success": True, "id": new_id})


@app.route("/api/schedule/<int:cid>", methods=["DELETE"])
def api_schedule_delete(cid):
    if not require_auth():
        return unauthorized()

    conn = get_db()
    conn.execute("DELETE FROM classes WHERE id=?", (cid,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/grades", methods=["GET"])
def api_grades_list():
    if not require_auth():
        return unauthorized()

    student_id = request.args.get("student_id", "").strip()
    subject = request.args.get("subject", "").strip()

    conn = get_db()
    query = """
        SELECT g.*, s.name as student_name, s.grade as student_grade
        FROM grades g
        JOIN students s ON g.student_id = s.id
        WHERE 1=1
    """
    params = []

    if student_id:
        query += " AND g.student_id = ?"
        params.append(student_id)
    if subject:
        query += " AND g.subject = ?"
        params.append(subject)

    query += " ORDER BY g.exam_date DESC, g.id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify({"success": True, "grades": [dict(r) for r in rows]})


@app.route("/api/grades", methods=["POST"])
def api_grades_add():
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}
    try:
        student_id = int(data.get("student_id"))
        score = float(data.get("score"))
        max_score = float(data.get("max_score", 100))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "بيانات غير صحيحة"}), 400

    subject = (data.get("subject") or "").strip()
    if not subject:
        return jsonify({"success": False, "error": "المادة مطلوبة"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO grades (student_id, subject, score, max_score, exam_date, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (student_id, subject, score, max_score, data.get("exam_date", ""), data.get("notes", ""))
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({"success": True, "id": new_id})


@app.route("/api/grades/<int:gid>", methods=["DELETE"])
def api_grades_delete(gid):
    if not require_auth():
        return unauthorized()

    conn = get_db()
    conn.execute("DELETE FROM grades WHERE id=?", (gid,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/attendance", methods=["GET"])
def api_attendance_list():
    if not require_auth():
        return unauthorized()

    date = request.args.get("date", "").strip()
    grade = request.args.get("grade", "").strip()

    conn = get_db()
    query = """
        SELECT a.*, s.name as student_name, s.grade as student_grade
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE 1=1
    """
    params = []

    if date:
        query += " AND a.date = ?"
        params.append(date)
    if grade:
        query += " AND s.grade = ?"
        params.append(grade)

    query += " ORDER BY a.date DESC, s.name"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify({"success": True, "attendance": [dict(r) for r in rows]})


@app.route("/api/attendance", methods=["POST"])
def api_attendance_add():
    if not require_auth():
        return unauthorized()

    data = request.get_json() or {}
    try:
        student_id = int(data.get("student_id"))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "الطالب غير صحيح"}), 400

    date = (data.get("date") or "").strip()
    status = (data.get("status") or "").strip()

    if not date or status not in ("present", "absent", "late"):
        return jsonify({"success": False, "error": "البيانات غير صحيحة"}), 400

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM attendance WHERE student_id=? AND date=?",
        (student_id, date)
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE attendance SET status=?, notes=? WHERE id=?",
            (status, data.get("notes", ""), existing["id"])
        )
    else:
        conn.execute(
            "INSERT INTO attendance (student_id, date, status, notes) VALUES (?, ?, ?, ?)",
            (student_id, date, status, data.get("notes", ""))
        )

    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/report/student/<int:sid>")
def api_report_student(sid):
    if not require_auth():
        return unauthorized()

    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    if not student:
        conn.close()
        return jsonify({"success": False, "error": "الطالب غير موجود"}), 404

    grades = conn.execute(
        "SELECT subject, score, max_score, exam_date FROM grades WHERE student_id=? ORDER BY exam_date DESC",
        (sid,)
    ).fetchall()

    attendance = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM attendance WHERE student_id=? GROUP BY status",
        (sid,)
    ).fetchall()

    conn.close()

    grades_list = [dict(g) for g in grades]
    total_score = sum(g["score"] for g in grades_list)
    total_max = sum(g["max_score"] for g in grades_list)
    average = round((total_score / total_max * 100) if total_max > 0 else 0, 1)

    attendance_dict = {a["status"]: a["cnt"] for a in attendance}

    return jsonify({
        "success": True,
        "student": dict(student),
        "grades": grades_list,
        "attendance": attendance_dict,
        "average": average,
        "total_grades": len(grades_list),
    })


@app.route("/api/export/<string:kind>")
def api_export(kind):
    if not require_auth():
        return unauthorized()

    conn = get_db()
    output = io.StringIO()
    writer = csv.writer(output)

    if kind == "students":
        writer.writerow(["ID", "الاسم", "الصف", "تاريخ الميلاد", "هاتف ولي الأمر", "العنوان"])
        rows = conn.execute("SELECT * FROM students ORDER BY grade, name").fetchall()
        for r in rows:
            writer.writerow([r["id"], r["name"], r["grade"], r["birth_date"], r["guardian_phone"], r["address"]])

    elif kind == "teachers":
        writer.writerow(["ID", "الاسم", "المادة", "الهاتف", "البريد", "تاريخ التعيين"])
        rows = conn.execute("SELECT * FROM teachers ORDER BY name").fetchall()
        for r in rows:
            writer.writerow([r["id"], r["name"], r["subject"], r["phone"], r["email"], r["hire_date"]])

    elif kind == "grades":
        writer.writerow(["ID", "الطالب", "الصف", "المادة", "الدرجة", "من", "التاريخ", "ملاحظات"])
        rows = conn.execute("""
            SELECT g.*, s.name as sname, s.grade as sgrade
            FROM grades g JOIN students s ON g.student_id = s.id
            ORDER BY s.grade, s.name
        """).fetchall()
        for r in rows:
            writer.writerow([r["id"], r["sname"], r["sgrade"], r["subject"], r["score"], r["max_score"], r["exam_date"], r["notes"]])

    elif kind == "attendance":
        writer.writerow(["ID", "الطالب", "الصف", "التاريخ", "الحالة", "ملاحظات"])
        rows = conn.execute("""
            SELECT a.*, s.name as sname, s.grade as sgrade
            FROM attendance a JOIN students s ON a.student_id = s.id
            ORDER BY a.date DESC
        """).fetchall()
        for r in rows:
            writer.writerow([r["id"], r["sname"], r["sgrade"], r["date"], r["status"], r["notes"]])
    else:
        conn.close()
        return jsonify({"success": False, "error": "نوع التصدير غير معروف"}), 400

    conn.close()

    csv_bytes = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    csv_bytes.seek(0)

    return send_file(
        csv_bytes,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"{kind}_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    )


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
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