from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models.operacao import Usuario


SECRET_KEY = "troque-esta-chave-por-uma-chave-secreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_senha(senha: str) -> str:
    return password_hash.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return password_hash.verify(senha, senha_hash)


def criar_token(usuario: Usuario) -> str:
    expiracao = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(usuario.id),
        "perfil": usuario.perfil,
        "exp": expiracao,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def autenticar_usuario(
    username: str,
    password: str,
    db: Session
):
    usuario = db.query(Usuario).filter(
        Usuario.email == username
    ).first()

    if not usuario or not verificar_senha(
        password, usuario.senha_hash
    ):
        return None

    return usuario


def usuario_atual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    erro = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        usuario_id = int(payload.get("sub"))
    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise erro

    usuario = db.query(Usuario).filter(
        Usuario.id == usuario_id,
        Usuario.ativo == True
    ).first()

    if usuario is None:
        raise erro

    return usuario


def exigir_perfis(*perfis):
    def verificar(usuario: Usuario = Depends(usuario_atual)):
        if usuario.perfil not in perfis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para esta operação."
            )
        return usuario

    return verificar
