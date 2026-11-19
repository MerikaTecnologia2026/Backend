from flask import Blueprint, request, jsonify
from services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    dados = request.get_json()

    try:
        resultado = AuthService.login(dados)

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 400

@auth_bp.route("/register", methods=["POST"])
def register():
    dados = request.get_json()

    try:
        usuario = AuthService.register(dados)

        return jsonify({
            "mensagem": "Usuário cadastrado com sucesso.",
            "id": usuario.id
        }), 201

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 400