from fastapi import FastAPI

app = FastAPI(
    title="Rede Raízes do Nordeste",
    description="API de gerenciamento da rede de lanchonetes.",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "API Rede Raízes do Nordeste funcionando!"
    }


@app.get("/health")
def health():
    return {
        "status": "online"
    }
