import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
import yt_dlp

# Initialize Flask app
app = Flask(_name_)
app.secret_key = 'supersecretkey'  # Replace with a secure key in production

# Admin login details
ADMIN_USERNAME = 'Ravindranadh'
ADMIN_PASSWORD = 'Syam@54321'

# Download and database paths
DOWNLOAD_DIR = "/tmp/downloads"
DB_PATH = "/tmp/downloads.db"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Helper function 
def save_cookie_from_env(env_key, target_path):
    raw_cookie = os.getenv(env_key)
    if not raw_cookie:
        return None
    decoded = raw_cookie.encode().decoded('unicode_escape')
    with open(target_path,"w") as f:
        f.write(decoded)
        return target_path

# Initialize database for download logs
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            format TEXT,
            timestamp TEXT,
            ip_address TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Home page
@app.route('/')
def index():
    return render_template("index.html")

# Handle video downloads
@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    quality = request.form.get('format')

    if not url:
        flash("Please enter a video URL")
        return redirect(url_for("index"))

    print("URL received:", url)
    print("Format selected:", quality)

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Quality map for yt_dlp
    format_map = {
        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "240p": "bestvideo[height<=240]+bestaudio/best[height<=240]",
        "best": "bestvideo+bestaudio/best"
    }

    selected_format = format_map.get(quality, "bestvideo+bestaudio/best")

    # Determine cookie source based on platform
    cookies_path = None
    if 'youtube.com' in url or 'youtu.be' in url:
        cookies_path = save_cookie_from_env("YT_COOKIES","/tmp/cookies.txt")
    elif 'instagram.com' in url:
        cookies_path = "/etc/secrets/INSTA_COOKIES"
    elif 'facebook.com' in url:
        cookies_path = "/etc/secrets/FB_COOKIES"

    # Write cookie data to temp file if available
    local_cookie_file = None
    if cookies_path and os.path.exists(cookies_path):
        local_cookie_file = os.path.join("/tmp", os.path.basename(cookies_path))
        with open(cookies_path, "r") as src, open(local_cookie_file, "w") as dst:
            dst.write(src.read())

    # yt-dlp options
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'quiet': False,
        'noplaylist': True,
        'no_warnings': True,
        'format': selected_format,
        'merge_output_format': 'mp4'
    }

    if local_cookie_file:
        ydl_opts['cookiefile'] = local_cookie_file

    # Attempt download
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown Title')
            filename = ydl.prepare_filename(info).split("/")[-1]
        message = "✅ Download completed!"
    except Exception as e:
        message = f"❌ Error: {str(e)}"
        title = "Download Failed"

    # Log to database
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO downloads (title, format, timestamp, ip_address) VALUES (?, ?, ?, ?)",
            (title, quality or "unknown", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), request.remote_addr)
        )
        conn.commit()
        conn.close()
    except Exception as db_err:
        print(f"Database error: {db_err}")

    return render_template("index.html", message=message)

# Serve downloaded files
@app.route('/downloads/<filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

# Admin login page
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

# Admin dashboard with logs
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM downloads ORDER BY id DESC")
    logs = c.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', logs=logs)

# Admin logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# Delete a specific log entry
@app.route('/admin/delete/<int:log_id>', methods=['POST'])
def delete_log(log_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM downloads WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))

# Uncomment to run locally
# if _name_ == "_main_":
#     app.run(debug=True