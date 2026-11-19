
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from services.despesa_service import DespesaService


despesa_bp = Blueprint("despesa", __name__)


def despesa_to_dict(despesa):
    return {
        "id": despesa.id,
        "empresa_id": despesa.empresa_id,
        "categoria_id": despesa.categoria_id,
        "recorrencia_id": despesa.recorrencia_id,
        "numero_parcela": despesa.numero_parcela,
        "nome": despesa.nome,
        "descricao": despesa.descricao,
        "valor": (
            str(despesa.valor)
            if despesa.valor is not None
            else "0.00"
        ),
        "data_vencimento": (
            despesa.data_vencimento.isoformat()
            if despesa.data_vencimento
            else None
        ),
        "data_pagamento": (
            despesa.data_pagamento.isoformat()
            if despesa.data_pagamento
            else None
        ),
        "status": despesa.status,
        "criado_em": (
            despesa.criado_em.isoformat()
            if despesa.criado_em
            else None
        ),
        "atualizado_em": (
            despesa.atualizado_em.isoformat()
            if despesa.atualizado_em
            else None
        ),
    }


def obter_empresa_id():
    claims = get_jwt()
    empresa_id = claims.get("empresa_id")

    if empresa_id is None:
        return None

    return empresa_id



@despesa_bp.route(
    "/", methods=["POST"], strict_slashes=False
)
@jwt_required()
def registrar():
    dados = request.get_json(silent=True)

    empresa_id = obter_empresa_id()

    if empresa_id is None:
        return jsonify({
            "mensagem": "Empresa não identificada"
        }), 403

    # Categoria obrigatória
    if not isinstance(dados, dict):
        return jsonify({
            "mensagem": "Dados da despesa inválidos."
        }), 400

    categoria_id = dados.get("categoria_id")

    if categoria_id is None or categoria_id == "":
        return jsonify({
            "mensagem": "Selecione uma categoria."
        }), 400

    resultado = DespesaService.registrar(
        dados, empresa_id
    )

    if isinstance(resultado, list):
        return jsonify({
            "mensagem": (
                "Despesas recorrentes cadastradas "
                "com sucesso"
            ),
            "recorrencia_id": (
                resultado[0].recorrencia_id
                if resultado else None
            ),
            "quantidade": len(resultado),
            "despesas": [
                despesa_to_dict(despesa)
                for despesa in resultado
            ],
        }), 201

    return jsonify({
        "mensagem": "Despesa cadastrada com sucesso",
        "despesa": despesa_to_dict(resultado),
    }), 201

@despesa_bp.route(
    "/", methods=["GET"], strict_slashes=False
)
@jwt_required()
def listar():
    empresa_id = obter_empresa_id()

    if empresa_id is None:
        return jsonify({
            "mensagem": "Empresa não identificada"
        }), 403

    despesas = DespesaService.listar(empresa_id)

    return jsonify([
        despesa_to_dict(despesa)
        for despesa in despesas
    ]), 200


@despesa_bp.route(
    "/<int:despesa_id>", methods=["GET"]
)
@jwt_required()
def buscar(despesa_id):
    empresa_id = obter_empresa_id()

    if empresa_id is None:
        return jsonify({
            "mensagem": "Empresa não identificada"
        }), 403

    despesa = DespesaService.buscar_por_id(
        despesa_id, empresa_id
    )

    return jsonify(
        despesa_to_dict(despesa)
    ), 200


@despesa_bp.route(
    "/<int:despesa_id>", methods=["PUT"]
)
@jwt_required()
def atualizar(despesa_id):
    dados = request.get_json(silent=True)

    empresa_id = obter_empresa_id()

    if empresa_id is None:
        return jsonify({
            "mensagem": "Empresa não identificada"
        }), 403

    despesa = DespesaService.atualizar(
        despesa_id, dados, empresa_id
    )

    return jsonify({
        "mensagem": "Despesa atualizada com sucesso",
        "despesa": despesa_to_dict(despesa),
    }), 200


@despesa_bp.route(
    "/<int:despesa_id>", methods=["DELETE"]
)
@jwt_required()
def excluir(despesa_id):
    empresa_id = obter_empresa_id()

    if empresa_id is None:
        return jsonify({
            "mensagem": "Empresa não identificada"
        }), 403

    DespesaService.excluir(
        despesa_id, empresa_id
    )

    return jsonify({
        "mensagem": "Despesa excluída com sucesso"
    }), 200
