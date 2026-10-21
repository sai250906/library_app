from db import get_connection

try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, username, password FROM students ORDER BY id")
    rows = cursor.fetchall()

    print("=== STUDENT ACCOUNTS (SQLite) ===\n")
    print(f"{'ID':<5} {'Name':<20} {'Username':<15} {'Password Hash'}")
    print("-" * 70)
    for r in rows:
        print(f"{r['id']:<5} {r['name']:<20} {r['username']:<15} {r[3]}")
    
    print(f"\nTotal: {len(rows)} students")
except Exception as e:
    print(f"Error accessing SQLite database: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()
