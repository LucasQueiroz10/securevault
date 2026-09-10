from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def create(self, username: str, password_hash: str, encryption_salt: bytes) -> User:
        user = User(
            username=username,
            password_hash=password_hash,
            encryption_salt=encryption_salt,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user