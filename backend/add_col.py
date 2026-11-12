import sqlite3

def migrate():
    conn = sqlite3.connect('backend/access_control.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(devices)")
    cols = [r[1] for r in cursor.fetchall()]
    if 'universal_options' not in cols:
        cursor.execute("ALTER TABLE devices ADD COLUMN universal_options TEXT DEFAULT 'check_in,break_out,break_in,check_out'")
        conn.commit()
        print("Column universal_options added!")
    else:
        print("Column universal_options already exists")
    conn.close()

if __name__ == '__main__':
    migrate()
