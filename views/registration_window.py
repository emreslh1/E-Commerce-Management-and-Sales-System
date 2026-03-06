"""Registration window."""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from utils.validators import Validators

class RegistrationWindow(QMainWindow):
    registration_successful = pyqtSignal()
    back_to_login = pyqtSignal()
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setWindowTitle("E-Commerce System - Register")
        self.setMinimumSize(450, 550)
        self._setup_ui()
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 40)
        main_layout.setSpacing(15)
        
        title_label = QLabel("Create Account")
        title_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Register as a new customer")
        subtitle_label.setFont(QFont("Arial", 11))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666;")
        main_layout.addWidget(subtitle_label)
        
        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 10px; padding: 15px; }")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(12)
        
        form_layout.addWidget(QLabel("Username *"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username")
        self.username_input.setMinimumHeight(38)
        form_layout.addWidget(self.username_input)
        
        form_layout.addWidget(QLabel("Email *"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setMinimumHeight(38)
        form_layout.addWidget(self.email_input)
        
        form_layout.addWidget(QLabel("Password *"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Create a password (min 6 characters)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(38)
        form_layout.addWidget(self.password_input)
        
        form_layout.addWidget(QLabel("Confirm Password *"))
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Re-enter your password")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setMinimumHeight(38)
        form_layout.addWidget(self.confirm_input)
        
        main_layout.addWidget(form_frame)
        
        info_label = QLabel("* All fields are required")
        info_label.setStyleSheet("color: #999; font-size: 10px;")
        main_layout.addWidget(info_label)
        
        self.register_button = QPushButton("Create Account")
        self.register_button.setMinimumHeight(45)
        self.register_button.clicked.connect(self._attempt_registration)
        self.register_button.setStyleSheet("""
            QPushButton { background-color: #28a745; color: white; border: none; border-radius: 5px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #218838; }
        """)
        main_layout.addWidget(self.register_button)
        
        back_layout = QHBoxLayout()
        back_layout.addStretch()
        back_label = QLabel("Already have an account?")
        back_label.setStyleSheet("color: #666;")
        back_layout.addWidget(back_label)
        self.back_button = QPushButton("Sign In")
        self.back_button.setStyleSheet("QPushButton { background: none; border: none; color: #0078d4; font-weight: bold; text-decoration: underline; }")
        self.back_button.clicked.connect(lambda: (self.back_to_login.emit(), self._clear_form()))
        back_layout.addWidget(self.back_button)
        back_layout.addStretch()
        main_layout.addLayout(back_layout)
    
    def _validate_inputs(self):
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        valid, msg = Validators.validate_username(username)
        if not valid:
            return False, msg
        if self.db_manager.get_user_by_username(username):
            return False, "Username is already taken"
        
        valid, msg = Validators.validate_email(email)
        if not valid:
            return False, msg
        if self.db_manager.get_user_by_email(email):
            return False, "Email is already registered"
        
        valid, msg = Validators.validate_password(password)
        if not valid:
            return False, msg
        if password != confirm:
            return False, "Passwords do not match"
        return True, ""
    
    def _attempt_registration(self):
        valid, error_msg = self._validate_inputs()
        if not valid:
            QMessageBox.warning(self, "Registration Error", error_msg)
            return
        
        user_id = self.db_manager.create_user(
            username=self.username_input.text().strip(),
            password=self.password_input.text(),
            email=self.email_input.text().strip(),
            role='user'
        )
        
        if user_id:
            QMessageBox.information(self, "Registration Successful", "Your account has been created successfully!")
            self._clear_form()
            self.registration_successful.emit()
        else:
            QMessageBox.warning(self, "Registration Failed", "Could not create your account.")
    
    def _clear_form(self):
        self.username_input.clear()
        self.email_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()
