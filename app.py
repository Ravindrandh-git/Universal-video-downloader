import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
import yt_dlp
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

ADMIN_USERNAME = 'Ravindranadh'
ADMIN_PASSWORD = 'Syam@54321'


os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\ffmpeg\ffmpeg-7.1.1-essentials_build\bin"


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

#  Admin Routes  #
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('downloads.db')
    c = conn.cursor()
    c.execute("SELECT * FROM downloads ORDER BY id DESC")
    logs = c.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', logs=logs)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# ---------- Main Routes --------- #-
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/download', methods=['GET', 'POST'])
def download():
    message = ""
    if request.method == 'POST':
        url = request.form.get('url')
        quality = request.form.get('quality')

        format_map = {
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "240p": "bestvideo[height<=240]+bestaudio/best[height<=240]",
            "best": "bestvideo+bestaudio/best"
        }

        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'quiet': True,
            'noplaylist': True,
            'format': format_map.get(quality, 'bestvideo+bestaudio/best'),
            'merge_output_format': 'mp4'
        }

        # Add cookies if needed #
        if any(site in url for site in ['instagram.com', 'facebook.com']):
            ydl_opts['cookiefile'] = 'cookies.txt'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown Title')

            message = "✅ Download completed! Check the downloads folder."
        except Exception as e:
            message = f"❌ Error: {str(e)}"
            title = "Download Failed"

        # Log the download attempt #
        format_selected = quality or "unknown"
        ip = request.remote_addr
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = sqlite3.connect('downloads.db')
            c = conn.cursor()
            c.execute("""
                INSERT INTO downloads (title, format, timestamp, ip_address)
                VALUES (?, ?, ?, ?)""",
                (title, format_selected, time_now, ip)
            )
            conn.commit()
            conn.close()
        except Exception as db_err:
            print(f"Database error: {db_err}")

    return render_template("index.html", message=message)

# ---------- Run App ----------
if __name__ == "__main__":
    app.run(debug=True)
