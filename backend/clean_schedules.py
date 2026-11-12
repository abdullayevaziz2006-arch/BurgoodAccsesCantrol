import sqlite3

def clean(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM schedules WHERE id IN (2, 3) OR name LIKE '%qish%'")
    conn.commit()
    c.execute("SELECT id, name FROM schedules")
    print("Schedules in", db_path, ":", c.fetchall())
    conn.close()

if __name__ == '__main__':
    clean('backend/access_control.db')
