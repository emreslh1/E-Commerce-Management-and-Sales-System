"""
User panel for the E-Commerce System.
Modern card-based product browsing with detail view and shopping cart.
"""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QMessageBox, QDialog, QFormLayout,
    QLineEdit, QHeaderView, QComboBox,
    QAbstractItemView, QFrame, QSpinBox, QGroupBox,
    QScrollArea, QGridLayout, QSizePolicy, QGridLayout,
    QGraphicsDropShadowEffect, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPixmap, QColor, QCursor

from database.models import User, Product
from typing import Dict, List


PRODUCT_IMAGES_DIR = "product_images"


class CartItem:
    """Represents an item in the shopping cart."""
    
    def __init__(self, product: Product, quantity: int = 1):
        self.product = product
        self.quantity = quantity
    
    @property
    def total(self) -> float:
        return self.product.price * self.quantity


class ShoppingCart:
    """Shopping cart management."""
    
    def __init__(self):
        self._items: Dict[int, CartItem] = {}
    
    def add_item(self, product: Product, quantity: int = 1) -> bool:
        if product.stock < quantity:
            return False
        if product.id in self._items:
            new_qty = self._items[product.id].quantity + quantity
            if new_qty > product.stock:
                return False
            self._items[product.id].quantity = new_qty
        else:
            self._items[product.id] = CartItem(product, quantity)
        return True
    
    def remove_item(self, product_id: int):
        if product_id in self._items:
            del self._items[product_id]
    
    def update_quantity(self, product_id: int, quantity: int) -> bool:
        if product_id not in self._items:
            return False
        if quantity <= 0:
            self.remove_item(product_id)
            return True
        if quantity > self._items[product_id].product.stock:
            return False
        self._items[product_id].quantity = quantity
        return True
    
    def get_items(self) -> List[CartItem]:
        return list(self._items.values())
    
    def get_total(self) -> float:
        return sum(item.total for item in self._items.values())
    
    def get_item_count(self) -> int:
        return sum(item.quantity for item in self._items.values())
    
    def clear(self):
        self._items.clear()


class ProductDetailDialog(QDialog):
    """Modern product detail dialog with all product information."""
    
    def __init__(self, product: Product, company_name: str, category_name: str, 
                 db_manager, cart: ShoppingCart, parent=None):
        super().__init__(parent)
        self.product = product
        self.company_name = company_name
        self.category_name = category_name
        self.db_manager = db_manager
        self.cart = cart
        self.setWindowTitle(f"Product Details")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)
        self._setup_ui()
    
    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Left side - Product Image
        image_container = QFrame()
        image_container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 15px;
            }
        """)
        image_layout = QVBoxLayout(image_container)
        
        self.image_label = QLabel()
        self.image_label.setFixedSize(280, 280)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border-radius: 10px;
            }
        """)
        
        if self.product.image_path and os.path.exists(self.product.image_path):
            pixmap = QPixmap(self.product.image_path)
            if not pixmap.isNull():
                self.image_label.setPixmap(
                    pixmap.scaled(260, 260, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                )
            else:
                self.image_label.setText("No Image Available")
                self.image_label.setStyleSheet("color: #999; font-size: 14px;")
        else:
            self.image_label.setText("No Image Available")
            self.image_label.setStyleSheet("color: #999; font-size: 14px;")
        
        image_layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(image_container)
        
        # Right side - Product Info
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setSpacing(15)
        
        # Product Name
        name_label = QLabel(self.product.name)
        name_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #1a1a2e;")
        name_label.setWordWrap(True)
        info_layout.addWidget(name_label)
        
        # Category Badge
        if self.category_name != "N/A":
            category_badge = QLabel(self.category_name)
            category_badge.setStyleSheet("""
                QLabel {
                    background-color: #e3f2fd;
                    color: #1976d2;
                    padding: 5px 15px;
                    border-radius: 15px;
                    font-size: 12px;
                    font-weight: bold;
                }
            """)
            info_layout.addWidget(category_badge)
        
        # Vendor
        vendor_layout = QHBoxLayout()
        vendor_label = QLabel("Vendor:")
        vendor_label.setStyleSheet("color: #666; font-size: 14px;")
        vendor_layout.addWidget(vendor_label)
        
        vendor_name = QLabel(self.company_name)
        vendor_name.setStyleSheet("color: #333; font-size: 14px; font-weight: bold;")
        vendor_layout.addWidget(vendor_name)
        vendor_layout.addStretch()
        info_layout.addLayout(vendor_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #eee;")
        info_layout.addWidget(separator)
        
        # Description
        if self.product.description:
            desc_label = QLabel("Description")
            desc_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            desc_label.setStyleSheet("color: #333;")
            info_layout.addWidget(desc_label)
            
            desc_text = QLabel(self.product.description)
            desc_text.setWordWrap(True)
            desc_text.setStyleSheet("color: #666; font-size: 13px; line-height: 1.5;")
            desc_text.setMaximumHeight(80)
            info_layout.addWidget(desc_text)
        
        # Price Section
        price_container = QFrame()
        price_container.setStyleSheet("""
            QFrame {
                background-color: #f0fff4;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        price_layout = QVBoxLayout(price_container)
        
        price_label = QLabel(f"${self.product.price:.2f}")
        price_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        price_label.setStyleSheet("color: #28a745;")
        price_layout.addWidget(price_label)
        
        info_layout.addWidget(price_container)
        
        # Stock Status
        stock_layout = QHBoxLayout()
        if self.product.stock > 0:
            stock_icon = QLabel("✓")
            stock_icon.setStyleSheet("color: #28a745; font-size: 18px; font-weight: bold;")
            stock_layout.addWidget(stock_icon)
            
            stock_text = QLabel(f"In Stock ({self.product.stock} available)")
            stock_text.setStyleSheet("color: #28a745; font-size: 14px; font-weight: bold;")
            stock_layout.addWidget(stock_text)
        else:
            stock_icon = QLabel("✗")
            stock_icon.setStyleSheet("color: #dc3545; font-size: 18px; font-weight: bold;")
            stock_layout.addWidget(stock_icon)
            
            stock_text = QLabel("Out of Stock")
            stock_text.setStyleSheet("color: #dc3545; font-size: 14px; font-weight: bold;")
            stock_layout.addWidget(stock_text)
        
        stock_layout.addStretch()
        info_layout.addLayout(stock_layout)
        
        info_layout.addStretch()
        
        # Quantity and Add to Cart
        if self.product.stock > 0:
            action_container = QFrame()
            action_container.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border-radius: 10px;
                    padding: 15px;
                }
            """)
            action_layout = QHBoxLayout(action_container)
            
            qty_label = QLabel("Quantity:")
            qty_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            action_layout.addWidget(qty_label)
            
            self.quantity_spin = QSpinBox()
            self.quantity_spin.setRange(1, self.product.stock)
            self.quantity_spin.setValue(1)
            self.quantity_spin.setStyleSheet("""
                QSpinBox {
                    padding: 8px;
                    border: 2px solid #0078d4;
                    border-radius: 8px;
                    font-size: 16px;
                    min-width: 80px;
                }
            """)
            action_layout.addWidget(self.quantity_spin)
            
            action_layout.addStretch()
            
            self.total_label = QLabel(f"Total: ${self.product.price:.2f}")
            self.total_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            self.total_label.setStyleSheet("color: #333;")
            action_layout.addWidget(self.total_label)
            
            self.quantity_spin.valueChanged.connect(self._update_total)
            
            info_layout.addWidget(action_container)
            
            # Add to Cart Button
            self.add_btn = QPushButton("Add to Cart")
            self.add_btn.setMinimumHeight(50)
            self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
            """)
            self.add_btn.clicked.connect(self._add_to_cart)
            info_layout.addWidget(self.add_btn)
        else:
            notify_btn = QPushButton("Notify When Available")
            notify_btn.setMinimumHeight(50)
            notify_btn.setEnabled(False)
            notify_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ccc;
                    color: #666;
                    border: none;
                    border-radius: 10px;
                    font-size: 16px;
                }
            """)
            info_layout.addWidget(notify_btn)
        
        # Close Button
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(40)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #999;
            }
        """)
        close_btn.clicked.connect(self.reject)
        info_layout.addWidget(close_btn)
        
        main_layout.addWidget(info_container)
    
    def _update_total(self):
        quantity = self.quantity_spin.value()
        total = self.product.price * quantity
        self.total_label.setText(f"Total: ${total:.2f}")
    
    def _add_to_cart(self):
        quantity = self.quantity_spin.value()
        if self.cart.add_item(self.product, quantity):
            QMessageBox.information(
                self,
                "Added to Cart",
                f"{quantity} x {self.product.name} has been added to your cart!"
            )
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Could not add item to cart. Please try again."
            )


class ProductCardWidget(QFrame):
    """Modern product card widget with hover effects."""
    
    add_to_cart_clicked = pyqtSignal(object)
    view_details_clicked = pyqtSignal(object)
    
    def __init__(self, product: Product, company_name: str, category_name: str, parent=None):
        super().__init__(parent)
        self.product = product
        self.company_name = company_name
        self.category_name = category_name
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFixedSize(250, 350)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 15px;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Image Container
        image_container = QFrame()
        image_container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
            }
        """)
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(5, 5, 5, 5)
        
        self.image_label = QLabel()
        self.image_label.setFixedSize(210, 140)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if self.product.image_path and os.path.exists(self.product.image_path):
            pixmap = QPixmap(self.product.image_path)
            if not pixmap.isNull():
                self.image_label.setPixmap(
                    pixmap.scaled(200, 130, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                )
            else:
                self._set_placeholder_image()
        else:
            self._set_placeholder_image()
        
        image_layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(image_container)
        
        # Product Name
        name_label = QLabel(self.product.name)
        name_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #1a1a2e;")
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(40)
        main_layout.addWidget(name_label)
        
        # Vendor/Company Name
        vendor_label = QLabel(f"by {self.company_name}")
        vendor_label.setStyleSheet("color: #888; font-size: 11px;")
        main_layout.addWidget(vendor_label)
        
        # Price and Stock Row
        price_stock_layout = QHBoxLayout()
        
        price_label = QLabel(f"${self.product.price:.2f}")
        price_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        price_label.setStyleSheet("color: #28a745;")
        price_stock_layout.addWidget(price_label)
        
        price_stock_layout.addStretch()
        
        # Stock indicator
        if self.product.stock > 0:
            stock_badge = QLabel(f"{self.product.stock}")
            stock_badge.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    color: #155724;
                    padding: 3px 8px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
        else:
            stock_badge = QLabel("Out")
            stock_badge.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 3px 8px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
        price_stock_layout.addWidget(stock_badge)
        
        main_layout.addLayout(price_stock_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        # View Details Button
        self.details_btn = QPushButton("Details")
        self.details_btn.setMinimumHeight(35)
        self.details_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.details_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #ccc;
            }
        """)
        self.details_btn.clicked.connect(lambda: self.view_details_clicked.emit(self.product))
        btn_layout.addWidget(self.details_btn)
        
        # Add to Cart Button
        self.add_btn = QPushButton("Add to Cart")
        self.add_btn.setMinimumHeight(35)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setEnabled(self.product.stock > 0)
        if self.product.stock > 0:
            self.add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
            """)
        else:
            self.add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ccc;
                    color: #666;
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                }
            """)
        self.add_btn.clicked.connect(lambda: self.add_to_cart_clicked.emit(self.product))
        btn_layout.addWidget(self.add_btn)
        
        main_layout.addLayout(btn_layout)
    
    def _set_placeholder_image(self):
        self.image_label.setText("📦")
        self.image_label.setStyleSheet("font-size: 48px; color: #ccc;")
    
    def enterEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #0078d4;
                border-radius: 15px;
            }
        """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 15px;
            }
        """)
        super().leaveEvent(event)


class CartDialog(QDialog):
    """Modern shopping cart dialog with instant updates."""
    
    checkout_completed = pyqtSignal()
    
    def __init__(self, cart: ShoppingCart, db_manager, user_id: int, parent=None):
        super().__init__(parent)
        self.cart = cart
        self.db_manager = db_manager
        self.user_id = user_id
        self.setWindowTitle("Shopping Cart")
        self.setMinimumSize(650, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)
        self._setup_ui()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Shopping Cart")
        title_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1a1a2e;")
        header_layout.addWidget(title_label)
        
        item_count = QLabel(f"{self.cart.get_item_count()} items")
        item_count.setStyleSheet("color: #666; font-size: 14px;")
        header_layout.addWidget(item_count)
        header_layout.addStretch()
        
        clear_btn = QPushButton("Clear All")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #dc3545;
                border: 1px solid #dc3545;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #dc3545;
                color: white;
            }
        """)
        clear_btn.clicked.connect(self._clear_cart)
        header_layout.addWidget(clear_btn)
        
        main_layout.addLayout(header_layout)
        
        # Cart Items
        items_frame = QFrame()
        items_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
            }
        """)
        items_layout = QVBoxLayout(items_frame)
        items_layout.setSpacing(15)
        items_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create item widgets list for updating
        self.item_widgets = []
        
        for item in self.cart.get_items():
            item_widget = self._create_cart_item_widget(item)
            items_layout.addWidget(item_widget)
            self.item_widgets.append((item.product.id, item_widget))
        
        # Add stretch at bottom
        items_layout.addStretch()
        
        # Scroll area for items
        scroll = QScrollArea()
        scroll.setWidget(items_frame)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        main_layout.addWidget(scroll)
        
        # Summary Section
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f8ff;
                border-radius: 10px;
            }
        """)
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(20, 15, 20, 15)
        
        # Subtotal
        subtotal_layout = QHBoxLayout()
        subtotal_label = QLabel("Subtotal:")
        subtotal_label.setStyleSheet("font-size: 14px; color: #666;")
        subtotal_layout.addWidget(subtotal_label)
        subtotal_layout.addStretch()
        
        self.subtotal_value = QLabel(f"${self.cart.get_total():.2f}")
        self.subtotal_value.setStyleSheet("font-size: 16px; font-weight: bold;")
        subtotal_layout.addWidget(self.subtotal_value)
        summary_layout.addLayout(subtotal_layout)
        
        # Shipping (free for now)
        shipping_layout = QHBoxLayout()
        shipping_label = QLabel("Shipping:")
        shipping_label.setStyleSheet("font-size: 14px; color: #666;")
        shipping_layout.addWidget(shipping_label)
        shipping_layout.addStretch()
        
        shipping_value = QLabel("FREE")
        shipping_value.setStyleSheet("font-size: 14px; color: #28a745; font-weight: bold;")
        shipping_layout.addWidget(shipping_value)
        summary_layout.addLayout(shipping_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        summary_layout.addWidget(separator)
        
        # Total
        total_layout = QHBoxLayout()
        total_label = QLabel("Total:")
        total_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        total_label.setStyleSheet("color: #1a1a2e;")
        total_layout.addWidget(total_label)
        total_layout.addStretch()
        
        self.total_value = QLabel(f"${self.cart.get_total():.2f}")
        self.total_value.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.total_value.setStyleSheet("color: #0078d4;")
        total_layout.addWidget(self.total_value)
        summary_layout.addLayout(total_layout)
        
        main_layout.addWidget(summary_frame)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        continue_btn = QPushButton("Continue Shopping")
        continue_btn.setMinimumHeight(50)
        continue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        continue_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #333;
                border: 2px solid #ddd;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #999;
            }
        """)
        continue_btn.clicked.connect(self.reject)
        btn_layout.addWidget(continue_btn)
        
        self.checkout_btn = QPushButton("Buy Now")
        self.checkout_btn.setMinimumHeight(50)
        self.checkout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkout_btn.setEnabled(self.cart.get_item_count() > 0)
        self.checkout_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.checkout_btn.clicked.connect(self._checkout)
        btn_layout.addWidget(self.checkout_btn)
        
        main_layout.addLayout(btn_layout)
    
    def _create_cart_item_widget(self, item: CartItem) -> QFrame:
        """Create a widget for a cart item."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #eee;
            }
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # Product Image
        img_label = QLabel()
        img_label.setFixedSize(70, 70)
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setStyleSheet("background-color: #f5f5f5; border-radius: 8px;")
        
        if item.product.image_path and os.path.exists(item.product.image_path):
            pixmap = QPixmap(item.product.image_path)
            if not pixmap.isNull():
                img_label.setPixmap(
                    pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                )
        
        layout.addWidget(img_label)
        
        # Product Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        name_label = QLabel(item.product.name)
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #333;")
        info_layout.addWidget(name_label)
        
        price_each = QLabel(f"${item.product.price:.2f} each")
        price_each.setStyleSheet("color: #888; font-size: 11px;")
        info_layout.addWidget(price_each)
        
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # Quantity Controls
        qty_layout = QHBoxLayout()
        qty_layout.setSpacing(5)
        
        minus_btn = QPushButton("-")
        minus_btn.setFixedSize(30, 30)
        minus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        minus_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        minus_btn.clicked.connect(lambda: self._update_item_quantity(item.product.id, -1))
        qty_layout.addWidget(minus_btn)
        
        qty_label = QLabel(str(item.quantity))
        qty_label.setMinimumWidth(40)
        qty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qty_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        qty_label.setStyleSheet("color: #333;")
        qty_layout.addWidget(qty_label)
        frame.qty_label = qty_label
        
        plus_btn = QPushButton("+")
        plus_btn.setFixedSize(30, 30)
        plus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        plus_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        plus_btn.clicked.connect(lambda: self._update_item_quantity(item.product.id, 1))
        qty_layout.addWidget(plus_btn)
        
        layout.addLayout(qty_layout)
        
        # Item Total
        total_label = QLabel(f"${item.total:.2f}")
        total_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        total_label.setStyleSheet("color: #28a745;")
        total_label.setMinimumWidth(80)
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(total_label)
        frame.total_label = total_label
        
        # Remove Button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(30, 30)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #dc3545;
                border: none;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc3545;
                color: white;
                border-radius: 5px;
            }
        """)
        remove_btn.clicked.connect(lambda: self._remove_item(item.product.id))
        layout.addWidget(remove_btn)
        
        return frame
    
    def _update_item_quantity(self, product_id: int, delta: int):
        """Update item quantity by delta (+1 or -1)."""
        current_qty = 0
        for item in self.cart.get_items():
            if item.product.id == product_id:
                current_qty = item.quantity
                break
        
        new_qty = current_qty + delta
        
        if new_qty <= 0:
            self._remove_item(product_id)
            return
        
        if self.cart.update_quantity(product_id, new_qty):
            self._refresh_totals()
            
            # Update the specific item widget
            for pid, widget in self.item_widgets:
                if pid == product_id:
                    widget.qty_label.setText(str(new_qty))
                    for item in self.cart.get_items():
                        if item.product.id == product_id:
                            widget.total_label.setText(f"${item.total:.2f}")
                            break
                    break
    
    def _remove_item(self, product_id: int):
        """Remove an item from the cart."""
        self.cart.remove_item(product_id)
        
        # Find and remove the widget
        for i, (pid, widget) in enumerate(self.item_widgets):
            if pid == product_id:
                widget.deleteLater()
                self.item_widgets.pop(i)
                break
        
        self._refresh_totals()
        
        if self.cart.get_item_count() == 0:
            self.reject()
    
    def _clear_cart(self):
        """Clear all items from cart."""
        reply = QMessageBox.question(
            self,
            "Clear Cart",
            "Are you sure you want to remove all items from your cart?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.cart.clear()
            self.reject()
    
    def _refresh_totals(self):
        """Refresh the total displays."""
        total = self.cart.get_total()
        self.subtotal_value.setText(f"${total:.2f}")
        self.total_value.setText(f"${total:.2f}")
        self.checkout_btn.setEnabled(self.cart.get_item_count() > 0)
    
    def _checkout(self):
        """Process the checkout."""
        if self.cart.get_item_count() == 0:
            QMessageBox.warning(self, "Empty Cart", "Your cart is empty.")
            return
        
        # Confirm purchase
        reply = QMessageBox.question(
            self,
            "Confirm Purchase",
            f"Total: ${self.cart.get_total():.2f}\n\nProceed with checkout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Create order (this will deduct stock)
        items = [
            (item.product.id, item.quantity, item.product.price)
            for item in self.cart.get_items()
        ]
        
        order_id = self.db_manager.create_order(self.user_id, items)
        
        if order_id:
            self.cart.clear()
            QMessageBox.information(
                self,
                "Order Placed!",
                f"Your order #{order_id} has been placed successfully!\n\nThank you for your purchase!"
            )
            self.checkout_completed.emit()
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to place order. Some items may be out of stock. Please try again."
            )


class UserPanel(QMainWindow):
    """Main user panel with modern product browsing."""
    
    logout_requested = pyqtSignal()
    
    def __init__(self, db_manager, auth_controller, user: User):
        super().__init__()
        self.db_manager = db_manager
        self.auth_controller = auth_controller
        self.current_user = user
        self.cart = ShoppingCart()
        
        self.setWindowTitle(f"Shop - {user.username}")
        self.setMinimumSize(1200, 800)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(20)
        
        # Header
        self._create_header(main_layout)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 12px 25px;
                margin-right: 5px;
                background-color: #f5f5f5;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 3px solid #0078d4;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e8e8e8;
            }
        """)
        
        # Shop Tab
        shop_tab = QWidget()
        shop_layout = QVBoxLayout(shop_tab)
        shop_layout.setContentsMargins(5, 15, 5, 5)
        self._setup_shop_tab(shop_layout)
        self.tabs.addTab(shop_tab, "🛍️ Shop")
        
        # Orders Tab
        orders_tab = QWidget()
        orders_layout = QVBoxLayout(orders_tab)
        orders_layout.setContentsMargins(5, 15, 5, 5)
        self._setup_orders_tab(orders_layout)
        self.tabs.addTab(orders_tab, "📦 My Orders")
        
        main_layout.addWidget(self.tabs)
    
    def _create_header(self, layout):
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Welcome
        welcome_layout = QVBoxLayout()
        
        welcome_label = QLabel(f"Welcome back, {self.current_user.username}!")
        welcome_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        welcome_label.setStyleSheet("color: #1a1a2e;")
        welcome_layout.addWidget(welcome_label)
        
        subtitle = QLabel("Discover amazing products from our vendors")
        subtitle.setStyleSheet("color: #666; font-size: 13px;")
        welcome_layout.addWidget(subtitle)
        
        header_layout.addLayout(welcome_layout)
        header_layout.addStretch()
        
        # Cart Button
        self.cart_button = QPushButton("🛒 Cart (0)")
        self.cart_button.setMinimumHeight(45)
        self.cart_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cart_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 25px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        self.cart_button.clicked.connect(self._show_cart)
        header_layout.addWidget(self.cart_button)
        
        # Logout Button
        logout_btn = QPushButton("Logout")
        logout_btn.setMinimumHeight(45)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #dc3545;
                border: 2px solid #dc3545;
                border-radius: 10px;
                padding: 0 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc3545;
                color: white;
            }
        """)
        logout_btn.clicked.connect(self._logout)
        header_layout.addWidget(logout_btn)
        
        layout.addWidget(header_frame)
    
    def _setup_shop_tab(self, layout):
        # Filters
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(20, 10, 20, 10)
        
        filter_layout.addWidget(QLabel("Filter by:"))
        
        self.company_filter = QComboBox()
        self.company_filter.addItem("All Vendors", None)
        self.company_filter.setMinimumWidth(150)
        filter_layout.addWidget(self.company_filter)
        
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories", None)
        self.category_filter.setMinimumWidth(150)
        filter_layout.addWidget(self.category_filter)
        
        filter_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        refresh_btn.clicked.connect(self._load_products)
        filter_layout.addWidget(refresh_btn)
        
        layout.addWidget(filter_frame)
        
        # Connect filters
        self.company_filter.currentIndexChanged.connect(self._filter_products)
        self.category_filter.currentIndexChanged.connect(self._filter_products)
        
        # Products Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #fafafa;
                border-radius: 10px;
            }
        """)
        
        self.products_container = QWidget()
        self.products_container.setStyleSheet("background-color: #fafafa;")
        self.products_grid = QGridLayout(self.products_container)
        self.products_grid.setSpacing(20)
        self.products_grid.setContentsMargins(20, 20, 20, 20)
        
        scroll.setWidget(self.products_container)
        layout.addWidget(scroll)
    
    def _setup_orders_tab(self, layout):
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Order History")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        refresh_btn.clicked.connect(self._load_orders)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Orders Table
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels([
            "Order ID", "Date", "Items", "Total", "Status"
        ])
        self.orders_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.orders_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.orders_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.orders_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                background-color: white;
                gridline-color: #f0f0f0;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                font-weight: bold;
                color: #333;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #333;
            }
        """)
        
        layout.addWidget(self.orders_table)
    
    def _load_data(self):
        self._load_filters()
        self._load_products()
        self._load_orders()
    
    def _load_filters(self):
        companies = self.db_manager.get_active_companies()
        for company in companies:
            self.company_filter.addItem(company.name, company.id)
        
        categories = self.db_manager.get_all_categories()
        for category in categories:
            self.category_filter.addItem(category.name, category.id)
    
    def _load_products(self):
        # Clear existing cards
        while self.products_grid.count():
            item = self.products_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        products = self.db_manager.get_all_active_products()
        
        # Apply filters
        company_id = self.company_filter.currentData()
        category_id = self.category_filter.currentData()
        
        if company_id:
            products = [p for p in products if p.company_id == company_id]
        
        if category_id:
            products = [p for p in products if p.category_id == category_id]
        
        # Add product cards
        columns = 4
        for i, product in enumerate(products):
            company = self.db_manager.get_company_by_id(product.company_id)
            company_name = company.name if company else "Unknown Vendor"
            
            category_name = "N/A"
            if product.category_id:
                category = self.db_manager.get_category_by_id(product.category_id)
                category_name = category.name if category else "N/A"
            
            card = ProductCardWidget(product, company_name, category_name)
            card.add_to_cart_clicked.connect(self._quick_add_to_cart)
            card.view_details_clicked.connect(self._show_product_details)
            
            row = i // columns
            col = i % columns
            self.products_grid.addWidget(card, row, col, Qt.AlignmentFlag.AlignTop)
        
        # Add empty state if no products
        if not products:
            empty_label = QLabel("No products available at the moment.\nCheck back later!")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #999; font-size: 16px; padding: 50px;")
            self.products_grid.addWidget(empty_label, 0, 0, 1, columns, Qt.AlignmentFlag.AlignCenter)
    
    def _filter_products(self):
        self._load_products()
    
    def _load_orders(self):
        orders = self.db_manager.get_orders_by_user(self.current_user.id)
        
        self.orders_table.setRowCount(len(orders))
        
        for row, order in enumerate(orders):
            self.orders_table.setItem(row, 0, QTableWidgetItem(f"#{order.id}"))
            self.orders_table.setItem(row, 1, QTableWidgetItem(order.created_at.strftime("%B %d, %Y %I:%M %p")))
            self.orders_table.setItem(row, 2, QLabel("View Details"))  # Placeholder
            self.orders_table.setItem(row, 3, QTableWidgetItem(f"${order.total_amount:.2f}"))
            
            # Status with styling
            status_item = QTableWidgetItem(order.status.capitalize())
            status_colors = {
                'pending': ('#fff3cd', '#856404'),
                'confirmed': ('#cce5ff', '#004085'),
                'shipped': ('#d4edda', '#155724'),
                'delivered': ('#d1ecf1', '#0c5460'),
                'cancelled': ('#f8d7da', '#721c24')
            }
            bg_color, text_color = status_colors.get(order.status, ('#f8f9fa', '#333'))
            status_item.setBackground(QColor(bg_color))
            status_item.setForeground(QColor(text_color))
            self.orders_table.setItem(row, 4, status_item)
    
    def _quick_add_to_cart(self, product: Product):
        """Quickly add a product to cart with quantity 1."""
        if product.stock <= 0:
            QMessageBox.warning(self, "Out of Stock", "This product is currently out of stock.")
            return
        
        if self.cart.add_item(product, 1):
            self._update_cart_button()
            QMessageBox.information(
                self,
                "Added!",
                f"{product.name} added to cart!"
            )
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Could not add item to cart. Maximum available quantity reached."
            )
    
    def _show_product_details(self, product: Product):
        """Show the product detail dialog."""
        company = self.db_manager.get_company_by_id(product.company_id)
        company_name = company.name if company else "Unknown Vendor"
        
        category_name = "N/A"
        if product.category_id:
            category = self.db_manager.get_category_by_id(product.category_id)
            category_name = category.name if category else "N/A"
        
        dialog = ProductDetailDialog(
            product, company_name, category_name,
            self.db_manager, self.cart, self
        )
        
        if dialog.exec():
            self._update_cart_button()
            self._load_products()  # Refresh to update stock display
    
    def _show_cart(self):
        """Show the shopping cart dialog."""
        if self.cart.get_item_count() == 0:
            QMessageBox.information(self, "Empty Cart", "Your cart is empty. Add some products first!")
            return
        
        dialog = CartDialog(self.cart, self.db_manager, self.current_user.id, self)
        dialog.checkout_completed.connect(self._on_checkout_complete)
        dialog.exec()
        self._update_cart_button()
    
    def _on_checkout_complete(self):
        """Called when checkout is completed."""
        self._load_products()  # Refresh products to show updated stock
        self._load_orders()  # Refresh orders
        self.tabs.setCurrentIndex(1)  # Switch to orders tab
    
    def _update_cart_button(self):
        """Update the cart button text."""
        count = self.cart.get_item_count()
        self.cart_button.setText(f"🛒 Cart ({count})")
    
    def _logout(self):
        if self.cart.get_item_count() > 0:
            reply = QMessageBox.question(
                self,
                "Items in Cart",
                "You have items in your cart. Logging out will clear your cart.\n\nContinue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.auth_controller.logout()
            self.cart.clear()
            self.logout_requested.emit()
