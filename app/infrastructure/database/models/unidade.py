from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.connection import Base


class Unidade(Base):
    __tablename__ = "unidades"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    cidade: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    estado: Mapped[str] = mapped_column(
        String(2),
        nullable=False
    )

    endereco: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    ativa: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
