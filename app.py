from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import get_connection
import hashlib
from functools import wraps
from datetime import datetime, timedelta

app = Flask(__name__)
# In production, use a secure secret key from env variables!
app.secret_key = 'super_secret_library_key'

# Hardcoded admin password from old system
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()

def check_admin_password(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH

# Decorators for auth
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Admin access required", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'user':
            flash("User access required", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        if login_type == 'admin':
            password = request.form.get('admin_password')
            if check_admin_password(password):
                session['role'] = 'admin'
                flash("Logged in successfully as Admin", "success")
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid admin password", "error")
        elif login_type == 'user':
            username = request.form.get('username')
            password = request.form.get('password')

            try:
                conn = get_connection()
                cursor = conn.cursor()
                hashed = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute(
                    "SELECT id, name FROM students WHERE username=? AND password=?",
                    (username, hashed)
                )
                user = cursor.fetchone()
                if user:
                    session['role'] = 'user'
                    session['user_id'] = user['id']
                    session['user_name'] = user['name']
                    flash(f"Welcome, {user['name']}!", "success")
                    return redirect(url_for('user_dashboard'))
                else:
                    flash("Invalid username or password", "error")
            except Exception as e:
                flash(f"Database error: {str(e)}", "error")
            finally:
                if 'conn' in locals() and conn:
                    conn.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        if not all([name, email, username, password]):
            flash("All fields are required.", "error")
            return render_template('register.html')

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Check if username already exists
            cursor.execute("SELECT id FROM students WHERE username=?", (username,))
            if cursor.fetchone():
                flash("Username already taken. Please choose another.", "error")
                return render_template('register.html')

            hashed = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO students (name, email, username, password) VALUES (?, ?, ?, ?)",
                (name, email, username, hashed)
            )
            conn.commit()
            flash("Account created successfully! Please sign in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error creating account: {str(e)}", "error")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    return render_template('register.html')

# --- ADMIN ROUTES ---
@app.route('/admin')
@admin_required
def admin_dashboard():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()

        cursor.execute("SELECT id, name, email, username FROM students")
        students = cursor.fetchall()

        cursor.execute("""
            SELECT l.id, s.name as student_name, b.title as book_title, l.issue_date, l.returned 
            FROM loans l 
            JOIN students s ON l.student_id = s.id 
            JOIN books b ON l.book_id = b.id 
            ORDER BY l.issue_date DESC
        """)
        loans = cursor.fetchall()
        
        return render_template('admin_dashboard.html', books=books, students=students, loans=loans)
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "error")
        return redirect(url_for('index'))
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/admin/add_book', methods=['POST'])
@admin_required
def admin_add_book():
    title = request.form.get('title')
    author = request.form.get('author')
    category = request.form.get('category', 'Uncategorized')
    try:
        quantity = int(request.form.get('quantity', 1))
    except ValueError:
        quantity = 1

    if not title or not author:
        flash("Title and Author are required", "error")
        return redirect(url_for('admin_dashboard'))

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO books (title, author, category, quantity, remaining) VALUES (?, ?, ?, ?, ?)", (title, author, category, quantity, quantity))
        conn.commit()
        flash("Book added successfully!", "success")
    except Exception as e:
        flash(f"Error adding book: {str(e)}", "error")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_book/<int:book_id>', methods=['POST'])
@admin_required
def admin_delete_book(book_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM loans WHERE book_id=?", (book_id,))
        cursor.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
        flash("Book deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting book: {str(e)}", "error")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_student', methods=['POST'])
@admin_required
def admin_add_student():
    name = request.form.get('name')
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')

    if not all([name, email, username, password]):
        flash("All fields are required", "error")
        return redirect(url_for('admin_dashboard'))

    try:
        conn = get_connection()
        cursor = conn.cursor()
        hashed = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO students (name, email, username, password) VALUES (?, ?, ?, ?)",
            (name, email, username, hashed)
        )
        conn.commit()
        flash("Student added successfully!", "success")
    except Exception as e:
        flash(f"Error adding student: {str(e)}", "error")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_student/<int:student_id>', methods=['POST'])
@admin_required
def admin_delete_student(student_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Free up any books this student is holding before deleting
        cursor.execute("SELECT book_id FROM loans WHERE student_id=? AND returned=0", (student_id,))
        active_loans = cursor.fetchall()
        for loan in active_loans:
            cursor.execute("UPDATE books SET remaining=remaining+1 WHERE id=?", (loan['book_id'],))

        cursor.execute("DELETE FROM loans WHERE student_id=?", (student_id,))
        cursor.execute("DELETE FROM students WHERE id=?", (student_id,))
        conn.commit()
        flash("Student deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting student: {str(e)}", "error")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    return redirect(url_for('admin_dashboard'))

# --- USER ROUTES ---
@app.route('/user')
@user_required
def user_dashboard():
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    try:
        conn = get_connection()
        cursor = conn.cursor()


        query = "SELECT * FROM books WHERE 1=1"
        params = []
        if search_query:
            query += " AND (title LIKE ? OR author LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        if category_filter:
            query += " AND category = ?"
            params.append(category_filter)
        
        cursor.execute(query, params)
        all_books = cursor.fetchall()
        
        # We need ALL categories for a dropdown filter
        cursor.execute("SELECT DISTINCT category FROM books WHERE category IS NOT NULL AND category != ''")
        categories = [row['category'] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT b.id, b.title, b.author, l.issue_date, l.due_date, l.returned, l.id as loan_id
            FROM loans l
            JOIN books b ON l.book_id = b.id
            WHERE l.student_id = ?
            ORDER BY l.issue_date DESC
        """, (session['user_id'],))
        my_loans_raw = cursor.fetchall()

        now = datetime.now()
        my_loans = []
        for loan in my_loans_raw:
            loan_dict = dict(loan)
            loan_dict['fine_due'] = 0.0
            if not loan_dict['returned'] and loan_dict['due_date']:
                try:
                    # SQLite CURRENT_TIMESTAMP is like '2026-04-09 05:24:41'
                    due = datetime.strptime(loan_dict['due_date'], "%Y-%m-%d %H:%M:%S")
                    if now > due:
                        loan_dict['fine_due'] = float((now - due).days) * 1.0
                except:
                    pass
            my_loans.append(loan_dict)
            
        cursor.execute("""
            SELECT h.id, b.title, b.author, h.request_date, h.status
            FROM holds h
            JOIN books b ON h.book_id = b.id
            WHERE h.student_id = ?
            ORDER BY h.request_date DESC
        """, (session['user_id'],))
        my_holds = cursor.fetchall()

        return render_template('user_dashboard.html', books=all_books, my_loans=my_loans, my_holds=my_holds, search_query=search_query, category_filter=category_filter, categories=categories)
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "error")
        return redirect(url_for('index'))
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/user/apply_book', methods=['POST'])
@user_required
def user_apply_book():
    book_id = request.form.get('book_id')
    if not book_id:
        flash("Select a book to apply for", "error")
        return redirect(url_for('user_dashboard'))

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT remaining FROM books WHERE id=?", (book_id,))
        result = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) as count FROM loans WHERE student_id=? AND returned=0", (session['user_id'],))
        active_loans = cursor.fetchone()['count']

        if active_loans >= 3:
            flash("You have reached the maximum limit of 3 active loans. Please return a book first.", "error")
        elif not result:
            flash("Book not found", "error")
        elif result['remaining'] <= 0:
            flash("Book is already taken, you can place a hold instead.", "error")
        else:
            due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO loans (student_id, book_id, due_date) VALUES (?, ?, ?)",
                (session['user_id'], book_id, due_date)
            )
            cursor.execute("UPDATE books SET remaining=remaining-1 WHERE id=?", (book_id,))
            conn.commit()
            flash("Book applied successfully! It is due in 14 days.", "success")
    except Exception as e:
        flash(f"Error applying for book: {str(e)}", "error")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    return redirect(url_for('user_dashboard'))

@app.route('/user/place_hold', methods=['POST'])
@user_required
def user_place_hold():
    book_id = request.form.get('book_id')
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if already on hold
        cursor.execute("SELECT id FROM holds WHERE student_id=? AND book_id=? AND status='active'", (session['user_id'], book_id))
        if cursor.fetchone():
            flash("You are already on the waitlist for this book.", "error")
        else:
            # Check if user already has it loaned
            cursor.execute("SELECT id FROM loans WHERE student_id=? AND book_id=? AND returned=0", (session['user_id'], book_id))
            if cursor.fetchone():
                flash("You currently have this book borrowed.", "error")
            else:
                cursor.execute("INSERT INTO holds (student_id, book_id) VALUES (?, ?)", (session['user_id'], book_id))
                conn.commit()
                flash("Successfully joined the waitlist for this book!", "success")
    except Exception as e:
        flash(f"Error placing hold: {str(e)}", "error")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    return redirect(url_for('user_dashboard'))

@app.route('/user/return_book/<int:book_id>', methods=['POST'])
@user_required
def user_return_book(book_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE loans SET returned=1 WHERE student_id=? AND book_id=? AND returned=0",
            (session['user_id'], book_id)
        )
        if cursor.rowcount == 0:
            flash("No active loan found for this book", "error")
        else:
            # Check holds
            cursor.execute("SELECT id, student_id FROM holds WHERE book_id=? AND status='active' ORDER BY request_date ASC LIMIT 1", (book_id,))
            hold = cursor.fetchone()
            
            if hold:
                # Fulfill hold and loan it
                cursor.execute("UPDATE holds SET status='fulfilled' WHERE id=?", (hold['id'],))
                due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO loans (student_id, book_id, due_date) VALUES (?, ?, ?)", (hold['student_id'], book_id, due_date))
                conn.commit()
                flash("Book returned successfully! It was immediately issued to the next person on the waitlist.", "success")
            else:
                cursor.execute("UPDATE books SET remaining=remaining+1 WHERE id=?", (book_id,))
                conn.commit()
                flash("Book returned successfully!", "success")
    except Exception as e:
        flash(f"Error returning book: {str(e)}", "error")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    return redirect(url_for('user_dashboard'))

if __name__ == '__main__':
    from init_db import init_database
    init_database()
    app.run(debug=True, port=5000)
