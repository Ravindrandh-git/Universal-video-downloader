import sqlite3

def init_db():
    conn = sqlite3.connect('downloads.db')
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

# Run when script is executed
if __name__ == '__main__':
    init_db()
    print("✅ Database initialized!")