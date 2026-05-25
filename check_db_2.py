import sqlite3

conn = sqlite3.connect('kargo_data.db')
cursor = conn.cursor()

# Check if the plate exists
cursor.execute("SELECT * FROM yakit WHERE plaka = '46AHR076' LIMIT 5;")
rows = cursor.fetchall()
print(f"Records for 46AHR076: {len(rows)}")
for row in rows:
    print(row)

# Let's also check column names
cursor.execute("PRAGMA table_info(yakit);")
cols = cursor.fetchall()
print("\nYakit table columns:")
for col in cols:
    print(col)

conn.close()
