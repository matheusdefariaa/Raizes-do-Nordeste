# Rede Raízes do Nordeste

API REST para gerenciamento de uma rede de lanchonetes em expansão, desenvolvida como projeto acadêmico na trilha Back-end. O sistema permite administrar unidades, usuários, produtos, estoque, pedidos e pagamentos, oferecendo suporte a diferentes canais de atendimento.

## Objetivo

Desenvolver uma solução backend para centralizar as operações da Rede Raízes do Nordeste, permitindo o gerenciamento das unidades, controle de estoque, processamento de pedidos e acompanhamento de pagamentos.

## Tecnologias utilizadas

- **Python 3.14** — linguagem de programação.
- **FastAPI** — desenvolvimento da API REST.
- **SQLite** — banco de dados relacional.
- **SQLAlchemy** — mapeamento objeto-relacional (ORM).
- **Alembic** — gerenciamento de migrações do banco de dados.
- **Pydantic** — validação e estruturação de dados.
- **Pydantic Settings** — gerenciamento de configurações.
- **JWT** — autenticação baseada em tokens.
- **Argon2** — proteção de senhas por hash.
- **Pytest** — testes automatizados.
- **HTTPX** — cliente para testes da API.

## Funcionalidades implementadas

### Autenticação e usuários

- Cadastro público de usuários com perfil CLIENTE.
- Cadastro de funcionários por administrador.
- Criação do primeiro administrador por comando CLI.
- Login com e-mail e senha.
- Autenticação por token JWT.
- Proteção de rotas.
- Controle de acesso baseado em perfis: ADMIN, GERENTE, COZINHA, ATENDENTE e CLIENTE.
- Consulta dos dados do usuário autenticado.

### Unidades

- Cadastro de unidades, restrito a usuários com perfil ADMIN.
- Consulta de unidades cadastradas.
- Armazenamento de informações como nome, cidade, estado e endereço.

### Produtos e estoque

- Cadastro de produtos.
- Consulta de produtos.
- Atualização de estoque.
- Validação de disponibilidade antes da criação de pedidos.
- Registro de movimentações de estoque.
- Devolução de estoque em situações aplicáveis.

### Pedidos

- Criação de pedidos vinculados a uma unidade.
- Associação de produtos e quantidades.
- Identificação do canal de origem do pedido.
- Consulta de pedidos.
- Atualização de status.
- Cancelamento de pedidos.
- Validação de estoque considerando quantidades repetidas do mesmo produto.
- Proteção contra operações duplicadas de pagamento e cancelamento.

### Pagamentos

- Simulação de integração com serviço externo de pagamento.
- Processamento de pagamentos aprovados e recusados.
- Registro das informações de pagamento.
- Tratamento de pagamentos recusados e devolução de estoque.

**Observação:** o processamento de pagamentos é simulado. Não existe integração efetiva com um provedor financeiro externo.

### Auditoria

- Registro de operações relevantes do sistema.
- Armazenamento do usuário responsável pela operação, quando disponível.
- Registro da entidade afetada e de seus detalhes.
- Consulta dos registros de auditoria por usuários com perfil ADMIN ou GERENTE.
- Limitação da quantidade de registros retornados.

## Canais de atendimento

O sistema permite identificar a origem de cada pedido:

| Canal | Descrição |
|---|---|
| APP | Aplicativo |
| TOTEM | Terminal de autoatendimento |
| BALCAO | Atendimento presencial |
| PICKUP | Retirada no estabelecimento |
| WEB | Pedido pelo site |

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
│   ├── cli/
│   │   ├── __init__.py
│   │   └── __main__.py
│   ├── core/
│   │   └── config.py
│   ├── infrastructure/
│   │   └── database/
│   │       ├── models/
│   │       │   ├── unidade.py
│   │       │   └── operacao.py
│   │       └── connection.py
│   └── main.py
├── migrations/
│   ├── versions/
│   └── env.py
├── tests/
│   └── test_api.py
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

## Como executar o projeto

### 1. Clonar o repositório

```bash
git clone git@github.com:matheusdefariaa/Raizes-do-Nordeste.git
cd Trabalho
```

Substitua `URL_DO_REPOSITORIO` pelo endereço real do repositório.

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

### 5. Configurar as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto, utilizando o `.env.example` como referência.

Gere uma chave secreta com:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Configure o arquivo `.env`:

```env
SECRET_KEY=sua_chave_secreta
DATABASE_URL=sqlite:///./raizes.db
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Substitua `sua_chave_secreta` pelo valor gerado.

Não compartilhe o arquivo `.env` nem envie suas credenciais ao repositório.

### 6. Executar as migrações

```bash
alembic upgrade head
```

Esse comando cria ou atualiza a estrutura do banco de dados conforme as migrações disponíveis.

### 7. Criar o primeiro administrador

Em uma instalação nova, execute:

```bash
python -m app.cli
```

O comando solicitará nome, e-mail e senha para criar o primeiro usuário com perfil ADMIN.

A senha será armazenada utilizando hash Argon2.

O comando impede a criação de outro administrador inicial quando já existe um usuário com esse perfil.

### 8. Iniciar a aplicação

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

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/` | Informações iniciais da API |
| GET | `/health` | Verificação de disponibilidade |
| POST | `/auth/usuarios` | Cadastro público de usuário |
| POST | `/auth/usuarios/funcionarios` | Cadastro de funcionário por ADMIN |
| POST | `/auth/login` | Autenticação |
| GET | `/auth/me` | Consulta do usuário autenticado |
| POST | `/unidades/` | Cadastro de unidade (ADMIN) |
| GET | `/unidades/` | Listagem de unidades |
| GET | `/unidades/{unidade_id}` | Consulta de unidade específica |
| POST | `/produtos` | Cadastro de produto |
| GET | `/produtos` | Listagem de produtos |
| PATCH | `/produtos/{produto_id}/estoque` | Atualização de estoque |
| POST | `/pedidos` | Criação de pedido |
| GET | `/pedidos` | Consulta de pedidos |
| GET | `/pedidos/{pedido_id}` | Consulta de pedido específico |
| POST | `/pedidos/{pedido_id}/pagamento` | Processamento de pagamento |
| PATCH | `/pedidos/{pedido_id}/status` | Atualização de status |
| POST | `/pedidos/{pedido_id}/cancelar` | Cancelamento de pedido |
| GET | `/auditoria` | Consulta dos registros de auditoria |

**Observação:** os endpoints protegidos exigem autenticação por token JWT. Os perfis de usuário determinam quais operações podem ser realizadas.

## Testes automatizados

O projeto utiliza Pytest e FastAPI TestClient para verificar o funcionamento dos principais recursos da aplicação.

Para executar os testes, utilize:

```bash
python -m pytest -v
```

### Resultados dos testes

**25 testes automatizados aprovados**, cobrindo:

- Cadastro e autenticação de usuários.
- Consulta de usuário autenticado.
- Cadastro e listagem de produtos.
- Criação e consulta de pedidos.
- Processamento de pagamentos.
- Fluxo de atualização de pedidos.
- Cancelamento de pedidos.
- Devolução de estoque.
- Tentativas de acesso sem autenticação.
- Controle de permissões por perfil.
- Validação de produtos inexistentes.
- Validação de estoque insuficiente.
- Validação de cadastro de usuários.
- Validação de produtos repetidos em um mesmo pedido.
- Prevenção de pagamentos duplicados.
- Prevenção de cancelamentos duplicados.
- Consulta de auditoria por administrador e gerente.
- Restrição de acesso à auditoria para clientes.
- Cadastro de unidades por administrador.
- Restrição de cadastro de unidades para clientes e gerentes.

## Segurança

O projeto implementa mecanismos básicos de segurança, incluindo:

- Senhas armazenadas utilizando hash Argon2.
- Autenticação baseada em JWT.
- Controle de acesso por perfil.
- Proteção de endpoints que exigem autenticação.
- Validação de dados de entrada.
- Configurações sensíveis armazenadas em variáveis de ambiente.
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

## Limitações e evoluções futuras

Embora a API implemente as principais operações de gerenciamento, alguns recursos do cenário de negócio ainda podem ser desenvolvidos em etapas futuras:

- Integração real com provedores externos de pagamento.
- Programa de fidelização e acúmulo de pontos.
- Campanhas promocionais e descontos progressivos.
- Recursos de consentimento, anonimização e gerenciamento de dados pessoais conforme a LGPD.
- Relatórios gerenciais consolidados por unidade e região.
- Testes específicos de desempenho e disponibilidade.
- Estratégias de escalabilidade e tolerância a falhas para ambientes de produção.

Essas funcionalidades fazem parte das possibilidades de evolução da solução e não devem ser confundidas com recursos já implementados.

## Considerações finais

O projeto demonstra a aplicação de conceitos de desenvolvimento backend, arquitetura de APIs REST, persistência de dados, autenticação, autorização, validação de informações e testes automatizados.

A solução foi desenvolvida com foco na organização das operações da Rede Raízes do Nordeste, buscando oferecer uma base funcional que possa ser expandida futuramente com novas funcionalidades e integrações.
