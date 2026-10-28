"""
Modelo Cadencia — registra cada contato (D0, D3, D7, D12) de uma conta
que está no status "Em Cadência".

Uma conta pode ter várias cadências ao longo do tempo (se voltou de Nutrição
e entrou em cadência novamente), mas apenas UMA cadência ativa por vez.
"""
from datetime import datetime, timezone

from app.extensions import db


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Cadencia(db.Model):
    __tablename__ = "cadencias"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False, index=True)

    data_d0 = db.Column(db.Date, nullable=False)
    ativa = db.Column(db.Boolean, nullable=False, default=True, index=True)

    d0_realizado = db.Column(db.Boolean, nullable=False, default=False)
    d3_realizado = db.Column(db.Boolean, nullable=False, default=False)
    d7_realizado = db.Column(db.Boolean, nullable=False, default=False)
    d12_realizado = db.Column(db.Boolean, nullable=False, default=False)

    d0_data_realizado = db.Column(db.Date, nullable=True)
    d3_data_realizado = db.Column(db.Date, nullable=True)
    d7_data_realizado = db.Column(db.Date, nullable=True)
    d12_data_realizado = db.Column(db.Date, nullable=True)

    d0_obs = db.Column(db.Text, nullable=True)
    d3_obs = db.Column(db.Text, nullable=True)
    d7_obs = db.Column(db.Text, nullable=True)
    d12_obs = db.Column(db.Text, nullable=True)

    respondeu = db.Column(db.Boolean, nullable=False, default=False)
    motivo_encerramento = db.Column(db.String(120), nullable=True)

    criado_em = db.Column(db.DateTime(timezone=True), default=_agora)

    cliente = db.relationship("Cliente", backref=db.backref("cadencias", lazy="dynamic"))

    CONTATOS = ["d0", "d3", "d7", "d12"]

    def proximo_contato(self) -> str | None:
        for c in self.CONTATOS:
            if not getattr(self, f"{c}_realizado"):
                return c
        return None

    @property
    def todos_realizados(self) -> bool:
        return all(getattr(self, f"{c}_realizado") for c in self.CONTATOS)

    def datas_previstas(self) -> list[dict]:
        from app.domain import proximos_contatos
        contatos = proximos_contatos(self.data_d0)
        resultado = []
        for rotulo, data in contatos:
            chave = rotulo.lower()
            resultado.append({
                "rotulo": rotulo,
                "chave": chave,
                "data_prevista": data,
                "realizado": getattr(self, f"{chave}_realizado"),
                "data_realizado": getattr(self, f"{chave}_data_realizado"),
                "obs": getattr(self, f"{chave}_obs"),
            })
        return resultado

    def __repr__(self) -> str:
        return f"<Cadencia #{self.id} cliente={self.cliente_id} ativa={self.ativa}>"
