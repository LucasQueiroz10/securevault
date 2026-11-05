from fastapi import FastAPI
from app.api.routes import auth
from app.core.config import settings

app = FastAPI(title="SecureVault API", version=settings.app_version)
app.include_router(auth.router)


# Usado pelo HEALTHCHECK da imagem e pelo pipeline para saber se a API está no ar
# e qual versão está rodando.
@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "version": settings.app_version}
