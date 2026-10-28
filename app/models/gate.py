"""
Modelo Gate (Ficha de Passagem) — Fase 7.

Checklist dos 8 itens obrigatórios antes de liberar a conta para a Operação.
Só quando os 8 itens estiverem "Sim" a conta pode receber o status
"Liberado p/ Setup".
"""
from datetime import datetime, timezone

from app.extensions import db


def _agora():
    return datetime.now(timezone.utc)


class Gate(db.Model):
    __tablename__ = "gates"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(
        db.Integer, db.ForeignKey("clientes.id"), unique=True, nullable=False
    )

    item_1 = db.Column(db.Boolean, nullable=False, default=False)
    item_2 = db.Column(db.Boolean, nullable=False, default=False)
    item_3 = db.Column(db.Boolean, nullable=False, default=False)
    item_4 = db.Column(db.Boolean, nullable=False, default=False)
    item_5 = db.Column(db.Boolean, nullable=False, default=False)
    item_6 = db.Column(db.Boolean, nullable=False, default=False)
    item_7 = db.Column(db.Boolean, nullable=False, default=False)
    item_8 = db.Column(db.Boolean, nullable=False, default=False)

    obs_1 = db.Column(db.Text, nullable=True)
    obs_2 = db.Column(db.Text, nullable=True)
    obs_3 = db.Column(db.Text, nullable=True)
    obs_4 = db.Column(db.Text, nullable=True)
    obs_5 = db.Column(db.Text, nullable=True)
    obs_6 = db.Column(db.Text, nullable=True)
    obs_7 = db.Column(db.Text, nullable=True)
    obs_8 = db.Column(db.Text, nullable=True)

    atualizado_em = db.Column(db.DateTime(timezone=True), default=_agora,
                              onupdate=_agora)

    cliente = db.relationship("Cliente", backref=db.backref("gate", uselist=False))

    CAMPOS_ITENS = [f"item_{i}" for i in range(1, 9)]
    CAMPOS_OBS = [f"obs_{i}" for i in range(1, 9)]

    @property
    def itens_marcados(self) -> list[bool]:
        return [bool(getattr(self, f"item_{i}")) for i in range(1, 9)]

    @property
    def liberado(self) -> bool:
        from app import domain
        return domain.gate_liberado(self.itens_marcados)

    @property
    def itens_sim(self) -> int:
        return sum(1 for m in self.itens_marcados if m)

    def __repr__(self) -> str:
        return f"<Gate cliente_id={self.cliente_id} {self.itens_sim}/8>"
