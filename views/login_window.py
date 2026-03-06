"""Login window."""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class LoginWindow(QMainWindow):
    login_successful = pyqtSignal(object)
    register_requested = pyqtSignal()
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setWindowTitle("E-Commerce System - Login")
        self.setMinimumSize(400, 500)
        self._setup_ui()
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        title_label = QLabel("E-Commerce System")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Sign in to your account")
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666;")
        main_layout.addWidget(subtitle_label)
        main_layout.addSpacing(20)
        
        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 10px; padding: 20px; }")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)
        
        form_layout.addWidget(QLabel("Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(40)
        self.username_input.returnPressed.connect(self._attempt_login)
        form_layout.addWidget(self.username_input)
        
        form_layout.addWidget(QLabel("Password"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.returnPressed.connect(self._attempt_login)
        form_layout.addWidget(self.password_input)
        
        self.login_button = QPushButton("Sign In")
        self.login_button.setMinimumHeight(45)
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.clicked.connect(self._attempt_login)
        self.login_button.setStyleSheet("""
            QPushButton { background-color: #0078d4; color: white; border: none; border-radius: 5px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #106ebe; }
            QPushButton:pressed { background-color: #005a9e; }
        """)
        form_layout.addWidget(self.login_button)
        
        main_layout.addWidget(form_frame)
        
        register_layout = QHBoxLayout()
        register_layout.addStretch()
        register_layout.addWidget(QLabel("Don't have an account?"))
        self.register_button = QPushButton("Register")
        self.register_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_button.setStyleSheet("QPushButton { background: none; border: none; color: #0078d4; font-weight: bold; text-decoration: underline; }")
        self.register_button.clicked.connect(lambda: self.register_requested.emit())
        register_layout.addWidget(self.register_button)
        register_layout.addStretch()
        main_layout.addLayout(register_layout)
        
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        info_label = QLabel("Default Admin: admin / admin123")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #999; font-size: 10px;")
        main_layout.addWidget(info_label)
    
    def _attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username:
            QMessageBox.warning(self, "Login Error", "Please enter your username.")
            return
        if not password:
            QMessageBox.warning(self, "Login Error", "Please enter your password.")
            return
        
        user = self.db_manager.verify_user_credentials(username, password)
        if user:
            QMessageBox.information(self, "Login Successful", f"Welcome, {user.username}!\nYou are logged in as: {user.role.capitalize()}")
            self.login_successful.emit(user)
            self.username_input.clear()
            self.password_input.clear()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
            self.password_input.clear()
