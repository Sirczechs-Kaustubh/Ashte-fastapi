from fastapi import status, HTTPException, APIRouter, Depends, Query, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database.database import SessionLocal
from models.models import User
from schema.schema import NewUser, ResUser, Role, Login, UpdateUser, ResUpdateUser
from datetime import date, datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from passlib.context import CryptContext
import time

from emails import *
import secret
import jwt
from schema.schema import SignUser, PRTokenModel
from dateutil.parser import parse
from database.database import *
from sqlalchemy import or_
from sqlalchemy.orm import Session

# essentials
from user import oauth2_scheme
from schema.schema import PayDetails
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")
cart_router=APIRouter()
payment_router=APIRouter()

def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, secret.JWT_SECRET, algorithms=[secret.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")
        return user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")


def get_cart_from_db(user_id: int, session:Session=Depends(get_db)):
    cart = session.query(Cart).filter(Cart.user_id == user_id).first()
    return cart

def add_products_to_cart(user_id,product_id):
    session=get_db()
    cart= session.query(Cart).filter(Cart.user_id==user_id).first()
    if cart is None:
        cart = Cart(user_id=user_id)
        session.add(cart)
    cart_item = session.query(CartItem).filter(CartItem.cart_id==cart.id, CartItem.product_id == product_id).first()

    if cart_item is None:
        cart_item = CartItem(cart_id=cart.id,product_id=product_id, quantity=1)
        session.add(cart_item)
    else:
        cart_item.quatity +=1
        session.commit()
        session.close()

def remove_product_from_cart_db(user_id, product_id):
    session=get_db()
    cart = session.query(Cart).filter(Cart.user_id == user_id).first()
    if cart is not None:
        cart_item=session.query(CartItem).filter(CartItem.cart_id==cart.id,CartItem.product_id==product_id).first()

        if cart_item is not None:
            session.delete(cart_item)
            session.commit()
            
def update_cart_items(user_id,product_id,quantity):
    session=get_db()
    cart=session.query(Cart).filter(Cart.user_id==user_id).first()
    if cart is not None:
        cart_item=session.query(CartItem).filter(CartItem.cart_id==cart.id,
                                                 CartItem.product_id == product_id).first()
        if cart_item is not None:
            cart_item.quantity = quantity
            session.commit()

def get_total_amount(user_id:int):
    session=get_db()
    cart=session.query(Cart).filter(Cart.user_id==user_id).first()
    total_amount=0
    if cart is not None:
        cart_items=session.query(CartItem).filter(CartItem.cart_id==cart.id).all()

        for cart_item in cart_items:
            product=session.query(Product).filter(Product.id==cart_item.product_id).first()
            if product is not None:
                total_amount += cart_item.quantity*product.price
    return total_amount
# routes

@cart_router.get("/cart")
async def show_cart(token: str = Depends(oauth2_scheme)):
    user_id=get_current_user_id(token)
    cart=get_cart_from_db(user_id)
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart

@cart_router.post("/cart/add/{product_id}")
async def add_to_cart(product_id:int,token: str = Depends(oauth2_scheme)):
    user_id = get_current_user_id(token)
    add_products_to_cart(user_id,product_id)

@cart_router.delete("/cart/remove/{product_id}")
async def remove_from_cart(product_id:int,token: str = Depends(oauth2_scheme)):
    user_id = get_current_user_id(token)
    remove_product_from_cart_db(user_id,product_id)

@cart_router.put("/cart/update/{product_id}") # unnecessary route actually but can be used for checkout
async def update_cart(product_id:int,quantity:int,token:str=Depends(oauth2_scheme)):
    user_id = get_current_user_id(token)
    update_cart_items(user_id,product_id,quantity)


# for checkout which approach is better ?
#i want to return a jwt token of the encoded checkout data or should i just pass the jwt token
#of the encoded user_id and checkout_id  and later access the data from the
#session and use it for the payment gateway.
@payment_router.get("/checkout")
async def user_checkout(data:PayDetails,token:str=Depends(oauth2_scheme)):
    session=get_db()
    user_id=get_current_user_id(token)
    cart=session.query(Cart).filter(user_id==user_id).first()
    total_amount=get_total_amount(user_id)
    checkout_data=Checkout(user_id=user_id,cart_id=cart.id,email=data.email,name=data.name,phone_no=data.phone_no,
                           address=data.address,postal_code=data.postal_code,amount=total_amount)
    session.add(checkout_data)
    session.commit()
    payload={
        "sub":str(user_id),
        "cart_id":str(cart.id),
        "iat":datetime.utcnow(),
        "exp":datetime.utcnow()+timedelta(minutes=10)}
    token=jwt.encode(payload,secret.JWT_SECRET,secret.JWT_ALGORITHM)
    return token

import razorpay

templates = Jinja2Templates(directory="templates")
client = razorpay.Client(auth=(secret.secret_id, secret.secret_key))
@payment_router.get("/payment")
async def payment(token: str = Depends(oauth2_scheme)):
    session=get_db()
    try:
        decoded_token = jwt.decode(token, secret.JWT_SECRET, algorithms=[secret.JWT_ALGORITHM])
        if datetime.utcnow() > decoded_token['exp']:
            raise HTTPException(status_code=400, detail="Token has expired")
        user_id=decode_token['sub']
        checkout_data=session.query(Checkout).filter(user_id==user_id).first()
        print(checkout_data)
        data={"amount":checkout_data.amount*100,"currency":"INR",
              "receipt":f"order_receipt_{checkout_data.cart_id}_{checkout_data.postal_code}","payment_capture": "1"}
        payment=client.order.create(data=data)
        return templates.TemplateResponse("pay.html", {"request": request,"data":checkout_data,"payment": payment,"key_id":secret.secret_key})
    except JWTError as e:
        raise HTTPException(status_code=400, detail="Invalid token")

@payment_router.post("/verify_payment")
async def verify_payment(order_id: str, payment_id: str, razorpay_signature: str):
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': razorpay_signature
        })
        return {"detail": "Payment verification succeeded"}
    except:
        raise HTTPException(status_code=400, detail="Payment verification failed")


