"""
Telas de cadastro de contas (Fase 1).

Rotas:
  GET  /contas                 -> lista com busca e filtros
  GET  /contas/nova            -> formulário de nova conta
  POST /contas/nova            -> cria a conta
  GET  /contas/<id>            -> detalhe da conta
  GET  /contas/<id>/editar     -> formulário de edição
  POST /contas/<id>/editar     -> salva a edição
  POST /contas/<id>/arquivar   -> arquiva (nunca apaga)
  POST /contas/<id>/desarquivar-> reativa uma conta arquivada
"""
from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, url_for)

from app import domain
from app.models.cliente import Cliente, so_digitos
from app.repositories import clientes

bp = Blueprint("contas", __name__, url_prefix="/contas")


# ----------------------------------------------------------------------------
# Helpers para ler o formulário com segurança
# ----------------------------------------------------------------------------
def _texto(form, campo):
    valor = (form.get(campo) or "").strip()
    return valor or None


def _inteiro(form, campo):
    bruto = (form.get(campo) or "").strip()
    # aceita "180.000" ou "180000"
    bruto = bruto.replace(".", "").replace(" ", "")
    return int(bruto) if bruto.isdigit() else None


def _decimal(form, campo):
    bruto = (form.get(campo) or "").strip().replace(",", ".")
    if not bruto:
        return None
    try:
        return float(bruto)
    except ValueError:
        return None


def _data(form, campo):
    """Lê uma data de um campo <input type=date> (formato AAAA-MM-DD)."""
    from datetime import date
    bruto = (form.get(campo) or "").strip()
    if not bruto:
        return None
    try:
        return date.fromisoformat(bruto)
    except ValueError:
        return None


def _ler_form(form) -> dict:
    """Lê todos os campos do formulário e devolve um dicionário pronto para o
    modelo, já convertendo números."""
    return {
        "nome_fantasia": _texto(form, "nome_fantasia"),
        "cnpj": _texto(form, "cnpj"),
        "razao_social": _texto(form, "razao_social"),
        "confianca_identificacao": _texto(form, "confianca_identificacao"),
        "cidade": _texto(form, "cidade"),
        "segmento": _texto(form, "segmento"),
        "origem": _texto(form, "origem"),
        "triagem_ifood": _texto(form, "triagem_ifood"),
        "nota_ifood": _decimal(form, "nota_ifood"),
        "avaliacoes_ifood": _inteiro(form, "avaliacoes_ifood"),
        "rede_independencia": _texto(form, "rede_independencia"),
        "unidades": _inteiro(form, "unidades"),
        "marcas": _inteiro(form, "marcas"),
        "canais": _texto(form, "canais"),
        "faturamento_estimado": _inteiro(form, "faturamento_estimado"),
        "fonte_faturamento": _texto(form, "fonte_faturamento"),
        "gatilho": _texto(form, "gatilho"),
        "plano_contratado": _texto(form, "plano_contratado"),
        "data_inicio": _data(form, "data_inicio"),
        "responsavel": _texto(form, "responsavel"),
        "status": _texto(form, "status") or "Pesquisa",
        "observacoes": _texto(form, "observacoes"),
    }


def _validar(dados, cliente_atual=None) -> list[str]:
    """Devolve a lista de erros (vazia = tudo certo)."""
    erros = []
    if not dados.get("nome_fantasia"):
        erros.append("O nome da empresa / marca é obrigatório.")

    # CNPJ: se preenchido, precisa ter 14 dígitos e ser único.
    cnpj = so_digitos(dados.get("cnpj"))
    if dados.get("cnpj") and (cnpj is None or len(cnpj) != 14):
        erros.append("O CNPJ deve ter 14 dígitos (ex.: 12.225.988/0001-76).")
    elif cnpj:
        existente = clientes.buscar_por_cnpj(cnpj)
        if existente and (cliente_atual is None or existente.id != cliente_atual.id):
            erros.append(f"Já existe uma conta com este CNPJ ({existente.conta_id} — "
                         f"{existente.nome_fantasia}).")

    nota = dados.get("nota_ifood")
    if nota is not None and not (0 <= nota <= 5):
        erros.append("A nota do iFood deve ficar entre 0 e 5.")
    return erros


def _contexto_form():
    """Dados comuns que os formulários precisam (as listas suspensas)."""
    return {"listas": domain.LISTAS}


# ----------------------------------------------------------------------------
# Lista de contas
# ----------------------------------------------------------------------------
@bp.route("/")
def lista():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    prioridade = request.args.get("prioridade", "").strip()
    cidade = request.args.get("cidade", "").strip()
    arquivadas = request.args.get("arquivadas") == "1"
    visao = request.args.get("visao", "").strip()  # "", "ativos" ou "prospeccao"

    contas = clientes.listar(
        q=q or None, status=status or None, prioridade=prioridade or None,
        cidade=cidade or None, incluir_arquivadas=arquivadas,
        visao=visao or None,
    )
    return render_template(
        "contas/lista.html",
        contas=contas,
        q=q, status=status, prioridade=prioridade, cidade=cidade,
        arquivadas=arquivadas, visao=visao,
        total_ativos=clientes.contar_ativos(),
        status_opcoes=domain.STATUS_NOMES,
        prioridade_opcoes=domain.PRIORIDADES,
        cidades=clientes.cidades(),
        status_tipo=domain.STATUS_TIPO,
    )


# ----------------------------------------------------------------------------
# Nova conta
# ----------------------------------------------------------------------------
@bp.route("/nova", methods=["GET", "POST"])
def nova():
    if request.method == "POST":
        dados = _ler_form(request.form)
        erros = _validar(dados)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("contas/form.html", valores=dados,
                                   modo="nova", **_contexto_form())
        cliente = clientes.criar(dados)
        flash(f"Conta {cliente.conta_id} criada com sucesso.", "ok")
        return redirect(url_for("contas.detalhe", id=cliente.id))

    # GET: formulário em branco, com um Conta ID de prévia.
    return render_template("contas/form.html", valores={}, modo="nova",
                           proximo_id=clientes.proximo_conta_id(),
                           **_contexto_form())


# ----------------------------------------------------------------------------
# Detalhe
# ----------------------------------------------------------------------------
@bp.route("/<int:id>")
def detalhe(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)
    return render_template("contas/detalhe.html", c=cliente,
                           status_tipo=domain.STATUS_TIPO,
                           status_fase=domain.STATUS_FASE)


# ----------------------------------------------------------------------------
# Editar
# ----------------------------------------------------------------------------
@bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    if request.method == "POST":
        dados = _ler_form(request.form)
        erros = _validar(dados, cliente_atual=cliente)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("contas/form.html", valores=dados,
                                   modo="editar", cliente=cliente,
                                   **_contexto_form())
        clientes.atualizar(cliente, dados)
        flash(f"Conta {cliente.conta_id} atualizada.", "ok")
        return redirect(url_for("contas.detalhe", id=cliente.id))

    return render_template("contas/form.html", valores=cliente.para_dict(),
                           modo="editar", cliente=cliente, **_contexto_form())


# ----------------------------------------------------------------------------
# Arquivar / Desarquivar (nunca apagar)
# ----------------------------------------------------------------------------
@bp.route("/<int:id>/arquivar", methods=["POST"])
def arquivar(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)
    clientes.arquivar(cliente)
    flash(f"Conta {cliente.conta_id} arquivada. Ela não aparece mais na lista, "
          f"mas continua guardada.", "ok")
    return redirect(url_for("contas.detalhe", id=cliente.id))


@bp.route("/<int:id>/desarquivar", methods=["POST"])
def desarquivar(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)
    clientes.desarquivar(cliente)
    flash(f"Conta {cliente.conta_id} reativada.", "ok")
    return redirect(url_for("contas.detalhe", id=cliente.id))
