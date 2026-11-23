class AssistenteVozService:

    _modelo = None

    @classmethod
    def obter_modelo(cls):
        if cls._modelo is None:
            from faster_whisper import WhisperModel

            cls._modelo = WhisperModel(
                "tiny",
                device="cpu",
                compute_type="int8"
            )

        return cls._modelo

    @classmethod
    def transcrever(cls, caminho_audio):
        modelo = cls.obter_modelo()

        segmentos, informacoes = modelo.transcribe(
            caminho_audio,
            language="pt",
            beam_size=1,
            vad_filter=True
        )

        texto = " ".join(
            segmento.text.strip()
            for segmento in segmentos
        ).strip()

        return texto