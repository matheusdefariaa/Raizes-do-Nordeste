from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict

from typing import Literal


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=100)
    email: str
    senha: str = Field(min_length=8)


class UsuarioFuncionarioCreate(UsuarioCreate):
    perfil: Literal[
        "ADMIN",
        "GERENTE",
        "COZINHA",
        "ATENDENTE",
    ]


class LoginRequest(BaseModel):
    email: str
    senha: str


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    perfil: str


class ProdutoCreate(BaseModel):
    unidade_id: int
    nome: str = Field(min_length=2, max_length=120)
    descricao: str = ""
    preco: Decimal = Field(gt=0)
    estoque: int = Field(ge=0)


class ProdutoResponse(BaseModel):
    id: int
    unidade_id: int
    nome: str
    descricao: str
    preco: Decimal
    estoque: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)

class ItemPedidoCreate(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0)


class PedidoCreate(BaseModel):
    unidade_id: int
    canalPedido: Literal["APP", "TOTEM", "BALCAO", "PICKUP", "WEB"]
    itens: list[ItemPedidoCreate] = Field(min_length=1)


class PagamentoMock(BaseModel):
    aprovado: bool


class StatusPedidoUpdate(BaseModel):
    status: Literal[
        "EM_PREPARACAO",
        "PRONTO",
        "ENTREGUE"
    ]
