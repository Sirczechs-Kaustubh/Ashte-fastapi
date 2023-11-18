
##class TShirt(Base):
##    __tablename__ = "tshirts"
##
##    id = Column(Integer, primary_key=True, index=True)
##    name = Column(String, index=True)
##    description = Column(String)
##    size = Column(String)
##    image = Column(String)
##
##class Order(Base):
##    __tablename__ = "orders"
##
##    id = Column(Integer, primary_key=True, index=True)
##    user_id = Column(Integer, ForeignKey("usertable.id"))
##    tshirt_id = Column(Integer, ForeignKey("tshirts.id"))
##    status = Column(String)

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel, EmailStr




class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(200), unique=True, index=True)
    password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=False)
    join_date = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=True)

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Integer, nullable=False)

class UserCreateIn(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserOutResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    join_date: datetime

class ProductBase(BaseModel):
    title: str
    description: str
    price: int

class ProductOutResponse(ProductBase):
    id: int

user_pydantic_in = UserCreateIn
user_pydantic_out = UserOutResponse

product_pydantic_out = ProductOutResponse
    
