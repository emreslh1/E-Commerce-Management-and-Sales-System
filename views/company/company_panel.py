"""Company panel."""
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
from database.models import User, Product
from utils.validators import Validators

PRODUCT_IMAGES_DIR = "product_images"

def ensure_images_dir():
    if not os.path.exists(PRODUCT_IMAGES_DIR):
        os.makedirs(PRODUCT_IMAGES_DIR)

class AddProductDialog(QDialog):
    def __init__(self, db_manager, company_id: int, categories: list, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.company_id = company_id
        self.categories = categories
        self.selected_image_path = ""
        self.setWindowTitle("Add New Product")
        self.setMinimumWidth(500)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        product_group = QGroupBox("Product Information")
        product_layout = QFormLayout(product_group)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product name")
        product_layout.addRow("Product Name *:", self.name_input)
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Product description")
        self.description_input.setMaximumHeight(80)
        product_layout.addRow("Description:", self.description_input)
        self.category_combo = QComboBox()
        self.category_combo.addItem("-- Select Category --", None)
        for category in self.categories:
            self.category_combo.addItem(category.name, category.id)
        product_layout.addRow("Category:", self.category_combo)
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.01, 999999.99)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$ ")
        self.price_input.setValue(0.01)
        product_layout.addRow("Price *:", self.price_input)
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 999999)
        self.stock_input.setValue(0)
        product_layout.addRow("Stock *:", self.stock_input)
        layout.addWidget(product_group)
        
        image_group = QGroupBox("Product Image")
        image_layout = QVBoxLayout(image_group)
        self.image_preview = QLabel("No image selected")
        self.image_preview.setFixedSize(150, 150)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet("QLabel { border: 2px dashed #ccc; border-radius: 5px; background-color: #f9f9f9; color: #999; }")
        self.image_preview.setScaledContents(True)
        image_btn_layout = QHBoxLayout()
        self.select_image_btn = QPushButton("Select Image")
        self.select_image_btn.clicked.connect(self._select_image)
        image_btn_layout.addWidget(self.select_image_btn)
        self.clear_image_btn = QPushButton("Clear")
        self.clear_image_btn.clicked.connect(self._clear_image)
        image_btn_layout.addWidget(self.clear_image_btn)
        image_layout.addWidget(self.image_preview, alignment=Qt.AlignmentFlag.AlignCenter)
        image_layout.addLayout(image_btn_layout)
        layout.addWidget(image_group)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        save_btn = QPushButton("Add Product")
        save_btn.setStyleSheet("background-color: #28a745; color: white;")
        save_btn.clicked.connect(self._add_product)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
    
    def _select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Product Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            self.selected_image_path = file_path
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.image_preview.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    
    def _clear_image(self):
        self.selected_image_path = ""
        self.image_preview.clear()
        self.image_preview.setText("No image selected")
    
    def _validate(self):
        valid, msg = Validators.validate_product_name(self.name_input.text().strip())
        if not valid:
            return False, msg
        if self.price_input.value() <= 0:
            return False, "Price must be greater than 0"
        return True, ""
    
    def _add_product(self):
        valid, error = self._validate()
        if not valid:
            QMessageBox.warning(self, "Validation Error", error)
            return
        
        image_path = ""
        if self.selected_image_path:
            ensure_images_dir()
            ext = os.path.splitext(self.selected_image_path)[1]
            filename = f"{uuid.uuid4()}{ext}"
            image_path = os.path.join(PRODUCT_IMAGES_DIR, filename)
            shutil.copy(self.selected_image_path, image_path)
        
        product_id = self.db_manager.create_product(
            company_id=self.company_id,
            name=self.name_input.text().strip(),
            description=self.description_input.toPlainText().strip(),
            price=self.price_input.value(),
            stock=self.stock_input.value(),
            category_id=self.category_combo.currentData(),
            image_path=image_path
        )
        
        if product_id:
            QMessageBox.information(self, "Success", "Product added successfully")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to add product")

class EditProductDialog(QDialog):
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

class CompanyPanel(QMainWindow):
    logout_requested = pyqtSignal()
    
    def __init__(self, db_manager, auth_controller, user: User):
        super().__init__()
        self.db_manager = db_manager
        self.auth_controller = auth_controller
        self.current_user = user
        self.company = self.db_manager.get_company_by_id(user.company_id) if user.company_id else None
        self.setWindowTitle(f"Company Panel - {user.username}")
        self.setMinimumSize(1000, 700)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        company_name = self.company.name if self.company else self.current_user.username
        welcome_label = QLabel(f"Welcome, {company_name}")
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
        products_tab = QWidget()
        products_layout = QVBoxLayout(products_tab)
        self._setup_products_tab(products_layout)
        self.tabs.addTab(products_tab, "Product Management")
        
        orders_tab = QWidget()
        orders_layout = QVBoxLayout(orders_tab)
        self._setup_orders_tab(orders_layout)
        self.tabs.addTab(orders_tab, "Orders")
        main_layout.addWidget(self.tabs)
    
    def _create_stats_section(self, layout):
        if not self.company:
            return
        stats_frame = QFrame()
        stats_frame.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 8px; padding: 10px; }")
        stats_layout = QHBoxLayout(stats_frame)
        stats = self.db_manager.get_company_statistics(self.company.id)
        stats_items = [
            ("Products", stats['total_products'], "#28a745"),
            ("Orders", stats['total_orders'], "#0078d4"),
            ("Revenue", f"${stats['total_revenue']:.2f}", "#6f42c1")
        ]
        for label, value, color in stats_items:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(30, 10, 30, 10)
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
    
    def _setup_products_tab(self, layout):
        toolbar = QHBoxLayout()
        add_btn = QPushButton("Add Product")
        add_btn.setStyleSheet("background-color: #28a745; color: white;")
        add_btn.clicked.connect(self._add_product)
        toolbar.addWidget(add_btn)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_products)
        toolbar.addWidget(refresh_btn)
        toolbar.addWidget(QLabel("Filter:"))
        self.product_filter = QComboBox()
        self.product_filter.addItems(["All", "Active", "Inactive"])
        self.product_filter.currentTextChanged.connect(self._filter_products)
        toolbar.addWidget(self.product_filter)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels(["ID", "Image", "Name", "Category", "Price", "Stock", "Status", "Actions"])
        self.products_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.products_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.products_table.setIconSize(QSize(60, 60))
        layout.addWidget(self.products_table)
    
    def _setup_orders_tab(self, layout):
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Filter by status:"))
        self.order_status_filter = QComboBox()
        self.order_status_filter.addItems(["All", "pending", "confirmed", "shipped", "delivered", "cancelled"])
        self.order_status_filter.currentTextChanged.connect(self._filter_orders)
        toolbar.addWidget(self.order_status_filter)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_orders)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels(["Order ID", "Customer", "Total", "Status", "Actions"])
        self.orders_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.orders_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.orders_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.orders_table)
    
    def _load_data(self):
        self.categories = self.db_manager.get_all_categories()
        self._load_products()
        self._load_orders()
    
    def _load_products(self):
        if not self.company:
            return
        products = self.db_manager.get_products_by_company(self.company.id, include_inactive=True)
        filter_text = self.product_filter.currentText()
        if filter_text == "Active":
            products = [p for p in products if p.is_active]
        elif filter_text == "Inactive":
            products = [p for p in products if not p.is_active]
        
        self.products_table.setRowCount(len(products))
        for row, product in enumerate(products):
            self.products_table.setRowHeight(row, 70)
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product.id)))
            
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
            self.products_table.setCellWidget(row, 1, img_label)
            
            self.products_table.setItem(row, 2, QTableWidgetItem(product.name))
            category_name = "N/A"
            if product.category_id:
                category = self.db_manager.get_category_by_id(product.category_id)
                category_name = category.name if category else "N/A"
            self.products_table.setItem(row, 3, QTableWidgetItem(category_name))
            self.products_table.setItem(row, 4, QTableWidgetItem(f"${product.price:.2f}"))
            self.products_table.setItem(row, 5, QTableWidgetItem(str(product.stock)))
            status_item = QTableWidgetItem("Active" if product.is_active else "Inactive")
            status_item.setForeground(Qt.GlobalColor.darkGreen if product.is_active else Qt.GlobalColor.red)
            self.products_table.setItem(row, 6, status_item)
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, p=product: self._edit_product(p))
            actions_layout.addWidget(edit_btn)
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #dc3545; color: white;")
            delete_btn.clicked.connect(lambda checked, p=product: self._delete_product(p))
            actions_layout.addWidget(delete_btn)
            self.products_table.setCellWidget(row, 7, actions_widget)
    
    def _filter_products(self):
        self._load_products()
    
    def _load_orders(self):
        if not self.company:
            return
        orders = self.db_manager.get_orders_by_company(self.company.id)
        status_filter = self.order_status_filter.currentText()
        if status_filter != "All":
            orders = [o for o in orders if o['status'] == status_filter]
        
        self.orders_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(order['id'])))
            self.orders_table.setItem(row, 1, QTableWidgetItem(order.get('customer_name', 'N/A')))
            self.orders_table.setItem(row, 2, QTableWidgetItem(f"${order['total_amount']:.2f}"))
            self.orders_table.setItem(row, 3, QTableWidgetItem(order['status'].capitalize()))
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            if order['status'] == 'pending':
                confirm_btn = QPushButton("Confirm")
                confirm_btn.setStyleSheet("background-color: #28a745; color: white;")
                confirm_btn.clicked.connect(lambda checked, oid=order['id']: self._update_order_status(oid, 'confirmed'))
                actions_layout.addWidget(confirm_btn)
            elif order['status'] == 'confirmed':
                ship_btn = QPushButton("Ship")
                ship_btn.setStyleSheet("background-color: #17a2b8; color: white;")
                ship_btn.clicked.connect(lambda checked, oid=order['id']: self._update_order_status(oid, 'shipped'))
                actions_layout.addWidget(ship_btn)
            elif order['status'] == 'shipped':
                deliver_btn = QPushButton("Delivered")
                deliver_btn.setStyleSheet("background-color: #6f42c1; color: white;")
                deliver_btn.clicked.connect(lambda checked, oid=order['id']: self._update_order_status(oid, 'delivered'))
                actions_layout.addWidget(deliver_btn)
            self.orders_table.setCellWidget(row, 4, actions_widget)
    
    def _filter_orders(self):
        self._load_orders()
    
    def _add_product(self):
        if not self.company:
            QMessageBox.warning(self, "Error", "No company associated with this account")
            return
        dialog = AddProductDialog(self.db_manager, self.company.id, self.categories, self)
        if dialog.exec():
            self._load_products()
    
    def _edit_product(self, product: Product):
        dialog = EditProductDialog(self.db_manager, product, self.categories, self)
        if dialog.exec():
            self._load_products()
    
    def _delete_product(self, product: Product):
        if QMessageBox.question(self, "Delete Product", f"Delete '{product.name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if product.image_path and os.path.exists(product.image_path):
                try:
                    os.remove(product.image_path)
                except:
                    pass
            if self.db_manager.delete_product(product.id):
                QMessageBox.information(self, "Success", "Product deleted")
                self._load_products()
    
    def _update_order_status(self, order_id: int, status: str):
        if self.db_manager.update_order_status(order_id, status):
            QMessageBox.information(self, "Success", f"Order status updated to {status}")
            self._load_orders()
    
    def _logout(self):
        if QMessageBox.question(self, "Logout", "Are you sure?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.auth_controller.logout()
            self.logout_requested.emit()
