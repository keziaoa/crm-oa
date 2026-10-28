"""
Painel de Indicadores (Fase 9).

Rota:
  GET /painel -> resumo automático do funil, prioridades, conversões,
                 por responsável e por origem.
"""
from flask import Blueprint, render_template
from flask_login import login_required

from app import domain
from app.repositories import cadencias, clientes, pos_vendas

bp = Blueprint("painel", __name__, url_prefix="/painel")


@bp.before_request
@login_required
def _exigir_login():
    pass


@bp.route("/")
def index():
    ind = clientes.indicadores()

    cad_ativas = cadencias.contar_ativas()

    pv_lista = pos_vendas.listar_ativos()
    saude_counts = {"Verde": 0, "Amarelo": 0, "Vermelho": 0}
    for pv in pv_lista:
        if "Verde" in pv.saude:
            saude_counts["Verde"] += 1
        elif "Amarelo" in pv.saude:
            saude_counts["Amarelo"] += 1
        else:
            saude_counts["Vermelho"] += 1

    status_funil_contagem = []
    for ordem, nome, fase, tipo in domain.STATUS_FUNIL:
        status_funil_contagem.append({
            "ordem": ordem,
            "nome": nome,
            "fase": fase,
            "tipo": tipo,
            "qtd": ind["por_status"].get(nome, 0),
        })

    pipeline_total = sum(s["qtd"] for s in status_funil_contagem if s["tipo"] == "pipeline")

    conversoes = _calcular_conversoes(ind["por_status"])

    return render_template(
        "painel/painel.html",
        ind=ind,
        cad_ativas=cad_ativas,
        saude_counts=saude_counts,
        status_funil_contagem=status_funil_contagem,
        pipeline_total=pipeline_total,
        conversoes=conversoes,
        prioridades=domain.PRIORIDADES,
    )


def _calcular_conversoes(por_status: dict) -> list[dict]:
    """Calcula taxas de conversão entre estágios-chave do funil."""
    etapas = [
        ("Pesquisa → Em Cadência",
         ["Pesquisa", "Verificar Rede", "Qualificar Porte", "Encontrar Decisor"],
         ["Em Cadência", "Qualificado", "Diagnóstico Agendado",
          "Diagnóstico Realizado", "Proposta Enviada", "Proposta Aceita",
          "Contrato Enviado", "Contrato Assinado", "Pagamento Confirmado",
          "Liberado p/ Setup"]),
        ("Em Cadência → Qualificado",
         ["Em Cadência"],
         ["Qualificado", "Diagnóstico Agendado", "Diagnóstico Realizado",
          "Proposta Enviada", "Proposta Aceita", "Contrato Enviado",
          "Contrato Assinado", "Pagamento Confirmado", "Liberado p/ Setup"]),
        ("Qualificado → Diagnóstico",
         ["Qualificado", "Diagnóstico Agendado"],
         ["Diagnóstico Realizado", "Proposta Enviada", "Proposta Aceita",
          "Contrato Enviado", "Contrato Assinado", "Pagamento Confirmado",
          "Liberado p/ Setup"]),
        ("Proposta → Fechamento",
         ["Proposta Enviada", "Proposta Aceita"],
         ["Contrato Enviado", "Contrato Assinado", "Pagamento Confirmado",
          "Liberado p/ Setup"]),
    ]
    resultado = []
    for nome, origens, destinos in etapas:
        total_origem = sum(por_status.get(s, 0) for s in origens)
        total_destino = sum(por_status.get(s, 0) for s in destinos)
        total = total_origem + total_destino
        taxa = (total_destino / total * 100) if total > 0 else 0
        resultado.append({
            "nome": nome,
            "origem": total_origem,
            "destino": total_destino,
            "total": total,
            "taxa": taxa,
        })
    return resultado
