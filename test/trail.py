from dateutil.parser import parse
import jwt
import datetime

@router.get("/checkout")
async def user_checkout(data:PayDetails):
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
        "exp":datetime.utcnow()+timedelta(minutes=10)}
    token=jwt.encode(payload,secret.JWT_SECRET,secret.JWT_ALGORITHM)
    return token

import razorpay
templates = Jinja2Templates(directory="templates")
client = razorpay.Client(auth=(secret.secret_id, secret.secret_key))
@router.get("/payment")
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
              "receipt":f"order_receipt_{checkout_data.cart_id}_{checkout_data.postal_code}","payment_capture": "1"})
        payment=client.order.create(data=data)
        return templates.TemplateResponse("pay.html", {"request": request,"data":checkout_data,"payment": payment,"key_id":secret.secret_key})
    except JWTError as e:
        raise HTTPException(status_code=400, detail="Invalid token")

@router.post("/verify_payment")
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
