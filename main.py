#!/usr/bin/env python3
"""Desktop E-Commerce System - Main entry point."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtCore import Qt
from database.db_manager import DatabaseManager
from controllers.auth_controller import AuthController
from views.login_window import LoginWindow
from views.registration_window import RegistrationWindow
from views.admin.admin_panel import AdminPanel
from views.company.company_panel import CompanyPanel
from views.user.user_panel import UserPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.db_manager.initialize_database()
        self.auth_controller = AuthController()
        self.setWindowTitle("E-Commerce Management System")
        self.setMinimumSize(800, 600)
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self._create_views()
        self._show_login()
    
    def _create_views(self):
        self.login_window = LoginWindow(self.db_manager)
        self.login_window.login_successful.connect(self._on_login_success)
        self.login_window.register_requested.connect(self._show_registration)
        self.stacked_widget.addWidget(self.login_window)
        
        self.registration_window = RegistrationWindow(self.db_manager)
        self.registration_window.registration_successful.connect(self._show_login)
        self.registration_window.back_to_login.connect(self._show_login)
        self.stacked_widget.addWidget(self.registration_window)
        
        self.admin_panel = None
        self.company_panel = None
        self.user_panel = None
    
    def _show_login(self):
        self.stacked_widget.setCurrentWidget(self.login_window)
        self.setWindowTitle("E-Commerce System - Login")
    
    def _show_registration(self):
        self.stacked_widget.setCurrentWidget(self.registration_window)
        self.setWindowTitle("E-Commerce System - Register")
    
    def _on_login_success(self, user):
        self.auth_controller.set_current_user(user)
        if user.is_admin():
            self._show_admin_panel(user)
        elif user.is_company():
            self._show_company_panel(user)
        elif user.is_user():
            self._show_user_panel(user)
    
    def _show_admin_panel(self, user):
        if self.admin_panel:
            self.stacked_widget.removeWidget(self.admin_panel)
            self.admin_panel.deleteLater()
        self.admin_panel = AdminPanel(self.db_manager, self.auth_controller, user)
        self.admin_panel.logout_requested.connect(self._on_logout)
        self.stacked_widget.addWidget(self.admin_panel)
        self.stacked_widget.setCurrentWidget(self.admin_panel)
    
    def _show_company_panel(self, user):
        if self.company_panel:
            self.stacked_widget.removeWidget(self.company_panel)
            self.company_panel.deleteLater()
        self.company_panel = CompanyPanel(self.db_manager, self.auth_controller, user)
        self.company_panel.logout_requested.connect(self._on_logout)
        self.stacked_widget.addWidget(self.company_panel)
        self.stacked_widget.setCurrentWidget(self.company_panel)
    
    def _show_user_panel(self, user):
        if self.user_panel:
            self.stacked_widget.removeWidget(self.user_panel)
            self.user_panel.deleteLater()
        self.user_panel = UserPanel(self.db_manager, self.auth_controller, user)
        self.user_panel.logout_requested.connect(self._on_logout)
        self.stacked_widget.addWidget(self.user_panel)
        self.stacked_widget.setCurrentWidget(self.user_panel)
    
    def _on_logout(self):
        for panel in ['admin_panel', 'company_panel', 'user_panel']:
            if hasattr(self, panel) and getattr(self, panel):
                self.stacked_widget.removeWidget(getattr(self, panel))
                getattr(self, panel).deleteLater()
                setattr(self, panel, None)
        self._show_login()
    
    def closeEvent(self, event):
        self.db_manager.close_connection()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QMainWindow { background-color: #ffffff; }
        QWidget { font-family: Arial, sans-serif; }
        QPushButton { padding: 8px 16px; border-radius: 4px; border: none; background-color: #e0e0e0; }
        QPushButton:hover { background-color: #d0d0d0; }
        QPushButton:pressed { background-color: #c0c0c0; }
        QLineEdit { padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
        QLineEdit:focus { border-color: #0078d4; }
        QTableWidget { border: 1px solid #ddd; border-radius: 4px; gridline-color: #eee; }
        QTableWidget::item { padding: 8px; }
        QTableWidget::item:selected { background-color: #0078d4; color: white; }
        QHeaderView::section { background-color: #f5f5f5; padding: 8px; border: none; border-bottom: 1px solid #ddd; font-weight: bold; }
        QTabWidget::pane { border: 1px solid #ddd; border-radius: 4px; }
        QTabBar::tab { padding: 10px 20px; margin-right: 2px; background-color: #f5f5f5; border-top-left-radius: 4px; border-top-right-radius: 4px; }
        QTabBar::tab:selected { background-color: white; border-bottom: 2px solid #0078d4; }
        QTabBar::tab:hover { background-color: #e5e5e5; }
        QComboBox { padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
        QGroupBox { font-weight: bold; border: 1px solid #ddd; border-radius: 4px; margin-top: 10px; padding-top: 10px; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        QScrollArea { border: none; }
    """)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
