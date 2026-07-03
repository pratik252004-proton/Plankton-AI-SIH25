import sqlite3

conn = sqlite3.connect('database/detection_db.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(detections)')
cols = cursor.fetchall()

print('DATABASE SCHEMA:')
for col in cols:
    print(f"  {col[1]} ({col[2]})")

cursor.execute('SELECT COUNT(*) FROM detections')
count = cursor.fetchone()[0]
print(f"\nTotal records: {count}")

conn.close()
