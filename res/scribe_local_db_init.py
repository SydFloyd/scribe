import sqlite3

# Connect to SQLite database (or create if it doesn’t exist)
conn = sqlite3.connect('scribe.db')

# Create a cursor object
cur = conn.cursor()

# Create a table
cur.execute('''CREATE TABLE IF NOT EXISTS speech 
            (id INTEGER PRIMARY KEY, 
            file_path TEXT,
            transcript TEXT,
            start_timestamp TEXT,
            end_timestamp TEXT,
            start_year INTEGER, 
            start_month INTEGER, 
            start_day INTEGER,
            start_hour INTEGER,
            start_minute INTEGER,
            start_second INTEGER,
            end_year INTEGER,
            end_month INTEGER,
            end_day INTEGER,
            end_hour INTEGER,
            end_minute INTEGER,
            end_second INTEGER,
            comment TEXT
            )''')

# Save (commit) the changes
conn.commit()

# Always close the connection when done
conn.close()