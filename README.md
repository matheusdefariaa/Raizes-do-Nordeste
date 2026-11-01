

# Rede Raízes do Nordeste

API REST para gerenciamento de uma rede de lanchonetes em expansão, desenvolvida como projeto acadêmico. O sistema permite administrar unidades, usuários, produtos, estoque, pedidos e pagamentos, oferecendo suporte a diferentes canais de atendimento.

## Objetivo

Desenvolver uma solução backend para centralizar as operações da Rede Raízes do Nordeste, permitindo o gerenciamento das unidades, controle de estoque, processamento de pedidos e acompanhamento de pagamentos.

## Tecnologias utilizadas

- **Python 3.14** — linguagem de programação.
- **FastAPI** — desenvolvimento da API REST.
- **SQLite** — banco de dados relacional.
- **SQLAlchemy** — mapeamento objeto-relacional (ORM).
- **Alembic** — gerenciamento de migrações do banco de dados.
- **Pydantic** — validação e estruturação de dados.
- **JWT** — autenticação baseada em tokens.
- **Argon2** — proteção de senhas por hash.
- **Pytest** — testes automatizados.
- **HTTPX** — cliente para testes da API.

## Funcionalidades implementadas

### Autenticação e usuários

- Cadastro de usuários.
- Login com e-mail e senha.
- Autenticação por token JWT.
- Proteção de rotas.
- Controle de acesso baseado em perfis.

### Unidades

- Cadastro de unidades.
- Consulta de unidades cadastradas.
- Armazenamento de informações como nome, cidade, estado e endereço.

### Produtos e estoque

- Cadastro de produtos.
- Consulta de produtos.
- Atualização de estoque.
- Validação de disponibilidade antes da criação de pedidos.
- Registro de movimentações de estoque.

### Pedidos

- Criação de pedidos vinculados a uma unidade.
- Associação de produtos e quantidades.
- Identificação do canal de origem do pedido.
- Consulta de pedidos.
- Atualização de status.
- Cancelamento de pedidos.
- Devolução de estoque em situações aplicáveis.

### Pagamentos

- Simulação de integração com serviço externo de pagamento.
- Processamento de pagamentos aprovados e recusados.
- Registro das informações de pagamento.
- Tratamento de pagamentos recusados e devolução de estoque.

### Auditoria

- Registro de operações relevantes do sistema.
- Armazenamento de informações para rastreabilidade das ações.

## Canais de atendimento

O sistema permite identificar a origem de cada pedido:

| Canal  | Descrição                   |
| ------ | --------------------------- |
| APP    | Aplicativo                  |
| TOTEM  | Terminal de autoatendimento |
| BALCAO | Atendimento presencial      |
| PICKUP | Retirada no estabelecimento |
| WEB    | Pedido pelo site            |

Também é possível consultar pedidos filtrando pelo canal de atendimento.

## Estrutura do projeto

```text
Trabalho/
├── app/
│   ├── api/
│   │   ├── dependencies/
│   │   │   └── auth.py
│   │   ├── routes/
│   │   │   ├── sistema.py
│   │   │   └── unidades.py
│   │   └── schemas/
│   │       ├── sistema.py
│   │       └── unidade.py
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   │   └── database/
│   │       ├── models/
│   │       │   ├── unidade.py
│   │       │   └── operacao.py
│   │       └── connection.py
│   └── main.py
├── migrations/
├── tests/
│   └── test_api.py
├── alembic.ini
└── README.md
```

## Como executar o projeto

### 1. Clonar o repositório

```bash
git clone URL_DO_REPOSITORIO
cd Trabalho
```

### 2. Criar o ambiente virtual

```bash
python -m venv .venv
```

### 3. Ativar o ambiente virtual

No Linux:

```bash
source .venv/bin/activate
```

### 4. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 5. Executar as migrações

```bash
alembic upgrade head
```

### 6. Iniciar a aplicação

```bash
uvicorn app.main:app --reload
```

A API estará disponível em:

```text
http://127.0.0.1:8000
```

## Documentação da API

O FastAPI disponibiliza documentação interativa por meio do Swagger UI.

Após iniciar a aplicação, acesse:

```text
http://127.0.0.1:8000/docs
```

A documentação permite visualizar os endpoints, consultar os parâmetros, enviar requisições e verificar as respostas da API.

Também está disponível a documentação alternativa:

```text
http://127.0.0.1:8000/redoc
```

## Principais endpoints

| Método | Endpoint                  | Descrição                       |
| ------ | ------------------------- | ------------------------------- |
| POST   | `/auth/usuarios`          | Cadastro de usuário             |
| POST   | `/auth/login`             | Autenticação                    |
| GET    | `/auth/me`                | Consulta do usuário autenticado |
| POST   | `/unidades`               | Cadastro de unidade             |
| GET    | `/unidades`               | Listagem de unidades            |
| POST   | `/produtos`               | Cadastro de produto             |
| GET    | `/produtos`               | Listagem de produtos            |
| PATCH  | `/produtos/{id}/estoque`  | Atualização de estoque          |
| POST   | `/pedidos`                | Criação de pedido               |
| GET    | `/pedidos`                | Consulta de pedidos             |
| GET    | `/pedidos/{id}`           | Consulta de pedido específico   |
| POST   | `/pedidos/{id}/pagamento` | Processamento de pagamento      |
| PATCH  | `/pedidos/{id}/status`    | Atualização de status           |
| POST   | `/pedidos/{id}/cancelar`  | Cancelamento de pedido          |

**Observação:** os endpoints protegidos exigem autenticação por token JWT. Os perfis de usuário determinam quais operações podem ser realizadas.

## Testes automatizados

O projeto utiliza Pytest e FastAPI TestClient para verificar o funcionamento dos principais recursos da aplicação.

Para executar os testes, utilize:

```bash
python -m pytest -v
```

### Resultados dos testes

**15 testes automatizados aprovados**, cobrindo:

- Autenticação e login.
- Consulta de usuário autenticado.
- Cadastro e listagem de produtos.
- Criação e consulta de pedidos.
- Processamento de pagamentos.
- Fluxo de atualização de pedidos até a entrega.
- Cancelamento de pedidos.
- Devolução de estoque.
- Tentativas de acesso sem autenticação.
- Controle de permissões.
- Validação de produtos inexistentes.
- Validação de estoque insuficiente.
- Validação de cadastro de usuários.

## Segurança

O projeto implementa mecanismos básicos de segurança, incluindo:

- Senhas armazenadas utilizando hash Argon2.
- Autenticação baseada em JWT.
- Controle de acesso por perfil.
- Proteção de endpoints que exigem autenticação.
- Validação de dados de entrada.
- Registro de operações relevantes para auditoria.

## Banco de dados

O SQLite é utilizado para persistência dos dados durante a execução do projeto. O SQLAlchemy realiza o mapeamento das entidades, enquanto o Alembic gerencia as alterações na estrutura do banco de dados.

As principais entidades incluem:

- Usuários.
- Unidades.
- Produtos.
- Pedidos.
- Itens de pedido.
- Pagamentos.
- Movimentações de estoque.
- Auditoria.

## Considerações finais

O projeto demonstra a aplicação de conceitos de desenvolvimento backend, arquitetura de APIs REST, persistência de dados, autenticação, autorização, validação de informações e testes automatizados.

A solução foi desenvolvida com foco na organização das operações da Rede Raízes do Nordeste, buscando oferecer uma base funcional que possa ser expandida futuramente com novas funcionalidades e integrações.

