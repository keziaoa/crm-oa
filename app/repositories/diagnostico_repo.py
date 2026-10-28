"""
Repositório de Diagnósticos e Propostas (Fase 6).
"""
from datetime import date

from app.extensions import db
from app.models.diagnostico import Diagnostico
from app.models.proposta import Proposta


class DiagnosticoRepository:

    def buscar_por_cliente(self, cliente_id: int) -> Diagnostico | None:
        return Diagnostico.query.filter_by(cliente_id=cliente_id).first()

    def criar_ou_atualizar(self, cliente_id: int, dados: dict) -> Diagnostico:
        diag = self.buscar_por_cliente(cliente_id)
        if not diag:
            diag = Diagnostico(cliente_id=cliente_id)
            db.session.add(diag)

        for campo, valor in dados.items():
            if hasattr(diag, campo):
                setattr(diag, campo, valor)

        db.session.commit()
        return diag


class PropostaRepository:

    def buscar_por_id(self, id_: int) -> Proposta | None:
        return db.session.get(Proposta, id_)

    def listar_por_cliente(self, cliente_id: int) -> list[Proposta]:
        return (Proposta.query
                .filter_by(cliente_id=cliente_id)
                .order_by(Proposta.criado_em.desc())
                .all())

    def criar(self, dados: dict) -> Proposta:
        prop = Proposta(**dados)
        db.session.add(prop)
        db.session.commit()
        return prop

    def atualizar_status(self, proposta: Proposta, status: str,
                         data_envio: date | None = None) -> None:
        proposta.status = status
        if data_envio:
            proposta.data_envio = data_envio
        db.session.commit()
