from flask import Flask, render_template, request, redirect, url_for, session, flash
import pyodbc

app = Flask(__name__)
app.secret_key = 'key'


def get_db_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=TECNO\\SQLEXPRESS;'
        'DATABASE=campus;'
        'Trusted_Connection=yes;'
    )


@app.route("/")
def home():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.code AS id, e.title, e.description, e.starts_at, e.capacity,
            (SELECT COUNT(*) FROM [dbo].[Регистрации$] r WHERE r.event_code = e.code) AS taken
            FROM [dbo].[Events_] e
        """)
        events = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    return render_template("index.html", events=events)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contacts")
def contacts():
    return render_template("contacts.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email, password = request.form.get("email"), request.form.get("password")
        if not email or not password:
            flash("Email и пароль обязательны")
            return render_template("login.html")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, name FROM users WHERE email = ? AND password = ?", (email, password))
            user = cursor.fetchone()
            if user:
                session.update({"user_email": email, "user_role": user[0], "user_name": user[1]})
                return redirect("/")
            flash("Неверный email или пароль")
    return render_template("login.html")


@app.route("/register_page", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        data = {k: request.form.get(k) for k in ["surname", "name", "email", "password", "role"]}
        if not all(data.values()):
            flash("Заполните все поля")
            return render_template("register.html")

        with get_db_connection() as conn:
            try:
                conn.cursor().execute(
                    "INSERT INTO users (email, password, surname, name, role) VALUES (?, ?, ?, ?, ?)",
                    tuple(data.values())
                )
                conn.commit()
                flash("Аккаунт создан! Теперь войдите.")
                return redirect("/login")
            except Exception:
                flash("Этот email уже занят")
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/cabinet")
def cabinet():
    if "user_email" not in session:
        flash("Сначала войдите в систему")
        return redirect("/login")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.code, e.title, e.starts_at 
            FROM [dbo].[Events_] e
            JOIN [dbo].[Регистрации$] r ON e.code = r.event_code
            WHERE r.student_email = ?
        """, (session["user_email"],))
        events = cursor.fetchall()
    return render_template("cabinet.html", events=events)


@app.route("/enroll/<event_code>")
def enroll(event_code):
    if "user_email" not in session:
        flash("Сначала войдите в систему")
        return redirect("/login")
    if str(session.get("user_role")) != "2":
        flash("Только студенты могут записываться на мероприятия")
        return redirect("/")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            if cursor.execute("SELECT 1 FROM [dbo].[Регистрации$] WHERE event_code = ? AND student_email = ?",
                              (event_code, session["user_email"])).fetchone():
                flash("Вы уже записаны на это мероприятие")
                return redirect("/")

            capacity, taken = cursor.execute(
                "SELECT capacity, (SELECT COUNT(*) FROM [dbo].[Регистрации$] WHERE event_code = ?) FROM [dbo].[Events_] WHERE code = ?",
                (event_code, event_code)
            ).fetchone()

            if taken >= capacity:
                flash("К сожалению, мест больше нет")
                return redirect("/")

            cursor.execute("INSERT INTO [dbo].[Регистрации$] (event_code, student_email) VALUES (?, ?)",
                           (event_code, session["user_email"]))
            conn.commit()
            flash("Вы успешно записались на мероприятие!")
        except Exception as e:
            conn.rollback()
            flash(f"Ошибка при записи: {e}")
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)