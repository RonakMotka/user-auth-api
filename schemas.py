from pydantic import BaseModel, Field, validator
from email_validator import EmailNotValidError, validate_email
from fastapi import HTTPException, status


class MobileNumber(BaseModel):
    number: str = Field(min_length=10, max_length=10, regex="^[0-9]*$")

class UserLogin(MobileNumber):
    otp: str = Field(min_length=6, max_length=6, regex="^[0-9]*$")


class UserSignUp(BaseModel):
    first_name: str = Field(min_length=3, max_length=50)
    last_name: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=200)
    number: str = Field(min_length=10, max_length=10, regex="^[0-9]*$")
    password: str = Field(min_length=3, max_length=50)

    @validator("email")
    def valid_email(cls, email):
        try:
            valid = validate_email(email)
            return valid.email
        except EmailNotValidError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
            )


class UserLoginResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    number: str
    token: str

    class Config:
        orm_mode = True


class UserChangePassword(BaseModel):
    old_password: str = Field(min_length=3, max_length=50)
    new_password: str = Field(min_length=3, max_length=50)


class UserForgotPassword(BaseModel):
    email: str = Field(min_length=5, max_length=200)

    @validator("email")
    def valid_email(cls, email):
        try:
            valid = validate_email(email)
            return valid.email
        except EmailNotValidError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
            )


class UserConfirmForgotPassword(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    otp: str = Field(min_length=6, max_length=6)
    password: str = Field(min_length=3, max_length=50)

    @validator("email")
    def valid_email(cls, email):
        try:
            valid = validate_email(email)
            return valid.email
        except EmailNotValidError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
            )


class VerifyEmail(BaseModel):
    token: str = Field(..., min_length=36, max_length=36)


class UserProfileUpdate(BaseModel):
    first_name: str = Field(min_length=3, max_length=50)
    last_name: str = Field(min_length=3, max_length=50)
    number: str = Field(min_length=10, max_length=10, regex="^[0-9]*$")


class UserProfile(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    verified: bool

    class Config:
        orm_mode = True