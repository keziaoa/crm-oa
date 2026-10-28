"""
Rotas de Pós-venda (Fase 8).

Rotas:
  GET       /pos-venda               -> painel de clientes ativos
  GET/POST  /contas/<id>/pos-venda   -> marcos e saúde da conta
  POST      /contas/<id>/pos-venda/marco/<num>  -> registrar um marco
"""
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import domain
from app.repositories import clientes, pos_vendas

bp = Blueprint("pos_venda", __name__)


@bp.before_request
@login_required
def _exigir_login():
    pass


@bp.route("/pos-venda")
def painel():
    """Painel com todos os clientes ativos e seus marcos."""
    todos = clientes.listar(visao="ativos")
    registros = []
    hoje = date.today()
    for c in todos:
        pv = pos_vendas.buscar_por_cliente(c.id)
        marcos = None
        proximo = None
        if c.data_inicio:
            marcos = domain.datas_pos_venda(c.data_inicio)
            for i, m in enumerate(marcos):
                num = i + 1
                st = pv.status_marco(num) if pv else "Pendente"
                m["status"] = st
                m["atrasado"] = (st in ("Pendente", "Agendado")
                                 and m["data_prevista"] < hoje)
                if not proximo and st in ("Pendente", "Agendado"):
                    proximo = m
        registros.append({
            "cliente": c,
            "pos_venda": pv,
            "marcos": marcos,
            "proximo": proximo,
        })

    return render_template("pos_venda/painel.html", registros=registros,
                           hoje=hoje)


@bp.route("/contas/<int:id>/pos-venda", methods=["GET", "POST"])
def detalhe(id):
    """Detalhe dos marcos de pós-venda de uma conta."""
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    if not cliente.data_inicio:
        flash("Esta conta ainda não tem data de início (kickoff). "
              "Preencha na edição da conta.", "erro")
        return redirect(url_for("contas.detalhe", id=id))

    pv = pos_vendas.buscar_por_cliente(cliente.id)

    if request.method == "POST":
        dados = {}
        nova_saude = (request.form.get("saude") or "").strip()
        if nova_saude:
            dados["saude"] = nova_saude

        pv = pos_vendas.criar_ou_atualizar(cliente.id, dados)
        flash(f"Saúde de {cliente.conta_id} atualizada para {pv.saude}.", "ok")
        return redirect(url_for("pos_venda.detalhe", id=id))

    marcos = domain.datas_pos_venda(cliente.data_inicio)
    hoje = date.today()
    for i, m in enumerate(marcos):
        num = i + 1
        if pv:
            m["status"] = pv.status_marco(num)
            m["data_realizado"] = getattr(pv, f"marco_{num}_data_realizado")
            m["obs"] = getattr(pv, f"marco_{num}_obs") or ""
        else:
            m["status"] = "Pendente"
            m["data_realizado"] = None
            m["obs"] = ""
        m["atrasado"] = (m["status"] in ("Pendente", "Agendado")
                         and m["data_prevista"] < hoje)

    return render_template("pos_venda/detalhe.html", cliente=cliente,
                           marcos=marcos, pv=pv, hoje=hoje,
                           opcoes_saude=domain.LISTAS["saude"],
                           opcoes_marco=domain.LISTAS["marco"])


@bp.route("/contas/<int:id>/pos-venda/marco/<int:num>", methods=["POST"])
def registrar_marco(id, num):
    """Registrar status de um marco específico."""
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    if num < 1 or num > 5:
        abort(400)

    novo_status = (request.form.get("status") or "").strip()
    if novo_status not in domain.LISTAS["marco"]:
        flash("Status inválido.", "erro")
        return redirect(url_for("pos_venda.detalhe", id=id))

    obs = (request.form.get("obs") or "").strip() or None

    dados = {f"marco_{num}_status": novo_status, f"marco_{num}_obs": obs}
    if novo_status == "Realizado":
        dados[f"marco_{num}_data_realizado"] = date.today()
    elif novo_status in ("Pendente", "Agendado"):
        dados[f"marco_{num}_data_realizado"] = None

    pos_vendas.criar_ou_atualizar(cliente.id, dados)

    nome_marco = domain.MARCOS_POS_VENDA[num - 1]["nome"]
    flash(f"Marco {nome_marco} de {cliente.conta_id} → {novo_status}.", "ok")
    return redirect(url_for("pos_venda.detalhe", id=id))
