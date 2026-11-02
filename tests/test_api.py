
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.infrastructure.database.connection import Base, get_db
from app.infrastructure.database.models.unidade import Unidade
from app.infrastructure.database import models

from app.api.dependencies.auth import hash_senha
from app.infrastructure.database.models.operacao import Usuario


@pytest.fixture
def cenario():
    # Banco SQLite temporário exclusivo para os testes
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSession = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Criar unidade de teste
    db = TestingSession()
    unidade = Unidade(
        nome="Unidade de Testes",
        cidade="Barra do Piraí",
        estado="RJ",
        endereco="Rua de Testes, 100",
    )
    db.add(unidade)
    db.commit()
    db.close()

    with TestClient(app) as client:
    # Criar administrador diretamente no banco de testes
        db = TestingSession()

        administrador = Usuario(
            nome="Administrador Teste",
            email="admin@teste.com",
            senha_hash=hash_senha("12345678"),
            perfil="ADMIN",
        )

        db.add(administrador)
        db.commit()
        db.close()

        # Autenticar administrador
        login = client.post(
            "/auth/login",
            data={
                "username": "admin@teste.com",
                "password": "12345678",
            },
        )
        assert login.status_code == 200

        token = login.json()["access_token"]

        headers = {
            "Authorization": f"Bearer {token}"
        }

        yield {
            "client": client,
            "headers": headers,
        }

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def criar_produto(cenario, estoque=10):
    response = cenario["client"].post(
        "/produtos",
        headers=cenario["headers"],
        json={
            "unidade_id": 1,
            "nome": "Hambúrguer Teste",
            "descricao": "Produto para testes",
            "preco": 25.90,
            "estoque": estoque,
        },
    )

    assert response.status_code == 201
    return response.json()


def criar_pedido(cenario, produto_id, quantidade=1):
    return cenario["client"].post(
        "/pedidos",
        headers=cenario["headers"],
        json={
            "unidade_id": 1,
            "canalPedido": "APP",
            "itens": [
                {
                    "produto_id": produto_id,
                    "quantidade": quantidade,
                }
            ],
        },
    )


# 1. Login com credenciais válidas
def test_login_sucesso(cenario):
    response = cenario["client"].post(
        "/auth/login",
        data={
            "username": "admin@teste.com",
            "password": "12345678",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


# 2. Consultar usuário autenticado
def test_consultar_usuario(cenario):
    response = cenario["client"].get(
        "/auth/me",
        headers=cenario["headers"],
    )

    assert response.status_code == 200
    assert response.json()["perfil"] == "ADMIN"


# 3. Cadastrar produto
def test_cadastrar_produto(cenario):
    produto = criar_produto(cenario)

    assert produto["nome"] == "Hambúrguer Teste"
    assert produto["estoque"] == 10


# 4. Listar produtos
def test_listar_produtos(cenario):
    criar_produto(cenario)

    response = cenario["client"].get(
        "/produtos",
        headers=cenario["headers"],
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


# 5. Criar pedido
def test_criar_pedido(cenario):
    produto = criar_produto(cenario)

    response = criar_pedido(
        cenario,
        produto["id"],
    )

    assert response.status_code == 201
    assert response.json()["status"] == "AGUARDANDO_PAGAMENTO"


# 6. Aprovar pagamento
def test_pagamento_aprovado(cenario):
    produto = criar_produto(cenario)
    pedido = criar_pedido(cenario, produto["id"]).json()

    response = cenario["client"].post(
        f"/pedidos/{pedido['id']}/pagamento",
        headers=cenario["headers"],
        json={"aprovado": True},
    )

    assert response.status_code == 200
    assert response.json()["pagamento"] == "APROVADO"
    assert response.json()["status_pedido"] == "AGUARDANDO_PREPARO"


# 7. Atualizar pedido até ENTREGUE
def test_fluxo_pedido_entregue(cenario):
    produto = criar_produto(cenario)
    pedido = criar_pedido(cenario, produto["id"]).json()

    client = cenario["client"]
    headers = cenario["headers"]
    pedido_id = pedido["id"]

    pagamento = client.post(
        f"/pedidos/{pedido_id}/pagamento",
        headers=headers,
        json={"aprovado": True},
    )
    assert pagamento.status_code == 200

    for status_pedido in [
        "EM_PREPARACAO",
        "PRONTO",
        "ENTREGUE",
    ]:
        response = client.patch(
            f"/pedidos/{pedido_id}/status",
            headers=headers,
            json={"status": status_pedido},
        )

        assert response.status_code == 200
        assert response.json()["status_atual"] == status_pedido


# 8. Recusar pagamento e devolver estoque
def test_pagamento_recusado_devolve_estoque(cenario):
    produto = criar_produto(cenario, estoque=10)

    pedido = criar_pedido(
        cenario,
        produto["id"],
        quantidade=2,
    ).json()

    client = cenario["client"]
    headers = cenario["headers"]

    response = client.post(
        f"/pedidos/{pedido['id']}/pagamento",
        headers=headers,
        json={"aprovado": False},
    )

    assert response.status_code == 200
    assert response.json()["pagamento"] == "RECUSADO"

    produtos = client.get(
        "/produtos",
        headers=headers,
    ).json()

    assert produtos[0]["estoque"] == 10


# 9. Cancelar pedido e devolver estoque
def test_cancelar_pedido_devolve_estoque(cenario):
    produto = criar_produto(cenario, estoque=10)

    pedido = criar_pedido(
        cenario,
        produto["id"],
        quantidade=2,
    ).json()

    response = cenario["client"].post(
        f"/pedidos/{pedido['id']}/cancelar",
        headers=cenario["headers"],
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELADO"

    produtos = cenario["client"].get(
        "/produtos",
        headers=cenario["headers"],
    ).json()

    assert produtos[0]["estoque"] == 10


# 10. Login com senha incorreta
def test_login_invalido(cenario):
    response = cenario["client"].post(
        "/auth/login",
        data={
            "username": "admin@teste.com",
            "password": "senha_errada",
        },
    )

    assert response.status_code == 401


# 11. Acesso sem token
def test_acesso_sem_token(cenario):
    response = cenario["client"].get("/auth/me")

    assert response.status_code == 401


# 12. Cliente sem permissão para cadastrar produto
def test_cliente_sem_permissao(cenario):
    client = cenario["client"]

    cadastro = client.post(
        "/auth/usuarios",
        json={
            "nome": "Cliente Teste",
            "email": "cliente@teste.com",
            "senha": "12345678",
        },
    )
    assert cadastro.status_code == 201

    login = client.post(
        "/auth/login",
        data={
            "username": "cliente@teste.com",
            "password": "12345678",
        },
    )

    token_cliente = login.json()["access_token"]

    response = client.post(
        "/produtos",
        headers={
            "Authorization": f"Bearer {token_cliente}"
        },
        json={
            "unidade_id": 1,
            "nome": "Produto não autorizado",
            "descricao": "Teste de permissão",
            "preco": 10,
            "estoque": 5,
        },
    )

    assert response.status_code == 403


# 13. Pedido com produto inexistente
def test_produto_inexistente(cenario):
    response = criar_pedido(
        cenario,
        produto_id=9999,
    )

    assert response.status_code == 404


# 14. Pedido com estoque insuficiente
def test_estoque_insuficiente(cenario):
    produto = criar_produto(cenario, estoque=2)

    response = criar_pedido(
        cenario,
        produto["id"],
        quantidade=999,
    )

    assert response.status_code == 409


# 15. Validação de campos obrigatórios
def test_cadastro_usuario_invalido(cenario):
    response = cenario["client"].post(
        "/auth/usuarios",
        json={
            "nome": "Usuário sem e-mail",
            "senha": "12345678",
        },
    )

    assert response.status_code == 422



# 16. Pedido com produto repetido e estoque suficiente
def test_pedido_produto_repetido_com_estoque_suficiente(cenario):
    produto = criar_produto(cenario, estoque=6)

    response = cenario["client"].post(
        "/pedidos",
        headers=cenario["headers"],
        json={
            "unidade_id": 1,
            "canalPedido": "APP",
            "itens": [
                {
                    "produto_id": produto["id"],
                    "quantidade": 2,
                },
                {
                    "produto_id": produto["id"],
                    "quantidade": 3,
                },
            ],
        },
    )

    assert response.status_code == 201

    produtos = cenario["client"].get(
        "/produtos",
        headers=cenario["headers"],
    ).json()

    assert produtos[0]["estoque"] == 1


# 17. Pedido com produto repetido e estoque insuficiente
def test_pedido_produto_repetido_com_estoque_insuficiente(cenario):
    produto = criar_produto(cenario, estoque=6)

    response = cenario["client"].post(
        "/pedidos",
        headers=cenario["headers"],
        json={
            "unidade_id": 1,
            "canalPedido": "APP",
            "itens": [
                {
                    "produto_id": produto["id"],
                    "quantidade": 4,
                },
                {
                    "produto_id": produto["id"],
                    "quantidade": 3,
                },
            ],
        },
    )

    assert response.status_code == 409

    produtos = cenario["client"].get(
        "/produtos",
        headers=cenario["headers"],
    ).json()

    assert produtos[0]["estoque"] == 6



# 18. Impedir pagamento duplicado
def test_impedir_pagamento_duplicado(cenario):
    produto = criar_produto(cenario, estoque=10)
    resposta_pedido = criar_pedido(cenario, produto["id"])
    pedido = resposta_pedido.json()

    primeiro_pagamento = cenario["client"].post(
        f'/pedidos/{pedido["id"]}/pagamento',
        headers=cenario["headers"],
        json={"aprovado": True},
    )

    assert primeiro_pagamento.status_code == 200

    segundo_pagamento = cenario["client"].post(
        f'/pedidos/{pedido["id"]}/pagamento',
        headers=cenario["headers"],
        json={"aprovado": True},
    )

    assert segundo_pagamento.status_code == 409

# 19. Impedir cancelamento duplicado
def test_impedir_cancelamento_duplicado(cenario):
    produto = criar_produto(cenario, estoque=10)
    resposta_pedido = criar_pedido(cenario, produto["id"])
    pedido = resposta_pedido.json()

    primeiro_cancelamento = cenario["client"].post(
        f'/pedidos/{pedido["id"]}/cancelar',
        headers=cenario["headers"],
    )

    assert primeiro_cancelamento.status_code == 200

    segundo_cancelamento = cenario["client"].post(
        f'/pedidos/{pedido["id"]}/cancelar',
        headers=cenario["headers"],
    )

    assert segundo_cancelamento.status_code == 409



# 20. ADMIN consegue consultar auditoria
def test_admin_consultar_auditoria(cenario):
    produto = criar_produto(cenario, estoque=10)

    response = cenario["client"].get(
        "/auditoria",
        headers=cenario["headers"],
    )

    assert response.status_code == 200

    dados = response.json()

    assert dados["total"] >= 1
    assert any(
        registro["acao"] == "PRODUTO_CRIADO"
        for registro in dados["registros"]
    )


# 21. CLIENTE não consegue consultar auditoria
def test_cliente_sem_acesso_auditoria(cenario):
    cadastro = cenario["client"].post(
        "/auth/usuarios",
        json={
            "nome": "Cliente Teste",
            "email": "cliente@teste.com",
            "senha": "12345678",
        },
    )

    assert cadastro.status_code in (200, 201)

    login = cenario["client"].post(
        "/auth/login",
        data={
            "username": "cliente@teste.com",
            "password": "12345678",
        },
    )

    assert login.status_code == 200

    token_cliente = login.json()["access_token"]

    response = cenario["client"].get(
        "/auditoria",
        headers={
            "Authorization": f"Bearer {token_cliente}"
        },
    )

    assert response.status_code == 403

