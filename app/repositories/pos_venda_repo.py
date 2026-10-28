"""
Repositório do Pós-venda — Fase 8.
"""
from app.extensions import db
from app.models.pos_venda import PosVenda


class PosVendaRepository:

    def buscar_por_cliente(self, cliente_id: int) -> PosVenda | None:
        return PosVenda.query.filter_by(cliente_id=cliente_id).first()

    def criar_ou_atualizar(self, cliente_id: int, dados: dict) -> PosVenda:
        pv = self.buscar_por_cliente(cliente_id)
        if not pv:
            pv = PosVenda(cliente_id=cliente_id)
            db.session.add(pv)

        for campo, valor in dados.items():
            if hasattr(pv, campo):
                setattr(pv, campo, valor)

        db.session.commit()
        return pv

    def listar_ativos(self) -> list[PosVenda]:
        """Lista todos os registros de pós-venda (contas que já passaram pelo gate)."""
        return (PosVenda.query
                .join(PosVenda.cliente)
                .order_by(PosVenda.atualizado_em.desc())
                .all())
