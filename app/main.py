from fastapi import FastAPI

from app.api.routes import unidades
from app.api.routes import sistema

app = FastAPI(
    title="Rede Raízes do Nordeste",
    description="API de gerenciamento da rede de lanchonetes.",
    version="1.0.0"
)

app.include_router(unidades.router)
app.include_router(sistema.router)


@app.get("/")
def home():
    return {
        "message": "API Rede Raízes do Nordeste funcionando!"
    }


@app.get("/health")
def health():
    return {"status": "online"}
