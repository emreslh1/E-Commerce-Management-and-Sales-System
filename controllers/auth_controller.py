"""Authentication controller."""
from typing import Optional
from database.models import User

class AuthController:
    def __init__(self):
        self._current_user: Optional[User] = None
    
    @property
    def current_user(self) -> Optional[User]:
        return self._current_user
    
    @property
    def is_authenticated(self) -> bool:
        return self._current_user is not None
    
    @property
    def user_role(self) -> Optional[str]:
        return self._current_user.role if self._current_user else None
    
    def set_current_user(self, user: User):
        self._current_user = user
    
    def logout(self):
        self._current_user = None
    
    def is_admin(self) -> bool:
        return self._current_user is not None and self._current_user.is_admin()
    
    def is_company(self) -> bool:
        return self._current_user is not None and self._current_user.is_company()
    
    def is_user(self) -> bool:
        return self._current_user is not None and self._current_user.is_user()
    
    def get_company_id(self) -> Optional[int]:
        return self._current_user.company_id if self._current_user else None
