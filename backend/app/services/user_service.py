import os
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.repositories.user_repository import UserRepository


class UsernameAlreadyExistsError(Exception):
    pass


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def register(self, username: str, password: str):
        if self.repository.get_by_username(username):
            raise UsernameAlreadyExistsError(f"Username '{username}' already exists")

        password_hash = hash_password(password)
        encryption_salt = os.urandom(16)  # usado depois para derivar a chave de criptografia

        return self.repository.create(username, password_hash, encryption_salt)