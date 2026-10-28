"""
Repositório do Gate (Ficha de Passagem) — Fase 7.
"""
from app.extensions import db
from app.models.gate import Gate


class GateRepository:

    def buscar_por_cliente(self, cliente_id: int) -> Gate | None:
        return Gate.query.filter_by(cliente_id=cliente_id).first()

    def criar_ou_atualizar(self, cliente_id: int, dados: dict) -> Gate:
        gate = self.buscar_por_cliente(cliente_id)
        if not gate:
            gate = Gate(cliente_id=cliente_id)
            db.session.add(gate)

        for campo, valor in dados.items():
            if hasattr(gate, campo):
                setattr(gate, campo, valor)

        db.session.commit()
        return gate
