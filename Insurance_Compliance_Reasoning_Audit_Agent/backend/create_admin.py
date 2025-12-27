from app import models, database
from sqlalchemy.orm import Session
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def create_admin():
    db = database.SessionLocal()
    try:
        username = "admin"
        password = "adminpassword"
        db_user = db.query(models.User).filter(models.User.username == username).first()
        if db_user:
            print(f"User {username} already exists")
            return
        
        hashed_password = get_password_hash(password)
        new_user = models.User(username=username, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        print(f"User {username} created successfully")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
