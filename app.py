from flask import Flask, request, redirect, url_for, render_template, session, flash
from flask_caching import Cache
import csv

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Настройка кэширования
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# Пути к файлам с данными
USERS_FILE = 'users.csv'
BOOKS_FILE = 'books.csv'
ORDERS_FILE = 'orders.csv'
ISSUED_BOOKS_FILE = 'issued_books.csv'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = validate_user(username, password)
        if role:
            session['username'] = username
            session['role'] = role
            flash("Login successful! Welcome, {}.".format(role))
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif role == 'librarian':
                return redirect(url_for('librarian_dashboard'))
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if register_user(username, password, role):
            flash("Registration successful!")
            return redirect(url_for('login'))
        else:
            flash("Username already exists.")
    return render_template('register.html')

@app.route('/admin_dashboard')
@cache.cached(timeout=60, key_prefix='admin_dashboard')  # Кэширование на 60 секунд
def admin_dashboard():
    if 'username' not in session or session['role'] != 'admin':
        flash("Access denied.")
        return redirect(url_for('home'))
    users = get_users()
    return render_template('admin_dashboard.html', users=users)

@app.route('/create_librarian', methods=['GET', 'POST'])
def create_librarian():
    if 'username' not in session or session['role'] != 'admin':
        flash("Access denied.")
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if register_user(username, password, 'librarian'):
            flash("Librarian account created successfully!")
            cache.delete('admin_dashboard')  # Очистка кэша после изменения данных
        else:
            flash("Failed to create librarian account.")
        return redirect(url_for('admin_dashboard'))
    return render_template('create_librarian.html')

@app.route('/delete_user', methods=['POST'])
def delete_user():
    if 'username' not in session or session['role'] != 'admin':
        flash("Access denied.")
        return redirect(url_for('home'))
    username = request.form['username']
    if delete_user_account(username):
        flash(f"User '{username}' deleted successfully!")
        cache.delete('admin_dashboard')  # Очистка кэша после изменения данных
    else:
        flash("Failed to delete user.")
    return redirect(url_for('admin_dashboard'))

@app.route('/assign_role', methods=['POST'])
def assign_role():
    if 'username' not in session or session['role'] != 'admin':
        flash("Access denied.")
        return redirect(url_for('home'))
    username = request.form['username']
    role = request.form['role']
    if assign_role_to_user(username, role):
        flash(f"Role '{role}' assigned to '{username}' successfully!")
        cache.delete('admin_dashboard')  # Очистка кэша после изменения данных
    else:
        flash("Failed to assign role.")
    return redirect(url_for('admin_dashboard'))

@app.route('/librarian_dashboard')
@cache.cached(timeout=60, key_prefix='librarian_dashboard')  # Кэширование на 60 секунд
def librarian_dashboard():
    if 'username' not in session or session['role'] != 'librarian':
        flash("Access denied.")
        return redirect(url_for('home'))
    books = get_books()
    return render_template('librarian_dashboard.html', books=books)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'username' not in session or session['role'] != 'librarian':
        flash("Access denied.")
        return redirect(url_for('home'))
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        cover_url = request.form['cover_url']
        description = request.form['description']
        if add_book_to_catalog(title, author, cover_url, description):
            flash("Book added successfully!")
            cache.delete('librarian_dashboard')  # Очистка кэша после изменения данных
        else:
            flash("Failed to add book.")
        return redirect(url_for('librarian_dashboard'))
    return render_template('add_book.html')

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if 'username' not in session or session['role'] != 'librarian':
        flash("Access denied.")
        return redirect(url_for('home'))
    books = get_books()
    if book_id < 0 or book_id >= len(books):
        flash("Book not found.")
        return redirect(url_for('librarian_dashboard'))
    book = books[book_id]
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        cover_url = request.form['cover_url']
        description = request.form['description']
        if edit_book_in_catalog(book_id, title, author, cover_url, description):
            flash("Book edited successfully!")
            cache.delete('librarian_dashboard')  # Очистка кэша после изменения данных
        else:
            flash("Failed to edit book.")
        return redirect(url_for('librarian_dashboard'))
    return render_template('edit_book.html', book=book)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'username' not in session or session['role'] != 'librarian':
        flash("Access denied.")
        return redirect(url_for('home'))
    if delete_book_from_catalog(book_id):
        flash("Book deleted successfully!")
        cache.delete('librarian_dashboard')  # Очистка кэша после изменения данных
    else:
        flash("Failed to delete book.")
    return redirect(url_for('librarian_dashboard'))

@app.route('/find_reader', methods=['GET', 'POST'])
def find_reader():
    if 'username' not in session or session['role'] != 'librarian':
        flash("Access denied.")
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        user = find_user_by_username(username)
        if user:
            flash(f"Reader found: {user['Username']} ({user['Role']})")
        else:
            flash("Reader not found.")
        return redirect(url_for('librarian_dashboard'))
    return render_template('find_reader.html')

@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    if 'username' not in session or session['role'] != 'librarian':
        flash("Access denied.")
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        book_title = request.form['book_title']
        if issue_book_to_reader(username, book_title):
            flash(f"Book '{book_title}' issued to {username}.")
        else:
            flash("Failed to issue book.")
        return redirect(url_for('librarian_dashboard'))
    return render_template('issue_book.html')

@app.route('/return_book', methods=['GET', 'POST'])
def return_book():
    if 'username' not in session or session['role'] != 'librarian':
        flash("Access denied.")
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        book_title = request.form['book_title']
        if return_book_from_reader(username, book_title):
            flash(f"Book '{book_title}' returned from {username}.")
        else:
            flash("Failed to return book.")
        return redirect(url_for('librarian_dashboard'))
    return render_template('return_book.html')

@app.route('/catalog')
def catalog():
    books = get_books()
    return render_template('catalog.html', books=books)

def validate_user(username, password):
    with open(USERS_FILE, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == username and row[1] == password:
                return row[2]
    return None

def register_user(username, password, role):
    with open(USERS_FILE, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == username:
                return False

    with open(USERS_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([username, password, role])
    return True

def get_users():
    users = []
    with open(USERS_FILE, mode='r') as file:
        reader = csv.DictReader(file, fieldnames=['Username', 'Password', 'Role'])
        for row in reader:
            users.append(row)
    return users

def get_books():
    books = []
    with open(BOOKS_FILE, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            books.append(row)
    return books

def delete_user_account(username):
    users = []
    with open(USERS_FILE, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] != username:
                users.append(row)

    with open(USERS_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(users)
    return True

def assign_role_to_user(username, role):
    users = []
    with open(USERS_FILE, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == username:
                row[2] = role
            users.append(row)

    with open(USERS_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(users)
    return True

def add_book_to_catalog(title, author, cover_url, description):
    with open(BOOKS_FILE, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['Title', 'Author', 'CoverURL', 'Description'])
        writer.writerow({'Title': title, 'Author': author, 'CoverURL': cover_url, 'Description': description})
    return True

def edit_book_in_catalog(book_id, title, author, cover_url, description):
    books = get_books()
    if book_id < 0 or book_id >= len(books):
        return False
    books[book_id] = {'Title': title, 'Author': author, 'CoverURL': cover_url, 'Description': description}
    with open(BOOKS_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['Title', 'Author', 'CoverURL', 'Description'])
        writer.writeheader()
        writer.writerows(books)
    return True

def delete_book_from_catalog(book_id):
    books = get_books()
    if book_id < 0 or book_id >= len(books):
        return False
    del books[book_id]
    with open(BOOKS_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['Title', 'Author', 'CoverURL', 'Description'])
        writer.writeheader()
        writer.writerows(books)
    return True

def find_user_by_username(username):
    with open(USERS_FILE, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Username'] == username:
                return row
    return None

def issue_book_to_reader(username, book_title):
    with open(ISSUED_BOOKS_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([username, book_title])
    return True

def return_book_from_reader(username, book_title):
    issued_books = []
    with open(ISSUED_BOOKS_FILE, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == username and row[1] == book_title:
                continue
            issued_books.append(row)

    with open(ISSUED_BOOKS_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(issued_books)
    return True

if __name__ == '__main__':
    app.run(debug=True)