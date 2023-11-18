from pydantic import BaseModel, validator, EmailStr
from typing import Optional
from enum import Enum
from dataclasses import dataclass
import re
from datetime import date, datetime
class Role(str,Enum):
    USER = "user"
    ADMIN = "admin"

@dataclass
class SignUser:
    fullname: str
    email: str
    role: Role
    verified:bool

class NewUser(BaseModel):
    fullname: str
    email: str
    password: str

    class Config:
        orm_mode = True

    # remove validator decorator if it can be handled with html
##    @validator('password')
##    def password_must_be_strong(cls, v) -> str:
##        """Validate that the password is strong."""
##        regex = '(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[@#$%^&+=]).{8,}'
##        if not re.match(regex, v):
##            raise ValueError('Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one number, and one special character.')
##        return v

class UpdateUser(BaseModel):
    fullname: str
    password: str

    class Config:
        orm_mode = True

        
class ResUser(BaseModel):
    id: int
    fullname: str
    email: str
    role: Role
    date: str
    time: str
 
    class Config:
        orm_mode = True

class ResUpdateUser(BaseModel):
    id: int
    fullname: str
    email: str
    password: str
    role: Role
    date: str
    time: str
    verified:bool
 

    class Config:
        orm_mode = True


class Login(BaseModel):
    email: str
    password: str

    class Config:
        orm_mode = True

class DeletionSuccess(BaseModel):
    status: str = "Success"
    message: str = "User deleted successfully."

class OtpGen(BaseModel):
    email: EmailStr
    
class OtpValuation(BaseModel):
    email: EmailStr
    otp: int
    
class PRTokenModel(BaseModel):
    email: str
    expires: datetime

class PayDetails(BaseModel):
    email:EmailStr
    name:str
    phone_no:int
    address:str
    postal_code:str
    @validator('postal_code')
    def verify_postal(cls, v):
        regex='([1-9]{1}[0-9]{5}|[1-9]{1}[0-9]{3}\\s[0-9]{3})'
        if not re.match(regex, v):
            raise ValueError('Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one number, and one special character.')
        return v
