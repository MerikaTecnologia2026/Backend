
import os
import threading
from faster_whisper import WhisperModel


class AssistenteVozService:
    _modelo = None
    _lock = threading.Lock()

    @classmethod
    def obter_modelo(cls):
        if cls._modelo is None:
            with cls._lock:
                if cls._modelo is None:
                    cls._modelo = WhisperModel(
                        "tiny",
                        device="cpu",
                        compute_type="int8",
                        cpu_threads=2,
                        num_workers=1,
                    )

        return cls._modelo

    @classmethod
    def transcrever(cls, caminho_audio):
        if not os.path.isfile(caminho_audio):
            raise FileNotFoundError("Arquivo de áudio não encontrado.")

        modelo = cls.obter_modelo()

        segmentos, _ = modelo.transcribe(
            caminho_audio,
            language="pt",
            beam_size=1,
            vad_filter=False,
        )

        texto = " ".join(
            segmento.text.strip()
            for segmento in segmentos
        ).strip()

        return texto
