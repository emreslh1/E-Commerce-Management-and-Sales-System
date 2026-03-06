# E-Commerce Management and Sales System

A desktop e-commerce application built with Python and PyQt6, using SQLite for data storage. The system features three authorization levels: Admin, Company, and User.

## Features

### Three Authorization Levels

1. **Admin**
   - Pre-defined account (username: `admin`, password: `admin123`)
   - Manage companies (create, edit, activate/deactivate)
   - Manage users (view, activate/deactivate)
   - **General Inventory**: View and manage all products from all companies
   - View system statistics

2. **Company**
   - Accounts created by Admin only (companies cannot self-register)
   - **My Products**: Full CRUD operations for products
     - Add products with image, name, price, stock, and category
     - Edit existing products
     - Delete products permanently
   - View and manage orders for their products
   - View company statistics

3. **User**
   - Self-registration through the registration page
   - Browse products with images and categories
   - Shopping cart functionality
   - Place and track orders

### Product Management Features

- **Product Images**: Upload and display product images
- **Categories**: Organize products into predefined categories
  - Electronics, Clothing, Home & Garden, Sports, Books, Toys, Food & Beverages, Health & Beauty, Other
- **Stock Management**: Track and update inventory levels
- **Product Status**: Activate/deactivate products

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install PyQt6 bcrypt
```

## Running the Application

```bash
python main.py
```

## Default Credentials

The system comes with a pre-configured admin account:

- **Username:** `admin`
- **Password:** `admin123`

**Important:** Change the default admin password after first login in a production environment.

## Project Structure

```
E-Commerce-Management-and-Sales-System/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── product_images/            # Directory for product images (created at runtime)
├── ecommerce.db               # SQLite database (created at runtime)
├── database/
│   ├── __init__.py
│   ├── db_manager.py          # Database connection and operations
│   └── models.py              # Data classes for database entities
├── models/                    # (Reserved for future use)
├── views/
│   ├── __init__.py
│   ├── login_window.py        # Login screen
│   ├── registration_window.py # User registration
│   ├── admin/
│   │   ├── __init__.py
│   │   └── admin_panel.py     # Admin dashboard with General Inventory
│   ├── company/
│   │   ├── __init__.py
│   │   └── company_panel.py   # Company dashboard with My Products
│   └── user/
│       ├── __init__.py
│       └── user_panel.py      # User shopping interface
├── controllers/
│   ├── __init__.py
│   └── auth_controller.py     # Authentication management
├── utils/
│   ├── __init__.py
│   ├── password_hasher.py     # Password hashing utilities
│   └── validators.py          # Input validation
└── resources/
    └── styles.qss             # Qt stylesheet
```

## Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `password_hash` - Bcrypt hashed password
- `email` - Unique email address
- `role` - User role ('admin', 'company', 'user')
- `company_id` - Foreign key to companies (for company users)
- `created_at` - Account creation timestamp
- `is_active` - Account status flag

### Companies Table
- `id` - Primary key
- `name` - Company name
- `description` - Company description
- `created_at` - Creation timestamp
- `is_active` - Company status flag

### Products Table
- `id` - Primary key
- `company_id` - Foreign key to companies
- `name` - Product name
- `description` - Product description
- `price` - Product price
- `stock` - Available stock
- `category_id` - Foreign key to categories
- `image_path` - Path to product image
- `created_at` - Creation timestamp
- `is_active` - Product status flag

### Categories Table
- `id` - Primary key
- `name` - Category name
- `description` - Category description
- `created_at` - Creation timestamp

### Orders Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `total_amount` - Order total
- `status` - Order status ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')
- `created_at` - Order timestamp

### Order Items Table
- `id` - Primary key
- `order_id` - Foreign key to orders
- `product_id` - Foreign key to products
- `quantity` - Item quantity
- `price` - Price at time of purchase

## Workflow

### Admin Workflow
1. Login with admin credentials
2. Create company accounts through the "Add Company" button
3. Each company creation automatically creates a company user account
4. View and manage all products in **General Inventory**
5. View and manage all users in the system
6. Monitor system statistics

### Company Workflow
1. Login with company credentials (created by admin)
2. Add products with image, name, description, price, stock, and category
3. Edit or delete existing products from **My Products** tab
4. Manage product inventory
5. Process incoming orders (confirm, ship, deliver)
6. View company statistics

### User Workflow
1. Register a new account through the registration page
2. Login with user credentials
3. Browse available products with images and categories
4. Filter products by company or category
5. Add products to shopping cart
6. Checkout and place orders
7. Track order status in "My Orders"

## Security Features

- Passwords are hashed using bcrypt
- Input validation on all forms
- Role-based access control
- SQL injection prevention through parameterized queries

## Technologies Used

- **Python 3** - Programming language
- **PyQt6** - GUI framework
- **SQLite** - Embedded database
- **bcrypt** - Password hashing

## License

This project is open source and available for educational and commercial use.