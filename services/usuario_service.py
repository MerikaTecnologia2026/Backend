


from exceptions.api_exception import BadRequest
from werkzeug.security import generate_password_hash, check_password_hash

from models.usuario import Usuario

from extensions import db


class UsuarioService:

    @staticmethod
    def registrar(dados, empresa_id):

        if not dados.get("nome"):
            raise BadRequest("Nome é obrigatório")

        if not dados.get("email"):
            raise BadRequest("E-mail é obrigatório")

        if not dados.get("senha"):
            raise BadRequest("Senha é obrigatória")

        usuario_existente = Usuario.query.filter_by(
            email=dados["email"]
        ).first()

        if usuario_existente:
            raise BadRequest("E-mail já cadastrado")

        usuario = Usuario(
            empresa_id=empresa_id,
            nome=dados["nome"],
            email=dados["email"],
            senha_hash=generate_password_hash(
                dados["senha"]
            ),
            tipo=dados.get("tipo", "USUARIO")
        )

        try:
            db.session.add(usuario)
            db.session.commit()

            return usuario

        except Exception:
            db.session.rollback()

            raise BadRequest(
                "Não foi possível cadastrar o usuário."
            )

    @staticmethod
    def buscar_por_id(usuario_id):

        usuario = Usuario.query.get(usuario_id)

        if not usuario:
            raise ValueError(
                "Usuário não encontrado."
            )

        return usuario

    
    @staticmethod
    def atualizar(usuario_id, dados):

        usuario = db.session.get(Usuario, usuario_id)

        if not usuario:
            raise ValueError("Usuário não encontrado.")

        if not isinstance(dados, dict):
            raise BadRequest("Dados inválidos.")

        nome = str(dados.get("nome") or "").strip()
        email = str(dados.get("email") or "").strip().lower()

        telefone = "".join(
            c for c in str(dados.get("telefone") or "")
            if c.isdigit()
        )

        cpf = "".join(
            c for c in str(dados.get("cpf") or "")
            if c.isdigit()
        )

        if not nome:
            raise BadRequest("Nome é obrigatório.")

        if not email:
            raise BadRequest("E-mail é obrigatório.")

        if cpf and len(cpf) != 11:
            raise BadRequest("CPF deve conter 11 números.")

        if telefone and len(telefone) not in (10, 11):
            raise BadRequest("Telefone inválido.")

        outro_usuario = Usuario.query.filter(
            Usuario.email == email,
            Usuario.id != usuario.id
        ).first()

        if outro_usuario:
            raise BadRequest("E-mail já cadastrado.")

        if cpf:
            cpf_existente = Usuario.query.filter(
                Usuario.cpf == cpf,
                Usuario.id != usuario.id
            ).first()

            if cpf_existente:
                raise BadRequest("CPF já cadastrado.")

        usuario.nome = nome
        usuario.email = email
        usuario.telefone = telefone or None
        usuario.cpf = cpf or None

        try:
            db.session.commit()
            return usuario

        except Exception:
            db.session.rollback()
            raise


    @staticmethod
    def alterar_senha(usuario_id, dados):

        usuario = db.session.get(Usuario, usuario_id)

        if not usuario:
            raise ValueError("Usuário não encontrado.")

        if not isinstance(dados, dict):
            raise BadRequest("Dados inválidos.")

        senha_atual = dados.get("senha_atual")
        nova_senha = dados.get("nova_senha")

        if not isinstance(senha_atual, str) or not senha_atual:
            raise BadRequest("Informe sua senha atual.")

        if not isinstance(nova_senha, str) or not nova_senha:
            raise BadRequest("Informe a nova senha.")

        if not check_password_hash(usuario.senha_hash, senha_atual):
            raise BadRequest("Senha atual incorreta.")

        if len(nova_senha) < 8:
            raise BadRequest(
                "A nova senha deve ter pelo menos 8 caracteres."
            )

        if senha_atual == nova_senha:
            raise BadRequest(
                "A nova senha deve ser diferente da senha atual."
            )

        usuario.senha_hash = generate_password_hash(nova_senha)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return True

