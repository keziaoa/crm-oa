"""
Rotas de Diagnóstico e Proposta (Fase 6).

Rotas:
  GET/POST /contas/<id>/diagnostico           -> ficha de diagnóstico
  GET      /contas/<id>/diagnostico/ver       -> ver diagnóstico preenchido
  GET/POST /contas/<id>/proposta/nova         -> gerar proposta
  GET      /contas/<id>/proposta/<pid>        -> ver proposta
  POST     /contas/<id>/proposta/<pid>/enviar -> marcar como enviada
"""
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import domain
from app.repositories import clientes, diagnosticos, propostas

bp = Blueprint("diagnostico", __name__)


@bp.before_request
@login_required
def _exigir_login():
    pass


# --------------------------------------------------------------------------
# Diagnóstico
# --------------------------------------------------------------------------
@bp.route("/contas/<int:id>/diagnostico", methods=["GET", "POST"])
def diagnostico(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    diag = diagnosticos.buscar_por_cliente(cliente.id)

    if request.method == "POST":
        dados = {}
        for bloco in domain.BLOCOS_DIAGNOSTICO:
            campo = f"bloco_{bloco['chave']}"
            dados[campo] = (request.form.get(campo) or "").strip() or None

        data_str = (request.form.get("data_reuniao") or "").strip()
        if data_str:
            try:
                dados["data_reuniao"] = date.fromisoformat(data_str)
            except ValueError:
                pass

        dados["produto_recomendado"] = (request.form.get("produto_recomendado") or "").strip() or None
        dados["exclusoes"] = (request.form.get("exclusoes") or "").strip() or None
        dados["observacoes"] = (request.form.get("observacoes") or "").strip() or None

        diag = diagnosticos.criar_ou_atualizar(cliente.id, dados)

        if cliente.status == "Diagnóstico Agendado":
            clientes.alterar_status(cliente, "Diagnóstico Realizado")

        flash(f"Diagnóstico de {cliente.conta_id} salvo ({diag.blocos_preenchidos}/10 blocos).", "ok")
        return redirect(url_for("diagnostico.ver_diagnostico", id=cliente.id))

    valores = {}
    if diag:
        for campo in diag.CAMPOS_BLOCOS:
            valores[campo] = getattr(diag, campo) or ""
        valores["data_reuniao"] = diag.data_reuniao
        valores["produto_recomendado"] = diag.produto_recomendado or ""
        valores["exclusoes"] = diag.exclusoes or ""
        valores["observacoes"] = diag.observacoes or ""

    return render_template("diagnostico/form.html", cliente=cliente,
                           blocos=domain.BLOCOS_DIAGNOSTICO,
                           valores=valores, planos=domain.PLANOS)


@bp.route("/contas/<int:id>/diagnostico/ver")
def ver_diagnostico(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    diag = diagnosticos.buscar_por_cliente(cliente.id)
    if not diag:
        flash("Ainda não há diagnóstico para esta conta.", "erro")
        return redirect(url_for("diagnostico.diagnostico", id=id))

    blocos_valores = {c: getattr(diag, c) or "" for c in diag.CAMPOS_BLOCOS}
    return render_template("diagnostico/ver.html", cliente=cliente, diag=diag,
                           blocos=domain.BLOCOS_DIAGNOSTICO,
                           blocos_valores=blocos_valores,
                           produtos=domain.PRODUTOS)


# --------------------------------------------------------------------------
# Proposta
# --------------------------------------------------------------------------
@bp.route("/contas/<int:id>/proposta/nova", methods=["GET", "POST"])
def nova_proposta(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    if request.method == "POST":
        produto_nome = (request.form.get("produto") or "").strip()
        produto = domain.produto_por_nome(produto_nome)
        if not produto:
            flash("Selecione um produto válido.", "erro")
            return redirect(url_for("diagnostico.nova_proposta", id=id))

        lojas = int(request.form.get("lojas_extra") or 0)
        marcas_ = int(request.form.get("marcas_extra") or 0)

        mensalidade_base = produto["mensalidade"]
        setup_base = produto["setup"] or 0

        adicional_loja = domain.produto_por_nome("Adicional loja extra")
        adicional_marca = domain.produto_por_nome("Adicional marca extra")

        mensal_lojas = (adicional_loja["mensalidade"] * lojas) if adicional_loja else 0
        mensal_marcas = (adicional_marca["mensalidade"] * marcas_) if adicional_marca else 0

        valor_total_mensal = mensalidade_base + mensal_lojas + mensal_marcas
        valor_setup_total = setup_base

        data_envio_str = (request.form.get("data_envio") or "").strip()
        data_envio = None
        data_validade = None
        if data_envio_str:
            try:
                data_envio = date.fromisoformat(data_envio_str)
                data_validade = domain.proximos_contatos(data_envio, [10])[0][1]
            except (ValueError, IndexError):
                pass

        obs = (request.form.get("observacoes") or "").strip() or None
        status_prop = "Enviada" if data_envio else "Rascunho"

        prop = propostas.criar({
            "cliente_id": cliente.id,
            "produto": produto_nome,
            "setup": produto["setup"],
            "mensalidade": mensalidade_base,
            "fidelidade_meses": produto["fidelidade_meses"],
            "lojas_extra": lojas,
            "marcas_extra": marcas_,
            "valor_total_mensal": valor_total_mensal,
            "valor_setup_total": valor_setup_total,
            "data_envio": data_envio,
            "data_validade": data_validade,
            "status": status_prop,
            "observacoes": obs,
        })

        if data_envio and cliente.status in ("Diagnóstico Realizado", "Diagnóstico Agendado"):
            clientes.alterar_status(cliente, "Proposta Enviada")

        flash(f"Proposta #{prop.id} criada para {cliente.conta_id} "
              f"({produto_nome}, R$ {valor_total_mensal:,.0f}/mês).", "ok")
        return redirect(url_for("diagnostico.ver_proposta", id=cliente.id, pid=prop.id))

    diag = diagnosticos.buscar_por_cliente(cliente.id)
    return render_template("diagnostico/proposta_form.html", cliente=cliente,
                           produtos=domain.PRODUTOS, regras=domain.REGRAS_PROPOSTA,
                           diag=diag)


@bp.route("/contas/<int:id>/proposta/<int:pid>")
def ver_proposta(id, pid):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    prop = propostas.buscar_por_id(pid)
    if not prop or prop.cliente_id != cliente.id:
        abort(404)

    return render_template("diagnostico/proposta_ver.html", cliente=cliente,
                           prop=prop, regras=domain.REGRAS_PROPOSTA)


@bp.route("/contas/<int:id>/proposta/<int:pid>/enviar", methods=["POST"])
def enviar_proposta(id, pid):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    prop = propostas.buscar_por_id(pid)
    if not prop or prop.cliente_id != cliente.id:
        abort(404)

    hoje = date.today()
    data_validade = domain.proximos_contatos(hoje, [10])[0][1]

    prop.data_envio = hoje
    prop.data_validade = data_validade
    propostas.atualizar_status(prop, "Enviada", hoje)

    if cliente.status in ("Diagnóstico Realizado", "Diagnóstico Agendado"):
        clientes.alterar_status(cliente, "Proposta Enviada")

    flash(f"Proposta #{prop.id} marcada como enviada. "
          f"Válida até {data_validade.strftime('%d/%m/%Y')}.", "ok")
    return redirect(url_for("diagnostico.ver_proposta", id=id, pid=pid))
