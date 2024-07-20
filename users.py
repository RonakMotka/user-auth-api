import json
import traceback
from uuid import uuid4
import bcrypt
import requests

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from jwcrypto import jwk, jwt

from config import config
from libs.mail_templates import email_verification_template, otp_template
from libs.mails import send_mail
from models import NumberOtpModel, UserModel
from schemas import UserChangePassword, UserConfirmForgotPassword, UserForgotPassword, UserLogin, UserProfileUpdate, UserSignUp, VerifyEmail
from libs.utils import date_time_diff_min, generate_id, generate_otp, now, object_as_dict


def get_user_by_id(db: Session, id: str):
    return db.query(UserModel).filter(UserModel.id == id).first()


def get_user_by_number(db: Session, number: str):
    return (
        db.query(UserModel)
        .filter(UserModel.number == number, UserModel.is_deleted == False)
        .first()
    )


def get_user_by_email(db: Session, email: str):
    return db.query(UserModel).filter(UserModel.email == email).first()


def _create_password(password):
    password = bytes(password, "utf-8")
    password = bcrypt.hashpw(password, config["salt"])
    password = password.decode("utf-8")
    return password


def send_otp(db: Session, number: str, user_id: str):
        otp = str(generate_otp())
        url = f"API of third party sms app"
        try:
            requests.get(url)
        except:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OTP service is not working")
        id = generate_id()
        db_otp = NumberOtpModel(id=id, number=number, otp=otp, user_id=user_id)
        db.add(db_otp)
        db.commit()
        return


def get_token(user_id, email):
    claims = {"id": user_id, "email": email, "time": str(now())}

    # Create a signed token with the generated key
    key = jwk.JWK(**config["jwt_key"])
    Token = jwt.JWT(header={"alg": "HS256"}, claims=claims)
    Token.make_signed_token(key)

    # Further encrypt the token with the same key
    encrypted_token = jwt.JWT(
        header={"alg": "A256KW", "enc": "A256CBC-HS512"}, claims=Token.serialize()
    )
    encrypted_token.make_encrypted_token(key)
    token = encrypted_token.serialize()
    return token


def verify_token(db: Session, token: str):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token."
        )
    else:
        try:
            key = jwk.JWK(**config["jwt_key"])
            ET = jwt.JWT(key=key, jwt=token)
            ST = jwt.JWT(key=key, jwt=ET.claims)
            claims = ST.claims
            claims = json.loads(claims)
            db_user = get_user_by_id(db, id=claims["id"])
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token."
            )
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if db_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        elif db_user.is_deleted:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return db_user


def check_number(db: Session, number: str):
    db_user = get_user_by_number(db=db, number=number)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    send_otp(db=db, number=db_user.number, user_id=db_user.id)
    return


def sign_up(db: Session, user: UserSignUp):
    id = str(uuid4())
    user = user.dict()
    email = user["email"]
    db_user = get_user_by_email(db, email=email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exist"
        )
    user["password"] = _create_password(user["password"])
    temp_token = str(uuid4())
    db_user = UserModel(id=id, temp_token=temp_token, **user)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    verification_url = config["url"] + "verify?token=" + temp_token
    body = email_verification_template(url=verification_url)
    subject = "userAuth - Email Verification"
    send_mail(email=db_user.email, subject=subject, body=body)
    user = object_as_dict(db_user)
    user["token"] = get_token(db_user.id, db_user.email)
    return user


def sign_in(db: Session, user: UserLogin):
    db_user = get_user_by_number(db, number=user.number)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    date_time = now()
    db_otp = (
        db.query(NumberOtpModel)
        .filter(NumberOtpModel.number == user.number)
        .order_by(NumberOtpModel.created_at.desc())
        .first()
    )
    if db_otp.is_redeemed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid OTP."
        )
    elif (
        date_time_diff_min(start=db_otp.created_at, end=date_time) >= config["otp_time"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="OTP expired."
        )
    elif db_otp.otp != user.otp:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid OTP."
        )

    db_otp.is_redeemed = True
    db_user.token = get_token(db_user.id, db_user.email)
    db.commit()
    return db_user


def change_password(db: Session, user: UserChangePassword, token: str):
    db_user = verify_token(db, token=token)
    try:
        hashed = bytes(db_user.password, "utf-8")
        password = bytes(user.old_password, "utf-8")
        result = bcrypt.checkpw(password, hashed)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect old password"
        )
    else:
        password = _create_password(user.new_password)
        db_user.password = password
        db_user.updated_at = now()
        db.commit()


def forgot_password(db: Session, user: UserForgotPassword):
    db_user = get_user_by_email(db, email=user.email)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    otp = generate_otp()
    user_otp = {"id": str(uuid4()), "otp": otp, "user_id": db_user.id}

    db_opt = NumberOtpModel(**user_otp)
    db.add(db_opt)
    db.commit()

    body = otp_template(otp)
    subject = "Password Reset"
    send_mail(email=user.email, subject=subject, body=body)


def confirm_forgot_password(db: Session, user: UserConfirmForgotPassword):
    date_time = now()
    db_user = get_user_by_email(db, email=user.email)
    db_otp = (
        db.query(NumberOtpModel)
        .filter(NumberOtpModel.user_id == db_user.id)
        .order_by(NumberOtpModel.created_at.desc())
        .first()
    )

    if db_otp.is_redeemed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid OTP")
    elif (
        date_time_diff_min(start=db_otp.created_at, end=date_time) >= config["otp_time"]
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OTP expired")
    elif int( db_otp.otp) != int(user.otp):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid OTP")

    password = _create_password(user.password)
    db_user.password = password
    db_user.updated_at = date_time
    db_otp.is_redeemed = True
    db_otp.updated_at = date_time
    db.commit()


def verify_email(db: Session, data: VerifyEmail):
    db_user = (
        db.query(UserModel)
        .filter(UserModel.verified == False, UserModel.temp_token == data.token)
        .first()
    )
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    db_user.temp_token = ("0",)
    db_user.verified = True
    db.commit()
    return


def resend_verification_email(db: Session, token: str):
    db_user = verify_token(db, token=token)
    if db_user.verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verified")
    temp_token = str(uuid4())
    verification_url = config["url"] + "verify?token=" + temp_token
    body = email_verification_template(url=verification_url)
    subject = "userAuth - Email Verification"
    send_mail(email=db_user.email, subject=subject, body=body)
    db_user.temp_token = temp_token
    db.commit()


def get_profile(db: Session, token: str):
    db_user = verify_token(db, token=token)
    return db_user


def update_profile(db: Session, token: str, user: UserProfileUpdate):
    db_user = verify_token(db, token=token)
    db_user.first_name = user.first_name
    db_user.last_name = user.last_name
    db_user.number = user.number
    db_user.updated_at = now()
    db.commit()
    return db_user
