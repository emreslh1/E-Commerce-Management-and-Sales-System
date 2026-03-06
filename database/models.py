"""Database models."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: Optional[int]
    username: str
    password_hash: str
    email: str
    role: str
    company_id: Optional[int]
    created_at: datetime
    is_active: bool = True
    
    def is_admin(self) -> bool:
        return self.role == 'admin'
    
    def is_company(self) -> bool:
        return self.role == 'company'
    
    def is_user(self) -> bool:
        return self.role == 'user'

@dataclass
class Company:
    id: Optional[int]
    name: str
    description: str
    created_at: datetime
    is_active: bool = True

@dataclass
class Category:
    id: Optional[int]
    name: str
    description: str
    created_at: datetime

@dataclass
class Product:
    id: Optional[int]
    company_id: int
    name: str
    description: str
    price: float
    stock: int
    category_id: Optional[int]
    image_path: str
    created_at: datetime
    is_active: bool = True

@dataclass
class Order:
    id: Optional[int]
    user_id: int
    total_amount: float
    status: str
    created_at: datetime

@dataclass
class OrderItem:
    id: Optional[int]
    order_id: int
    product_id: int
    quantity: int
    price: float
