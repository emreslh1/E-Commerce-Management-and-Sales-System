"""Admin panel."""
import os
import shutil
import uuid
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, QDialog, QFormLayout,
    QLineEdit, QTextEdit, QHeaderView, QComboBox, QAbstractItemView, QFrame, QGroupBox,
    QDoubleSpinBox, QSpinBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPixmap
from database.models import User, Company, Product
from utils.validators import Validators

PRODUCT_IMAGES_DIR = "product_images"

def ensure_images_dir():
    if not os.path.exists(PRODUCT_IMAGES_DIR):
        os.makedirs(PRODUCT_IMAGES_DIR)

class AddCompanyDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Add New Company")
        self.setMinimumWidth(450)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        company_group = QGroupBox("Company Information")
        company_layout = QFormLayout(company_group)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Company name")
        company_layout.addRow("Company Name *:", self.name_input)
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Company description")
        self.description_input.setMaximumHeight(80)
        company_layout.addRow("Description:", self.description_input)
        layout.addWidget(company_group)
        
        account_group = QGroupBox("Company Account Credentials")
        account_layout = QFormLayout(account_group)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Login username")
        account_layout.addRow("Username *:", self.username_input)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Company email")
        account_layout.addRow("Email *:", self.email_input)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password (min 6 characters)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        account_layout.addRow("Password *:", self.password_input)
        layout.addWidget(account_group)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        save_btn = QPushButton("Create Company")
        save_btn.setStyleSheet("background-color: #28a745; color: white;")
        save_btn.clicked.connect(self._create_company)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
    
    def _validate(self):
        name = self.name_input.text().strip()
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not name:
            return False, "Company name is required"
        valid, msg = Validators.validate_username(username)
        if not valid:
            return False, msg
        if self.db_manager.get_user_by_username(username):
            return False, "Username already exists"
        valid, msg = Validators.validate_email(email)
        if not valid:
            return False, msg
        if self.db_manager.get_user_by_email(email):
            return False, "Email already registered"
        valid, msg = Validators.validate_password(password)
        if not valid:
            return False, msg
        return True, ""
    
    def _create_company(self):
        valid, error = self._validate()
        if not valid:
            QMessageBox.warning(self, "Validation Error", error)
            return
        
        company_id = self.db_manager.create_company(
            self.name_input.text().strip(),
            self.description_input.toPlainText().strip()
        )
        if not company_id:
            QMessageBox.critical(self, "Error", "Failed to create company")
            return
        
        user_id = self.db_manager.create_user(
            username=self.username_input.text().strip(),
            password=self.password_input.text(),
            email=self.email_input.text().strip(),
            role='company',
            company_id=company_id
        )
        if not user_id:
            self.db_manager.delete_company(company_id)
            QMessageBox.critical(self, "Error", "Failed to create company account")
            return
        
        QMessageBox.information(self, "Success", f"Company '{self.name_input.text().strip()}' created!")
        self.accept()

class EditCompanyDialog(QDialog):
    def __init__(self, db_manager, company: Company, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.company = company
        self.setWindowTitle(f"Edit Company: {company.name}")
        self.setMinimumWidth(400)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.name_input.setText(self.company.name)
        layout.addRow("Company Name:", self.name_input)
        self.description_input = QTextEdit()
        self.description_input.setPlainText(self.company.description)
        self.description_input.setMaximumHeight(80)
        layout.addRow("Description:", self.description_input)
        self.active_input = QComboBox()
        self.active_input.addItems(["Active", "Inactive"])
        self.active_input.setCurrentIndex(0 if self.company.is_active else 1)
        layout.addRow("Status:", self.active_input)
        
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self._save_changes)
        button_layout.addWidget(save_btn)
        layout.addRow(button_layout)
    
    def _save_changes(self):
        success = self.db_manager.update_company(
            self.company.id,
            name=self.name_input.text().strip(),
            description=self.description_input.toPlainText().strip(),
            is_active=self.active_input.currentIndex() == 0
        )
        if success:
            QMessageBox.information(self, "Success", "Company updated successfully")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to update company")

class EditProductAdminDialog(QDialog):
    def __init__(self, db_manager, product: Product, categories: list, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.product = product
        self.categories = categories
        self.selected_image_path = product.image_path
        self.image_changed = False
        self.setWindowTitle(f"Edit Product: {product.name}")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._load_product_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        product_group = QGroupBox("Product Information")
        product_layout = QFormLayout(product_group)
        self.name_input = QLineEdit()
        product_layout.addRow("Product Name:", self.name_input)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        product_layout.addRow("Description:", self.description_input)
        self.category_combo = QComboBox()
        self.category_combo.addItem("-- No Category --", None)
        for category in self.categories:
            self.category_combo.addItem(category.name, category.id)
        product_layout.addRow("Category:", self.category_combo)
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.01, 999999.99)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$ ")
        product_layout.addRow("Price:", self.price_input)
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 999999)
        product_layout.addRow("Stock:", self.stock_input)
        self.active_input = QComboBox()
        self.active_input.addItems(["Active", "Inactive"])
        product_layout.addRow("Status:", self.active_input)
        layout.addWidget(product_group)
        
        image_group = QGroupBox("Product Image")
        image_layout = QVBoxLayout(image_group)
        self.image_preview = QLabel("No image")
        self.image_preview.setFixedSize(150, 150)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet("QLabel { border: 2px dashed #ccc; border-radius: 5px; background-color: #f9f9f9; }")
        self.image_preview.setScaledContents(True)
        image_btn_layout = QHBoxLayout()
        self.select_image_btn = QPushButton("Change Image")
        self.select_image_btn.clicked.connect(self._select_image)
        image_btn_layout.addWidget(self.select_image_btn)
        self.clear_image_btn = QPushButton("Remove Image")
        self.clear_image_btn.clicked.connect(self._clear_image)
        image_btn_layout.addWidget(self.clear_image_btn)
        image_layout.addWidget(self.image_preview, alignment=Qt.AlignmentFlag.AlignCenter)
        image_layout.addLayout(image_btn_layout)
        layout.addWidget(image_group)
        
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self._save_changes)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
    
    def _load_product_data(self):
        self.name_input.setText(self.product.name)
        self.description_input.setPlainText(self.product.description)
        self.price_input.setValue(self.product.price)
        self.stock_input.setValue(self.product.stock)
        self.active_input.setCurrentIndex(0 if self.product.is_active else 1)
        if self.product.category_id:
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == self.product.category_id:
                    self.category_combo.setCurrentIndex(i)
                    break
        if self.product.image_path and os.path.exists(self.product.image_path):
            pixmap = QPixmap(self.product.image_path)
            if not pixmap.isNull():
                self.image_preview.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.image_preview.setText("No image")
    
    def _select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Product Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            self.selected_image_path = file_path
            self.image_changed = True
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.image_preview.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    
    def _clear_image(self):
        self.selected_image_path = ""
        self.image_changed = True
        self.image_preview.clear()
        self.image_preview.setText("No image")
    
    def _save_changes(self):
        image_path = self.product.image_path
        if self.image_changed:
            if self.selected_image_path:
                ensure_images_dir()
                ext = os.path.splitext(self.selected_image_path)[1]
                filename = f"{uuid.uuid4()}{ext}"
                image_path = os.path.join(PRODUCT_IMAGES_DIR, filename)
                shutil.copy(self.selected_image_path, image_path)
            else:
                image_path = ""
        
        success = self.db_manager.update_product(
            self.product.id,
            name=self.name_input.text().strip(),
            description=self.description_input.toPlainText().strip(),
            price=self.price_input.value(),
            stock=self.stock_input.value(),
            category_id=self.category_combo.currentData(),
            image_path=image_path,
            is_active=self.active_input.currentIndex() == 0
        )
        if success:
            QMessageBox.information(self, "Success", "Product updated successfully")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to update product")

class AdminPanel(QMainWindow):
    logout_requested = pyqtSignal()
    
    def __init__(self, db_manager, auth_controller, user: User):
        super().__init__()
        self.db_manager = db_manager
        self.auth_controller = auth_controller
        self.current_user = user
        self.setWindowTitle(f"Admin Panel - {user.username}")
        self.setMinimumSize(1100, 750)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        welcome_label = QLabel(f"Welcome, {self.current_user.username}")
        welcome_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(welcome_label)
        header_layout.addStretch()
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self._logout)
        logout_btn.setStyleSheet("background-color: #dc3545; color: white;")
        header_layout.addWidget(logout_btn)
        main_layout.addLayout(header_layout)
        
        self._create_stats_section(main_layout)
        
        self.tabs = QTabWidget()
        
        inventory_tab = QWidget()
        inventory_layout = QVBoxLayout(inventory_tab)
        self._setup_inventory_tab(inventory_layout)
        self.tabs.addTab(inventory_tab, "General Inventory")
        
        companies_tab = QWidget()
        companies_layout = QVBoxLayout(companies_tab)
        self._setup_companies_tab(companies_layout)
        self.tabs.addTab(companies_tab, "Companies")
        
        users_tab = QWidget()
        users_layout = QVBoxLayout(users_tab)
        self._setup_users_tab(users_layout)
        self.tabs.addTab(users_tab, "Users")
        
        main_layout.addWidget(self.tabs)
    
    def _create_stats_section(self, layout):
        stats_frame = QFrame()
        stats_frame.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 8px; padding: 10px; }")
        stats_layout = QHBoxLayout(stats_frame)
        stats = self.db_manager.get_admin_statistics()
        stats_items = [
            ("Total Users", stats['total_users'], "#0078d4"),
            ("Companies", stats['total_companies'], "#28a745"),
            ("Products", stats['total_products'], "#ffc107"),
            ("Orders", stats['total_orders'], "#17a2b8"),
            ("Revenue", f"${stats['total_revenue']:.2f}", "#6f42c1")
        ]
        for label, value, color in stats_items:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(20, 10, 20, 10)
            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
            value_label.setStyleSheet(f"color: {color};")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_label)
            name_label = QLabel(label)
            name_label.setStyleSheet("color: #666;")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(name_label)
            stats_layout.addWidget(stat_widget)
        layout.addWidget(stats_frame)
    
    def _setup_inventory_tab(self, layout):
        toolbar = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_inventory)
        toolbar.addWidget(refresh_btn)
        toolbar.addWidget(QLabel("Company:"))
        self.inventory_company_filter = QComboBox()
        self.inventory_company_filter.addItem("All Companies", None)
        toolbar.addWidget(self.inventory_company_filter)
        toolbar.addWidget(QLabel("Category:"))
        self.inventory_category_filter = QComboBox()
        self.inventory_category_filter.addItem("All Categories", None)
        toolbar.addWidget(self.inventory_category_filter)
        toolbar.addWidget(QLabel("Status:"))
        self.inventory_status_filter = QComboBox()
        self.inventory_status_filter.addItems(["All", "Active", "Inactive"])
        toolbar.addWidget(self.inventory_status_filter)
        self.inventory_company_filter.currentIndexChanged.connect(self._filter_inventory)
        self.inventory_category_filter.currentIndexChanged.connect(self._filter_inventory)
        self.inventory_status_filter.currentTextChanged.connect(self._filter_inventory)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(9)
        self.inventory_table.setHorizontalHeaderLabels(["ID", "Image", "Name", "Company", "Category", "Price", "Stock", "Status", "Actions"])
        self.inventory_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.inventory_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.inventory_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.inventory_table)
    
    def _setup_companies_tab(self, layout):
        toolbar = QHBoxLayout()
        add_btn = QPushButton("Add Company")
        add_btn.setStyleSheet("background-color: #28a745; color: white;")
        add_btn.clicked.connect(self._add_company)
        toolbar.addWidget(add_btn)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_companies)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        self.companies_table = QTableWidget()
        self.companies_table.setColumnCount(5)
        self.companies_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Status", "Actions"])
        self.companies_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.companies_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.companies_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.companies_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.companies_table)
    
    def _setup_users_tab(self, layout):
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Filter by role:"))
        self.role_filter = QComboBox()
        self.role_filter.addItems(["All", "admin", "company", "user"])
        self.role_filter.currentTextChanged.connect(self._filter_users)
        toolbar.addWidget(self.role_filter)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_users)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels(["ID", "Username", "Email", "Role", "Status", "Actions"])
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.users_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.users_table)
    
    def _load_data(self):
        self.categories = self.db_manager.get_all_categories()
        self._load_inventory_filters()
        self._load_inventory()
        self._load_companies()
        self._load_users()
    
    def _load_inventory_filters(self):
        for company in self.db_manager.get_all_companies():
            self.inventory_company_filter.addItem(company.name, company.id)
        for category in self.categories:
            self.inventory_category_filter.addItem(category.name, category.id)
    
    def _load_inventory(self):
        products = self.db_manager.get_all_products(include_inactive=True)
        company_id = self.inventory_company_filter.currentData()
        category_id = self.inventory_category_filter.currentData()
        status = self.inventory_status_filter.currentText()
        
        if company_id:
            products = [p for p in products if p.company_id == company_id]
        if category_id:
            products = [p for p in products if p.category_id == category_id]
        if status == "Active":
            products = [p for p in products if p.is_active]
        elif status == "Inactive":
            products = [p for p in products if not p.is_active]
        
        self.inventory_table.setRowCount(len(products))
        for row, product in enumerate(products):
            self.inventory_table.setRowHeight(row, 70)
            self.inventory_table.setItem(row, 0, QTableWidgetItem(str(product.id)))
            
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if product.image_path and os.path.exists(product.image_path):
                pixmap = QPixmap(product.image_path)
                if not pixmap.isNull():
                    img_label.setPixmap(pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                else:
                    img_label.setText("N/A")
            else:
                img_label.setText("N/A")
                img_label.setStyleSheet("color: #999;")
            self.inventory_table.setCellWidget(row, 1, img_label)
            
            self.inventory_table.setItem(row, 2, QTableWidgetItem(product.name))
            company = self.db_manager.get_company_by_id(product.company_id)
            self.inventory_table.setItem(row, 3, QTableWidgetItem(company.name if company else "N/A"))
            category_name = "N/A"
            if product.category_id:
                category = self.db_manager.get_category_by_id(product.category_id)
                category_name = category.name if category else "N/A"
            self.inventory_table.setItem(row, 4, QTableWidgetItem(category_name))
            self.inventory_table.setItem(row, 5, QTableWidgetItem(f"${product.price:.2f}"))
            self.inventory_table.setItem(row, 6, QTableWidgetItem(str(product.stock)))
            
            status_item = QTableWidgetItem("Active" if product.is_active else "Inactive")
            status_item.setForeground(Qt.GlobalColor.darkGreen if product.is_active else Qt.GlobalColor.red)
            self.inventory_table.setItem(row, 7, status_item)
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, p=product: self._edit_product_admin(p))
            actions_layout.addWidget(edit_btn)
            toggle_btn = QPushButton("Deactivate" if product.is_active else "Activate")
            toggle_btn.clicked.connect(lambda checked, p=product: self._toggle_product_status(p))
            actions_layout.addWidget(toggle_btn)
            self.inventory_table.setCellWidget(row, 8, actions_widget)
    
    def _filter_inventory(self):
        self._load_inventory()
    
    def _load_companies(self):
        companies = self.db_manager.get_all_companies()
        self.companies_table.setRowCount(len(companies))
        for row, company in enumerate(companies):
            self.companies_table.setItem(row, 0, QTableWidgetItem(str(company.id)))
            self.companies_table.setItem(row, 1, QTableWidgetItem(company.name))
            self.companies_table.setItem(row, 2, QTableWidgetItem(company.description[:50] + "..." if len(company.description) > 50 else company.description))
            self.companies_table.setItem(row, 3, QTableWidgetItem("Active" if company.is_active else "Inactive"))
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, c=company: self._edit_company(c))
            actions_layout.addWidget(edit_btn)
            toggle_btn = QPushButton("Deactivate" if company.is_active else "Activate")
            toggle_btn.clicked.connect(lambda checked, c=company: self._toggle_company_status(c))
            actions_layout.addWidget(toggle_btn)
            self.companies_table.setCellWidget(row, 4, actions_widget)
    
    def _load_users(self):
        role_filter = self.role_filter.currentText()
        users = self.db_manager.get_all_users() if role_filter == "All" else self.db_manager.get_users_by_role(role_filter)
        self.users_table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user.id)))
            self.users_table.setItem(row, 1, QTableWidgetItem(user.username))
            self.users_table.setItem(row, 2, QTableWidgetItem(user.email))
            self.users_table.setItem(row, 3, QTableWidgetItem(user.role.capitalize()))
            self.users_table.setItem(row, 4, QTableWidgetItem("Active" if user.is_active else "Inactive"))
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            if user.role != 'admin':
                toggle_btn = QPushButton("Deactivate" if user.is_active else "Activate")
                toggle_btn.clicked.connect(lambda checked, u=user: self._toggle_user_status(u))
                actions_layout.addWidget(toggle_btn)
            else:
                actions_layout.addWidget(QLabel("System Admin"))
            self.users_table.setCellWidget(row, 5, actions_widget)
    
    def _filter_users(self):
        self._load_users()
    
    def _add_company(self):
        dialog = AddCompanyDialog(self.db_manager, self)
        if dialog.exec():
            self._load_companies()
            self._load_users()
            self._load_inventory()
    
    def _edit_company(self, company: Company):
        dialog = EditCompanyDialog(self.db_manager, company, self)
        if dialog.exec():
            self._load_companies()
    
    def _toggle_company_status(self, company: Company):
        new_status = not company.is_active
        if self.db_manager.update_company(company.id, is_active=new_status):
            QMessageBox.information(self, "Success", f"Company {'activated' if new_status else 'deactivated'}")
            self._load_companies()
    
    def _edit_product_admin(self, product: Product):
        dialog = EditProductAdminDialog(self.db_manager, product, self.categories, self)
        if dialog.exec():
            self._load_inventory()
    
    def _toggle_product_status(self, product: Product):
        new_status = not product.is_active
        if self.db_manager.update_product(product.id, is_active=new_status):
            QMessageBox.information(self, "Success", f"Product {'activated' if new_status else 'deactivated'}")
            self._load_inventory()
    
    def _toggle_user_status(self, user: User):
        new_status = not user.is_active
        if self.db_manager.update_user(user.id, is_active=new_status):
            QMessageBox.information(self, "Success", f"User {'activated' if new_status else 'deactivated'}")
            self._load_users()
    
    def _logout(self):
        if QMessageBox.question(self, "Logout", "Are you sure?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.auth_controller.logout()
            self.logout_requested.emit()
