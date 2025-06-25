import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
import yt_dlp

app = Flask(__name__)
app.secret_key = 'supersecretkey'

ADMIN_USERNAME = 'Ravindranadh'
ADMIN_PASSWORD = 'Syam@54321'

DOWNLOAD_DIR = "/tmp/downloads"
DB_PATH = "/tmp/downloads.db"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    quality = request.form.get('format')

    if not url:
        flash("Please enter a video URL")
        return redirect(url_for("index"))

    print("URL received:", url)
    print("Format selected:", quality)

    os.environ["PATH"] = os.getenv("PATH", "") + os.pathsep + "/usr/bin"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    format_map = {
        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "240p": "bestvideo[height<=240]+bestaudio/best[height<=240]",
        "best": "bestvideo+bestaudio/best"
    }

    if 'youtube.com' in url or 'youtu.be' in url:
        selected_format = format_map.get(quality, "bestvideo+bestaudio/best")
        cookie_file = 'auth/yt_cookies.txt'
    elif 'instagram.com' in url:
        selected_format = 'best'
        cookie_file = 'auth/insta_cookies.txt'
    elif 'facebook.com' in url:
        selected_format = 'best'
        cookie_file = 'auth/fb_cookies.txt'
    else:
        selected_format = 'best'
        cookie_file = None

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'quiet': False,
        'noplaylist': True,
        'no_warnings': True,
        'format': selected_format,
        'merge_output_format': 'mp4',
        'ffmpeg_location': 'c:\\ffmpeg\\ffmpeg\\ffmpeg-7.1.1-essentials_build\\bin\\ffmpeg.exe'
    }

    if cookie_file and os.path.exists(cookie_file):
        ydl_opts['cookiefile'] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown Title')
            filename = ydl.prepare_filename(info).split("/")[-1]
        message = "✅ Download completed!"
    except Exception as e:
        message = f"❌ Error: {str(e)}"
        title = "Download Failed"

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

@app.route('/downloads/<filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

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

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

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
# if __name__ == "__main__":
#     app.run(debug=True)
