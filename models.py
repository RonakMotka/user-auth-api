from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from datetime import datetime
from database import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(50))
    password = Column(String(255))
    number = Column(String(13), index=True)
    temp_token = Column(String(36))
    verified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    user_otp = relationship("NumberOtpModel", backref="user")


class NumberOtpModel(Base):
    __tablename__ = "number_otps"

    id = Column(String(36), primary_key=True)
    number = Column(String(13), index=True)
    otp = Column(String(6))
    is_redeemed = Column(Boolean, default=False)
    user_id = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now)


