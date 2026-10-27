"""
Repositório de Clientes: o ÚNICO lugar que conversa com o banco de dados.
Nenhuma tela escreve comandos de banco direto — tudo passa por aqui, o que
permitirá trocar SQLite por PostgreSQL no futuro sem mexer no resto.
"""
import re

from app.extensions import db
from app.models.cliente import Cliente, so_digitos


class ClienteRepository:
    # ----- Leitura -----
    def listar(self, q=None, status=None, prioridade=None, cidade=None,
               incluir_arquivadas=False) -> list[Cliente]:
        query = Cliente.query
        if not incluir_arquivadas:
            query = query.filter(Cliente.arquivado.is_(False))
        if q:
            like = f"%{q.strip()}%"
            query = query.filter(db.or_(
                Cliente.nome_fantasia.ilike(like),
                Cliente.razao_social.ilike(like),
                Cliente.conta_id.ilike(like),
            ))
        if status:
            query = query.filter(Cliente.status == status)
        if prioridade:
            query = query.filter(Cliente.prioridade == prioridade)
        if cidade:
            query = query.filter(Cliente.cidade == cidade)
        return query.order_by(Cliente.conta_id).all()

    def contar(self, incluir_arquivadas=False) -> int:
        query = Cliente.query
        if not incluir_arquivadas:
            query = query.filter(Cliente.arquivado.is_(False))
        return query.count()

    def cidades(self) -> list[str]:
        """Cidades distintas já cadastradas (para o filtro)."""
        linhas = (Cliente.query.with_entities(Cliente.cidade)
                  .filter(Cliente.cidade.isnot(None), Cliente.cidade != "")
                  .distinct().order_by(Cliente.cidade).all())
        return [c for (c,) in linhas]

    def buscar_por_id(self, id_: int) -> Cliente | None:
        return db.session.get(Cliente, id_)

    def buscar_por_conta_id(self, conta_id: str) -> Cliente | None:
        return Cliente.query.filter_by(conta_id=conta_id).first()

    def buscar_por_cnpj(self, cnpj: str) -> Cliente | None:
        """Busca sempre pelo CNPJ só com dígitos — a chave de integração."""
        d = so_digitos(cnpj)
        if not d:
            return None
        return Cliente.query.filter_by(cnpj=d).first()

    # ----- Geração do Conta ID -----
    def proximo_conta_id(self) -> str:
        """Gera o próximo Conta ID no formato CT-001, CT-002, ...

        Olha o maior número já usado (mesmo entre contas arquivadas) e soma 1,
        para nunca repetir um ID.
        """
        maior = 0
        for (cid,) in Cliente.query.with_entities(Cliente.conta_id).all():
            m = re.match(r"^CT-(\d+)$", cid or "")
            if m:
                maior = max(maior, int(m.group(1)))
        return f"CT-{maior + 1:03d}"

    # ----- Escrita -----
    def criar(self, dados: dict) -> Cliente:
        dados = dict(dados)
        dados.pop("conta_id", None)  # o ID é sempre gerado aqui, nunca recebido
        if "cnpj" in dados:
            dados["cnpj"] = so_digitos(dados["cnpj"])
        cliente = Cliente(conta_id=self.proximo_conta_id(), **dados)
        db.session.add(cliente)
        db.session.commit()
        return cliente

    def atualizar(self, cliente: Cliente, dados: dict) -> Cliente:
        for campo, valor in dados.items():
            if campo in ("conta_id", "id"):
                continue  # nunca trocamos o identificador
            if campo == "cnpj":
                valor = so_digitos(valor)
            setattr(cliente, campo, valor)
        db.session.commit()
        return cliente

    def arquivar(self, cliente: Cliente) -> None:
        cliente.arquivado = True
        db.session.commit()

    def desarquivar(self, cliente: Cliente) -> None:
        cliente.arquivado = False
        db.session.commit()
