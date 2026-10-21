import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'library.db')

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    # Database tables will be created below if they do not exist
    # Create students table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Create books table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        category TEXT DEFAULT 'Uncategorized',
        quantity INTEGER DEFAULT 1,
        remaining INTEGER DEFAULT 1
    )
    """)

    # Create loans table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        issue_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        due_date DATETIME,
        returned INTEGER DEFAULT 0,
        fine_paid REAL DEFAULT 0.0,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
    )
    """)

    # Create holds table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS holds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
    )
    """)

    # Seed some sample books if the table is empty
    cursor.execute("SELECT COUNT(*) FROM books")
    if cursor.fetchone()[0] == 0:
        sample_books = [
            ("To Kill a Mockingbird", "Harper Lee", "Fiction", 2, 2),
            ("1984", "George Orwell", "Sci-Fi", 3, 3),
            ("The Great Gatsby", "F. Scott Fitzgerald", "Fiction", 1, 1),
            ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "Fantasy", 5, 5),
            ("The Alchemist", "Paulo Coelho", "Adventure", 4, 4),
            ("Pride and Prejudice", "Jane Austen", "Romance", 2, 2),
            ("The Hobbit", "J.R.R. Tolkien", "Fantasy", 3, 3),
            ("Animal Farm", "George Orwell", "Satire", 2, 2),
        ]
        cursor.executemany("INSERT INTO books (title, author, category, quantity, remaining) VALUES (?, ?, ?, ?, ?)", sample_books)
        print("Sample books added.")

    # Seed Indian student accounts if none exist
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        indian_students = [
            ("Aarav Sharma",   "aarav.sharma@library.com",   "aarav",   "pass123"),
            ("Priya Patel",    "priya.patel@library.com",    "priya",   "pass123"),
            ("Rohan Mehta",    "rohan.mehta@library.com",    "rohan",   "pass123"),
            ("Ananya Iyer",    "ananya.iyer@library.com",    "ananya",  "pass123"),
            ("Vikram Singh",   "vikram.singh@library.com",   "vikram",  "pass123"),
            ("Sneha Reddy",    "sneha.reddy@library.com",    "sneha",   "pass123"),
            ("Arjun Nair",     "arjun.nair@library.com",     "arjun",   "pass123"),
            ("Kavya Verma",    "kavya.verma@library.com",    "kavya",   "pass123"),
            ("Ishaan Kapoor",  "ishaan.kapoor@library.com",  "ishaan",  "pass123"),
            ("Divya Joshi",    "divya.joshi@library.com",    "divya",   "pass123"),
        ]
        for name, email, username, password in indian_students:
            hashed = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO students (name, email, username, password) VALUES (?, ?, ?, ?)",
                (name, email, username, hashed)
            )
        print("10 Indian students added. All passwords: pass123")

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_database()
