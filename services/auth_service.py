from datetime import datetime

from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash
from email_validator import validate_email, EmailNotValidError

from extensions import db
from models.usuario import Usuario
from exceptions.api_exception import BadRequest, Unauthorized


# ========================================
# VALIDAÇÃO DE SENHA
# ========================================

def validar_senha(senha):

    if not isinstance(senha, str) or len(senha) < 6:
        raise BadRequest(
            "A senha deve ter no mínimo 6 caracteres."
        )

    sequencias = [
        "0123456789",
        "9876543210",
        "abcdefghijklmnopqrstuvwxyz",
        "zyxwvutsrqponmlkjihgfedcba"
    ]

    senha_normalizada = senha.lower()

    for sequencia in sequencias:
        for i in range(len(sequencia) - 5):
            trecho = sequencia[i:i + 6]

            if trecho in senha_normalizada:
                raise BadRequest(
                    "A senha não pode conter sequências "
                   
                )

    if len(set(senha)) == 1:
        raise BadRequest(
            "A senha não pode conter apenas caracteres repetidos."
        )

    senhas_comuns = [
        "123123",
        "121212",
        "senha123",
        "password",
        "qwerty",
        "abc123"
    ]

    if senha_normalizada in senhas_comuns:
        raise BadRequest(
            "Senha muito comum. Escolha uma senha mais segura."
        )


# ========================================
# VALIDAÇÃO DE E-MAIL
# ========================================

def validar_email(email):

    if not isinstance(email, str):
        raise BadRequest("Informe um e-mail válido.")

    try:
        resultado = validate_email(
            email.strip().lower(),
            check_deliverability=True
        )

        return resultado.normalized

    except EmailNotValidError:
        raise BadRequest(
            "Informe um endereço de e-mail válido."
        )


# ========================================
# SERVIÇO DE AUTENTICAÇÃO
# ========================================

class AuthService:

    @staticmethod
    def login(dados):

        usuario = Usuario.query.filter_by(
            email=dados["email"].strip().lower()
        ).first()

        if not usuario:
            raise Unauthorized("E-mail ou senha inválidos.")

        if not usuario.ativo:
            raise Unauthorized("Usuário desativado.")

        if usuario.empresa and usuario.empresa.deletado_em is not None:
            raise Unauthorized("Empresa desativada.")

        if not check_password_hash(
            usuario.senha_hash,
            dados["senha"]
        ):
            raise Unauthorized("E-mail ou senha inválidos.")

        token = create_access_token(
            identity=str(usuario.id),
            additional_claims={
                "empresa_id": usuario.empresa_id,
                "tipo": usuario.tipo
            }
        )

        usuario.ultimo_login = datetime.utcnow()

        db.session.commit()

        return {
            "access_token": token,
            "usuario": {
                "id": usuario.id,
                "nome": usuario.nome
            }
        }

    # ========================================
    # CADASTRO DE USUÁRIO
    # ========================================

    @staticmethod
    def register(dados):

        if not dados.get("nome"):
            raise BadRequest("Nome é obrigatório.")

        if not dados.get("email"):
            raise BadRequest("E-mail é obrigatório.")

        if not dados.get("senha"):
            raise BadRequest("Senha é obrigatória.")

        # Validar e-mail
        email_validado = validar_email(dados["email"])

        # Validar senha
        validar_senha(dados["senha"])

        usuario_existente = Usuario.query.filter_by(
            email=email_validado
        ).first()

        if usuario_existente:
            raise BadRequest("E-mail já cadastrado.")

        usuario = Usuario(
            nome=dados["nome"].strip(),
            email=email_validado,
            senha_hash=generate_password_hash(dados["senha"]),
            tipo="usuario",
            ativo=True,
            empresa_id=None
        )

        try:
            db.session.add(usuario)
            db.session.commit()

            return usuario

        except Exception:
            db.session.rollback()
            raise