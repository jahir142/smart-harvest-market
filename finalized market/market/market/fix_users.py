import pymysql

conn = pymysql.connect(
    host='localhost', user='root', password='root',
    database='bakery_market',
    cursorclass=pymysql.cursors.Cursor
)
cur = conn.cursor()

# Drop old table and create with correct schema
cur.execute("DROP TABLE IF EXISTS users")
cur.execute("""
    CREATE TABLE users (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        username   VARCHAR(100) UNIQUE NOT NULL,
        password   TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()
cur.close()
conn.close()
print("Done — users table recreated with username column")
