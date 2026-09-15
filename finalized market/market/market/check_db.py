import pymysql

passwords = ['root', '', '1234', 'admin', 'mysql', 'password', 'toor']

print("Testing MySQL passwords...")
for pw in passwords:
    try:
        c = pymysql.connect(host='localhost', user='root', password=pw)
        print(f"\n✅ SUCCESS: password = \"{pw}\"")
        # Check if bakery_back database exists
        cur = c.cursor()
        cur.execute("SHOW DATABASES")
        dbs = [row[0] for row in cur.fetchall()]
        print(f"   Databases found: {dbs}")
        if 'bakery_back' in dbs:
            print("   ✅ bakery_back database EXISTS")
            cur.execute("USE bakery_back")
            cur.execute("SHOW TABLES")
            tables = [row[0] for row in cur.fetchall()]
            print(f"   Tables: {tables}")
        else:
            print("   ❌ bakery_back does NOT exist — need to create it")
        cur.close()
        c.close()
        break
    except Exception as e:
        print(f"FAIL pw={repr(pw)}: {e}")
