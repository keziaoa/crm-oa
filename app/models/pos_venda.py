"""
Modelo PosVenda — acompanhamento pós-venda (Fase 8).

Registra os 5 marcos de acompanhamento (D+7, D+21, D+45, D+90, D+150)
e a saúde geral da conta após o kickoff.
"""
from datetime import datetime, timezone

from app.extensions import db


def _agora():
    return datetime.now(timezone.utc)


class PosVenda(db.Model):
    __tablename__ = "pos_vendas"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(
        db.Integer, db.ForeignKey("clientes.id"), unique=True, nullable=False
    )

    saude = db.Column(db.String(30), nullable=False, default="Verde (Saudável)")

    marco_1_status = db.Column(db.String(20), nullable=False, default="Pendente")
    marco_1_data_realizado = db.Column(db.Date, nullable=True)
    marco_1_obs = db.Column(db.Text, nullable=True)

    marco_2_status = db.Column(db.String(20), nullable=False, default="Pendente")
    marco_2_data_realizado = db.Column(db.Date, nullable=True)
    marco_2_obs = db.Column(db.Text, nullable=True)

    marco_3_status = db.Column(db.String(20), nullable=False, default="Pendente")
    marco_3_data_realizado = db.Column(db.Date, nullable=True)
    marco_3_obs = db.Column(db.Text, nullable=True)

    marco_4_status = db.Column(db.String(20), nullable=False, default="Pendente")
    marco_4_data_realizado = db.Column(db.Date, nullable=True)
    marco_4_obs = db.Column(db.Text, nullable=True)

    marco_5_status = db.Column(db.String(20), nullable=False, default="Pendente")
    marco_5_data_realizado = db.Column(db.Date, nullable=True)
    marco_5_obs = db.Column(db.Text, nullable=True)

    atualizado_em = db.Column(db.DateTime(timezone=True), default=_agora,
                              onupdate=_agora)

    cliente = db.relationship("Cliente", backref=db.backref("pos_venda", uselist=False))

    NUM_MARCOS = 5

    @property
    def marcos_realizados(self) -> int:
        return sum(
            1 for i in range(1, self.NUM_MARCOS + 1)
            if getattr(self, f"marco_{i}_status") == "Realizado"
        )

    def status_marco(self, num: int) -> str:
        return getattr(self, f"marco_{num}_status")

    def __repr__(self) -> str:
        return f"<PosVenda cliente_id={self.cliente_id} {self.marcos_realizados}/5>"
