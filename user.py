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



db = SessionLocal()

router=APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# global var
token_repository={}

############ add some salt bae to the password ############

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def hash_password(password:str):
        
    hashed_password=password_context.hash(password)
    #print(hashed_password)
    return hashed_password

async def verify_hashed_password(password:str,hashed_password:str):  
    try:
        pass_validity = password_context.verify(password,hashed_password)
        return pass_validity
    except Exception as e:
        return False

###########################################################

############ JWT TOKENS ############
JWT_SECRET = secret.JWT_SECRET
JWT_ALGORITHM=secret.JWT_ALGORITHM
expiration_time = time.time() + (16 * 60 * 60) #16 hours

def sign_jwt(user: SignUser):
    payload = {
        "user_id":user.fullname,
        "user_email": user.email,
        "role":user.role,
        "expires": expiration_time
    }

    token = jwt.encode(payload, JWT_SECRET,JWT_ALGORITHM)
    return token_response(token)



def decode_jwt(token:str):
    try:
        decoded_token = jwt.decode(token,JWT_SECRET,algorithms=[JWT_ALGORITHM])
        # Convert the 'expires' string to a datetime object
        expire_time = parse(decoded_token['expires'])
        # Convert the current UTC time to a datetime object
        comp_time = datetime.datetime.utcnow()
        return decoded_token if expire_time >= comp_time else {}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

def token_response(token:str):
    return {
        "access_token": token
    }

#####################################

# Endpoint for user signup
@router.post('/signup/', response_model=ResUser, status_code=status.HTTP_201_CREATED)
async def create_a_user(user:NewUser, background_tasks: BackgroundTasks):
    try:
        hashed_password = await hash_password(user.password)

        new_user = User(
            fullname=user.fullname,
            email=user.email,
            password=hashed_password,
            role="user",
            verified=False,
            date=date.today(),
            time=datetime.datetime.utcnow().strftime("%H:%M:%S"),
            )
        
        db_item = db.query(User).filter(User.email==new_user.email).first()

        if db_item is not None:
            raise HTTPException(status_code=400, detail="User with the email already exists")

        db.add(new_user)
        db.commit()
        email_schema = EmailSchema(email=[user.email])
        background_tasks.add_task(send_email, email_schema, new_user)

        return new_user
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error while creating the user")
    
#Endpoint for user sign in
    
    # OAuth2PasswordRequestForm

##########################################
@router.post('/login/')
async def login_a_user(login:OAuth2PasswordRequestForm = Depends()):
    try:
    # Fetch the user from the database based on the provided email
        db_user = db.query(User).filter(User.email == login.username).first()

        if db_user is not None and db_user.verified:
            is_password_valid = await verify_hashed_password(login.password, db_user.password)

            if is_password_valid:
                token = sign_jwt(db_user)
                return token
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have entered a wrong password")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found or not verified")

    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in the database")
########################################## Pass reset inside
@router.put('/change-password')
async def change_password(email: str, old_password: str, new_password: str,token: str = Depends(oauth2_scheme)):
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        # Verify the old password
        is_password_valid = verify_hashed_password(old_password, db_user.password)
        if is_password_valid:
            # Hash the new password
            hashed_password = await hash_password(new_password)
            # Update the user's password in the database
            db_user.password = hashed_password
            db.commit()
            time=(datetime.datetime.utcnow()).strftime('%Y-%m-%d %H:%M')
            msg = await pass_change_mail(email,time)
            return {"detail": "Password updated successfully"}
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Old password is incorrect")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with email {email} not found")

############# Pass reset outside ###########
@router.put('/password-reset')
async def password_reset(email:str,background_tasks: BackgroundTasks):
    try:
    # Fetch the user from the database based on the provided email
        db_user = db.query(User).filter(User.email == email).first()

        if db_user is not None and db_user.verified:
            expires = (datetime.datetime.utcnow() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M') # 10 mins time
            token_data = { "email": email,"expires":expires}
            token = jwt.encode(token_data,JWT_SECRET,JWT_ALGORITHM)
            token_repository[email]=token
            print(token_repository)
            background_tasks.add_task(pass_reset_mail, email, token)
            print("password-reset email is sent and working")
            return {"message":"Password reset email sent. Check your inbox"}
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found or not verified")

    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in the database")

@router.post("/reset-password/")
async def reset_password(token,new_password: str,confirm_password: str):
    print(token)
    # check if it is present in repo solution needed either add to db and then check 
    decoded_token=jwt.decode(token,JWT_SECRET,algorithms=[JWT_ALGORITHM])
    if (datetime.datetime.utcnow()).strftime('%Y-%m-%d %H:%M') > decoded_token["expires"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired")
    if new_password!=confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")
    db_user = db.query(User).filter(User.email == decoded_token["email"]).first()
    if db_user:
        hashed_password= await hash_password(new_password)
        db_user.password = hashed_password
        db.commit()
        return {"message":"Password updated successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
user_routes=router
