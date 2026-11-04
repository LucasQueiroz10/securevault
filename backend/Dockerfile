# Estágio de build: instala as dependências em um venv. Nada além do venv
# passa para a imagem final.
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN python -m venv --without-pip /opt/venv \
    && pip --python /opt/venv/bin/python install --no-cache-dir --disable-pip-version-check -r requirements.txt


# Estágio final: é a imagem que vai para produção.
FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Usuário sem privilégios: se a aplicação for invadida, o atacante não é root
# dentro do container.
RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --no-create-home app

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app ./app

# UID numérico: o Kubernetes só consegue verificar "não é root" com o número.
USER 1000:1000

EXPOSE 8000

# A imagem slim não tem curl, então a checagem usa o próprio Python.
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --start-interval=2s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

# DATABASE_URL não tem valor aqui de propósito: é informada ao rodar o container
# e nunca fica gravada na imagem.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
