import sqlite3

# Connect to database
conn = sqlite3.connect('database/data.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:")
print(tables)

# Get schema for each table
for table in tables:
    table_name = table[0]
    print(f"\n\nTable: {table_name}")
    print("="*50)
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Get sample data
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
    rows = cursor.fetchall()
    print(f"\nSample data ({len(rows)} rows):")
    for row in rows:
        print(f"  {row}")

conn.close()
