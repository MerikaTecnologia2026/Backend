from flask import jsonify
from werkzeug.exceptions import HTTPException
from exceptions.api_exception import ApiException


def register_error_handlers(app):

    @app.errorhandler(ApiException)
    def handle_api_exception(e):
        return jsonify({
            "erro": e.mensagem
        }), e.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({
            "erro": e.description
        }), e.code

    @app.errorhandler(Exception)
    def handle_internal_error(e):
        import traceback

        traceback.print_exc()

        return jsonify({
            "erro": "Erro interno do servidor."
        }), 500