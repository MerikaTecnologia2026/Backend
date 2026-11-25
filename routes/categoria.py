from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.categoria_service import CategoriaService
from models.usuario import Usuario
from extensions import db
from exceptions.api_exception import NotFound


categoria = Blueprint("categoria", __name__)


# ========================================
# IDENTIFICAR EMPRESA
# ========================================

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


# ========================================
# SERIALIZAR CATEGORIA
# ========================================

def categoria_json(item):

    return {
        "id": item.id,
        "nome": item.nome,
        "tipo": item.tipo
    }


# ========================================
# OBTER OU CADASTRAR CATEGORIA
# ========================================

@categoria.route("/register", methods=["POST"])
@jwt_required()
def register():

    dados = request.get_json(silent=True)
    empresa_id = obter_empresa_id()

    item, criada = CategoriaService.obter_ou_criar(
        dados,
        empresa_id
    )

    return jsonify({
        "mensagem": (
            "Categoria cadastrada com sucesso."
            if criada
            else "Categoria já cadastrada."
        ),
        "criada": criada,
        "id": item.id,
        "categoria": categoria_json(item)
    }), 201 if criada else 200


# ========================================
# LISTAR CATEGORIAS
# ========================================

@categoria.route("/", methods=["GET"])
@jwt_required()
def listar():

    empresa_id = obter_empresa_id()

    tipo = request.args.get("tipo")

    categorias = CategoriaService.listar(
        empresa_id,
        tipo
    )

    return jsonify([
        categoria_json(item)
        for item in categorias
    ]), 200


# ========================================
# BUSCAR CATEGORIA POR ID
# ========================================

@categoria.route("/<int:id>", methods=["GET"])
@jwt_required()
def buscar_categoria(id):

    empresa_id = obter_empresa_id()

    item = CategoriaService.buscar_por_id(
        id,
        empresa_id
    )

    return jsonify(
        categoria_json(item)
    ), 200


# ========================================
# ATUALIZAR CATEGORIA
# ========================================

@categoria.route("/<int:id>", methods=["PUT"])
@jwt_required()
def atualizar(id):

    dados = request.get_json(silent=True)
    empresa_id = obter_empresa_id()

    item = CategoriaService.atualizar(
        id,
        dados,
        empresa_id
    )

    return jsonify({
        "mensagem": "Categoria atualizada com sucesso.",
        "categoria": categoria_json(item)
    }), 200


# ========================================
# EXCLUIR CATEGORIA
# ========================================

@categoria.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def deletar(id):

    empresa_id = obter_empresa_id()

    CategoriaService.deletar(
        id,
        empresa_id
    )

    return jsonify({
        "mensagem": "Categoria removida com sucesso."
    }), 200