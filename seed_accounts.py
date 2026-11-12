import sqlite3

conn = sqlite3.connect('/home/ubuntu/burgood/backend/access_control.db')
c = conn.cursor()

# Org 1: Urganch Davlat Universiteti
c.execute("UPDATE organizations SET admin_username='urdu_admin', admin_password='admin123' WHERE id=1")

# Org 3: Office
c.execute("SELECT id FROM organizations WHERE id=3")
if not c.fetchone():
    c.execute("""INSERT INTO organizations 
        (id, name, code, org_type, admin_username, admin_password, is_active, modules_enabled, created_at)
        VALUES 
        (3, 'Burgood Savdo Idorasi', 'BGD_OFFICE', 'office', 'idora_admin', 'admin123', 1, 'attendance,staff,schedules,structure', datetime('now'))
    """)

# Delete old test accounts to re-seed clean ones
c.execute("DELETE FROM system_accounts WHERE username IN ('kadr_urgu', 'tyutor_nodir', 'direktor_akmal', 'buxgalter_sarvar', 'kadr_umida')")

# University Accounts
c.execute("""INSERT INTO system_accounts 
    (full_name, username, password, role, organization_id, allowed_apps, allowed_modules, is_active, created_at)
    VALUES 
    ('Dilnoza Karimova (Kadr)', 'kadr_urgu', 'kadr123', 'otdel_kadr', 1, 'desktop,android', 'attendance,staff', 1, datetime('now')),
    ('Nodirbek Aliyev (Tyutor)', 'tyutor_nodir', 'tyutor123', 'tutor', 1, 'desktop,android', 'attendance,students', 1, datetime('now'))
""")

# Office Accounts
c.execute("""INSERT INTO system_accounts 
    (full_name, username, password, role, organization_id, allowed_apps, allowed_modules, is_active, created_at)
    VALUES 
    ('Akmal Rustamov (Bosh Direktor)', 'direktor_akmal', 'dir123', 'director', 3, 'desktop,android', 'attendance,staff,reports', 1, datetime('now')),
    ('Sarvar Xolmatov (Bosh Buxgalter)', 'buxgalter_sarvar', 'bux123', 'accountant', 3, 'desktop,android', 'attendance,staff,reports', 1, datetime('now')),
    ('Umida Karimova (Kadrlar bolimi)', 'kadr_umida', 'kadr123', 'otdel_kadr', 3, 'desktop,android', 'attendance,staff', 1, datetime('now'))
""")

conn.commit()
print('SUCCESS! Seeded test accounts:')
for row in c.execute('SELECT id, username, password, role, organization_id, allowed_apps FROM system_accounts'):
    print(row)
conn.close()
