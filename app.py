from fastapi import FastAPI
from user import * # Import user route file
from products import *
from cart import *
import uvicorn
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from database.database import get_db
from sqlalchemy.orm import Session
import math
import random
from schema.schema import *
from cart import templates


app=FastAPI()

def otp_generator():
    digits="0123456789"
    OTP=""
    for i in range(6):
        OTP+=digits[math.floor(random.random()*10)]
    otp = OTP + " is your OTP"
    return [otp,OTP]

app.include_router(user_routes,tags=["User"])
app.include_router(product_routes,tags=["Products"])
app.include_router(cart_router,tags=["Cart"])
app.include_router(payment_router,tags=["Payment"])
@app.get("/")
def index():
    return {"Message":"Wassup Nigga"}

@app.get("/verification", response_class=HTMLResponse)
async def verification(request: Request, token: str, db: Session = Depends(get_db)):
    try:
        payload = decode_jwt(token)
        if not payload:
            raise HTTPException(status_code=400, detail="Invalid token or token expired")

        user = db.query(User).filter(User.email == payload["email"]).first()

        if user:
            user.verified = True  
            db.commit()
            return templates.TemplateResponse("verification.html", {"request": request})
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException as e:
        raise e  # Reraise the HTTPException with the appropriate status code and detail


@app.post("/generate_otp")
async def generate_otp(data: OtpGen, db: Session = Depends(get_db)):
    email = data.email
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            otp = otp_generator()
            user.otp=otp[1]
            db.commit()
            msg = await send_otp_mail(email, otp[0])
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException as e:
        raise e
    

@app.post("/verify_otp")
async def verify_otp(data: OtpValuation, db: Session = Depends(get_db)):
    print(type(data.otp))
    otp = str(data.otp)
    email = data.email
    try:
        user = db.query(User).filter(User.email == email).first()
        if user and otp==user.otp:
            token=sign_jwt(user)
            return {"message": "Logged in successfully", "token": token}
        else:
            return {"message": "Invalid OTP"}
    except Exception as e:
        return (str(e))

##if __name__ == "__main__":
##    app_module = "app:app"
##    uvicorn.run(app_module, host="0.0.0.0", port=8000, reload=True)


