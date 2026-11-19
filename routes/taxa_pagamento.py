
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from services.taxa_pagamento_service import TaxaPagamentoService


taxa_pagamento_bp = Blueprint(
    "taxa_pagamento",
    __name__
)


# ==========================================
# CONFIGURAÇÕES DO ANOTA
# ==========================================

@taxa_pagamento_bp.route(
    "/configuracoes",
    methods=["GET"]
)
@jwt_required()
def listar_configuracoes():
    empresa_id = get_jwt().get("empresa_id")

    taxas = TaxaPagamentoService.listar_configuracoes(
        empresa_id
    )

    return jsonify(taxas), 200


@taxa_pagamento_bp.route(
    "/configuracoes",
    methods=["PUT"]
)
@jwt_required()
def salvar_configuracoes():
    empresa_id = get_jwt().get("empresa_id")
    dados = request.get_json(silent=True)

    taxas = TaxaPagamentoService.salvar_configuracoes(
        dados,
        empresa_id
    )

    return jsonify({
        "mensagem": "Taxas atualizadas com sucesso",
        "taxas": taxas
    }), 200


# ==========================================
# CADASTRAR TAXA
# ==========================================

@taxa_pagamento_bp.route(
    "/",
    methods=["POST"]
)
@jwt_required()
def registrar():
    dados = request.get_json(silent=True)
    empresa_id = get_jwt().get("empresa_id")

    taxa = TaxaPagamentoService.registrar(
        dados,
        empresa_id
    )

    return jsonify({
        "mensagem": "Taxa cadastrada com sucesso",
        "taxa": taxa
    }), 201


# ==========================================
# LISTAR TAXAS
# ==========================================

@taxa_pagamento_bp.route(
    "/",
    methods=["GET"]
)
@jwt_required()
def listar():
    empresa_id = get_jwt().get("empresa_id")

    taxas = TaxaPagamentoService.listar(
        empresa_id
    )

    return jsonify(taxas), 200


# ==========================================
# BUSCAR TAXA
# ==========================================

@taxa_pagamento_bp.route(
    "/<int:taxa_id>",
    methods=["GET"]
)
@jwt_required()
def buscar_por_id(taxa_id):
    empresa_id = get_jwt().get("empresa_id")

    taxa = TaxaPagamentoService.buscar_por_id(
        taxa_id,
        empresa_id
    )

    return jsonify(taxa), 200


# ==========================================
# ATUALIZAR TAXA
# ==========================================

@taxa_pagamento_bp.route(
    "/<int:taxa_id>",
    methods=["PUT"]
)
@jwt_required()
def atualizar(taxa_id):
    dados = request.get_json(silent=True)
    empresa_id = get_jwt().get("empresa_id")

    taxa = TaxaPagamentoService.atualizar(
        taxa_id,
        dados,
        empresa_id
    )

    return jsonify({
        "mensagem": "Taxa atualizada com sucesso",
        "taxa": taxa
    }), 200


# ==========================================
# EXCLUIR TAXA
# ==========================================

@taxa_pagamento_bp.route(
    "/<int:taxa_id>",
    methods=["DELETE"]
)
@jwt_required()
def excluir(taxa_id):
    empresa_id = get_jwt().get("empresa_id")

    TaxaPagamentoService.excluir(
        taxa_id,
        empresa_id
    )

    return jsonify({
        "mensagem": "Taxa excluída com sucesso"
    }), 200
