from fastapi import *
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel,EmailStr
from typing import List
import secret
from models.models import User
import jwt
import datetime



conf = ConnectionConfig(
    MAIL_USERNAME="creola.nicolas@ethereal.email",
    MAIL_PASSWORD="9V4bh27eZK1rbnDDc4",
    MAIL_FROM="creola.nicolas@ethereal.email",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.ethereal.email",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False
)
class EmailSchema(BaseModel):
    email:List[EmailStr]

class OTPEmailSchema(BaseModel):
    email: List[EmailStr]

async def send_email(email:EmailSchema, instance:User):
    exp=(datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()
    token_data = {
        "id": instance.id,
        "username": instance.fullname,
        "email": instance.email,
        "expires": exp
    }
    token = jwt.encode(token_data, secret.JWT_SECRET, algorithm=secret.JWT_ALGORITHM)
    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        <div style="display: flex; align-items: center; flex-direction: column;">
            <h3>Account Verification</h3>

            <br>

            <p>
                Thank you for choosing us. Please click on the button below
                to verify your account.
            </p> 
            
            <a style="display: margin-top: 1rem; padding: 1rem; border-radius: 0.5rem;
             font-size: 1rem; text-decoration: none; background: #0275d8; color:white;"
             href="{secret.site_url}/verification?token={token}">
                Verify your email
             </a>
        </div>
    </body>
    </html>
"""""
    message = MessageSchema(
        subject="Ashte account verification",
        recipients=email.email,  # List of recipients,
        body=template,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)


async def send_otp_mail(email: str, otp: str):
    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        <div style="display: flex; align-items: center; flex-direction: column;">
            <h3>Account Verification</h3>

            <br>

            <p>
                Thank you for choosing us. Your OTP code is {otp}
            </p>
            </div>
    </body>
    </html>
"""
    message = MessageSchema(
        subject="OTP for Login",
        recipients=[email], 
        body=template,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)

async def pass_change_mail(email: str, time: str):
    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        <div style="display: flex; align-items: center; flex-direction: column;">
            <h3>You password was changed at : {time}</h3>

            <br>

            <p>
                Thank you for choosing Ashte.
            </p>
            </div>
    </body>
    </html>
"""
    message = MessageSchema(
        subject="Password Change Notice",
        recipients=[email], 
        body=template,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)

async def pass_reset_mail(email: str, token):
    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        <div style="display: flex; align-items: center; flex-direction: column;">
            <h3>Click the button below to reset your password</h3>

            <br>
            <a style="display: margin-top: 1rem; padding: 1rem; border-radius: 0.5rem;
             font-size: 1rem; text-decoration: none; background: #0275d8; color:white;"
             href="{secret.site_url}/reset-password?token={token}">
                Reset Password
             </a>

            <p>
                Thank you for choosing Ashte.
            </p>
            </div>
    </body>
    </html>
"""
    message = MessageSchema(
        subject="Ashte Account Password Reset",
        recipients=[email], 
        body=template,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
