import sqlite3

def migrate(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("PRAGMA table_info(shifts)")
    cols = [r[1] for r in c.fetchall()]
    if 'lunch_start' not in cols:
        c.execute("ALTER TABLE shifts ADD COLUMN lunch_start VARCHAR(10) DEFAULT '12:00'")
        print("Added lunch_start to", db_path)
    if 'lunch_end' not in cols:
        c.execute("ALTER TABLE shifts ADD COLUMN lunch_end VARCHAR(10) DEFAULT '13:00'")
        print("Added lunch_end to", db_path)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate('backend/access_control.db')
