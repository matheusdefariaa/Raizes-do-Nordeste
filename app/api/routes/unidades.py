from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models.unidade import Unidade
from app.api.schemas.unidade import UnidadeCreate, UnidadeResponse

router = APIRouter(prefix="/unidades", tags=["Unidades"])


@router.post(
    "/",
    response_model=UnidadeResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_unidade(
    dados: UnidadeCreate,
    db: Session = Depends(get_db)
):
    unidade = Unidade(**dados.model_dump())

    db.add(unidade)
    db.commit()
    db.refresh(unidade)

    return unidade


@router.get("/", response_model=list[UnidadeResponse])
def listar_unidades(db: Session = Depends(get_db)):
    return db.query(Unidade).all()


@router.get("/{unidade_id}", response_model=UnidadeResponse)
def buscar_unidade(
    unidade_id: int,
    db: Session = Depends(get_db)
):
    unidade = db.query(Unidade).filter(
        Unidade.id == unidade_id
    ).first()

    if unidade is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade não encontrada."
        )

    return unidade
