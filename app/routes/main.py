"""
Páginas principais do CRM.

Nesta Fase 0 existe apenas a página inicial, que confirma que o sistema está
no ar e mostra um resumo das regras já configuradas. As telas de verdade
(cadastro, funil, qualificação etc.) entram nas próximas fases.
"""
from flask import Blueprint, current_app, render_template
from flask_login import login_required

from app import domain
from app.repositories import clientes

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def index():
    return render_template(
        "index.html",
        total_clientes=clientes.contar(),
        status_funil=domain.STATUS_FUNIL,
        criterios=domain.CRITERIOS_QUALIFICACAO,
        cadencia=domain.CADENCIA_DIAS_UTEIS,
        gate_itens=domain.GATE_ITENS,
        marcos=domain.MARCOS_POS_VENDA,
        produtos=domain.PRODUTOS,
        icp=domain.ICP,
        cores=current_app.config["BRAND_COLORS"],
    )
