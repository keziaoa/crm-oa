"""
Modelo Proposta — Proposta Comercial gerada a partir do diagnóstico (Fase 6).

Cada conta pode ter várias propostas (versões), mas normalmente só uma ativa.
"""
from datetime import datetime, timezone

from app.extensions import db


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Proposta(db.Model):
    __tablename__ = "propostas"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"),
                           nullable=False, index=True)

    produto = db.Column(db.String(60), nullable=False)
    setup = db.Column(db.Integer, nullable=True)
    mensalidade = db.Column(db.Integer, nullable=False)
    fidelidade_meses = db.Column(db.Integer, nullable=False, default=6)

    lojas_extra = db.Column(db.Integer, nullable=False, default=0)
    marcas_extra = db.Column(db.Integer, nullable=False, default=0)

    valor_total_mensal = db.Column(db.Integer, nullable=False)
    valor_setup_total = db.Column(db.Integer, nullable=True)

    data_envio = db.Column(db.Date, nullable=True)
    data_validade = db.Column(db.Date, nullable=True)

    status = db.Column(db.String(30), nullable=False, default="Rascunho")
    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime(timezone=True), default=_agora)

    cliente = db.relationship("Cliente", backref=db.backref("propostas", lazy="dynamic"))

    @property
    def expirada(self) -> bool:
        if not self.data_validade:
            return False
        from datetime import date
        return date.today() > self.data_validade

    def __repr__(self) -> str:
        return f"<Proposta #{self.id} {self.produto} cliente={self.cliente_id}>"
