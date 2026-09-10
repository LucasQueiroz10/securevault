from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService, UsernameAlreadyExistsError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    try:
        return service.register(payload.username, payload.password)
    except UsernameAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")