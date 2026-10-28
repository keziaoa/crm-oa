"""
Repositório de Cadências: acesso ao banco para a tabela cadencias.
"""
from datetime import date

from app.extensions import db
from app.models.cadencia import Cadencia
from app.models.cliente import Cliente


class CadenciaRepository:

    def cadencia_ativa(self, cliente_id: int) -> Cadencia | None:
        return (Cadencia.query
                .filter_by(cliente_id=cliente_id, ativa=True)
                .first())

    def contar_ativas(self) -> int:
        return (Cadencia.query
                .filter_by(ativa=True)
                .join(Cliente)
                .filter(Cliente.arquivado.is_(False))
                .count())

    def iniciar(self, cliente_id: int, data_d0: date) -> Cadencia:
        antigo = self.cadencia_ativa(cliente_id)
        if antigo:
            antigo.ativa = False

        cad = Cadencia(cliente_id=cliente_id, data_d0=data_d0)
        db.session.add(cad)
        db.session.commit()
        return cad

    def registrar_contato(self, cadencia: Cadencia, contato: str,
                          data_realizado: date, obs: str | None = None) -> None:
        if contato not in Cadencia.CONTATOS:
            raise ValueError(f"Contato inválido: {contato}")
        setattr(cadencia, f"{contato}_realizado", True)
        setattr(cadencia, f"{contato}_data_realizado", data_realizado)
        if obs:
            setattr(cadencia, f"{contato}_obs", obs)
        db.session.commit()

    def marcar_respondeu(self, cadencia: Cadencia) -> None:
        cadencia.respondeu = True
        cadencia.ativa = False
        db.session.commit()

    def encerrar(self, cadencia: Cadencia, motivo: str) -> None:
        cadencia.ativa = False
        cadencia.motivo_encerramento = motivo
        db.session.commit()

    def listar_ativas(self) -> list[dict]:
        """Lista todas as cadências ativas com dados do cliente e próxima ação.
        Retorna dicts com cadencia, cliente e info de próximo contato."""
        from app.domain import proximos_contatos
        cadencias = (Cadencia.query
                     .filter_by(ativa=True)
                     .join(Cliente)
                     .filter(Cliente.arquivado.is_(False))
                     .order_by(Cadencia.data_d0)
                     .all())

        hoje = date.today()
        resultado = []
        for cad in cadencias:
            proximo = cad.proximo_contato()
            datas = dict(proximos_contatos(cad.data_d0))
            data_proximo = datas.get(proximo.upper()) if proximo else None
            atrasado = data_proximo < hoje if data_proximo else False
            resultado.append({
                "cadencia": cad,
                "cliente": cad.cliente,
                "proximo_contato": proximo,
                "data_proximo": data_proximo,
                "atrasado": atrasado,
            })

        resultado.sort(key=lambda r: (not r["atrasado"], r["data_proximo"] or hoje))
        return resultado
