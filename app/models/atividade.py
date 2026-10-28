"""
Modelo Atividade — registro de cada interação com uma conta
(visita, ligação, WhatsApp, e-mail, reunião).

Serve como histórico cronológico para acompanhamento do trabalho comercial.
"""
from datetime import datetime, timezone

from app.extensions import db


def _agora() -> datetime:
    return datetime.now(timezone.utc)


TIPOS_ATIVIDADE = [
    "WhatsApp",
    "Ligação",
    "Visita",
    "Reunião",
    "E-mail",
    "Instagram",
    "Outro",
]


class Atividade(db.Model):
    __tablename__ = "atividades"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False, index=True)

    data = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(40), nullable=False)
    resumo = db.Column(db.Text, nullable=False)

    criado_em = db.Column(db.DateTime(timezone=True), default=_agora)

    cliente = db.relationship("Cliente", backref=db.backref("atividades", lazy="dynamic",
                                                            order_by="Atividade.data.desc()"))

    def __repr__(self) -> str:
        return f"<Atividade #{self.id} {self.tipo} cliente={self.cliente_id}>"
