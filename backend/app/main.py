from fastapi import FastAPI
from app.api.routes import auth

app = FastAPI(title="SecureVault API")
app.include_router(auth.router)


# Usado pelo HEALTHCHECK da imagem e pelo pipeline para saber se a API está no ar.
@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
