
import logging

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
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
        "logo": empresa.logo,
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

        if not isinstance(dados, dict):
            raise BadRequest("Envie um JSON válido.")

        empresa = EmpresaService.registrar(
            dados,
            usuario.id
        )

        return jsonify({
            "mensagem": "Empresa cadastrada com sucesso.",
            "id": empresa.id
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
