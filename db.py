from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
import datetime

now = datetime.datetime.utcnow()

DATABASE_URL = "sqlite:///./appdata.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True) # <-firebase uid
    username = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    round_id = Column(Integer, index=True)
    number_selected = Column(Integer)
    submitted_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    user = relationship("User")

Base.metadata.create_all(bind=engine)