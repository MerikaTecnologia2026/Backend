
import logging

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from extensions import db
from models.usuario import Usuario
from services.funcionario_service import FuncionarioService
from exceptions.api_exception import BadRequest, NotFound

funcionario_bp = Blueprint("funcionario", __name__)

logger = logging.getLogger(__name__)


def obter_empresa_id():
    usuario_id = get_jwt_identity()

    usuario = db.session.get(Usuario, usuario_id)

    if not usuario:
        raise NotFound("Usuário não encontrado.")

    if not usuario.empresa_id:
        raise NotFound(
            "Usuário não possui empresa vinculada."
        )

    return usuario.empresa_id


def resposta_funcionario(funcionario):
    return {
        "id": funcionario.id,
        "empresa_id": funcionario.empresa_id,
        "nome": funcionario.nome,
        "cargo": funcionario.cargo,
        "endereco": funcionario.endereco,
        "telefone": funcionario.telefone,
        "valor_salario": (
            str(funcionario.valor_salario)
            if funcionario.valor_salario is not None
            else None
        ),
        "data_admissao": (
            funcionario.data_admissao.isoformat()
            if funcionario.data_admissao
            else None
        ),
        "data_demissao": (
            funcionario.data_demissao.isoformat()
            if funcionario.data_demissao
            else None
        ),
        "status": funcionario.status,
    }


def tratar_erro(erro):
    if isinstance(erro, NotFound):
        return jsonify({"erro": str(erro)}), 404

    if isinstance(erro, (BadRequest, ValueError)):
        return jsonify({"erro": str(erro)}), 400

    if isinstance(erro, IntegrityError):
        db.session.rollback()
        logger.exception("Erro de integridade em funcionários")
        return jsonify({
            "erro": "Não foi possível salvar os dados do funcionário."
        }), 409

    if isinstance(erro, SQLAlchemyError):
        db.session.rollback()
        logger.exception("Erro no banco de funcionários")
        return jsonify({
            "erro": "Erro ao acessar o banco de dados."
        }), 500

    db.session.rollback()
    logger.exception("Erro inesperado em funcionários")
    return jsonify({
        "erro": "Erro interno do servidor."
    }), 500


@funcionario_bp.route("/", methods=["POST"])
@jwt_required()
def registrar():
    try:
        empresa_id = obter_empresa_id()
        dados = request.get_json(silent=True)

        if not isinstance(dados, dict):
            raise BadRequest("Envie um JSON válido.")

        funcionario = FuncionarioService.registrar(
            dados, empresa_id
        )

        return jsonify({
            "mensagem": "Funcionário cadastrado com sucesso.",
            "funcionario": resposta_funcionario(funcionario),
        }), 201

    except Exception as erro:
        return tratar_erro(erro)


@funcionario_bp.route("/", methods=["GET"])
@jwt_required()
def listar():
    try:
        empresa_id = obter_empresa_id()

        funcionarios = FuncionarioService.listar(empresa_id)

        return jsonify([
            resposta_funcionario(funcionario)
            for funcionario in funcionarios
        ]), 200

    except Exception as erro:
        return tratar_erro(erro)


@funcionario_bp.route("/<int:funcionario_id>", methods=["GET"])
@jwt_required()
def buscar(funcionario_id):
    try:
        empresa_id = obter_empresa_id()

        funcionario = FuncionarioService.buscar_por_id(
            funcionario_id, empresa_id
        )

        return jsonify(resposta_funcionario(funcionario)), 200

    except Exception as erro:
        return tratar_erro(erro)


@funcionario_bp.route("/<int:funcionario_id>", methods=["PUT"])
@jwt_required()
def atualizar(funcionario_id):
    try:
        empresa_id = obter_empresa_id()
        dados = request.get_json(silent=True)

        if not isinstance(dados, dict):
            raise BadRequest("Envie um JSON válido.")

        funcionario = FuncionarioService.atualizar(
            funcionario_id, dados, empresa_id
        )

        return jsonify({
            "mensagem": "Funcionário atualizado com sucesso.",
            "funcionario": resposta_funcionario(funcionario),
        }), 200

    except Exception as erro:
        return tratar_erro(erro)


@funcionario_bp.route("/<int:funcionario_id>", methods=["DELETE"])
@jwt_required()
def excluir(funcionario_id):
    try:
        empresa_id = obter_empresa_id()

        FuncionarioService.excluir(
            funcionario_id, empresa_id
        )

        return jsonify({
            "mensagem": "Funcionário excluído com sucesso."
        }), 200

    except Exception as erro:
        return tratar_erro(erro)
