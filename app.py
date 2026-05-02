from flask import Flask, request, jsonify, render_template, send_file
import sqlite3
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

def get_db():
    return sqlite3.connect("dyeing_system_pro.db")

def setup():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS invoices (id INTEGER PRIMARY KEY, customer TEXT, amount REAL, method TEXT, date TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, category TEXT, amount REAL, date TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS dyes (id INTEGER PRIMARY KEY, name TEXT, quantity REAL, price REAL, min_limit REAL)")
    cur.execute("CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY, name TEXT, job TEXT, salary REAL, balance REAL)")
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")

    cur.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('admin','1234')")

    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/login', methods=['POST'])
def login():
    d = request.json
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username=? AND password=?",
                (d['username'], d['password']))
    user = cur.fetchone()
    conn.close()

    return jsonify({"ok": bool(user)})

@app.route('/add_invoice', methods=['POST'])
def add_invoice():
    data = request.json
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO invoices (customer, amount, method, date) VALUES (?, ?, ?, date('now'))",
        (data['customer'], data['amount'], data['method'])
    )

    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route('/invoices')
def invoices():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM invoices ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/add_dye', methods=['POST'])
def add_dye():
    d = request.json
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO dyes (name, quantity, price, min_limit) VALUES (?,?,?,?)",
        (d['name'], d['qty'], d['price'], d['min'])
    )

    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route('/dyes')
def dyes():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM dyes")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/add_emp', methods=['POST'])
def add_emp():
    d = request.json
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO employees (name, job, salary, balance) VALUES (?,?,?,0)",
        (d['name'], d['job'], d['salary'])
    )

    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route('/emps')
def emps():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/report')
def report():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT SUM(amount) FROM invoices")
    sales = cur.fetchone()[0] or 0

    cur.execute("SELECT SUM(amount) FROM expenses")
    costs = cur.fetchone()[0] or 0

    conn.close()
    return jsonify({"sales": sales, "costs": costs, "net": sales - costs})

@app.route('/alerts')
def alerts():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT name, quantity, min_limit FROM dyes WHERE quantity <= min_limit")
    rows = cur.fetchall()

    conn.close()
    return jsonify(rows)

@app.route('/invoice_pdf/<int:id>')
def invoice_pdf(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM invoices WHERE id=?", (id,))
    inv = cur.fetchone()
    conn.close()

    if not inv:
        return "Not found"

    filename = f"invoice_{id}.pdf"

    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Royal Care Invoice", styles['Title']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Invoice ID: {inv[0]}", styles['Normal']))
    elements.append(Paragraph(f"Customer: {inv[1]}", styles['Normal']))
    elements.append(Paragraph(f"Amount: {inv[2]}", styles['Normal']))
    elements.append(Paragraph(f"Date: {inv[4]}", styles['Normal']))

    doc.build(elements)

    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    setup()
    app.run()
