from sqlalchemy import String,Boolean,Integer,Column,Text, Enum, Date, func,Float,ForeignKey
from database.database import Base
from schema.schema import Role
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True)
    fullname=Column(String(255),nullable=False)
    email=Column(Text,nullable=False,unique=True)
    password=Column(String(255),nullable=False)
    date=Column(String(255),nullable=False)
    time=Column(String(244),nullable=False)
    role=Column(Enum(Role))
    verified=Column(Boolean,default=False, unique=False)
    otp=Column(String(50))
    cart = relationship('Cart', uselist=False, back_populates='user')
    checkout = relationship('Checkout', uselist=False, back_populates='user')

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Float, nullable=False)
    release_date = Column(Date)
    quantity = Column(Integer)
    is_visible = Column(Boolean, default=False)
    created_date = Column(Date,default=func.current_date())
    updated_date = Column(Date,default=func.current_date(),onupdate=func.current_date())

class Cart(Base):
    __tablename__ = 'carts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))  # Link to User model
    user = relationship('User', back_populates='cart')
    items = relationship('CartItem', back_populates='cart')
    checkout = relationship('Checkout', uselist=False, back_populates='cart')

class CartItem(Base):
    __tablename__ = 'cart_items'

    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('carts.id'))
    product_id = Column(Integer, ForeignKey('products.id'))  # Link to Product model
    quantity = Column(Integer)
    cart = relationship('Cart', back_populates='items')
    product = relationship('Product')

class Checkout(Base):
    __tablename__ = 'checkouts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    cart_id = Column(Integer, ForeignKey('carts.id'))
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    phone_no = Column(Integer, nullable=False)
    address = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    amount=Column(Float,nullable=False)
    user = relationship('User', back_populates='checkout')
    cart = relationship('Cart', back_populates='checkout')
    

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
