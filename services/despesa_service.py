
from calendar import monthrange
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import SQLAlchemyError

from exceptions.api_exception import BadRequest, NotFound
from models.despesa import Despesa
from models.despesa_recorrencia import DespesaRecorrencia
from models.categoria import Categoria
from extensions import db


class DespesaService:

    @staticmethod
    def _validar_data(valor, campo, obrigatoria=False):
        if valor is None or valor == "":
            if obrigatoria:
                raise BadRequest(
                    f"{campo} é obrigatória"
                )
            return None

        try:
            return datetime.strptime(
                valor, "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            raise BadRequest(
                f"{campo} inválida. "
                "Use o formato YYYY-MM-DD"
            )

    @staticmethod
    def _validar_valor(valor):
        if valor is None:
            raise BadRequest("Valor é obrigatório")

        try:
            resultado = Decimal(str(valor))
        except (InvalidOperation, ValueError, TypeError):
            raise BadRequest("Valor inválido")

        if (
            not resultado.is_finite()
            or resultado < 0
            or resultado > Decimal("99999999.99")
            or resultado.as_tuple().exponent < -2
        ):
            raise BadRequest(
                "Valor inválido. Informe um valor "
                "entre 0 e 99999999.99, "
                "com até duas casas decimais."
            )

        return resultado

    @staticmethod
    def _validar_categoria(categoria_id, empresa_id):
        if categoria_id is None or categoria_id == "":
            return None

        try:
            categoria_id = int(categoria_id)
        except (ValueError, TypeError):
            raise BadRequest("Categoria inválida")

        categoria = Categoria.query.filter_by(
            id=categoria_id,
            empresa_id=empresa_id,
            tipo="DESPESA",
            deletado_em=None
        ).first()

        if not categoria:
            raise NotFound(
                "Categoria de despesa não encontrada"
            )

        return categoria.id

    @staticmethod
    def _validar_status(status, data_pagamento):
        status = str(status or "PENDENTE").upper()

        if status not in ("PENDENTE", "PAGO"):
            raise BadRequest(
                "Status deve ser PENDENTE ou PAGO"
            )

        if status == "PAGO" and not data_pagamento:
            raise BadRequest(
                "Informe a data de pagamento "
                "para uma despesa paga"
            )

        if status == "PENDENTE" and data_pagamento:
            raise BadRequest(
                "Despesa pendente não pode ter "
                "data de pagamento"
            )

        return status

    @staticmethod
    def _validar_dados(dados, empresa_id):
        if not isinstance(dados, dict):
            raise BadRequest(
                "Envie um objeto JSON válido"
            )

        nome = dados.get("nome")

        if not isinstance(nome, str) or not nome.strip():
            raise BadRequest(
                "Nome da despesa é obrigatório"
            )

        nome = nome.strip()

        if len(nome) > 150:
            raise BadRequest(
                "Nome deve ter até 150 caracteres"
            )

        valor = DespesaService._validar_valor(
            dados.get("valor")
        )

        categoria_id = DespesaService._validar_categoria(
            dados.get("categoria_id"),
            empresa_id
        )

        data_vencimento = DespesaService._validar_data(
            dados.get("data_vencimento"),
            "Data de vencimento",
            obrigatoria=True
        )

        data_pagamento = DespesaService._validar_data(
            dados.get("data_pagamento"),
            "Data de pagamento"
        )

        status = DespesaService._validar_status(
            dados.get("status", "PENDENTE"),
            data_pagamento
        )

        descricao = dados.get("descricao")

        if descricao is not None and not isinstance(
            descricao, str
        ):
            raise BadRequest("Descrição inválida")

        return {
            "empresa_id": empresa_id,
            "categoria_id": categoria_id,
            "nome": nome,
            "descricao": descricao,
            "valor": valor,
            "data_vencimento": data_vencimento,
            "data_pagamento": data_pagamento,
            "status": status,
        }

    @staticmethod
    def _data_parcela(data_inicial, frequencia, indice):
        if frequencia == "Semanal":
            return data_inicial + timedelta(
                weeks=indice
            )

        meses = (
            indice * 12
            if frequencia == "Anual"
            else indice
        )

        mes_total = (
            data_inicial.month - 1 + meses
        )

        ano = (
            data_inicial.year
            + mes_total // 12
        )

        mes = mes_total % 12 + 1

        ultimo_dia = monthrange(ano, mes)[1]

        dia = min(
            data_inicial.day,
            ultimo_dia
        )

        return data_inicial.replace(
            year=ano,
            month=mes,
            day=dia
        )

    @staticmethod
    def registrar(dados, empresa_id):
        dados_validados = DespesaService._validar_dados(
            dados, empresa_id
        )

        recorrente = dados.get("recorrente", False)

        if not isinstance(recorrente, bool):
            raise BadRequest(
                "Recorrente deve ser verdadeiro ou falso"
            )

        # Cadastro simples: preserva o comportamento
        # existente do endpoint.
        if not recorrente:
            despesa = Despesa(**dados_validados)

            try:
                db.session.add(despesa)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                raise

            return despesa

        frequencia = dados.get("frequencia")

        if frequencia not in (
            "Semanal",
            "Mensal",
            "Anual"
        ):
            raise BadRequest(
                "Frequência deve ser Semanal, "
                "Mensal ou Anual"
            )

        quantidade = dados.get("repeticoes")

        if (
            isinstance(quantidade, bool)
            or not isinstance(quantidade, int)
            or not 2 <= quantidade <= 120
        ):
            raise BadRequest(
                "Repetições deve ser um número "
                "inteiro entre 2 e 120"
            )

        datas = []

        try:
            for indice in range(quantidade):
                datas.append(
                    DespesaService._data_parcela(
                        dados_validados["data_vencimento"],
                        frequencia,
                        indice
                    )
                )
        except (ValueError, OverflowError):
            raise BadRequest(
                "As datas das parcelas excedem "
                "o intervalo permitido"
            )

        recorrencia = DespesaRecorrencia(
            empresa_id=empresa_id,
            frequencia=frequencia,
            quantidade=quantidade,
            data_inicio=dados_validados[
                "data_vencimento"
            ]
        )

        try:
            db.session.add(recorrencia)
            db.session.flush()

            despesas = []

            for indice, data in enumerate(datas):
                dados_parcela = {
                    **dados_validados,
                    "data_vencimento": data,
                    "recorrencia_id": recorrencia.id,
                    "numero_parcela": indice + 1,
                }

                # Somente a primeira parcela pode
                # começar como paga.
                if indice > 0:
                    dados_parcela["data_pagamento"] = None
                    dados_parcela["status"] = "PENDENTE"

                despesa = Despesa(**dados_parcela)
                db.session.add(despesa)
                despesas.append(despesa)

            db.session.commit()

            return despesas

        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def listar(empresa_id):
        return Despesa.query.filter_by(
            empresa_id=empresa_id,
            deletado_em=None
        ).order_by(
            Despesa.data_vencimento.asc(),
            Despesa.id.asc()
        ).all()

    @staticmethod
    def buscar_por_id(despesa_id, empresa_id):
        despesa = Despesa.query.filter_by(
            id=despesa_id,
            empresa_id=empresa_id,
            deletado_em=None
        ).first()

        if not despesa:
            raise NotFound(
                "Despesa não encontrada"
            )

        return despesa

    @staticmethod
    def atualizar(despesa_id, dados, empresa_id):
        despesa = DespesaService.buscar_por_id(
            despesa_id, empresa_id
        )

        if not isinstance(dados, dict):
            raise BadRequest(
                "Envie um objeto JSON válido"
            )

        # Recorrência não pode ser alterada
        # por este endpoint individual.
        campos_bloqueados = {
            "recorrencia_id",
            "numero_parcela",
            "recorrente",
            "frequencia",
            "repeticoes",
            "empresa_id",
        }

        if campos_bloqueados.intersection(dados):
            raise BadRequest(
                "Para atualizar esta despesa, "
                "envie apenas os campos individuais"
            )

        if "nome" in dados:
            nome = dados["nome"]

            if (
                not isinstance(nome, str)
                or not nome.strip()
            ):
                raise BadRequest(
                    "Nome da despesa é obrigatório"
                )

            if len(nome.strip()) > 150:
                raise BadRequest(
                    "Nome deve ter até 150 caracteres"
                )

            despesa.nome = nome.strip()

        if "descricao" in dados:
            descricao = dados["descricao"]

            if (
                descricao is not None
                and not isinstance(descricao, str)
            ):
                raise BadRequest(
                    "Descrição inválida"
                )

            despesa.descricao = descricao

        if "valor" in dados:
            despesa.valor = (
                DespesaService._validar_valor(
                    dados["valor"]
                )
            )

        if "categoria_id" in dados:
            despesa.categoria_id = (
                DespesaService._validar_categoria(
                    dados["categoria_id"],
                    empresa_id
                )
            )

        if "data_vencimento" in dados:
            despesa.data_vencimento = (
                DespesaService._validar_data(
                    dados["data_vencimento"],
                    "Data de vencimento",
                    obrigatoria=True
                )
            )

        if "data_pagamento" in dados:
            despesa.data_pagamento = (
                DespesaService._validar_data(
                    dados["data_pagamento"],
                    "Data de pagamento"
                )
            )

        if "status" in dados:
            status = str(dados["status"]).upper()

            if status not in ("PENDENTE", "PAGO"):
                raise BadRequest("Status inválido")

            despesa.status = status

        DespesaService._validar_status(
            despesa.status,
            despesa.data_pagamento
        )

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise

        return despesa

    @staticmethod
    def excluir(despesa_id, empresa_id):
        despesa = DespesaService.buscar_por_id(despesa_id, empresa_id)

        try:
            agora = datetime.utcnow()

            if despesa.recorrencia_id is not None:
                # Exclui todas as parcelas da mesma recorrência
                Despesa.query.filter_by(
                    empresa_id=empresa_id,
                    recorrencia_id=despesa.recorrencia_id,
                    deletado_em=None
                ).update(
                    {"deletado_em": agora},
                    synchronize_session=False
                )
            else:
                # Exclui somente a despesa individual
                despesa.deletado_em = agora

            db.session.commit()

        except SQLAlchemyError:
            db.session.rollback()
            raise

        return despesa