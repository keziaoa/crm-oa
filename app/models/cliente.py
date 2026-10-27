"""
Modelo Cliente — a conta comercial (uma hamburgueria).

Decisões pensando na integração futura com o cohab-control:
- O CNPJ é o identificador único "de verdade" do cliente (chave de negócio),
  além do Conta ID legível (CT-001, CT-002...).
- CNPJ é guardado SÓ com números (14 dígitos), sem pontos/barra/traço, para
  casar com o cohab-control sem ambiguidade. Há um campo auxiliar para exibir
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
    # Conta ID legível usado no dia a dia (CT-001). Único.
    conta_id = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # CNPJ só com dígitos (14). Identificador único de negócio e chave de
    # integração com o cohab-control. Pode ser nulo enquanto a conta ainda
    # está em pesquisa (CNPJ a confirmar), mas quando preenchido é único.
    cnpj = db.Column(db.String(14), unique=True, nullable=True, index=True)

    razao_social = db.Column(db.String(255), nullable=True)
    nome_fantasia = db.Column(db.String(255), nullable=False)  # Empresa / Marca

    # --- Contatos padronizados ---
    contato_financeiro_nome = db.Column(db.String(255), nullable=True)
    contato_financeiro_email = db.Column(db.String(255), nullable=True)
    contato_financeiro_telefone = db.Column(db.String(20), nullable=True)

    contato_operacional_nome = db.Column(db.String(255), nullable=True)
    contato_operacional_email = db.Column(db.String(255), nullable=True)
    contato_operacional_telefone = db.Column(db.String(20), nullable=True)

    # --- Controle ---
    criado_em = db.Column(db.DateTime(timezone=True), default=_agora)
    atualizado_em = db.Column(db.DateTime(timezone=True), default=_agora,
                              onupdate=_agora)

    def __repr__(self) -> str:
        return f"<Cliente {self.conta_id} {self.nome_fantasia!r}>"

    @property
    def cnpj_formatado(self) -> str | None:
        return formatar_cnpj(self.cnpj)
