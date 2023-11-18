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
# essentials
from database.database import *
from sqlalchemy import or_
from sqlalchemy.orm import Session


router=APIRouter()




##########################################
# Endpoints for products
# check for visiblity and date of rollout 
@router.get("/products")
async def get_all_products(session:Session=Depends(get_db)):
    products = session.query(Product).all()
    return products

@router.get("/products/{product_id}")
async def get_product_by_id(product_id:int,session:Session=Depends(get_db)):
    products = session.query(Product).filter(Product.id == product_id).first()
    if products is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return products

@router.get("/products/search/{search_term}")
async def search_products(search_term:str,session:Session=Depends(get_db)):
    products = session.query(Product).filter(or_(product.name.icontains(search_term),
                                                 product.description.icontains(search_term)).all())
    if products is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return products

product_routes=router
