from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth
from app.core.config import settings

STATIC_DIR = Path(__file__).parent / "static"

# A página só carrega arquivos da própria API e não pode ser embutida em outros
# sites. A regra fica só nela porque o Swagger em /docs carrega recursos de uma CDN.
WEB_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}

app = FastAPI(title="SecureVault API", version=settings.app_version)
app.include_router(auth.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def web_interface():
    return FileResponse(STATIC_DIR / "index.html", headers=WEB_HEADERS)


# Usado pelo HEALTHCHECK da imagem e pelo pipeline para saber se a API está no ar
# e qual versão está rodando.
@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "version": settings.app_version}
