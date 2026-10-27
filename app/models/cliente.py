"""
Modelo Cliente — a conta comercial (uma hamburgueria/pizzaria).

Os campos espelham a aba "Base de Prospecção" do Master Kit Comercial.

Decisões pensando na integração futura com o cohab-control:
- O CNPJ é o identificador único "de verdade" do cliente (chave de negócio),
  além do Conta ID legível (CT-001, CT-002...).
- CNPJ é guardado SÓ com números (14 dígitos), sem pontos/barra/traço, para
  casar com o cohab-control sem ambiguidade. Há um método para exibir
  formatado, mas o que vale para buscas e integração é o campo só-dígitos.
- Razão social e contatos (financeiro e operacional) ficam em campos próprios
  e padronizados, não misturados num campo de texto livre.
"""
import re
from datetime import datetime, timezone

from app.extensions import db


def so_digitos(valor: str | None) -> str | None:
    """Mantém apenas os números de um texto (para CNPJ/telefone)."""
    if valor is None:
        return None
    digitos = re.sub(r"\D", "", valor)
    return digitos or None


def formatar_cnpj(digitos: str | None) -> str | None:
    """Recebe 14 dígitos e devolve no formato 00.000.000/0000-00."""
    d = so_digitos(digitos)
    if not d or len(d) != 14:
        return d
    return f"{d[0:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)

    # --- Identificação ---
    # Conta ID legível usado no dia a dia (CT-001). Gerado automaticamente.
    conta_id = db.Column(db.String(20), unique=True, nullable=False, index=True)

    nome_fantasia = db.Column(db.String(255), nullable=False)  # Empresa / Marca

    # CNPJ só com dígitos (14). Identificador único de negócio e chave de
    # integração com o cohab-control. Pode ser nulo enquanto a conta ainda
    # está em pesquisa; quando preenchido, é único.
    cnpj = db.Column(db.String(14), unique=True, nullable=True, index=True)

    razao_social = db.Column(db.String(255), nullable=True)
    confianca_identificacao = db.Column(db.String(30), nullable=True)
    cidade = db.Column(db.String(120), nullable=True, index=True)
    segmento = db.Column(db.String(60), nullable=True)

    # --- Origem, estrutura e sinais de porte ---
    origem = db.Column(db.String(40), nullable=True)
    triagem_ifood = db.Column(db.String(1), nullable=True)      # A / B / C
    nota_ifood = db.Column(db.Float, nullable=True)             # ex.: 4.9
    avaliacoes_ifood = db.Column(db.Integer, nullable=True)     # ex.: 1439
    rede_independencia = db.Column(db.String(40), nullable=True)
    unidades = db.Column(db.Integer, nullable=True)
    marcas = db.Column(db.Integer, nullable=True)
    canais = db.Column(db.String(255), nullable=True)
    faturamento_estimado = db.Column(db.Integer, nullable=True)  # R$/mês
    fonte_faturamento = db.Column(db.String(30), nullable=True)
    gatilho = db.Column(db.Text, nullable=True)                  # sinais observados

    # --- Contrato / Plano (preenchido quando o cliente fecha) ---
    plano_contratado = db.Column(db.String(60), nullable=True)
    data_inicio = db.Column(db.Date, nullable=True)  # data do kickoff

    # --- Gestão comercial ---
    responsavel = db.Column(db.String(40), nullable=True)
    status = db.Column(db.String(40), nullable=False, default="Pesquisa", index=True)
    # Prioridade (A/B/C/D) nasce "Pendente" e é calculada na Fase 4 a partir
    # das 5 notas. Guardamos o campo desde já para o filtro da tela de Contas.
    prioridade = db.Column(db.String(12), nullable=False, default="Pendente", index=True)
    observacoes = db.Column(db.Text, nullable=True)

    # --- Contatos padronizados (preenchidos em fases futuras: Gate item 4) ---
    contato_financeiro_nome = db.Column(db.String(255), nullable=True)
    contato_financeiro_email = db.Column(db.String(255), nullable=True)
    contato_financeiro_telefone = db.Column(db.String(20), nullable=True)
    contato_operacional_nome = db.Column(db.String(255), nullable=True)
    contato_operacional_email = db.Column(db.String(255), nullable=True)
    contato_operacional_telefone = db.Column(db.String(20), nullable=True)

    # --- Controle ---
    # Nunca apagamos uma conta: marcamos como arquivada.
    arquivado = db.Column(db.Boolean, nullable=False, default=False, index=True)
    criado_em = db.Column(db.DateTime(timezone=True), default=_agora)
    atualizado_em = db.Column(db.DateTime(timezone=True), default=_agora,
                              onupdate=_agora)

    def __repr__(self) -> str:
        return f"<Cliente {self.conta_id} {self.nome_fantasia!r}>"

    @property
    def cnpj_formatado(self) -> str | None:
        return formatar_cnpj(self.cnpj)

    # Campos que os formulários preenchem (nomes iguais aos dos inputs no HTML).
    CAMPOS_FORM = (
        "nome_fantasia", "cnpj", "razao_social", "confianca_identificacao",
        "cidade", "segmento", "origem", "triagem_ifood", "nota_ifood",
        "avaliacoes_ifood", "rede_independencia", "unidades", "marcas",
        "canais", "faturamento_estimado", "fonte_faturamento", "gatilho",
        "plano_contratado", "data_inicio",
        "responsavel", "status", "observacoes",
    )

    def para_dict(self) -> dict:
        """Devolve os campos do formulário como dicionário, para pré-preencher
        o formulário de edição."""
        return {c: getattr(self, c) for c in self.CAMPOS_FORM}

    @property
    def eh_cliente_ativo(self) -> bool:
        """Verdadeiro quando a conta já virou cliente ativo (recebido pela
        Operação), ou seja, status 'Liberado p/ Setup'."""
        from app import domain
        return self.status == domain.STATUS_CLIENTE_ATIVO

    @property
    def plano_info(self) -> dict | None:
        """Dados do plano contratado (setup, mensalidade, fidelidade), puxados
        da tabela de preços."""
        from app import domain
        return domain.produto_por_nome(self.plano_contratado)

    @property
    def fim_fidelidade(self):
        """Data em que acaba a fidelidade (início + meses do plano, padrão 6)."""
        if not self.data_inicio:
            return None
        from app import domain
        info = self.plano_info
        meses = info["fidelidade_meses"] if info else 6
        return domain.somar_meses(self.data_inicio, meses)
