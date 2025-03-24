from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure key

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
def init_db():
    with sqlite3.connect('notice_board.db') as conn:
        c = conn.cursor()
        # Users table for signup/login
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                     )''')
        # Notices table (each notice linked to a department)
        c.execute('''CREATE TABLE IF NOT EXISTS notices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        department TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        filetype TEXT NOT NULL
                     )''')
        conn.commit()

init_db()

# Helper: Check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---

# Index Page
@app.route('/')
def index():
    return render_template('index.html')

# Sign Up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('notice_board.db') as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                flash('Signup successful. Please login.')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Username already exists. Try a different one.')
                return redirect(url_for('signup'))
    return render_template('signup.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('notice_board.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            if user:
                session['username'] = username
                flash('Login successful.')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials. Try again.')
                return redirect(url_for('login'))
    return render_template('login.html')

# Dashboard with animated department buttons
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        # Departments list (could be extended as needed)
        departments = ['extc', 'it', 'mech', 'cs']
        return render_template('dashboard.html', departments=departments)
    else:
        flash('Please login first.')
        return redirect(url_for('login'))

# Department Admin Page – asks for department admin password (e.g., extc@22)
@app.route('/department/<dept>', methods=['GET', 'POST'])
def department(dept):
    if request.method == 'POST':
        admin_pass = request.form['admin_pass']
        # For simplicity, the admin password is set as: dept + '@22'
        if admin_pass == f"{dept}@22":
            session['dept'] = dept
            return redirect(url_for('admin', dept=dept))
        else:
            flash('Incorrect department admin password.')
            return redirect(url_for('department', dept=dept))
    return render_template('department.html', department=dept)

# Admin Panel – Upload & manage notices
@app.route('/admin/<dept>', methods=['GET', 'POST'])
def admin(dept):
    if 'dept' in session and session['dept'] == dept:
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file part.')
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                flash('No selected file.')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                with sqlite3.connect('notice_board.db') as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO notices (department, filename, filetype) VALUES (?, ?, ?)",
                              (dept, filename, filename.rsplit('.', 1)[1].lower()))
                    conn.commit()
                flash('File uploaded successfully.')
                return redirect(url_for('admin', dept=dept))
        with sqlite3.connect('notice_board.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM notices WHERE department=?", (dept,))
            notices = c.fetchall()
        return render_template('admin.html', department=dept, notices=notices)
    else:
        flash('Unauthorized access. Please enter department admin password.')
        return redirect(url_for('department', dept=dept))

# Delete Notice
@app.route('/delete_notice/<int:notice_id>')
def delete_notice(notice_id):
    if 'dept' in session:
        with sqlite3.connect('notice_board.db') as conn:
            c = conn.cursor()
            c.execute("SELECT filename, department FROM notices WHERE id=?", (notice_id,))
            notice = c.fetchone()
            if notice:
                filename, department = notice
                if session['dept'] == department:
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    except Exception as e:
                        print(e)
                    c.execute("DELETE FROM notices WHERE id=?", (notice_id,))
                    conn.commit()
                    flash('Notice deleted successfully.')
                else:
                    flash('Unauthorized action.')
            else:
                flash('Notice not found.')
        return redirect(url_for('admin', dept=session['dept']))
    else:
        flash('Unauthorized access.')
        return redirect(url_for('login'))

# Serve Uploaded Files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Slideshow – Displays notices with a user-specified timer
@app.route('/slideshow/<dept>', methods=['GET', 'POST'])
def slideshow(dept):
    timer = 5  # default timer in seconds
    if request.method == 'POST':
        try:
            timer = int(request.form.get('timer', 5))
        except ValueError:
            timer = 5
    with sqlite3.connect('notice_board.db') as conn:
        c = conn.cursor()
        c.execute("SELECT filename, filetype FROM notices WHERE department=?", (dept,))
        notices = c.fetchall()
    return render_template('slideshow.html', department=dept, notices=notices, timer=timer)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
