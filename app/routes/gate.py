"""
Rotas do Gate — Ficha de Passagem (Fase 7).

Rotas:
  GET/POST /contas/<id>/gate  -> checklist dos 8 itens do gate
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import domain
from app.repositories import clientes, gates

bp = Blueprint("gate", __name__)


@bp.before_request
@login_required
def _exigir_login():
    pass


@bp.route("/contas/<int:id>/gate", methods=["GET", "POST"])
def gate(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    gate_obj = gates.buscar_por_cliente(cliente.id)

    if request.method == "POST":
        dados = {}
        for i in range(1, 9):
            dados[f"item_{i}"] = "1" in request.form.getlist(f"item_{i}")
            dados[f"obs_{i}"] = (request.form.get(f"obs_{i}") or "").strip() or None

        gate_obj = gates.criar_ou_atualizar(cliente.id, dados)

        itens = gate_obj.itens_marcados
        qtd = sum(1 for m in itens if m)

        if gate_obj.liberado:
            if cliente.status != "Liberado p/ Setup":
                clientes.alterar_status(cliente, "Liberado p/ Setup")
                flash(f"Gate completo! {cliente.conta_id} liberada para Setup. "
                      f"A Operação pode receber o cliente.", "ok")
            else:
                flash(f"Gate de {cliente.conta_id} atualizado ({qtd}/8).", "ok")
        else:
            flash(f"Gate de {cliente.conta_id} salvo ({qtd}/8 itens confirmados). "
                  f"Faltam {8 - qtd} para liberar.", "ok")

        return redirect(url_for("gate.gate", id=cliente.id))

    valores = {}
    if gate_obj:
        for i in range(1, 9):
            valores[f"item_{i}"] = getattr(gate_obj, f"item_{i}")
            valores[f"obs_{i}"] = getattr(gate_obj, f"obs_{i}") or ""

    return render_template("gate/checklist.html", cliente=cliente,
                           gate_itens=domain.GATE_ITENS, valores=valores,
                           gate_obj=gate_obj)
