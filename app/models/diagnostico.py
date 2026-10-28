"""
Modelo Diagnostico — Ficha de Diagnóstico Comercial (Fase 6).

Registra os 10 blocos do diagnóstico feito na reunião com o decisor.
Cada conta pode ter apenas um diagnóstico.
"""
from datetime import datetime, timezone

from app.extensions import db


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Diagnostico(db.Model):
    __tablename__ = "diagnosticos"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"),
                           nullable=False, unique=True, index=True)

    data_reuniao = db.Column(db.Date, nullable=True)

    bloco_contexto = db.Column(db.Text, nullable=True)
    bloco_dor_principal = db.Column(db.Text, nullable=True)
    bloco_financeiro_atual = db.Column(db.Text, nullable=True)
    bloco_controles = db.Column(db.Text, nullable=True)
    bloco_operacao = db.Column(db.Text, nullable=True)
    bloco_canais_venda = db.Column(db.Text, nullable=True)
    bloco_equipe_processos = db.Column(db.Text, nullable=True)
    bloco_tecnologia = db.Column(db.Text, nullable=True)
    bloco_expectativas = db.Column(db.Text, nullable=True)
    bloco_recomendacao = db.Column(db.Text, nullable=True)

    produto_recomendado = db.Column(db.String(60), nullable=True)
    exclusoes = db.Column(db.Text, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime(timezone=True), default=_agora)
    atualizado_em = db.Column(db.DateTime(timezone=True), default=_agora,
                              onupdate=_agora)

    cliente = db.relationship("Cliente", backref=db.backref("diagnostico", uselist=False))

    CAMPOS_BLOCOS = [
        "bloco_contexto", "bloco_dor_principal", "bloco_financeiro_atual",
        "bloco_controles", "bloco_operacao", "bloco_canais_venda",
        "bloco_equipe_processos", "bloco_tecnologia", "bloco_expectativas",
        "bloco_recomendacao",
    ]

    @property
    def blocos_preenchidos(self) -> int:
        return sum(1 for c in self.CAMPOS_BLOCOS if getattr(self, c))

    @property
    def completo(self) -> bool:
        return self.blocos_preenchidos == len(self.CAMPOS_BLOCOS)

    def __repr__(self) -> str:
        return f"<Diagnostico #{self.id} cliente={self.cliente_id}>"
