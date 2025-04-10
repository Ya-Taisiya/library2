import unittest
from flask import Flask
from flask_testing import TestCase
from app import app, USERS_FILE, BOOKS_FILE, ISSUED_BOOKS_FILE

class TestLibraryApp(TestCase):
    
    def create_app(self):
        # Убедитесь, что для тестов используется специальная конфигурация
        app.config['TESTING'] = True
        app.config['CACHE_TYPE'] = 'NullCache'  # Отключаем кэширование в тестах
        return app

    def setUp(self):
        # Тестовые файлы с данными, которые будут использоваться в тестах
        with open(USERS_FILE, 'w') as f:
            f.write('admin,adminpass,admin\n')
            f.write('librarian,librarianpass,librarian\n')
            f.write('reader,readerpass,reader\n')
        
        with open(BOOKS_FILE, 'w') as f:
            f.write('Title,Author,CoverURL,Description\n')
            f.write('Test Book,Test Author,http://example.com,Test Description\n')
        
        with open(ISSUED_BOOKS_FILE, 'w') as f:
            f.write('reader,Test Book\n')

    def tearDown(self):
        # Очистка данных после выполнения тестов
        open(USERS_FILE, 'w').close()
        open(BOOKS_FILE, 'w').close()
        open(ISSUED_BOOKS_FILE, 'w').close()

    def test_login_valid_admin(self):
        response = self.client.post('/login', data=dict(username='admin', password='adminpass'), follow_redirects=True)
        self.assertIn(b'Login successful! Welcome, admin.', response.data)
        self.assertRedirects(response, '/admin_dashboard')

    def test_login_invalid_user(self):
        response = self.client.post('/login', data=dict(username='nonexistent', password='wrongpass'), follow_redirects=True)
        self.assertIn(b'Invalid credentials.', response.data)

    def test_login_invalid_password(self):
        response = self.client.post('/login', data=dict(username='admin', password='wrongpass'), follow_redirects=True)
        self.assertIn(b'Invalid credentials.', response.data)

    def test_register_new_user(self):
        response = self.client.post('/register', data=dict(username='newuser', password='newpassword', role='reader'), follow_redirects=True)
        self.assertIn(b'Registration successful!', response.data)

    def test_create_librarian(self):
        # Авторизация как администратор
        self.client.post('/login', data=dict(username='admin', password='adminpass'), follow_redirects=True)
        response = self.client.post('/create_librarian', data=dict(username='newlibrarian', password='newpassword'), follow_redirects=True)
        self.assertIn(b'Librarian account created successfully!', response.data)
    
    def test_admin_dashboard_access(self):
        # Пробуем зайти в админ-панель без входа
        response = self.client.get('/admin_dashboard', follow_redirects=True)
        self.assertIn(b'Access denied.', response.data)

        # Авторизуемся как администратор
        self.client.post('/login', data=dict(username='admin', password='adminpass'), follow_redirects=True)
        response = self.client.get('/admin_dashboard', follow_redirects=True)
        self.assertIn(b'Users', response.data)  # Проверка наличия информации о пользователях

    def test_librarian_dashboard_access(self):
        # Пробуем зайти в панель библиотекаря без входа
        response = self.client.get('/librarian_dashboard', follow_redirects=True)
        self.assertIn(b'Access denied.', response.data)

        # Авторизуемся как библиотекарь
        self.client.post('/login', data=dict(username='librarian', password='librarianpass'), follow_redirects=True)
        response = self.client.get('/librarian_dashboard', follow_redirects=True)
        self.assertIn(b'Books', response.data)  # Проверка наличия списка книг

    def test_add_book(self):
        self.client.post('/login', data=dict(username='librarian', password='librarianpass'), follow_redirects=True)
        response = self.client.post('/add_book', data=dict(title='New Book', author='Author', cover_url='http://example.com', description='Description'), follow_redirects=True)
        self.assertIn(b'Book added successfully!', response.data)

    def test_issue_book(self):
        self.client.post('/login', data=dict(username='librarian', password='librarianpass'), follow_redirects=True)
        response = self.client.post('/issue_book', data=dict(username='reader', book_title='Test Book'), follow_redirects=True)
        self.assertIn(b"Book 'Test Book' issued to reader.", response.data)

    def test_return_book(self):
        self.client.post('/login', data=dict(username='librarian', password='librarianpass'), follow_redirects=True)
        response = self.client.post('/return_book', data=dict(username='reader', book_title='Test Book'), follow_redirects=True)
        self.assertIn(b"Book 'Test Book' returned from reader.", response.data)

    def test_delete_user(self):
        self.client.post('/login', data=dict(username='admin', password='adminpass'), follow_redirects=True)
        response = self.client.post('/delete_user', data=dict(username='reader'), follow_redirects=True)
        self.assertIn(b"User 'reader' deleted successfully!", response.data)

    def test_find_reader(self):
        self.client.post('/login', data=dict(username='librarian', password='librarianpass'), follow_redirects=True)
        response = self.client.post('/find_reader', data=dict(username='reader'), follow_redirects=True)
        self.assertIn(b'Reader found: reader (reader)', response.data)

if __name__ == '__main__':
    unittest.main()
