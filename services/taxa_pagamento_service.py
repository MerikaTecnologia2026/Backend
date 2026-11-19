
from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import IntegrityError

from exceptions.api_exception import BadRequest, NotFound
from extensions import db
from models.taxa_pagamento import TaxaPagamento
from models.forma_pagamento import FormaPagamento


class TaxaPagamentoService:

    FORMAS_PADRAO = {
        "cartao_credito": "Cartão de Crédito",
        "cartao_debito": "Cartão de Débito",
        "pix": "PIX",
        "dinheiro": "Dinheiro",
        "boleto": "Boleto",
    }

    # ==========================================
    # VALIDAÇÕES
    # ==========================================

    @staticmethod
    def _validar_empresa(empresa_id):
        if not empresa_id:
            raise BadRequest("Empresa não identificada")

    @staticmethod
    def _validar_percentual(valor):
        if isinstance(valor, bool) or not isinstance(
            valor, (str, int, float, Decimal)
        ):
            raise BadRequest("Percentual inválido")

        try:
            percentual = Decimal(
                str(valor).strip().replace(",", ".")
            )
        except InvalidOperation:
            raise BadRequest("Percentual inválido")

        if not percentual.is_finite():
            raise BadRequest("Percentual inválido")

        if percentual < 0 or percentual > 100:
            raise BadRequest(
                "O percentual deve estar entre 0 e 100"
            )

        if percentual != percentual.quantize(Decimal("0.01")):
            raise BadRequest(
                "O percentual aceita até duas casas decimais"
            )

        return percentual

    @staticmethod
    def _validar_parcelas(valor):
        if isinstance(valor, bool):
            raise BadRequest("Quantidade de parcelas inválida")

        try:
            parcelas = int(valor)
        except (TypeError, ValueError, OverflowError):
            raise BadRequest("Quantidade de parcelas inválida")

        if str(valor) != str(parcelas) or parcelas < 1:
            raise BadRequest(
                "Quantidade de parcelas deve ser maior que zero"
            )

        return parcelas

    @staticmethod
    def _buscar_modelo(taxa_id, empresa_id):
        TaxaPagamentoService._validar_empresa(empresa_id)

        taxa = (
            TaxaPagamento.query
            .join(FormaPagamento)
            .filter(
                TaxaPagamento.id == taxa_id,
                FormaPagamento.empresa_id == empresa_id
            )
            .first()
        )

        if not taxa:
            raise NotFound("Taxa de pagamento não encontrada")

        return taxa

    # ==========================================
    # CADASTRAR TAXA
    # ==========================================

    @staticmethod
    def registrar(dados, empresa_id):
        TaxaPagamentoService._validar_empresa(empresa_id)

        if not isinstance(dados, dict):
            raise BadRequest("Dados inválidos")

        forma_id = dados.get("forma_pagamento_id")

        if not forma_id:
            raise BadRequest(
                "Forma de pagamento é obrigatória"
            )

        parcelas = TaxaPagamentoService._validar_parcelas(
            dados.get("parcelas", 1)
        )

        percentual = TaxaPagamentoService._validar_percentual(
            dados.get("percentual", 0)
        )

        forma = FormaPagamento.query.filter_by(
            id=forma_id,
            empresa_id=empresa_id
        ).first()

        if not forma:
            raise NotFound(
                "Forma de pagamento não encontrada"
            )

        existente = TaxaPagamento.query.filter_by(
            forma_pagamento_id=forma.id,
            parcelas=parcelas
        ).first()

        if existente:
            raise BadRequest(
                "Já existe uma taxa para essa forma de pagamento "
                "e quantidade de parcelas"
            )

        taxa = TaxaPagamento(
            forma_pagamento_id=forma.id,
            parcelas=parcelas,
            percentual=percentual,
            ativo=True
        )

        try:
            db.session.add(taxa)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise BadRequest(
                "Já existe uma taxa com essa configuração"
            )

        return TaxaPagamentoService._to_dict(taxa)

    # ==========================================
    # LISTAR TAXAS
    # ==========================================

    @staticmethod
    def listar(empresa_id):
        TaxaPagamentoService._validar_empresa(empresa_id)

        taxas = (
            TaxaPagamento.query
            .join(FormaPagamento)
            .filter(
                FormaPagamento.empresa_id == empresa_id
            )
            .order_by(TaxaPagamento.id)
            .all()
        )

        return [
            TaxaPagamentoService._to_dict(taxa)
            for taxa in taxas
        ]

    # ==========================================
    # BUSCAR TAXA
    # ==========================================

    @staticmethod
    def buscar_por_id(taxa_id, empresa_id):
        taxa = TaxaPagamentoService._buscar_modelo(
            taxa_id, empresa_id
        )

        return TaxaPagamentoService._to_dict(taxa)

    # ==========================================
    # ATUALIZAR TAXA
    # ==========================================

    @staticmethod
    def atualizar(taxa_id, dados, empresa_id):
        if not isinstance(dados, dict):
            raise BadRequest("Dados inválidos")

        taxa = TaxaPagamentoService._buscar_modelo(
            taxa_id, empresa_id
        )

        parcelas = TaxaPagamentoService._validar_parcelas(
            dados.get("parcelas", taxa.parcelas)
        )

        percentual = TaxaPagamentoService._validar_percentual(
            dados.get("percentual", taxa.percentual)
        )

        ativo = dados.get("ativo", taxa.ativo)

        if not isinstance(ativo, bool):
            raise BadRequest("O campo ativo deve ser booleano")

        existente = TaxaPagamento.query.filter(
            TaxaPagamento.forma_pagamento_id
            == taxa.forma_pagamento_id,
            TaxaPagamento.parcelas == parcelas,
            TaxaPagamento.id != taxa.id
        ).first()

        if existente:
            raise BadRequest(
                "Já existe uma taxa para essa quantidade de parcelas"
            )

        taxa.parcelas = parcelas
        taxa.percentual = percentual
        taxa.ativo = ativo

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise BadRequest(
                "Já existe uma taxa com essa configuração"
            )

        return TaxaPagamentoService._to_dict(taxa)

    # ==========================================
    # EXCLUIR TAXA
    # ==========================================

    @staticmethod
    def excluir(taxa_id, empresa_id):
        taxa = TaxaPagamentoService._buscar_modelo(
            taxa_id, empresa_id
        )

        db.session.delete(taxa)
        db.session.commit()

    # ==========================================
    # LISTAR CONFIGURAÇÕES DO ANOTA
    # ==========================================

    @staticmethod
    def listar_configuracoes(empresa_id):
        TaxaPagamentoService._validar_empresa(empresa_id)

        resultado = {
            "cartao_credito": {
                str(parcela): None
                for parcela in range(1, 13)
            },
            "cartao_debito": None,
            "pix": None,
            "dinheiro": None,
            "boleto": None,
        }

        formas = FormaPagamento.query.filter_by(
            empresa_id=empresa_id
        ).all()

        for forma in formas:
            codigo = (forma.tipo or "").strip().lower()

            if codigo not in resultado:
                continue

            taxas = TaxaPagamento.query.filter_by(
                forma_pagamento_id=forma.id,
                ativo=True
            ).all()

            for taxa in taxas:
                percentual = str(
                    taxa.percentual.quantize(
                        Decimal("0.01")
                    )
                )

                if codigo == "cartao_credito":
                    if 1 <= taxa.parcelas <= 12:
                        resultado[codigo][
                            str(taxa.parcelas)
                        ] = percentual

                elif taxa.parcelas == 1:
                    resultado[codigo] = percentual

        return resultado

    # ==========================================
    # SALVAR CONFIGURAÇÕES DO ANOTA
    # ==========================================

    @staticmethod
    def salvar_configuracoes(dados, empresa_id):
        TaxaPagamentoService._validar_empresa(empresa_id)

        if not isinstance(dados, dict):
            raise BadRequest("Envie um JSON válido")

        nomes = TaxaPagamentoService.FORMAS_PADRAO

        if set(dados.keys()) != set(nomes.keys()):
            raise BadRequest(
                "Informe as cinco formas de pagamento"
            )

        credito = dados.get("cartao_credito")

        if not isinstance(credito, dict):
            raise BadRequest(
                "Informe as taxas de crédito por parcela"
            )

        chaves_validas = {
            str(i) for i in range(1, 13)
        }

        if set(credito.keys()) != chaves_validas:
            raise BadRequest(
                "Informe as taxas de crédito de 1x a 12x"
            )

        valores = {
            "cartao_credito": {
                parcela: TaxaPagamentoService._validar_percentual(
                    credito[str(parcela)]
                )
                for parcela in range(1, 13)
            }
        }

        for codigo in nomes:
            if codigo != "cartao_credito":
                valores[codigo] = {
                    1: TaxaPagamentoService._validar_percentual(
                        dados[codigo]
                    )
                }

        try:
            for codigo, nome in nomes.items():
                formas = FormaPagamento.query.filter_by(
                    empresa_id=empresa_id,
                    tipo=codigo
                ).all()

                if len(formas) > 1:
                    raise BadRequest(
                        f"Existem formas duplicadas para {nome}"
                    )

                forma = formas[0] if formas else None

                if not forma:
                    forma = FormaPagamento(
                        empresa_id=empresa_id,
                        nome=nome,
                        tipo=codigo,
                        ativo=True
                    )

                    db.session.add(forma)
                    db.session.flush()

                for parcelas, percentual in valores[codigo].items():
                    taxa = TaxaPagamento.query.filter_by(
                        forma_pagamento_id=forma.id,
                        parcelas=parcelas
                    ).first()

                    if taxa:
                        taxa.percentual = percentual
                        taxa.ativo = True
                    else:
                        db.session.add(
                            TaxaPagamento(
                                forma_pagamento_id=forma.id,
                                parcelas=parcelas,
                                percentual=percentual,
                                ativo=True
                            )
                        )

            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            raise BadRequest(
                "Conflito ao salvar as taxas de pagamento"
            )

        except Exception:
            db.session.rollback()
            raise

        return TaxaPagamentoService.listar_configuracoes(
            empresa_id
        )

    # ==========================================
    # CONVERTER PARA JSON
    # ==========================================

    @staticmethod
    def _to_dict(taxa):
        return {
            "id": taxa.id,
            "forma_pagamento_id": taxa.forma_pagamento_id,
            "forma_pagamento": taxa.forma_pagamento.nome,
            "parcelas": taxa.parcelas,
            "percentual": str(taxa.percentual),
            "ativo": taxa.ativo,
            "criado_em": (
                taxa.criado_em.isoformat()
                if taxa.criado_em else None
            ),
            "atualizado_em": (
                taxa.atualizado_em.isoformat()
                if taxa.atualizado_em else None
            )
        }
