
from datetime import datetime

from exceptions.api_exception import BadRequest, NotFound
from models.categoria import Categoria
from extensions import db


class CategoriaService:

    TIPOS_VALIDOS = ("PRODUTO", "SERVICO", "VENDA", "DESPESA")

    @staticmethod
    def validar_dados(dados):
        if not isinstance(dados, dict):
            raise BadRequest("Dados da categoria são obrigatórios.")

        nome = dados.get("nome")
        tipo = dados.get("tipo")

        if not isinstance(nome, str) or not nome.strip():
            raise BadRequest("Nome da categoria é obrigatório.")

        if not isinstance(tipo, str):
            raise BadRequest("Tipo da categoria é obrigatório.")

        nome = nome.strip()
        tipo = tipo.strip().upper()

        if tipo not in CategoriaService.TIPOS_VALIDOS:
            raise BadRequest("Tipo de categoria inválido.")

        return nome, tipo

    @staticmethod
    def registrar(dados, empresa_id):
        if not empresa_id:
            raise BadRequest("Empresa não identificada.")

        nome, tipo = CategoriaService.validar_dados(dados)

        existente = Categoria.query.filter(
            Categoria.empresa_id == empresa_id,
            db.func.lower(Categoria.nome) == nome.lower(),
            Categoria.tipo == tipo,
            Categoria.deletado_em.is_(None)
        ).first()

        if existente:
            raise BadRequest("Categoria já cadastrada para esse tipo.")

        categoria = Categoria(
            empresa_id=empresa_id,
            nome=nome,
            tipo=tipo
        )

        try:
            db.session.add(categoria)
            db.session.commit()
            return categoria
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def listar(empresa_id, tipo=None):
        if not empresa_id:
            raise BadRequest("Empresa não identificada.")

        consulta = Categoria.query.filter(
            Categoria.empresa_id == empresa_id,
            Categoria.deletado_em.is_(None)
        )

        if tipo:
            if not isinstance(tipo, str):
                raise BadRequest("Tipo de categoria inválido.")

            tipo = tipo.strip().upper()

            if tipo not in CategoriaService.TIPOS_VALIDOS:
                raise BadRequest("Tipo de categoria inválido.")

            consulta = consulta.filter(Categoria.tipo == tipo)

        return consulta.order_by(Categoria.nome.asc()).all()

    @staticmethod
    def buscar_por_id(categoria_id, empresa_id):
        if not empresa_id:
            raise BadRequest("Empresa não identificada.")

        categoria = Categoria.query.filter_by(
            id=categoria_id,
            empresa_id=empresa_id,
            deletado_em=None
        ).first()

        if not categoria:
            raise NotFound("Categoria não encontrada.")

        return categoria

    @staticmethod
    def atualizar(categoria_id, dados, empresa_id):
        categoria = CategoriaService.buscar_por_id(
            categoria_id, empresa_id
        )

        nome, tipo = CategoriaService.validar_dados(dados)

        existente = Categoria.query.filter(
            Categoria.id != categoria_id,
            Categoria.empresa_id == empresa_id,
            db.func.lower(Categoria.nome) == nome.lower(),
            Categoria.tipo == tipo,
            Categoria.deletado_em.is_(None)
        ).first()

        if existente:
             return existente

        # Não permitir mudar o tipo quando há registros vinculados.
        if tipo != categoria.tipo:
            if categoria.produtos or categoria.receitas or categoria.despesas:
                raise BadRequest(
                    "Não é possível alterar o tipo de uma categoria "
                    "que possui registros vinculados."
                )

        categoria.nome = nome
        categoria.tipo = tipo

        try:
            db.session.commit()
            return categoria
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def deletar(categoria_id, empresa_id):
        categoria = CategoriaService.buscar_por_id(
            categoria_id, empresa_id
        )

        if categoria.produtos:
            raise BadRequest(
                "Não é possível excluir: existem produtos vinculados."
            )

        if categoria.receitas:
            raise BadRequest(
                "Não é possível excluir: existem receitas vinculadas."
            )

        if categoria.despesas:
            raise BadRequest(
                "Não é possível excluir: existem despesas vinculadas."
            )

        categoria.deletado_em = datetime.utcnow()

        try:
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise
