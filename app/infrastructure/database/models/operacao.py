from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    String, Integer, Boolean, ForeignKey,
    DateTime, Numeric, Text
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.connection import Base


def agora():
    return datetime.now(timezone.utc)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[str] = mapped_column(String(20), default="CLIENTE")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, default="")
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    estoque: Mapped[int] = mapped_column(Integer, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id"), nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False
    )
    canal_pedido: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="AGUARDANDO_PAGAMENTO"
    )
    valor_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora
    )


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos.id"), nullable=False
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False
    )
    nome_produto: Mapped[str] = mapped_column(String(120), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )


class Pagamento(Base):
    __tablename__ = "pagamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos.id"), nullable=False
    )
    provedor: Mapped[str] = mapped_column(
        String(50), default="GATEWAY_MOCK"
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora
    )


class MovimentacaoEstoque(Base):
    __tablename__ = "movimentacoes_estoque"

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False
    )
    pedido_id: Mapped[int | None] = mapped_column(
        ForeignKey("pedidos.id"), nullable=True
    )
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora
    )


class Auditoria(Base):
    __tablename__ = "auditorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    acao: Mapped[str] = mapped_column(String(100), nullable=False)
    entidade: Mapped[str] = mapped_column(String(50), nullable=False)
    entidade_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detalhes: Mapped[str] = mapped_column(Text, default="")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora
    )
