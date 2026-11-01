from pydantic import BaseModel, Field, ConfigDict


class UnidadeCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=100)
    cidade: str = Field(min_length=2, max_length=100)
    estado: str = Field(min_length=2, max_length=2)
    endereco: str = Field(min_length=5, max_length=200)


class UnidadeResponse(BaseModel):
    id: int
    nome: str
    cidade: str
    estado: str
    endereco: str
    ativa: bool

    model_config = ConfigDict(from_attributes=True)
