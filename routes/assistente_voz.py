import os
import tempfile

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from services.assistente_voz_service import AssistenteVozService


assistente_voz_bp = Blueprint("assistente_voz", __name__)


@assistente_voz_bp.route("/transcrever", methods=["POST"])
@jwt_required()
def transcrever():

    caminho_audio = None

    try:
        if "audio" not in request.files:
            return jsonify({
                "erro": "Nenhum áudio foi enviado."
            }), 400

        audio = request.files["audio"]

        if not audio.filename:
            return jsonify({
                "erro": "Arquivo de áudio inválido."
            }), 400

        extensao = os.path.splitext(audio.filename)[1].lower()

        extensoes_permitidas = {
            ".m4a", ".mp3", ".wav", ".ogg", ".webm"
        }

        if extensao not in extensoes_permitidas:
            return jsonify({
                "erro": "Formato de áudio não permitido."
            }), 400

        audio.stream.seek(0, os.SEEK_END)
        tamanho = audio.stream.tell()
        audio.stream.seek(0)

        if tamanho == 0:
            return jsonify({
                "erro": "O áudio está vazio."
            }), 400

        if tamanho > 10 * 1024 * 1024:
            return jsonify({
                "erro": "O áudio deve ter até 10 MB."
            }), 413

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extensao
        ) as arquivo:
            caminho_audio = arquivo.name
            audio.save(arquivo)

        texto = AssistenteVozService.transcrever(
            caminho_audio
        )

        if not texto:
            return jsonify({
                "erro": "Não foi possível identificar a fala."
            }), 422

        return jsonify({
            "mensagem": "Áudio transcrito com sucesso.",
            "texto": texto
        }), 200

    except Exception:
        current_app.logger.exception(
            "Erro ao transcrever áudio"
        )

        return jsonify({
            "erro": "Não foi possível processar o áudio."
        }), 500

    finally:
        if caminho_audio and os.path.exists(caminho_audio):
            os.remove(caminho_audio)