
from decimal import Decimal
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models.unidade import Unidade
from app.infrastructure.database.models.operacao import (
    Usuario,
    Produto,
    Pedido,
    ItemPedido,
    Pagamento,
    MovimentacaoEstoque,
    Auditoria,
)
from app.api.schemas.sistema import (
    UsuarioCreate,
    UsuarioResponse,
    TokenResponse,
    ProdutoCreate,
    ProdutoResponse,
    PedidoCreate,
    PagamentoMock,
    StatusPedidoUpdate,
)
from app.api.dependencies.auth import (
    usuario_atual,
    exigir_perfis,
    hash_senha,
    verificar_senha,
    criar_token,
)

router = APIRouter(tags=["Sistema"])


# --------------------------------------------------
# FUNÇÕES AUXILIARES
# --------------------------------------------------

def registrar_auditoria(
    db: Session,
    usuario_id: int | None,
    acao: str,
    entidade: str,
    entidade_id: int | None = None,
    detalhes: dict | None = None,
):
    registro = Auditoria(
        usuario_id=usuario_id,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        detalhes=json.dumps(detalhes or {}, ensure_ascii=False),
    )

    db.add(registro)


def buscar_pedido(
    db: Session,
    pedido_id: int,
    usuario: Usuario,
):
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id
    ).first()

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado."
        )

    if usuario.perfil == "CLIENTE" and pedido.usuario_id != usuario.id:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para acessar este pedido."
        )

    return pedido


def devolver_estoque(db: Session, pedido: Pedido):
    itens = db.query(ItemPedido).filter(
        ItemPedido.pedido_id == pedido.id
    ).all()

    for item in itens:
        produto = db.query(Produto).filter(
            Produto.id == item.produto_id
        ).first()

        if produto:
            produto.estoque += item.quantidade

            db.add(
                MovimentacaoEstoque(
                    produto_id=produto.id,
                    pedido_id=pedido.id,
                    tipo="LIBERACAO_RESERVA",
                    quantidade=item.quantidade,
                )
            )


def resposta_pedido(db: Session, pedido: Pedido):
    itens = db.query(ItemPedido).filter(
        ItemPedido.pedido_id == pedido.id
    ).all()

    return {
        "id": pedido.id,
        "unidade_id": pedido.unidade_id,
        "usuario_id": pedido.usuario_id,
        "canalPedido": pedido.canal_pedido,
        "status": pedido.status,
        "valor_total": pedido.valor_total,
        "criado_em": pedido.criado_em,
        "itens": [
            {
                "produto_id": item.produto_id,
                "nome_produto": item.nome_produto,
                "quantidade": item.quantidade,
                "preco_unitario": item.preco_unitario,
                "subtotal": item.subtotal,
            }
            for item in itens
        ],
    }


# --------------------------------------------------
# AUTENTICAÇÃO E USUÁRIOS
# --------------------------------------------------

@router.post(
    "/auth/usuarios",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_usuario(
    dados: UsuarioCreate,
    db: Session = Depends(get_db),
):
    email = dados.email.strip().lower()

    existente = db.query(Usuario).filter(
        Usuario.email == email
    ).first()

    if existente:
        raise HTTPException(
            status_code=409,
            detail="Já existe um usuário com este e-mail."
        )

    primeiro_usuario = db.query(Usuario).count() == 0

    usuario = Usuario(
        nome=dados.nome,
        email=email,
        senha_hash=hash_senha(dados.senha),
        perfil="ADMIN" if primeiro_usuario else "CLIENTE",
    )

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return usuario


@router.post("/auth/login", response_model=TokenResponse)
def login(
    dados: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(
        Usuario.email == dados.username.strip().lower()
    ).first()

    if not usuario or not verificar_senha(
        dados.password,
        usuario.senha_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.ativo:
        raise HTTPException(
            status_code=403,
            detail="Usuário inativo."
        )

    return {
        "access_token": criar_token(usuario),
        "token_type": "bearer",
        "perfil": usuario.perfil,
    }


@router.get("/auth/me", response_model=UsuarioResponse)
def meus_dados(
    usuario: Usuario = Depends(usuario_atual),
):
    return usuario


# --------------------------------------------------
# PRODUTOS
# --------------------------------------------------

@router.post(
    "/produtos",
    response_model=ProdutoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_produto(
    dados: ProdutoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_perfis("ADMIN", "GERENTE")
    ),
):
    unidade = db.query(Unidade).filter(
        Unidade.id == dados.unidade_id,
        Unidade.ativa == True,
    ).first()

    if not unidade:
        raise HTTPException(
            status_code=404,
            detail="Unidade não encontrada ou inativa."
        )

    if dados.preco <= 0:
        raise HTTPException(
            status_code=422,
            detail="O preço deve ser maior que zero."
        )

    if dados.estoque < 0:
        raise HTTPException(
            status_code=422,
            detail="O estoque não pode ser negativo."
        )

    produto = Produto(
        unidade_id=dados.unidade_id,
        nome=dados.nome,
        descricao=dados.descricao,
        preco=dados.preco,
        estoque=dados.estoque,
    )

    db.add(produto)
    db.flush()

    registrar_auditoria(
        db,
        usuario.id,
        "PRODUTO_CRIADO",
        "Produto",
        produto.id,
    )

    db.commit()
    db.refresh(produto)

    return produto


@router.get("/produtos", response_model=list[ProdutoResponse])
def listar_produtos(
    unidade_id: int | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    consulta = db.query(Produto).filter(
        Produto.ativo == True
    )

    if unidade_id is not None:
        consulta = consulta.filter(
            Produto.unidade_id == unidade_id
        )

    return consulta.order_by(Produto.nome).all()


@router.patch("/produtos/{produto_id}/estoque")
def atualizar_estoque(
    produto_id: int,
    quantidade: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_perfis("ADMIN", "GERENTE")
    ),
):
    produto = db.query(Produto).filter(
        Produto.id == produto_id
    ).first()

    if not produto:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado."
        )

    if quantidade == 0:
        raise HTTPException(
            status_code=422,
            detail="A quantidade deve ser diferente de zero."
        )

    novo_estoque = produto.estoque + quantidade

    if novo_estoque < 0:
        raise HTTPException(
            status_code=409,
            detail="Estoque insuficiente."
        )

    produto.estoque = novo_estoque

    db.add(
        MovimentacaoEstoque(
            produto_id=produto.id,
            tipo="AJUSTE",
            quantidade=quantidade,
        )
    )

    registrar_auditoria(
        db,
        usuario.id,
        "ESTOQUE_ATUALIZADO",
        "Produto",
        produto.id,
        {"quantidade": quantidade},
    )

    db.commit()

    return {
        "mensagem": "Estoque atualizado.",
        "produto_id": produto.id,
        "estoque_atual": produto.estoque,
    }


# --------------------------------------------------
# PEDIDOS
# --------------------------------------------------

@router.post(
    "/pedidos",
    status_code=status.HTTP_201_CREATED,
)
def criar_pedido(
    dados: PedidoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    try:
        unidade = db.query(Unidade).filter(
            Unidade.id == dados.unidade_id,
            Unidade.ativa == True,
        ).first()

        if not unidade:
            raise HTTPException(
                status_code=404,
                detail="Unidade não encontrada ou inativa."
            )

        total = Decimal("0.00")
        itens_pedido = []

        for item in dados.itens:
            if item.quantidade <= 0:
                raise HTTPException(
                    status_code=422,
                    detail="A quantidade deve ser maior que zero."
                )

            produto = db.query(Produto).filter(
                Produto.id == item.produto_id,
                Produto.unidade_id == dados.unidade_id,
                Produto.ativo == True,
            ).first()

            if not produto:
                raise HTTPException(
                    status_code=404,
                    detail=f"Produto {item.produto_id} não encontrado nesta unidade."
                )

            if produto.estoque < item.quantidade:
                raise HTTPException(
                    status_code=409,
                    detail=f"Estoque insuficiente para {produto.nome}."
                )

            subtotal = produto.preco * item.quantidade
            total += subtotal

            itens_pedido.append(
                {
                    "produto": produto,
                    "quantidade": item.quantidade,
                    "subtotal": subtotal,
                }
            )

        pedido = Pedido(
            unidade_id=dados.unidade_id,
            usuario_id=usuario.id,
            canal_pedido=dados.canalPedido,
            status="AGUARDANDO_PAGAMENTO",
            valor_total=total,
        )

        db.add(pedido)
        db.flush()

        for item in itens_pedido:
            produto = item["produto"]
            quantidade = item["quantidade"]

            produto.estoque -= quantidade

            db.add(
                ItemPedido(
                    pedido_id=pedido.id,
                    produto_id=produto.id,
                    nome_produto=produto.nome,
                    quantidade=quantidade,
                    preco_unitario=produto.preco,
                    subtotal=item["subtotal"],
                )
            )

            db.add(
                MovimentacaoEstoque(
                    produto_id=produto.id,
                    pedido_id=pedido.id,
                    tipo="RESERVA",
                    quantidade=quantidade,
                )
            )

        registrar_auditoria(
            db,
            usuario.id,
            "PEDIDO_CRIADO",
            "Pedido",
            pedido.id,
            {"canalPedido": dados.canalPedido},
        )

        db.commit()
        db.refresh(pedido)

        return resposta_pedido(db, pedido)

    except Exception:
        db.rollback()
        raise


@router.get("/pedidos")
def listar_pedidos(
    canalPedido: str | None = None,
    status_pedido: str | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    consulta = db.query(Pedido)

    if usuario.perfil == "CLIENTE":
        consulta = consulta.filter(
            Pedido.usuario_id == usuario.id
        )

    if canalPedido:
        consulta = consulta.filter(
            Pedido.canal_pedido == canalPedido.upper()
        )

    if status_pedido:
        consulta = consulta.filter(
            Pedido.status == status_pedido.upper()
        )

    pedidos = consulta.order_by(
        Pedido.criado_em.desc()
    ).all()

    return [
        resposta_pedido(db, pedido)
        for pedido in pedidos
    ]


@router.get("/pedidos/{pedido_id}")
def consultar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    pedido = buscar_pedido(db, pedido_id, usuario)

    return resposta_pedido(db, pedido)


# --------------------------------------------------
# PAGAMENTO SIMULADO
# --------------------------------------------------

@router.post("/pedidos/{pedido_id}/pagamento")
def processar_pagamento(
    pedido_id: int,
    dados: PagamentoMock,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    pedido = buscar_pedido(db, pedido_id, usuario)

    if pedido.status != "AGUARDANDO_PAGAMENTO":
        raise HTTPException(
            status_code=409,
            detail="Este pedido não está aguardando pagamento."
        )

    pagamento = Pagamento(
        pedido_id=pedido.id,
        provedor="GATEWAY_MOCK",
        status="APROVADO" if dados.aprovado else "RECUSADO",
        valor=pedido.valor_total,
    )

    db.add(pagamento)

    if dados.aprovado:
        pedido.status = "AGUARDANDO_PREPARO"
    else:
        pedido.status = "PAGAMENTO_RECUSADO"
        devolver_estoque(db, pedido)

    registrar_auditoria(
        db,
        usuario.id,
        "PAGAMENTO_PROCESSADO",
        "Pedido",
        pedido.id,
        {"resultado": pagamento.status},
    )

    db.commit()

    return {
        "pedido_id": pedido.id,
        "pagamento": pagamento.status,
        "status_pedido": pedido.status,
        "mensagem": (
            "Pagamento aprovado."
            if dados.aprovado
            else "Pagamento recusado. Estoque devolvido."
        ),
    }


# --------------------------------------------------
# ATUALIZAÇÃO DE STATUS DO PEDIDO
# --------------------------------------------------

@router.patch("/pedidos/{pedido_id}/status")
def atualizar_status_pedido(
    pedido_id: int,
    dados: StatusPedidoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_perfis("ADMIN", "GERENTE", "COZINHA", "ATENDENTE")
    ),
):
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id
    ).first()

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado."
        )

    transicoes = {
        "AGUARDANDO_PREPARO": "EM_PREPARACAO",
        "EM_PREPARACAO": "PRONTO",
        "PRONTO": "ENTREGUE",
    }

    proximo_status = transicoes.get(pedido.status)

    if proximo_status != dados.status:
        raise HTTPException(
            status_code=409,
            detail="Transição de status não permitida."
        )

    status_anterior = pedido.status
    pedido.status = dados.status

    registrar_auditoria(
        db,
        usuario.id,
        "STATUS_PEDIDO_ATUALIZADO",
        "Pedido",
        pedido.id,
        {
            "status_anterior": status_anterior,
            "novo_status": dados.status,
        },
    )

    db.commit()

    return {
        "pedido_id": pedido.id,
        "status_anterior": status_anterior,
        "status_atual": pedido.status,
    }


# --------------------------------------------------
# CANCELAMENTO
# --------------------------------------------------

@router.post("/pedidos/{pedido_id}/cancelar")
def cancelar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    pedido = buscar_pedido(db, pedido_id, usuario)

    if pedido.status != "AGUARDANDO_PAGAMENTO":
        raise HTTPException(
            status_code=409,
            detail="Somente pedidos aguardando pagamento podem ser cancelados."
        )

    devolver_estoque(db, pedido)

    pedido.status = "CANCELADO"

    registrar_auditoria(
        db,
        usuario.id,
        "PEDIDO_CANCELADO",
        "Pedido",
        pedido.id,
    )

    db.commit()

    return {
        "pedido_id": pedido.id,
        "status": pedido.status,
        "mensagem": "Pedido cancelado e estoque devolvido.",
    }

