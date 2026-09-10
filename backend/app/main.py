from fastapi import FastAPI
from app.api.routes import auth

app = FastAPI(title="SecureVault API")
app.include_router(auth.router)