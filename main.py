import users
import models
import schemas

from fastapi import FastAPI, Depends, Header, Query, Path, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from database import engine
from dependencies import get_db


models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="User-Auth API",
    description="APIs for user-auth",
    version="0.1.0",
    # docs_url=None,
    redoc_url=None,
)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication

@app.post(
    "/sign-up",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserLoginResponse,
    tags=["Authentication"],
)
def sign_up(user: schemas.UserSignUp, db: Session = Depends(get_db)):
    db_user = users.sign_up(db, user)
    return db_user


@app.post(
    "/check-number",
    tags=["Authentication"]
)
def check_number(
    number: schemas.MobileNumber,
    db: Session = Depends(get_db)
):
    users.check_number(db=db, number=number.number)
    return


@app.post(
    "/login",
    response_model=schemas.UserLoginResponse,
    tags=["Authentication"],
)
def sign_in(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = users.sign_in(db, user)
    return db_user


@app.post("/change-password", status_code=status.HTTP_200_OK, tags=["Authentication"])
def change_password(
    user: schemas.UserChangePassword,
    token: str = Header(None),
    db: Session = Depends(get_db),
):
    users.change_password(db, user=user, token=token)
    return Response(status_code=status.HTTP_200_OK)


@app.post("/forgot-password", status_code=status.HTTP_200_OK, tags=["Authentication"])
def forgot_password(user: schemas.UserForgotPassword, db: Session = Depends(get_db)):
    users.forgot_password(db, user=user)
    return Response(status_code=status.HTTP_200_OK)


@app.post(
    "/confirm-forgot-password", status_code=status.HTTP_200_OK, tags=["Authentication"]
)
def confirm_forgot_password(
    user: schemas.UserConfirmForgotPassword, db: Session = Depends(get_db)
):
    users.confirm_forgot_password(db, user=user)
    return Response(status_code=status.HTTP_200_OK)


@app.post(
    "/verify",
    status_code=status.HTTP_200_OK,
    tags=["Authentication"]
)
def verify_email(
    data: schemas.VerifyEmail,
    db: Session = Depends(get_db)
):
    users.verify_email(db, data=data)
    return Response(status_code=status.HTTP_200_OK)


@app.post(
    "/verify/resend",
    status_code=status.HTTP_200_OK,
    tags=["Authentication"]
)
def resend_verification_email(token: str = Header(None), db: Session = Depends(get_db)):
    users.resend_verification_email(db, token=token)
    return Response(status_code=status.HTTP_200_OK)


# End Authentication

# Users

@app.get(
    "/profile",
    status_code=status.HTTP_200_OK,
    response_model=schemas.UserProfile,
    tags=["User"],
)
def get_profile(token: str = Header(None), db: Session = Depends(get_db)):
    data = users.get_profile(db, token=token)
    return data


@app.put(
    "/profile",
    status_code=status.HTTP_200_OK,
    response_model=schemas.UserProfile,
    tags=["User"],
)
def update_profile(
    user: schemas.UserProfileUpdate,
    token: str = Header(None),
    db: Session = Depends(get_db),
):
    data = users.update_profile(db, token=token, user=user)
    return data


# End Users
