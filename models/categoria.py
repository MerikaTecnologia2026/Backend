from datetime import datetime

from extensions import db


class Categoria(db.Model):

    __tablename__ = "categorias"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=False,
        index=True
    )

    nome = db.Column(
    db.String(150),
    nullable=False
    )

    tipo = db.Column(
        db.String(20),
        nullable=False,
        default="PRODUTO"
    )

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    atualizado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    deletado_em = db.Column(
        db.DateTime,
        nullable=True
    )

    empresa = db.relationship(
        "Empresa",
        back_populates="categorias"
    )

    produtos = db.relationship(
        "Produto",
        back_populates="categoria"
    )

    receitas = db.relationship(
        "Receita",
        back_populates="categoria"
    )

    despesas = db.relationship(
        "Despesa",
        back_populates="categoria"
    )

    def __repr__(self):
        return f"<Categoria {self.nome}>"