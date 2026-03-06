"""Database manager for SQLite operations."""
import sqlite3
from datetime import datetime
from typing import Optional, List
from contextlib import contextmanager

from .models import User, Company, Product, Order, OrderItem, Category
from utils.password_hasher import PasswordHasher

class DatabaseManager:
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_PASSWORD = "admin123"
    DEFAULT_ADMIN_EMAIL = "admin@ecommerce.com"
    
    DEFAULT_CATEGORIES = [
        ("Electronics", "Electronic devices and gadgets"),
        ("Clothing", "Apparel and fashion items"),
        ("Home & Garden", "Home decor and gardening supplies"),
        ("Sports", "Sports equipment and accessories"),
        ("Books", "Books and publications"),
        ("Toys", "Toys and games"),
        ("Food & Beverages", "Food items and drinks"),
        ("Health & Beauty", "Health and beauty products"),
        ("Other", "Miscellaneous items")
    ]
    
    def __init__(self, db_path: str = "ecommerce.db"):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
    
    @contextmanager
    def get_cursor(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
    
    def get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def close_connection(self):
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def initialize_database(self):
        with self.get_cursor() as cursor:
            cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'company', 'user')),
                company_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                category_id INTEGER,
                image_path TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )''')
            
            self._create_default_admin(cursor)
            self._create_default_categories(cursor)
    
    def _create_default_admin(self, cursor):
        cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
        if cursor.fetchone() is None:
            password_hash = PasswordHasher.hash_password(self.DEFAULT_ADMIN_PASSWORD)
            cursor.execute('''INSERT INTO users (username, password_hash, email, role, company_id, is_active)
                VALUES (?, ?, ?, 'admin', NULL, 1)''', 
                (self.DEFAULT_ADMIN_USERNAME, password_hash, self.DEFAULT_ADMIN_EMAIL))
    
    def _create_default_categories(self, cursor):
        for name, description in self.DEFAULT_CATEGORIES:
            cursor.execute("SELECT id FROM categories WHERE name = ?", (name,))
            if cursor.fetchone() is None:
                cursor.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, description))
    
    # Category Operations
    def get_all_categories(self) -> List[Category]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM categories ORDER BY name')
            return [self._row_to_category(row) for row in cursor.fetchall()]
    
    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
            row = cursor.fetchone()
            return self._row_to_category(row) if row else None
    
    def _row_to_category(self, row) -> Category:
        return Category(id=row['id'], name=row['name'], description=row['description'] or '',
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now())
    
    # User Operations
    def create_user(self, username: str, password: str, email: str, role: str = 'user', 
                    company_id: Optional[int] = None) -> Optional[int]:
        password_hash = PasswordHasher.hash_password(password)
        try:
            with self.get_cursor() as cursor:
                cursor.execute('INSERT INTO users (username, password_hash, email, role, company_id) VALUES (?, ?, ?, ?, ?)',
                    (username, password_hash, email, role, company_id))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None
    
    def get_all_users(self) -> List[User]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
            return [self._row_to_user(row) for row in cursor.fetchall()]
    
    def get_users_by_role(self, role: str) -> List[User]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE role = ? ORDER BY created_at DESC', (role,))
            return [self._row_to_user(row) for row in cursor.fetchall()]
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        allowed_fields = {'email', 'is_active', 'company_id'}
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not update_fields:
            return False
        set_clause = ', '.join(f'{k} = ?' for k in update_fields.keys())
        values = list(update_fields.values()) + [user_id]
        with self.get_cursor() as cursor:
            cursor.execute(f'UPDATE users SET {set_clause} WHERE id = ?', values)
            return cursor.rowcount > 0
    
    def verify_user_credentials(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if user and user.is_active and PasswordHasher.verify_password(password, user.password_hash):
            return user
        return None
    
    def _row_to_user(self, row) -> User:
        return User(id=row['id'], username=row['username'], password_hash=row['password_hash'],
            email=row['email'], role=row['role'], company_id=row['company_id'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            is_active=bool(row['is_active']))
    
    # Company Operations
    def create_company(self, name: str, description: str = '') -> Optional[int]:
        try:
            with self.get_cursor() as cursor:
                cursor.execute('INSERT INTO companies (name, description) VALUES (?, ?)', (name, description))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def get_company_by_id(self, company_id: int) -> Optional[Company]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM companies WHERE id = ?', (company_id,))
            row = cursor.fetchone()
            return self._row_to_company(row) if row else None
    
    def get_all_companies(self) -> List[Company]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM companies ORDER BY created_at DESC')
            return [self._row_to_company(row) for row in cursor.fetchall()]
    
    def get_active_companies(self) -> List[Company]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM companies WHERE is_active = 1 ORDER BY name')
            return [self._row_to_company(row) for row in cursor.fetchall()]
    
    def update_company(self, company_id: int, **kwargs) -> bool:
        allowed_fields = {'name', 'description', 'is_active'}
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not update_fields:
            return False
        set_clause = ', '.join(f'{k} = ?' for k in update_fields.keys())
        values = list(update_fields.values()) + [company_id]
        with self.get_cursor() as cursor:
            cursor.execute(f'UPDATE companies SET {set_clause} WHERE id = ?', values)
            return cursor.rowcount > 0
    
    def delete_company(self, company_id: int) -> bool:
        return self.update_company(company_id, is_active=False)
    
    def _row_to_company(self, row) -> Company:
        return Company(id=row['id'], name=row['name'], description=row['description'] or '',
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            is_active=bool(row['is_active']))
    
    # Product Operations
    def create_product(self, company_id: int, name: str, description: str, price: float, 
                       stock: int, category_id: Optional[int] = None, image_path: str = '') -> Optional[int]:
        try:
            with self.get_cursor() as cursor:
                cursor.execute('''INSERT INTO products (company_id, name, description, price, stock, category_id, image_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''', (company_id, name, description, price, stock, category_id, image_path))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
            row = cursor.fetchone()
            return self._row_to_product(row) if row else None
    
    def get_products_by_company(self, company_id: int, include_inactive: bool = False) -> List[Product]:
        with self.get_cursor() as cursor:
            if include_inactive:
                cursor.execute('SELECT * FROM products WHERE company_id = ? ORDER BY created_at DESC', (company_id,))
            else:
                cursor.execute('SELECT * FROM products WHERE company_id = ? AND is_active = 1 ORDER BY created_at DESC', (company_id,))
            return [self._row_to_product(row) for row in cursor.fetchall()]
    
    def get_all_products(self, include_inactive: bool = False) -> List[Product]:
        with self.get_cursor() as cursor:
            if include_inactive:
                cursor.execute('SELECT * FROM products ORDER BY created_at DESC')
            else:
                cursor.execute('SELECT * FROM products WHERE is_active = 1 ORDER BY name')
            return [self._row_to_product(row) for row in cursor.fetchall()]
    
    def get_all_active_products(self) -> List[Product]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM products WHERE is_active = 1 AND stock > 0 ORDER BY name')
            return [self._row_to_product(row) for row in cursor.fetchall()]
    
    def update_product(self, product_id: int, **kwargs) -> bool:
        allowed_fields = {'name', 'description', 'price', 'stock', 'category_id', 'image_path', 'is_active'}
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not update_fields:
            return False
        set_clause = ', '.join(f'{k} = ?' for k in update_fields.keys())
        values = list(update_fields.values()) + [product_id]
        with self.get_cursor() as cursor:
            cursor.execute(f'UPDATE products SET {set_clause} WHERE id = ?', values)
            return cursor.rowcount > 0
    
    def delete_product(self, product_id: int) -> bool:
        with self.get_cursor() as cursor:
            cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
            return cursor.rowcount > 0
    
    def _row_to_product(self, row) -> Product:
        return Product(id=row['id'], company_id=row['company_id'], name=row['name'],
            description=row['description'] or '', price=row['price'], stock=row['stock'],
            category_id=row['category_id'], image_path=row['image_path'] or '',
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            is_active=bool(row['is_active']))
    
    # Order Operations
    def create_order(self, user_id: int, items: List[tuple]) -> Optional[int]:
        """Create order and deduct stock from products."""
        try:
            total_amount = sum(qty * price for _, qty, price in items)
            with self.get_cursor() as cursor:
                cursor.execute('INSERT INTO orders (user_id, total_amount, status) VALUES (?, ?, \'pending\')',
                    (user_id, total_amount))
                order_id = cursor.lastrowid
                
                for product_id, quantity, price in items:
                    cursor.execute('INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                        (order_id, product_id, quantity, price))
                    # Deduct stock
                    cursor.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (quantity, product_id))
                
                return order_id
        except sqlite3.Error:
            return None
    
    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
            row = cursor.fetchone()
            return self._row_to_order(row) if row else None
    
    def get_orders_by_user(self, user_id: int) -> List[Order]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
            return [self._row_to_order(row) for row in cursor.fetchall()]
    
    def get_orders_by_company(self, company_id: int) -> List[dict]:
        with self.get_cursor() as cursor:
            cursor.execute('''SELECT DISTINCT o.*, u.username as customer_name
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN products p ON oi.product_id = p.id
                JOIN users u ON o.user_id = u.id
                WHERE p.company_id = ?
                ORDER BY o.created_at DESC''', (company_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_order_status(self, order_id: int, status: str) -> bool:
        valid_statuses = ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')
        if status not in valid_statuses:
            return False
        with self.get_cursor() as cursor:
            cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
            return cursor.rowcount > 0
    
    def _row_to_order(self, row) -> Order:
        return Order(id=row['id'], user_id=row['user_id'], total_amount=row['total_amount'],
            status=row['status'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now())
    
    # Statistics
    def get_admin_statistics(self) -> dict:
        with self.get_cursor() as cursor:
            stats = {}
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
            stats['total_users'] = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM companies WHERE is_active = 1')
            stats['total_companies'] = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM products WHERE is_active = 1')
            stats['total_products'] = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM orders')
            stats['total_orders'] = cursor.fetchone()[0]
            cursor.execute('SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status != "cancelled"')
            stats['total_revenue'] = cursor.fetchone()[0]
            return stats
    
    def get_company_statistics(self, company_id: int) -> dict:
        with self.get_cursor() as cursor:
            stats = {}
            cursor.execute('SELECT COUNT(*) FROM products WHERE company_id = ? AND is_active = 1', (company_id,))
            stats['total_products'] = cursor.fetchone()[0]
            cursor.execute('''SELECT COALESCE(SUM(oi.quantity * oi.price), 0)
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                JOIN orders o ON oi.order_id = o.id
                WHERE p.company_id = ? AND o.status != 'cancelled' ''', (company_id,))
            stats['total_revenue'] = cursor.fetchone()[0]
            cursor.execute('''SELECT COUNT(DISTINCT o.id) FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN products p ON oi.product_id = p.id
                WHERE p.company_id = ?''', (company_id,))
            stats['total_orders'] = cursor.fetchone()[0]
            return stats
