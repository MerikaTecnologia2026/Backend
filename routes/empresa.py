
import logging

from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    create_access_token
)
from models.empresa import Empresa
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from extensions import db
from models.usuario import Usuario
from services.empresa_service import EmpresaService
from exceptions.api_exception import BadRequest, NotFound

empresa_bp = Blueprint("empresa", __name__)

logger = logging.getLogger(__name__)


def obter_usuario():
    usuario_id = get_jwt_identity()

    usuario = db.session.get(Usuario, usuario_id)

    if not usuario:
        raise NotFound("Usuário não encontrado.")

    return usuario


def obter_empresa_id():
    usuario = obter_usuario()

    if not usuario.empresa_id:
        raise NotFound(
            "Usuário não possui empresa vinculada."
        )

    return usuario.empresa_id


def resposta_empresa(empresa):
    return {
        "id": empresa.id,
        "nome": empresa.nome,
        "cnpj": empresa.cnpj,
        "email": empresa.email,
        "telefone": empresa.telefone,
        "cidade": empresa.cidade,
        "estado": empresa.estado,
        "endereco": empresa.endereco,
        "cep": empresa.cep,
        "site": empresa.site,
        "instagram": empresa.instagram,
        "slogan": empresa.slogan,
        "logo": f"/empresa/logo" if empresa.logo else None,
    }


def tratar_erro(erro):
    if isinstance(erro, NotFound):
        return jsonify({"erro": str(erro)}), 404

    if isinstance(erro, (BadRequest, ValueError)):
        return jsonify({"erro": str(erro)}), 400

    if isinstance(erro, IntegrityError):
        db.session.rollback()
        logger.exception("Erro de integridade no banco")

        return jsonify({
            "erro": "Já existe um registro com esses dados."
        }), 409

    if isinstance(erro, SQLAlchemyError):
        db.session.rollback()
        logger.exception("Erro no banco de dados")

        return jsonify({
            "erro": "Erro ao acessar o banco de dados."
        }), 500

    db.session.rollback()
    logger.exception("Erro inesperado na empresa")

    return jsonify({
        "erro": "Erro interno do servidor."
    }), 500


@empresa_bp.route("/register", methods=["POST"])
@jwt_required()
def register():
    try:
        usuario = obter_usuario()
        dados = request.get_json(silent=True)

        if not usuario.ativo:
            return jsonify({
                "erro": "Usuário desativado."
            }), 403

        if not isinstance(dados, dict):
            raise BadRequest("Envie um JSON válido.")

        empresa = EmpresaService.registrar(
            dados,
            usuario.id
        )

        # Gerar novo token com a empresa vinculada
        novo_token = create_access_token(
            identity=str(usuario.id),
            additional_claims={
                "empresa_id": empresa.id,
                "tipo": usuario.tipo
            }
        )

        return jsonify({
            "mensagem": "Empresa cadastrada com sucesso.",
            "id": empresa.id,
            "access_token": novo_token
        }), 201

    except Exception as erro:
        return tratar_erro(erro)


@empresa_bp.route("/", methods=["GET"])
@jwt_required()
def listar():
    try:
        empresa_id = obter_empresa_id()

        empresa = EmpresaService.listar(empresa_id)

        return jsonify(resposta_empresa(empresa)), 200

    except Exception as erro:
        return tratar_erro(erro)


@empresa_bp.route("/", methods=["PUT"])
@jwt_required()
def atualizar():
    try:
        empresa_id = obter_empresa_id()
        dados = request.get_json(silent=True)

        if not isinstance(dados, dict):
            raise BadRequest("Envie um JSON válido.")

        empresa = EmpresaService.atualizar(
            empresa_id,
            dados
        )

        return jsonify({
            "mensagem": "Empresa atualizada com sucesso.",
            "empresa": resposta_empresa(empresa)
        }), 200

    except Exception as erro:
        return tratar_erro(erro)


@empresa_bp.route("/", methods=["DELETE"])
@jwt_required()
def deletar():
    try:
        empresa_id = obter_empresa_id()

        EmpresaService.deletar(empresa_id)

        return jsonify({
            "mensagem": "Empresa excluída com sucesso."
        }), 200

    except Exception as erro:
        return tratar_erro(erro)

@empresa_bp.route("/logo", methods=["POST"])
@jwt_required()
def salvar_logo():
    try:
        empresa_id = obter_empresa_id()

        imagem = request.files.get("logo")

        if not imagem:
            raise BadRequest("Selecione uma imagem.")

        if imagem.mimetype not in ("image/png", "image/jpeg", "image/webp"):
            raise BadRequest("Formato inválido. Use PNG, JPG ou WEBP.")

        conteudo = imagem.read(2 * 1024 * 1024 + 1)

        if len(conteudo) > 2 * 1024 * 1024:
            raise BadRequest("A imagem deve ter no máximo 2 MB.")

        if not conteudo:
            raise BadRequest("A imagem está vazia.")

        empresa = db.session.get(Empresa, empresa_id)

        if not empresa:
            raise NotFound("Empresa não encontrada.")

        empresa.logo = conteudo

        db.session.commit()

        return jsonify({
            "mensagem": "Logomarca salva com sucesso."
        }), 200

    except Exception as erro:
        return tratar_erro(erro)


@empresa_bp.route("/logo", methods=["GET"])
@jwt_required()
def visualizar_logo():
    try:
        empresa_id = obter_empresa_id()

        empresa = db.session.get(Empresa, empresa_id)

        if not empresa or not empresa.logo:
            raise NotFound("Logomarca não encontrada.")

        imagem = bytes(empresa.logo)

        if imagem.startswith(b"\x89PNG\r\n\x1a\n"):
            tipo = "image/png"
        elif imagem.startswith(b"\xff\xd8\xff"):
            tipo = "image/jpeg"
        elif imagem.startswith(b"RIFF") and imagem[8:12] == b"WEBP":
            tipo = "image/webp"
        else:
            raise BadRequest("Formato da imagem armazenada inválido.")

        return Response(imagem, mimetype=tipo)

    except Exception as erro:
        return tratar_erro(erro)
