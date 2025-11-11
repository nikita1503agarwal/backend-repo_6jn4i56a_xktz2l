"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogpost" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: Optional[str] = Field(None, description="Address")
    role: str = Field("customer", description="user role: admin|customer")
    is_active: bool = Field(True, description="Whether user is active")

class Category(BaseModel):
    slug: str = Field(..., description="url-safe identifier")
    title: str = Field(..., description="Display name")
    description: Optional[str] = Field(None)

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Category slug")
    images: List[HttpUrl] = Field(default_factory=list, description="Image URLs")
    in_stock: bool = Field(True, description="Whether product is in stock")
    tags: List[str] = Field(default_factory=list)

class OrderItem(BaseModel):
    product_id: str
    title: str
    unit_price: float
    quantity: int = 1

class Order(BaseModel):
    user_email: Optional[str] = None
    items: List[OrderItem]
    total: float
    status: str = Field("pending", description="pending|paid|failed|cancelled")

class BlogPost(BaseModel):
    title: str
    slug: str
    content: str
    author: str
    tags: List[str] = Field(default_factory=list)

class Testimonial(BaseModel):
    author: str
    company: Optional[str] = None
    quote: str
    url: Optional[HttpUrl] = None
    metric: Optional[str] = None

class PortfolioItem(BaseModel):
    client: str
    logo: Optional[HttpUrl] = None
    url: Optional[HttpUrl] = None
    title: str
    description: Optional[str] = None
    metrics: Optional[str] = None
