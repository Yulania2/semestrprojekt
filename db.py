from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from passlib.context import CryptContext

DATABASE_URL = "sqlite:///app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Хешування паролів
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

database = {
    "users": {
        "admin": {
            "username": "admin",
            "password": hash_password("admin123"),
            "is_admin": True,
            "favorites": []
        }
    },
    "posts": []  # List to store posts
}


# Моделі


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    image = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="posts")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, nullable=True)
    avatar = Column(String, nullable=True)
    is_admin = Column(Integer, default=0)
    posts = relationship("Post", back_populates="user")

Post.user = relationship("User", back_populates="posts")


Base.metadata.create_all(bind=engine)

# Залежність для бази даних
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
