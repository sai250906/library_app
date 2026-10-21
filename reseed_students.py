import hashlib
from db import get_connection

try:
    conn = get_connection()
    cursor = conn.cursor()

    # Step 1: Delete all existing loans and students
    cursor.execute("DELETE FROM loans")
    cursor.execute("DELETE FROM students")
    print("All existing students and loans removed (SQLite).")

    # Step 2: Hash the password "password"
    hashed = hashlib.sha256("password".encode()).hexdigest()

    # Step 3: New Indian students
    students = [
        ("Aarav Sharma",  "aarav@library.in",  "aarav",  hashed),
        ("Priya Patel",   "priya@library.in",  "priya",  hashed),
        ("Rohan Mehta",   "rohan@library.in",  "rohan",  hashed),
        ("Ananya Singh",  "ananya@library.in", "ananya", hashed),
        ("Karan Verma",   "karan@library.in",  "karan",  hashed),
        ("Sneha Iyer",    "sneha@library.in",  "sneha",  hashed),
        ("Vikram Rao",    "vikram@library.in", "vikram", hashed),
        ("Pooja Gupta",   "pooja@library.in",  "pooja",  hashed),
    ]

    cursor.executemany(
        "INSERT INTO students (name, email, username, password) VALUES (?, ?, ?, ?)",
        students
    )
    conn.commit()
    print(f"{len(students)} Indian students added to SQLite database.")

    # Step 4: Verify
    cursor.execute("SELECT id, name, username FROM students ORDER BY id")
    rows = cursor.fetchall()
    print("\n=== NEW STUDENT ACCOUNTS ===")
    print(f"{'ID':<6} {'Name':<20} {'Username'}")
    print("-" * 45)
    for r in rows:
        print(f"{r['id']:<6} {r['name']:<20} {r['username']}")
    print("\nPassword for all accounts: password")

except Exception as e:
    print(f"Error seeding SQLite database: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()
