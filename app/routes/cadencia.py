"""
Rotas da Cadência de prospecção (Fase 5).

Rotas:
  GET  /cadencia                     -> painel de cadências ativas
  POST /cadencia/<id>/iniciar        -> inicia cadência para uma conta
  POST /cadencia/<cad_id>/contato    -> registra contato D0/D3/D7/D12
  POST /cadencia/<cad_id>/respondeu  -> marca que o decisor respondeu
  POST /cadencia/<cad_id>/encerrar   -> encerra cadência (vai para Nutrição)
"""
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import domain
from app.repositories import cadencias, clientes

bp = Blueprint("cadencia", __name__, url_prefix="/cadencia")


@bp.before_request
@login_required
def _exigir_login():
    pass


@bp.route("/")
def painel():
    lista = cadencias.listar_ativas()
    return render_template("cadencia/painel.html", cadencias_ativas=lista,
                           hoje=date.today())


@bp.route("/<int:id>/iniciar", methods=["POST"])
def iniciar(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    data_d0_str = request.form.get("data_d0", "").strip()
    if data_d0_str:
        try:
            data_d0 = date.fromisoformat(data_d0_str)
        except ValueError:
            flash("Data D0 inválida.", "erro")
            return redirect(url_for("contas.detalhe", id=id))
    else:
        data_d0 = date.today()

    if cliente.status != "Em Cadência":
        clientes.alterar_status(cliente, "Em Cadência")

    cad = cadencias.iniciar(cliente.id, data_d0)
    flash(f"Cadência iniciada para {cliente.conta_id} — D0 em "
          f"{data_d0.strftime('%d/%m/%Y')}.", "ok")
    return redirect(url_for("cadencia.detalhe", cad_id=cad.id))


@bp.route("/<int:cad_id>")
def detalhe(cad_id):
    from app.models.cadencia import Cadencia
    cad = Cadencia.query.get_or_404(cad_id)
    contatos = cad.datas_previstas()
    return render_template("cadencia/detalhe.html", cad=cad, cliente=cad.cliente,
                           contatos=contatos, hoje=date.today())


@bp.route("/<int:cad_id>/contato", methods=["POST"])
def registrar_contato(cad_id):
    from app.models.cadencia import Cadencia
    cad = Cadencia.query.get_or_404(cad_id)

    if not cad.ativa:
        flash("Esta cadência já foi encerrada.", "erro")
        return redirect(url_for("cadencia.detalhe", cad_id=cad_id))

    contato = (request.form.get("contato") or "").strip().lower()
    obs = (request.form.get("obs") or "").strip() or None

    if contato not in Cadencia.CONTATOS:
        flash("Contato inválido.", "erro")
        return redirect(url_for("cadencia.detalhe", cad_id=cad_id))

    cadencias.registrar_contato(cad, contato, date.today(), obs)

    rotulo = contato.upper()
    flash(f"Contato {rotulo} registrado.", "ok")
    return redirect(url_for("cadencia.detalhe", cad_id=cad_id))


@bp.route("/<int:cad_id>/respondeu", methods=["POST"])
def respondeu(cad_id):
    from app.models.cadencia import Cadencia
    cad = Cadencia.query.get_or_404(cad_id)

    cadencias.marcar_respondeu(cad)

    cliente = cad.cliente
    if cliente.status == "Em Cadência":
        clientes.alterar_status(cliente, "Qualificado")

    flash(f"{cliente.conta_id} respondeu! Conta movida para \"Qualificado\".", "ok")
    return redirect(url_for("contas.detalhe", id=cliente.id))


@bp.route("/<int:cad_id>/encerrar", methods=["POST"])
def encerrar(cad_id):
    from app.models.cadencia import Cadencia
    cad = Cadencia.query.get_or_404(cad_id)

    motivo = (request.form.get("motivo") or "").strip() or "Sem resposta na cadência"
    cadencias.encerrar(cad, motivo)

    cliente = cad.cliente
    if cliente.status == "Em Cadência":
        clientes.alterar_status(cliente, "Nutrição (60 dias)")

    flash(f"Cadência de {cliente.conta_id} encerrada. Conta movida para \"Nutrição (60 dias)\".", "ok")
    return redirect(url_for("contas.detalhe", id=cliente.id))
