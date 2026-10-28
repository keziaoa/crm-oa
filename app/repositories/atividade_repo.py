"""
Repositório de Atividades: acesso ao banco para a tabela atividades.
"""
from datetime import date

from app.extensions import db
from app.models.atividade import Atividade
from app.models.cliente import Cliente


class AtividadeRepository:

    def listar_por_cliente(self, cliente_id: int) -> list[Atividade]:
        return (Atividade.query
                .filter_by(cliente_id=cliente_id)
                .order_by(Atividade.data.desc(), Atividade.criado_em.desc())
                .all())

    def criar(self, cliente_id: int, data: date, tipo: str, resumo: str) -> Atividade:
        atv = Atividade(cliente_id=cliente_id, data=data, tipo=tipo, resumo=resumo)
        db.session.add(atv)
        db.session.commit()
        return atv

    def obter(self, atividade_id: int) -> Atividade | None:
        return db.session.get(Atividade, atividade_id)

    def excluir(self, atividade: Atividade) -> None:
        db.session.delete(atividade)
        db.session.commit()

    def listar_recentes(self, limite: int = 20) -> list[Atividade]:
        return (Atividade.query
                .join(Cliente)
                .filter(Cliente.arquivado.is_(False))
                .order_by(Atividade.data.desc(), Atividade.criado_em.desc())
                .limit(limite)
                .all())

    def contar_por_cliente(self, cliente_id: int) -> int:
        return Atividade.query.filter_by(cliente_id=cliente_id).count()
