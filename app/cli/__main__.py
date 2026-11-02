
from getpass import getpass

from sqlalchemy.exc import IntegrityError

from app.api.dependencies.auth import hash_senha
from app.infrastructure.database.connection import SessionLocal
from app.infrastructure.database.models.operacao import Usuario


def criar_admin():
    db = SessionLocal()

    try:
        # Verifica se já existe um administrador
        administrador = db.query(Usuario).filter(
            Usuario.perfil == "ADMIN"
        ).first()

        if administrador:
            print("\nJá existe um administrador cadastrado.")
            print("Utilize esse usuário para cadastrar outros funcionários.")
            return 1

        print("\n=== Rede Raízes do Nordeste ===")
        print("Criação do administrador inicial\n")

        nome = input("Nome: ").strip()
        email = input("E-mail: ").strip().lower()
        senha = getpass("Senha: ")
        confirmacao = getpass("Confirme a senha: ")

        if not nome or not email:
            print("\nNome e e-mail são obrigatórios.")
            return 1

        if len(senha) < 8:
            print("\nA senha deve ter pelo menos 8 caracteres.")
            return 1

        if senha != confirmacao:
            print("\nAs senhas não coincidem.")
            return 1

        novo_admin = Usuario(
            nome=nome,
            email=email,
            senha_hash=hash_senha(senha),
            perfil="ADMIN",
        )

        db.add(novo_admin)
        db.commit()

        print("\nAdministrador criado com sucesso!")
        print(f"E-mail: {email}")

        return 0

    except IntegrityError:
        db.rollback()
        print("\nErro: este e-mail já está cadastrado.")
        return 1

    except Exception as erro:
        db.rollback()
        print(f"\nErro ao criar administrador: {erro}")
        return 1

    finally:
        db.close()


def main():
    try:
        raise SystemExit(criar_admin())
    except KeyboardInterrupt:
        print("\nOperação cancelada.")
        raise SystemExit(130)


if __name__ == "__main__":
    main()

