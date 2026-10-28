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
               incluir_arquivadas=False, visao=None) -> list[Cliente]:
        from app import domain
        query = Cliente.query
        if not incluir_arquivadas:
            query = query.filter(Cliente.arquivado.is_(False))
        # Visão rápida: clientes ativos x contas ainda em prospecção.
        if visao == "ativos":
            query = query.filter(Cliente.status == domain.STATUS_CLIENTE_ATIVO)
        elif visao == "prospeccao":
            em_prospeccao = [n for _, n, _, t in domain.STATUS_FUNIL
                             if t == "pipeline" and n != domain.STATUS_CLIENTE_ATIVO]
            query = query.filter(Cliente.status.in_(em_prospeccao))
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

    def contar_ativos(self) -> int:
        from app import domain
        return (Cliente.query
                .filter(Cliente.arquivado.is_(False),
                        Cliente.status == domain.STATUS_CLIENTE_ATIVO)
                .count())

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

    # ----- Funil (Fase 3) -----
    def agrupar_por_status(self) -> dict[str, list[Cliente]]:
        """Devolve um dicionário {status: [contas]} com todas as contas ativas
        (não arquivadas), agrupadas pelo status no funil."""
        from app import domain
        contas = (Cliente.query
                  .filter(Cliente.arquivado.is_(False))
                  .order_by(Cliente.conta_id)
                  .all())
        agrupado = {nome: [] for nome in domain.STATUS_NOMES}
        for c in contas:
            if c.status in agrupado:
                agrupado[c.status].append(c)
        return agrupado

    def alterar_status(self, cliente: Cliente, novo_status: str) -> None:
        """Altera o status de uma conta (validação feita na rota)."""
        cliente.status = novo_status
        db.session.commit()

    # ----- Qualificação (Fase 4) -----
    def salvar_qualificacao(self, cliente: Cliente, notas: dict,
                            prioridade: str) -> None:
        """Grava as 5 notas e a prioridade calculada."""
        for campo, valor in notas.items():
            setattr(cliente, campo, valor)
        cliente.prioridade = prioridade
        db.session.commit()

    # ----- Indicadores (Fase 9) -----
    def indicadores(self) -> dict:
        """Retorna todas as métricas agregadas para o painel de indicadores."""
        from app import domain
        from sqlalchemy import func

        base = Cliente.query.filter(Cliente.arquivado.is_(False))

        total = base.count()

        por_status = dict(
            base.with_entities(Cliente.status, func.count(Cliente.id))
            .group_by(Cliente.status).all()
        )

        por_prioridade = dict(
            base.with_entities(Cliente.prioridade, func.count(Cliente.id))
            .group_by(Cliente.prioridade).all()
        )

        por_responsavel = dict(
            base.with_entities(Cliente.responsavel, func.count(Cliente.id))
            .filter(Cliente.responsavel.isnot(None), Cliente.responsavel != "")
            .group_by(Cliente.responsavel).all()
        )

        por_origem = dict(
            base.with_entities(Cliente.origem, func.count(Cliente.id))
            .filter(Cliente.origem.isnot(None), Cliente.origem != "")
            .group_by(Cliente.origem).all()
        )

        em_prospeccao = sum(
            por_status.get(n, 0) for _, n, _, t in domain.STATUS_FUNIL
            if t == "pipeline" and n != domain.STATUS_CLIENTE_ATIVO
        )
        clientes_ativos = por_status.get(domain.STATUS_CLIENTE_ATIVO, 0)
        em_saida = sum(
            por_status.get(n, 0) for _, n, _, t in domain.STATUS_FUNIL
            if t == "saida"
        )

        return {
            "total": total,
            "em_prospeccao": em_prospeccao,
            "clientes_ativos": clientes_ativos,
            "em_saida": em_saida,
            "por_status": por_status,
            "por_prioridade": por_prioridade,
            "por_responsavel": por_responsavel,
            "por_origem": por_origem,
        }
