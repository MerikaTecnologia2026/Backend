
from datetime import datetime

from extensions import db


class DespesaRecorrencia(db.Model):
    __tablename__ = "despesa_recorrencias"

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

    frequencia = db.Column(
        db.String(20),
        nullable=False
    )

    quantidade = db.Column(
        db.Integer,
        nullable=False
    )

    data_inicio = db.Column(
        db.Date,
        nullable=False
    )

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    despesas = db.relationship(
        "Despesa",
        back_populates="recorrencia"
    )

    def __repr__(self):
        return (
            f"<DespesaRecorrencia "
            f"id={self.id} "
            f"frequencia={self.frequencia}>"
        )
