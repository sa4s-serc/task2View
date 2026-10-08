from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Task(Base):
    id = Column(Integer, primary_key=True)
    title = Column(String)
    owner_id = Column(ForeignKey("users.id"))
